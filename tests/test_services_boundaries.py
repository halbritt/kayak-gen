"""Regression: enforce architectural dependency direction for services.

Per ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`` Phase 3D:

- ``kayakgen.services`` imports nothing from ``ui`` or ``cli``. Services
  are the orchestration layer between evaluators / search / model and the
  surfaces that consume them; pulling a surface module into a service
  would invert the dependency direction and is forbidden.

This mirrors the structure of ``tests/test_import_boundaries.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KAYAKGEN_ROOT = REPO_ROOT / "kayakgen"


def _is_kayakgen_subpackage_import(module: str) -> str | None:
    """Return the top-level kayakgen subpackage of an import, or ``None``."""
    if not module:
        return None
    parts = module.split(".")
    if parts[0] != "kayakgen":
        return None
    if len(parts) == 1:
        return None
    return parts[1]


def _imports_from_module(path: Path) -> list[tuple[str, str | None]]:
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


@pytest.mark.parametrize("path", _python_files_under("services"))
def test_services_does_not_import_ui_or_cli(path: Path) -> None:
    forbidden = {"ui", "cli"}
    for module, name in _imports_from_module(path):
        sub = _is_kayakgen_subpackage_import(module)
        if sub is not None:
            assert sub not in forbidden, (
                f"{path.relative_to(REPO_ROOT)} imports from kayakgen.{sub} "
                f"(module={module!r}, name={name!r}); services layer must not."
            )


def test_services_subpackage_exists() -> None:
    assert (KAYAKGEN_ROOT / "services").is_dir(), (
        "kayakgen/services/ is missing; Phase 3D services migration not applied"
    )
