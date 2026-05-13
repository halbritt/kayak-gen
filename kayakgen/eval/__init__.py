"""kayakgen.eval — pure functions Hull → projected read models."""

from kayakgen.eval.calibration import ResistanceSourceRecord, default_resistance_source_registry
from kayakgen.eval.contract import EvaluationResult, ResistanceCurve
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import (
    evaluate_resistance,
    resistance_curve,
    viscous_resistance,
    wave_resistance_michell,
)

__all__ = [
    "EvaluationResult",
    "Hydrostatics",
    "ResistanceCurve",
    "ResistanceSourceRecord",
    "default_resistance_source_registry",
    "evaluate_hydrostatics",
    "evaluate_resistance",
    "resistance_curve",
    "viscous_resistance",
    "wave_resistance_michell",
]
