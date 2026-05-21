"""High-angle GZ result schemas and heel-grid helpers.

These types extend the canonical ``GZCurve`` contract with the generated-body
metadata fields required by RFC 0043. They live in their own module so the
heeled-section integrator and the public evaluator can import them without
pulling in the rest of the stability package.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import math
from typing import Literal

from pydantic import Field, model_validator

from kayakgen.eval.contract import GZCurve, GZHeelPointMetadata
from kayakgen.eval.stability.accepted_fit import StabilityFitRecord
from kayakgen.model.hull import Hull

DEFAULT_GZ_HEEL_GRID_DEG: tuple[float, ...] = tuple(float(angle) for angle in range(0, 95, 5))
GZ_HEEL_GRID_MIN_DEG = 0.0
GZ_HEEL_GRID_MAX_DEG = 90.0
AnalyticalClaimLabel = Literal[
    "unvalidated_hydrostatic_comparison",
    "validated_hydrostatic_comparison",
]


class GZNotImplementedError(NotImplementedError):
    """Raised when high-angle stability is requested before its RFC lands."""


class GeneratedBodyGZCurve(GZCurve):
    """RFC 0043 fixed-trim generated-body result subtype.

    The canonical ``GZCurve`` contract owns the additive generated-body
    metadata fields so this subtype can round-trip through public stability
    result serialization.
    """

    method: Literal[
        "generated_body_handoff",
        "fixture_only_math",
        "fixed_trim_generated_body_v1",
    ] = "fixed_trim_generated_body_v1"
    heel_point_metadata: list[GZHeelPointMetadata] = Field(default_factory=list)
    summary_semantics: Literal["grid_bounded"] = "grid_bounded"
    result_semantics: AnalyticalClaimLabel = "unvalidated_hydrostatic_comparison"

    @model_validator(mode="after")
    def _metadata_matches_availability(self) -> "GeneratedBodyGZCurve":
        if self.status == "computed" and len(self.heel_point_metadata) != len(
            self.heel_deg
        ):
            raise ValueError("computed generated-body GZ metadata must align with heel_deg")
        return self


def resolve_analytical_claim_label(
    hull: Hull,
    fit_registry: Iterable[StabilityFitRecord],
) -> AnalyticalClaimLabel:
    """Resolve the RFC 0058 analytical high-angle GZ comparison label."""

    hull_class = getattr(hull, "hull_class", None)
    hull_design_hash = _hull_design_hash(hull)
    if not isinstance(hull_class, str) or not isinstance(hull_design_hash, str):
        return "unvalidated_hydrostatic_comparison"

    for record in fit_registry:
        if record.acceptance_verdict != "accepted":
            continue
        scope = record.hull_family_scope
        if scope.hull_class != hull_class:
            continue
        if hull_design_hash in scope.design_hash_envelope:
            return "validated_hydrostatic_comparison"
    return "unvalidated_hydrostatic_comparison"


def _hull_design_hash(hull: Hull) -> str | None:
    design_hash = getattr(hull, "design_hash", None)
    if callable(design_hash):
        return design_hash()
    if isinstance(design_hash, str):
        return design_hash
    return None


def _normalize_heel_grid(heel_grid_deg: Sequence[float] | None) -> list[float]:
    grid = (
        list(DEFAULT_GZ_HEEL_GRID_DEG)
        if heel_grid_deg is None
        else [float(value) for value in heel_grid_deg]
    )
    if not grid:
        raise ValueError("heel_grid_deg must contain at least one angle")
    for value in grid:
        if not math.isfinite(value):
            raise ValueError("heel_grid_deg must contain only finite values")
        if value < GZ_HEEL_GRID_MIN_DEG or value > GZ_HEEL_GRID_MAX_DEG:
            raise ValueError("heel_grid_deg values must be between 0 and 90 degrees")
    for left, right in zip(grid, grid[1:], strict=False):
        if right <= left:
            raise ValueError("heel_grid_deg must be strictly increasing")
    return grid
