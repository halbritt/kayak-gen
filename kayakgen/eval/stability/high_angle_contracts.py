"""High-angle GZ result schemas and heel-grid helpers.

These types extend the canonical ``GZCurve`` contract with the generated-body
metadata fields required by RFC 0043. They live in their own module so the
heeled-section integrator and the public evaluator can import them without
pulling in the rest of the stability package.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Literal

from pydantic import Field, model_validator

from kayakgen.eval.contract import GZCurve, GZHeelPointMetadata

DEFAULT_GZ_HEEL_GRID_DEG: tuple[float, ...] = tuple(float(angle) for angle in range(0, 95, 5))
GZ_HEEL_GRID_MIN_DEG = 0.0
GZ_HEEL_GRID_MAX_DEG = 90.0


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
    result_semantics: Literal["unvalidated_hydrostatic_comparison"] = (
        "unvalidated_hydrostatic_comparison"
    )

    @model_validator(mode="after")
    def _metadata_matches_availability(self) -> "GeneratedBodyGZCurve":
        if self.status == "computed" and len(self.heel_point_metadata) != len(
            self.heel_deg
        ):
            raise ValueError("computed generated-body GZ metadata must align with heel_deg")
        return self


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
