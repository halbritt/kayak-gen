"""Regression: enforce architectural dependency direction.

Per `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md` Phase 2:

- ``kayakgen.model`` imports nothing from ``eval``, ``search``, ``ui``, or ``cli``.
- ``kayakgen.eval`` imports nothing from ``ui`` or ``cli``.
- ``kayakgen.search`` imports nothing from ``ui`` or ``cli``.
- ``kayakgen.cli`` and ``kayakgen.ui`` may import services/read models, not
  private evaluator helpers.

The first three rules are the load-bearing ones. The fourth is harder to
mechanically enforce; we check the simple direction (no private-name reach-in
from CLI/UI into internal-only evaluator helpers via underscore-prefixed
imports).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KAYAKGEN_ROOT = REPO_ROOT / "kayakgen"

PACKAGES = ("model", "eval", "search", "ui", "cli")


def _is_kayakgen_subpackage_import(module: str) -> str | None:
    """Return the top-level kayakgen subpackage (e.g. ``"eval"``) of an import
    that targets ``kayakgen.<sub>...``; None if the import does not target
    kayakgen at all.
    """
    if not module:
        return None
    parts = module.split(".")
    if parts[0] != "kayakgen":
        return None
    if len(parts) == 1:
        return None
    return parts[1]


def _imports_from_module(path: Path) -> list[tuple[str, str | None]]:
    """Return list of (module, name) imports from a Python source file.

    ``module`` is the dotted module string (post-resolution for ``from X
    import Y``). ``name`` is the imported name (or None for bare ``import X``).
    """
    text = path.read_text()
    tree = ast.parse(text, filename=str(path))
    out: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue
            module = node.module or ""
            for alias in node.names:
                out.append((module, alias.name))
    return out


def _python_files_under(subpackage: str) -> list[Path]:
    root = KAYAKGEN_ROOT / subpackage
    if not root.is_dir():
        return []
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


# ---------------------------------------------------------------------------
# Rule 1: kayakgen.model imports nothing from eval / search / ui / cli.


@pytest.mark.parametrize("path", _python_files_under("model"))
def test_model_does_not_import_eval_search_ui_or_cli(path: Path) -> None:
    forbidden = {"eval", "search", "ui", "cli"}
    for module, name in _imports_from_module(path):
        sub = _is_kayakgen_subpackage_import(module)
        if sub is not None:
            assert sub not in forbidden, (
                f"{path.relative_to(REPO_ROOT)} imports from kayakgen.{sub} "
                f"(module={module!r}, name={name!r}); model layer must not."
            )


# ---------------------------------------------------------------------------
# Rule 2: kayakgen.eval imports nothing from ui / cli.


@pytest.mark.parametrize("path", _python_files_under("eval"))
def test_eval_does_not_import_ui_or_cli(path: Path) -> None:
    forbidden = {"ui", "cli"}
    for module, name in _imports_from_module(path):
        sub = _is_kayakgen_subpackage_import(module)
        if sub is not None:
            assert sub not in forbidden, (
                f"{path.relative_to(REPO_ROOT)} imports from kayakgen.{sub} "
                f"(module={module!r}, name={name!r}); eval layer must not."
            )


# ---------------------------------------------------------------------------
# Rule 3: kayakgen.search imports nothing from ui / cli.


@pytest.mark.parametrize("path", _python_files_under("search"))
def test_search_does_not_import_ui_or_cli(path: Path) -> None:
    forbidden = {"ui", "cli"}
    for module, name in _imports_from_module(path):
        sub = _is_kayakgen_subpackage_import(module)
        if sub is not None:
            assert sub not in forbidden, (
                f"{path.relative_to(REPO_ROOT)} imports from kayakgen.{sub} "
                f"(module={module!r}, name={name!r}); search layer must not."
            )


# ---------------------------------------------------------------------------
# Rule 4: cli/ui must not reach into private (underscore-prefixed) evaluator
# helpers. Public adapters and read models are fine.


@pytest.mark.parametrize("layer", ("cli", "ui"))
def test_layer_does_not_import_private_evaluator_helpers(layer: str) -> None:
    offenders: list[str] = []
    for path in _python_files_under(layer):
        for module, name in _imports_from_module(path):
            sub = _is_kayakgen_subpackage_import(module)
            if sub != "eval":
                continue
            if name is None:
                continue
            if name.startswith("_"):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)} imports private "
                    f"{name!r} from {module!r}"
                )
    assert not offenders, "private-helper reach-ins found:\n  " + "\n  ".join(offenders)


# ---------------------------------------------------------------------------
# Sanity: every kayakgen.<sub> we test must actually exist (no silent skips).


def test_every_referenced_subpackage_exists() -> None:
    missing = [s for s in PACKAGES if not (KAYAKGEN_ROOT / s).is_dir()]
    assert not missing, f"missing referenced subpackages: {missing}"
