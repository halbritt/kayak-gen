"""JSON round-trip for Hull and EvaluationResult artifacts."""

from __future__ import annotations

from pathlib import Path

from kayakgen.eval.contract import EvaluationResult
from kayakgen.model.hull import Hull


def load_hull(path: str | Path) -> Hull:
    return Hull.model_validate_json(Path(path).read_text())


def save_hull(hull: Hull, path: str | Path) -> None:
    Path(path).write_text(hull.model_dump_json(indent=2))


def save_evaluation(result: EvaluationResult, path: str | Path) -> None:
    Path(path).write_text(result.model_dump_json(indent=2))
