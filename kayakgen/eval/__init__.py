"""kayakgen.eval — pure functions Hull → projected read models."""

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics

__all__ = ["EvaluationResult", "Hydrostatics", "evaluate_hydrostatics"]
