"""kayakgen.model — Hull aggregate and HullGeometry value objects."""

from kayakgen.model.classes import CLASSES, KayakClass, Range, get_class, list_classes
from kayakgen.model.geometry import HullGeometry, LoftedHullGeometry
from kayakgen.model.hull import Hull

__all__ = [
    "CLASSES",
    "Hull",
    "HullGeometry",
    "KayakClass",
    "LoftedHullGeometry",
    "Range",
    "get_class",
    "list_classes",
]
