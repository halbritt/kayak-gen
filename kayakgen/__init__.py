"""kayakgen — parametric kayak hull generator and evaluation pipeline."""

from kayakgen.model.hull import Hull
from kayakgen.model.geometry import HullGeometry, LoftedHullGeometry

__all__ = ["Hull", "HullGeometry", "LoftedHullGeometry"]
__version__ = "0.1.0"
