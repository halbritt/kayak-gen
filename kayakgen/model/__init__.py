"""kayakgen.model — Hull aggregate and HullGeometry value objects."""

from kayakgen.model.advisory import DesignAdvisory, design_advisory
from kayakgen.model.classes import CLASSES, KayakClass, Range, get_class, list_classes
from kayakgen.model.geometry import HullGeometry, LoftedHullGeometry
from kayakgen.model.hull import Hull

__all__ = [
    "CLASSES",
    "DesignAdvisory",
    "Hull",
    "HullGeometry",
    "KayakClass",
    "LoftedHullGeometry",
    "Range",
    "design_advisory",
    "get_class",
    "list_classes",
]
