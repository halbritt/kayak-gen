"""JSON round-trip for Hull and EvaluationResult artifacts."""

from __future__ import annotations

import os
from pathlib import Path

from kayakgen.eval.contract import EvaluationResult
from kayakgen.model.hull import Hull


def write_text_atomic(path: Path, text: str, *, newline: str | None = None) -> None:
    """Write ``text`` to ``path`` via a temp sibling + ``os.replace``.

    Audit R9 (2026-06-06): the previous bare ``write_text`` could leave a
    torn file behind a crash and used the locale's default encoding. The
    payload is written with explicit utf-8 to a dot-prefixed temp sibling
    and atomically renamed into place; the emitted JSON text itself is
    unchanged (``model_dump_json(indent=2)``), so saved artifacts stay
    byte-identical.
    """

    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8", newline=newline)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def load_hull(path: str | Path) -> Hull:
    return Hull.model_validate_json(Path(path).read_text(encoding="utf-8"))


def save_hull(hull: Hull, path: str | Path) -> None:
    write_text_atomic(Path(path), hull.model_dump_json(indent=2))


def save_evaluation(result: EvaluationResult, path: str | Path) -> None:
    write_text_atomic(Path(path), result.model_dump_json(indent=2))
