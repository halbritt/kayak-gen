"""kayakgen.model — Hull aggregate and HullGeometry value objects."""

from kayakgen.model.advisory import DesignAdvisory, design_advisory
from kayakgen.model.classes import CLASSES, KayakClass, Range, get_class, list_classes
from kayakgen.model.geometry import HullGeometry, LoftedHullGeometry
from kayakgen.model.hull import Hull
from kayakgen.model.validity import (
    DesignValidityFinding,
    DesignValidityReport,
    design_warning_messages,
    evaluate_design_validity,
)

__all__ = [
    "CLASSES",
    "DesignAdvisory",
    "DesignValidityFinding",
    "DesignValidityReport",
    "Hull",
    "HullGeometry",
    "KayakClass",
    "LoftedHullGeometry",
    "Range",
    "design_advisory",
    "design_warning_messages",
    "evaluate_design_validity",
    "get_class",
    "list_classes",
]
