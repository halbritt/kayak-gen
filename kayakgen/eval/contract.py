"""EvaluationResult — the integration object that joins evaluator outputs."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kayakgen.eval.claims import (
    ACCEPTED_USE_COMPARATIVE_FILTER,
    ClaimState,
    RawUnvalidatedClaimFields,
    ResistanceFitStatus,
    SerializedResistanceFitStatus,
    UNCALIBRATED_COMPARATIVE,
    uncalibrated_resistance_warnings,
)
from kayakgen.eval.hydrostatics import Hydrostatics
from kayakgen.eval.turning import TurningMetrics
from kayakgen.model.validity import DesignValidityReport


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
    fit_status: SerializedResistanceFitStatus | None = None
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


class ResistanceFitRecord(BaseModel):
    """RFC 0027 fit-state record for calibrated resistance models."""

    model_config = ConfigDict(extra="forbid")

    model_version: str
    fit_status: ResistanceFitStatus
    calibration_fixture_ids: list[str] = Field(default_factory=list)
    validation_fixture_ids: list[str] = Field(default_factory=list)
    fitted_parameters: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    residuals_ref: str | None = None
    validity_envelope: dict[str, Any] = Field(default_factory=dict)
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


class GZHeelPointMetadata(BaseModel):
    """Per-heel convergence and clipping metadata for generated-body GZ."""

    model_config = ConfigDict(extra="forbid")

    heel_deg: float
    status: Literal["computed", "non_converged", "skipped"]
    sinkage_m: float | None = None
    displaced_mass_kg: float | None = None
    displacement_residual_kg: float | None = None
    displacement_iterations: int = Field(ge=0)
    displacement_max_iterations: int = Field(ge=0)
    trim_angle_deg: float = 0.0
    longitudinal_moment_residual_kg_m: float | None = None
    clipping_status: Literal["computed", "failed", "skipped"]
    warnings: list[str] = Field(default_factory=list)

    @field_validator(
        "heel_deg",
        "sinkage_m",
        "displaced_mass_kg",
        "displacement_residual_kg",
        "trim_angle_deg",
        "longitudinal_moment_residual_kg_m",
    )
    @classmethod
    def _finite_or_none(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("GZ heel metadata values must be finite when present")
        return value


class GZCurve(BaseModel):
    """RFC 0024 high-angle GZ read model with explicit availability state.

    Legacy two-field curves are intentionally not accepted here: a GZ curve
    without body provenance can be a plotting artifact, but it is not kayak
    secondary-stability evidence.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    status: Literal["unavailable", "computed"] = "unavailable"
    method: Literal[
        "generated_body_handoff",
        "fixture_only_math",
        "fixed_trim_generated_body_v1",
    ] = "generated_body_handoff"
    fixture_only: bool = False
    body_ref: str | None = None
    body_type: str | None = None
    body_diagnostic_ref: str | None = None
    heel_grid_deg: list[float] = Field(default_factory=list)
    heel_deg: list[float] = Field(default_factory=list)
    gz_m: list[float] = Field(default_factory=list)
    righting_moment_nm: list[float] = Field(default_factory=list)
    max_gz_m: float | None = None
    heel_at_max_gz_deg: float | None = None
    range_positive_stability_deg: float | None = None
    area_under_positive_gz_m_deg: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    heel_point_metadata: list[GZHeelPointMetadata] = Field(default_factory=list)
    summary_semantics: Literal["grid_bounded"] | None = None
    result_semantics: Literal[
        "unvalidated_hydrostatic_comparison",
        "validated_hydrostatic_comparison",
    ] | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_legacy_minimal_curve(cls, data: Any) -> Any:
        if isinstance(data, dict) and "angles_deg" in data:
            raise ValueError(
                "legacy GZCurve angles_deg/gz_m data lacks RFC 0024 body provenance"
            )
        return data

    @field_validator(
        "heel_grid_deg",
        "heel_deg",
        "gz_m",
        "righting_moment_nm",
    )
    @classmethod
    def _curve_values_must_be_finite(cls, values: list[float]) -> list[float]:
        for value in values:
            if not math.isfinite(value):
                raise ValueError("GZ curve arrays must contain only finite values")
        return values

    @field_validator(
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
        "area_under_positive_gz_m_deg",
    )
    @classmethod
    def _summary_values_must_be_finite_or_none(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("GZ summary metrics must be finite when present")
        return value

    @model_validator(mode="after")
    def _availability_matches_payload(self) -> "GZCurve":
        if len(self.heel_deg) != len(self.gz_m) or len(self.gz_m) != len(
            self.righting_moment_nm
        ):
            raise ValueError("heel_deg, gz_m, and righting_moment_nm must align")

        summary_values = (
            self.max_gz_m,
            self.heel_at_max_gz_deg,
            self.range_positive_stability_deg,
            self.area_under_positive_gz_m_deg,
        )
        if self.status == "unavailable":
            if self.heel_deg or self.gz_m or self.righting_moment_nm:
                raise ValueError("unavailable GZ results must not contain curve values")
            if any(value is not None for value in summary_values):
                raise ValueError("unavailable GZ results must not contain summary metrics")
        else:
            if not self.heel_deg:
                raise ValueError("computed GZ results must contain at least one heel point")
            if self.body_type == "explicit_synthetic_triangle_mesh" and not self.fixture_only:
                raise ValueError("synthetic GZ results must be marked fixture_only")
            if self.method == "fixed_trim_generated_body_v1" and len(
                self.heel_point_metadata
            ) != len(self.heel_deg):
                raise ValueError(
                    "computed generated-body GZ metadata must align with heel_deg"
                )
        return self


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


class ConvergenceFlag(BaseModel):
    """RFC 0052 value object: per-evaluator-stage convergence status.

    Emitted additively on :class:`EvaluationResult` so designers can tell
    whether the upright trim solve converged, the per-heel GZ solve hit its
    residual, or the resistance/mesh-diagnostics stage simply ran. The
    ``residual`` field is the numeric driver of the convergence check when one
    exists (e.g. ``displacement_error_kg`` or ``moment_error_kg_m``); it is
    ``None`` for stages that do not iterate (resistance, mesh diagnostics).
    """

    model_config = ConfigDict(extra="forbid")

    stage: str
    status: Literal["converged", "not_converged", "iteration_cap"]
    residual: float | None = None

    @field_validator("residual")
    @classmethod
    def _residual_must_be_finite_or_none(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("ConvergenceFlag.residual must be finite when present")
        return value


def _flags_from_stability(stability: StabilityResult) -> list[ConvergenceFlag]:
    """Derive convergence flags from a stability result's iteration metadata."""
    flags: list[ConvergenceFlag] = []
    if stability.method == "design_waterline_initial":
        return flags

    iterations = stability.equilibrium_iterations
    max_iterations = stability.equilibrium_max_iterations
    if (
        iterations is not None
        and max_iterations is not None
        and iterations >= max_iterations
        and stability.status != "converged"
    ):
        upright_status: Literal["converged", "not_converged", "iteration_cap"] = (
            "iteration_cap"
        )
    elif stability.status == "converged":
        upright_status = "converged"
    else:
        upright_status = "not_converged"
    flags.append(
        ConvergenceFlag(
            stage="upright_equilibrium",
            status=upright_status,
            residual=stability.displacement_error_kg,
        )
    )

    if stability.method == "equilibrium_trim":
        trim_residual = stability.moment_error_kg_m
        if (
            iterations is not None
            and max_iterations is not None
            and iterations >= max_iterations
            and stability.status != "converged"
        ):
            trim_status: Literal["converged", "not_converged", "iteration_cap"] = (
                "iteration_cap"
            )
        elif stability.status == "converged":
            trim_status = "converged"
        else:
            trim_status = "not_converged"
        flags.append(
            ConvergenceFlag(
                stage="trim_equilibrium",
                status=trim_status,
                residual=trim_residual,
            )
        )

    if stability.gz_curve is not None and stability.gz_curve.heel_point_metadata:
        for point in stability.gz_curve.heel_point_metadata:
            if point.status == "computed":
                point_status: Literal[
                    "converged", "not_converged", "iteration_cap"
                ] = "converged"
            elif (
                point.displacement_iterations >= point.displacement_max_iterations
                and point.displacement_max_iterations > 0
            ):
                point_status = "iteration_cap"
            else:
                point_status = "not_converged"
            flags.append(
                ConvergenceFlag(
                    stage=f"evaluate_gz_curve@{point.heel_deg:g}deg",
                    status=point_status,
                    residual=point.displacement_residual_kg,
                )
            )
    return flags


class EvaluationResult(BaseModel):
    """Read-side join of evaluator outputs sharing a single hull."""

    model_config = ConfigDict(extra="forbid")

    hull_hash: str
    hydrostatics: Hydrostatics
    resistance: ResistanceCurve | None = None
    stability: StabilityResult | None = None
    cfd: CfdResult | None = None
    turning_metrics: TurningMetrics | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
    design_validity: DesignValidityReport = Field(default_factory=DesignValidityReport)
    convergence: list[ConvergenceFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _populate_convergence(self) -> "EvaluationResult":
        """Auto-emit RFC 0052 convergence flags from the evaluator outputs.

        Additive — runs only when ``convergence`` is empty so callers that
        explicitly pass a list (including a deserialized record) keep the
        round-trip identity ``EvaluationResult.model_validate(
        original.model_dump_json()) == original``.
        """

        if self.convergence:
            return self

        flags: list[ConvergenceFlag] = [
            ConvergenceFlag(stage="hydrostatics", status="converged", residual=None)
        ]
        if self.resistance is not None:
            flags.append(
                ConvergenceFlag(stage="resistance", status="converged", residual=None)
            )
        if self.stability is not None:
            flags.extend(_flags_from_stability(self.stability))
        # ``mesh_diagnostics`` is reported as a single converged entry whenever
        # an EvaluationResult is materialized with a mesh-bearing CFD record.
        # The default ``kayakgen evaluate`` flow does not attach mesh
        # diagnostics, so this entry only appears when the consumer wires it.
        self.convergence = flags
        return self
