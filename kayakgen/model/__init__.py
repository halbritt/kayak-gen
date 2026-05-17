"""kayakgen.model — Hull aggregate and HullGeometry value objects."""

from kayakgen.model.advisory import DesignAdvisory, design_advisory
from kayakgen.model.classes import CLASSES, KayakClass, Range, get_class, list_classes
from kayakgen.model.distribution_v2 import (
    CrossSectionFamily,
    DistributionV2Spec,
    KeyPointsDistribution,
    LongitudinalDistribution,
    PolynomialDistribution,
    UniformDistribution,
)
from kayakgen.model.geometry import (
    DistributionV2Geometry,
    HullGeometry,
    LoftedHullGeometry,
)
from kayakgen.model.hull import Hull
from kayakgen.model.validity import (
    DesignValidityFinding,
    DesignValidityReport,
    design_warning_messages,
    evaluate_design_validity,
)

__all__ = [
    "CLASSES",
    "CrossSectionFamily",
    "DesignAdvisory",
    "DesignValidityFinding",
    "DesignValidityReport",
    "DistributionV2Geometry",
    "DistributionV2Spec",
    "Hull",
    "HullGeometry",
    "KayakClass",
    "KeyPointsDistribution",
    "LoftedHullGeometry",
    "LongitudinalDistribution",
    "PolynomialDistribution",
    "Range",
    "UniformDistribution",
    "design_advisory",
    "design_warning_messages",
    "evaluate_design_validity",
    "get_class",
    "list_classes",
]
