"""EvaluationResult — the integration object that joins evaluator outputs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.hydrostatics import Hydrostatics


class ResistanceMetadata(BaseModel):
    """Provenance and validity warnings for resistance curves."""

    model_config = ConfigDict(extra="forbid")

    model_family: str = "raw_ittc_michell"
    calibration_status: str = "uncalibrated"
    accepted_use: list[str] = Field(default_factory=lambda: ["comparative_filter"])
    verification_fixtures: list[str] = Field(default_factory=list)
    constants: dict[str, float] = Field(default_factory=dict)
    quadrature: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ResistanceCurve(BaseModel):
    """Resistance sweep with explicit model provenance."""

    model_config = ConfigDict(extra="forbid")

    V_knots: list[float]
    Fn: list[float]
    Rv_N: list[float]
    Rw_N: list[float]
    Rt_N: list[float]
    metadata: ResistanceMetadata = Field(default_factory=ResistanceMetadata)


class GZCurve(BaseModel):
    """Reserved for a future stability evaluator."""

    model_config = ConfigDict(extra="forbid")

    angles_deg: list[float]
    gz_m: list[float]


class LoadCase(BaseModel):
    """Serializable design-waterline load case for initial stability."""

    model_config = ConfigDict(extra="forbid")

    name: str = "default"
    paddler_mass_kg: float = Field(default=85.0, ge=0)
    hull_mass_kg: float = Field(default=18.0, ge=0)
    cargo_mass_kg: float = Field(default=0.0, ge=0)
    kg_above_keel_m: float = Field(default=0.25, ge=0)
    seawater_density_kg_m3: float = Field(default=1025.0, gt=0)

    @property
    def total_mass_kg(self) -> float:
        return self.paddler_mass_kg + self.hull_mass_kg + self.cargo_mass_kg


class StabilityResult(BaseModel):
    """Initial-stability read model; high-angle GZ remains explicitly reserved."""

    model_config = ConfigDict(extra="forbid")

    load_case: LoadCase = Field(default_factory=LoadCase)
    method: Literal["design_waterline_initial"] = "design_waterline_initial"
    status: Literal["computed", "not_implemented"] = "computed"
    initial_GM0_m: float | None = None
    load_mass_kg: float
    displaced_mass_kg: float
    displacement_error_kg: float
    warnings: list[str] = Field(default_factory=list)
    gz_curve: GZCurve | None = None


class CfdResult(BaseModel):
    """Reserved for the heavy-CFD tier (RFC 0008 §6 job stub)."""

    model_config = ConfigDict(extra="forbid")

    solver: str
    drag_N: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Read-side join of evaluator outputs sharing a single hull."""

    model_config = ConfigDict(extra="forbid")

    hull_hash: str
    hydrostatics: Hydrostatics
    resistance: ResistanceCurve | None = None
    stability: StabilityResult | None = None
    cfd: CfdResult | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
