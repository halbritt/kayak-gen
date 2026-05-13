"""EvaluationResult — the integration object that joins evaluator outputs."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kayakgen.eval.claims import (
    ACCEPTED_USE_COMPARATIVE_FILTER,
    ClaimState,
    RawUnvalidatedClaimFields,
    UNCALIBRATED_COMPARATIVE,
    uncalibrated_resistance_warnings,
)
from kayakgen.eval.hydrostatics import Hydrostatics


class ResistanceMetadata(BaseModel):
    """Provenance and validity warnings for resistance curves."""

    model_config = ConfigDict(extra="forbid")

    claim_state: ClaimState = UNCALIBRATED_COMPARATIVE
    accepted_uses: list[str] = Field(
        default_factory=lambda: [ACCEPTED_USE_COMPARATIVE_FILTER]
    )
    calibration_fixture_ids: list[str] = Field(default_factory=list)
    validation_fixture_ids: list[str] = Field(default_factory=list)
    model_version: str | None = None
    fit_status: str | None = None
    fit_metrics: dict[str, float] = Field(default_factory=dict)
    validity_envelope: dict[str, Any] | None = None
    model_family: str = "raw_ittc_michell"
    calibration_status: str = "uncalibrated"
    calibration_name: str | None = None
    calibration_version: str | None = None
    valid_fn_range: tuple[float, float] | None = None
    valid_l_b_range: tuple[float, float] | None = None
    source_citation: str | None = None
    source_license: str | None = None
    extraction_method: str | None = None
    accepted_use: list[str] = Field(
        default_factory=lambda: [ACCEPTED_USE_COMPARATIVE_FILTER]
    )
    verification_fixtures: list[str] = Field(default_factory=list)
    constants: dict[str, float] = Field(default_factory=dict)
    quadrature: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=uncalibrated_resistance_warnings)

    @model_validator(mode="before")
    @classmethod
    def _sync_legacy_claim_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "accepted_uses" not in normalized and "accepted_use" in normalized:
            normalized["accepted_uses"] = normalized["accepted_use"]
        if "accepted_use" not in normalized and "accepted_uses" in normalized:
            normalized["accepted_use"] = normalized["accepted_uses"]
        if "model_version" not in normalized and "calibration_version" in normalized:
            normalized["model_version"] = normalized["calibration_version"]
        if "calibration_version" not in normalized and "model_version" in normalized:
            normalized["calibration_version"] = normalized["model_version"]
        return normalized

    @model_validator(mode="after")
    def _aliases_must_match(self) -> "ResistanceMetadata":
        if self.accepted_use != self.accepted_uses:
            raise ValueError("accepted_use and accepted_uses must match")
        if self.calibration_version != self.model_version:
            raise ValueError("calibration_version and model_version must match")
        return self


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


class LongitudinalLoadComponent(BaseModel):
    """One mass component for upright trim equilibrium.

    The longitudinal coordinate follows the mesh package convention:
    ``x_m < 0`` is forward toward the bow and ``x_m > 0`` is aft toward the
    stern.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    mass_kg: float = Field(ge=0)
    x_m: float = 0.0
    kg_above_keel_m: float | None = Field(default=None, ge=0)

    @field_validator("mass_kg", "x_m", "kg_above_keel_m")
    @classmethod
    def _finite_or_none(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("load component values must be finite")
        return value


class LoadCase(BaseModel):
    """Serializable design-waterline load case for initial stability."""

    model_config = ConfigDict(extra="forbid")

    name: str = "default"
    paddler_mass_kg: float = Field(default=85.0, ge=0)
    hull_mass_kg: float = Field(default=18.0, ge=0)
    cargo_mass_kg: float = Field(default=0.0, ge=0)
    kg_above_keel_m: float = Field(default=0.25, ge=0)
    kg_reference: Literal["keel", "waterline", "seat"] = "keel"
    kg_reference_value_m: float | None = None
    seat_height_above_keel_m: float | None = Field(default=None, ge=0)
    seawater_density_kg_m3: float = Field(default=1025.0, gt=0)
    components: list[LongitudinalLoadComponent] = Field(default_factory=list)

    @property
    def total_mass_kg(self) -> float:
        if self.components:
            return sum(component.mass_kg for component in self.components)
        return self.paddler_mass_kg + self.hull_mass_kg + self.cargo_mass_kg

    @property
    def uses_longitudinal_components(self) -> bool:
        return bool(self.components)

    def kg_above_keel_for_draft(self, draft_m: float) -> float:
        """Normalize the user-facing KG reference to a keel/baseline height."""
        if draft_m <= 0:
            raise ValueError("draft_m must be positive")
        if self.kg_reference_value_m is None:
            return self.kg_above_keel_m
        if self.kg_reference == "keel":
            if self.kg_reference_value_m < 0:
                raise ValueError("keel-referenced KG must be nonnegative")
            return self.kg_reference_value_m
        if self.kg_reference == "waterline":
            return draft_m + self.kg_reference_value_m
        if self.seat_height_above_keel_m is None:
            raise ValueError("seat-referenced KG requires seat_height_above_keel_m")
        return self.seat_height_above_keel_m + self.kg_reference_value_m

    def normalized_components(self, draft_m: float) -> list[LongitudinalLoadComponent]:
        """Return explicit components, expanding compact legacy fields if needed."""
        default_kg = self.kg_above_keel_for_draft(draft_m)
        if self.components:
            return [
                component.model_copy(
                    update={
                        "kg_above_keel_m": (
                            component.kg_above_keel_m
                            if component.kg_above_keel_m is not None
                            else default_kg
                        )
                    }
                )
                for component in self.components
            ]
        return [
            LongitudinalLoadComponent(
                name="paddler",
                mass_kg=self.paddler_mass_kg,
                x_m=0.0,
                kg_above_keel_m=default_kg,
            ),
            LongitudinalLoadComponent(
                name="hull",
                mass_kg=self.hull_mass_kg,
                x_m=0.0,
                kg_above_keel_m=default_kg,
            ),
            LongitudinalLoadComponent(
                name="cargo",
                mass_kg=self.cargo_mass_kg,
                x_m=0.0,
                kg_above_keel_m=default_kg,
            ),
        ]

    def load_lcg_m_for_draft(self, draft_m: float) -> float:
        components = self.normalized_components(draft_m)
        total = sum(component.mass_kg for component in components)
        if total <= 0:
            raise ValueError("load case total mass must be positive")
        return sum(component.mass_kg * component.x_m for component in components) / total

    def load_kg_above_keel_m_for_draft(self, draft_m: float) -> float:
        components = self.normalized_components(draft_m)
        total = sum(component.mass_kg for component in components)
        if total <= 0:
            raise ValueError("load case total mass must be positive")
        return (
            sum(
                component.mass_kg * float(component.kg_above_keel_m)
                for component in components
            )
            / total
        )


class StabilityResult(BaseModel):
    """Initial-stability read model; high-angle GZ remains explicitly reserved."""

    model_config = ConfigDict(extra="forbid")

    load_case: LoadCase = Field(default_factory=LoadCase)
    method: Literal[
        "design_waterline_initial",
        "equilibrium_sinkage",
        "equilibrium_trim",
    ] = "design_waterline_initial"
    status: Literal["computed", "converged", "not_converged", "not_implemented"] = "computed"
    initial_GM0_m: float | None = None
    load_mass_kg: float
    displaced_mass_kg: float
    displacement_error_kg: float
    draft_at_midship_m: float | None = Field(default=None, gt=0)
    equilibrium_draft_m: float | None = Field(default=None, gt=0)
    sinkage_m: float | None = None
    trim_angle_deg: float | None = None
    load_lcg_m: float | None = None
    buoyancy_lcb_m: float | None = None
    moment_error_kg_m: float | None = None
    moment_tolerance_kg_m: float | None = Field(default=None, gt=0)
    equilibrium_tolerance_kg: float | None = Field(default=None, gt=0)
    equilibrium_iterations: int | None = Field(default=None, ge=0)
    equilibrium_max_iterations: int | None = Field(default=None, ge=1)
    warnings: list[str] = Field(default_factory=list)
    gz_curve: GZCurve | None = None


class CfdResult(RawUnvalidatedClaimFields):
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
