"""Bounded no-rerun guards for evaluator functions in consumer tests.

Parser and report tests replace evaluator functions with raising stubs to prove
that saved results are read, not recomputed. A module that runs
``from kayakgen.eval.x import f`` while such a stub is installed keeps the stub
in its own namespace after the source module is restored. Later real
evaluations through that consumer then fail far from the guard that caused it
(retrospective E16: operating-equilibrium tests hit a stale
``immersed_geometry`` stub after ``test_recorded_method_binding.py`` ran first).

``forbid_evaluator_calls`` keeps that from happening:

1. It imports every guarded module and every declared consumer *before* any
   stub is installed, so the declared ``from``-imports bind the real functions.
2. It records every stub call, even when the raised ``AssertionError`` is
   swallowed or wrapped (pydantic turns validator ``AssertionError`` into
   ``ValidationError``). Callers keep a strict ``guard.calls == []`` assertion.
3. On exit it restores the originals, then inspects the guarded modules, the
   declared consumers and only the modules first imported while the guard was
   active. Any module-level binding still holding a stub is repaired to the
   real function and reported as an ``AssertionError``.

The leak check covers module-level bindings, the shape ``from x import f``
creates. It does not walk every loaded module, and it does not search closures,
containers or default arguments. Use plain ``monkeypatch`` for single-module
patches that cannot leak; use this helper whenever a guard covers functions that
other modules import by name.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable


@dataclass
class EvaluatorGuard:
    """Observed effects of one :func:`forbid_evaluator_calls` window."""

    calls: list[str] = field(default_factory=list)
    leaks: list[str] = field(default_factory=list)


def _stub(qualified_name: str, calls: list[str]) -> Callable[..., Any]:
    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        calls.append(qualified_name)
        raise AssertionError("parser reran evaluator: " + qualified_name)

    forbidden.__qualname__ = "forbidden[" + qualified_name + "]"
    return forbidden


def _captured_stubs(
    modules: Mapping[str, ModuleType], originals: Mapping[int, tuple[str, Any]]
) -> list[tuple[ModuleType, str, str, str, Any]]:
    found = []
    for module_name in sorted(modules):
        module = modules[module_name]
        for attr, value in list(vars(module).items()):
            entry = originals.get(id(value))
            if entry is not None:
                found.append((module, module_name, attr, *entry))
    return found


@contextmanager
def forbid_evaluator_calls(
    targets: Mapping[str, Sequence[str]],
    *,
    consumers: Sequence[str] = (),
) -> Iterator[EvaluatorGuard]:
    """Replace ``targets`` functions with recording stubs for one window.

    ``targets`` maps a module name to the function names to forbid there.
    ``consumers`` names extra modules that import those functions by name; they
    are preloaded so their aliases bind the real functions.
    """
    guard = EvaluatorGuard()
    preloaded = {
        name: importlib.import_module(name) for name in (*targets, *consumers)
    }
    installed: list[tuple[ModuleType, str, Any]] = []
    # id(stub) -> (qualified evaluator name, real function). ``stubs`` keeps each
    # stub alive through the leak scan, so no other object can reuse its id.
    originals: dict[int, tuple[str, Any]] = {}
    stubs: list[Callable[..., Any]] = []
    before = set(sys.modules)
    try:
        for module_name, names in targets.items():
            module = preloaded[module_name]
            for name in names:
                original = getattr(module, name)
                stub = _stub(module_name + "." + name, guard.calls)
                stubs.append(stub)
                originals[id(stub)] = (module_name + "." + name, original)
                installed.append((module, name, original))
                setattr(module, name, stub)
        yield guard
    finally:
        for module, name, original in reversed(installed):
            setattr(module, name, original)
        inspected = dict(preloaded)
        for name in set(sys.modules) - before:
            module = sys.modules.get(name)
            if isinstance(module, ModuleType):
                inspected[name] = module
        for module, module_name, attr, evaluator, original in _captured_stubs(
            inspected, originals
        ):
            setattr(module, attr, original)
            guard.leaks.append(module_name + "." + attr + " -> " + evaluator)
    if guard.leaks:
        raise AssertionError(
            "evaluator guard leaked stub aliases (repaired): " + ", ".join(guard.leaks)
        )
