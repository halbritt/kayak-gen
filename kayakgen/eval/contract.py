"""EvaluationResult — the integration object that joins evaluator outputs."""

from __future__ import annotations

import math
import hashlib
import json
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


class NumericalObservation(BaseModel):
    """One actually evaluated resolution, including bounded failed observations."""

    model_config = ConfigDict(extra="forbid")
    resolution: dict[str, int]
    total_resistance_N: list[float | None]
    seconds: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _finite_observation(self) -> "NumericalObservation":
        if not self.resolution or any(n <= 0 for n in self.resolution.values()):
            raise ValueError("numerical resolutions must contain positive sample counts")
        if any(x is not None and not math.isfinite(x) for x in self.total_resistance_N):
            raise ValueError("numerical observations must be finite or explicitly unavailable")
        return self


class NumericalSurfaceObservation(BaseModel):
    """Actual wetted-area refinement and its per-speed viscous contribution."""

    model_config = ConfigDict(extra="forbid")
    stations: int = Field(ge=3)
    wetted_surface_m2: float = Field(ge=0, allow_inf_nan=False)
    viscous_resistance_N: list[float]
    seconds: float = Field(ge=0, allow_inf_nan=False)

    @field_validator("viscous_resistance_N")
    @classmethod
    def _finite_viscous_values(cls, values: list[float]) -> list[float]:
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("numerical viscous observations must be finite and nonnegative")
        return values


class ResistanceComparisonInputs(BaseModel):
    """Actual assessment inputs and the shared physical comparison conditions."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    speeds_knots: list[float]
    hull_length_m: float = Field(gt=0, allow_inf_nan=False)
    density_kg_m3: float = Field(gt=0, allow_inf_nan=False)
    kinematic_viscosity_m2_s: float = Field(gt=0, allow_inf_nan=False)
    gravity_m_s2: float = Field(gt=0, allow_inf_nan=False)
    numerical_method_version: str = Field(min_length=1)
    model_family: str = Field(min_length=1)
    calibration_model_version: str | None = None

    @field_validator("speeds_knots")
    @classmethod
    def _finite_speeds(cls, speeds: list[float]) -> list[float]:
        if not speeds or any(not math.isfinite(v) or v < 0 for v in speeds):
            raise ValueError("comparison speeds must be finite and nonnegative")
        return speeds

    def comparison_key(self) -> tuple[Any, ...]:
        # Length is bound for Froude checking, but different-length hulls may
        # legitimately be compared at the same physical speeds and fluid.
        return (tuple(self.speeds_knots), self.density_kg_m3,
                self.kinematic_viscosity_m2_s, self.gravity_m_s2,
                self.numerical_method_version, self.model_family,
                self.calibration_model_version)


class NumericalQuality(BaseModel):
    """Resolution evidence, independent of calibration and physical validity."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    status: Literal["unknown", "converged", "not_converged"] = "unknown"
    policy_version: str | None = None
    resolutions: list[dict[str, int]] = Field(default_factory=list)
    relative_changes: list[float] = Field(default_factory=list)
    relative_tolerance: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    evidence: str | None = None

    speeds_knots: list[float] = Field(default_factory=list)
    absolute_uncertainty_N: list[float] = Field(default_factory=list)
    observations: list[NumericalObservation] = Field(default_factory=list)
    surface_observations: list[NumericalSurfaceObservation] = Field(default_factory=list)
    viscous_uncertainty_N: list[float] = Field(default_factory=list)
    comparison_inputs: ResistanceComparisonInputs | None = None
    input_fingerprint: str | None = None
    reference_fn_range: tuple[float, float] | None = None
    reference_resolution_floor: dict[str, int] = Field(default_factory=dict)
    reference_relative_allowance: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _assessment_requires_evidence(self) -> "NumericalQuality":
        if any(not math.isfinite(x) or x < 0 for x in self.relative_changes):
            raise ValueError("numerical relative changes must be finite and nonnegative")
        if any(not level or any(n <= 0 for n in level.values()) for level in self.resolutions):
            raise ValueError("numerical resolutions must contain positive sample counts")
        if self.status != "unknown":
            if not self.policy_version or not self.evidence or len(self.resolutions) < 3:
                raise ValueError("numerical assessment requires a policy, evidence and three resolutions")
            if len({tuple(sorted(level.items())) for level in self.resolutions}) < 3:
                raise ValueError("numerical assessment requires three distinct resolutions")
            if self.relative_tolerance is None or not self.relative_changes:
                raise ValueError("numerical assessment requires changes and tolerance")
            if self.status == "converged" and max(self.relative_changes) > self.relative_tolerance:
                raise ValueError("converged numerical evidence exceeds its tolerance")
        if any(not math.isfinite(x) or x < 0 for x in self.absolute_uncertainty_N + self.viscous_uncertainty_N):
            raise ValueError("numerical uncertainty must be finite and nonnegative")
        if any(not math.isfinite(x) or x < 0 for x in self.speeds_knots):
            raise ValueError("numerical speeds must be finite and nonnegative")
        if self.absolute_uncertainty_N and len(self.absolute_uncertainty_N) != len(self.speeds_knots):
            raise ValueError("numerical uncertainty must cover its exact speed grid")
        if any(len(o.total_resistance_N) != len(self.speeds_knots) for o in self.observations):
            raise ValueError("numerical observations must cover their exact speed grid")
        if self.observations and self.resolutions != [o.resolution for o in self.observations]:
            raise ValueError("numerical resolutions must match actual observations")
        if self.comparison_inputs is not None and self.comparison_inputs.speeds_knots != self.speeds_knots:
            raise ValueError("comparison inputs must bind the exact requested speed grid")
        if self.policy_version == "michell_linear_depth_screening_v1":
            from kayakgen.eval.michell_screening import (
                METHOD_VERSION, REFERENCE_FN_RANGE, REFERENCE_RESOLUTION_FLOOR,
                REFERENCE_RELATIVE_ALLOWANCE, SURFACE_STATIONS,
                achieved_uncertainty, refinement_levels,
            )
            if (self.reference_fn_range != REFERENCE_FN_RANGE
                    or self.reference_resolution_floor != REFERENCE_RESOLUTION_FLOOR
                    or self.reference_relative_allowance != REFERENCE_RELATIVE_ALLOWANCE):
                raise ValueError("screening policy scope, floor or reference allowance changed")
        if self.policy_version == "michell_linear_depth_screening_v1" and self.status != "unknown":
            if (not self.input_fingerprint or len(self.input_fingerprint) != 64
                    or not self.absolute_uncertainty_N or len(self.observations) != 8
                    or self.reference_fn_range is None or self.reference_relative_allowance is None
                    or self.comparison_inputs is None
                    or len(self.surface_observations) != 3
                    or len(self.viscous_uncertainty_N) != len(self.speeds_knots)):
                raise ValueError("screening assessment requires bound inputs, uncertainty and eight observations")
            if (len(self.relative_changes) != len(self.speeds_knots)
                    or any(value is None for o in self.observations for value in o.total_resistance_N)):
                raise ValueError("assessed screening observations must be complete at every speed")
            if any(len(o.viscous_resistance_N) != len(self.speeds_knots) for o in self.surface_observations):
                raise ValueError("surface observations must cover every assessed speed")
            for value, uncertainty, relative in zip(
                self.observations[0].total_resistance_N, self.absolute_uncertainty_N,
                self.relative_changes, strict=True,
            ):
                if value == 0 or not math.isclose(uncertainty / abs(value), relative, rel_tol=1e-12):
                    raise ValueError("screening relative and absolute uncertainty must agree")
            inputs = self.comparison_inputs
            assert inputs is not None
            if inputs.numerical_method_version != METHOD_VERSION:
                raise ValueError("screening policy method version changed")
            if any(not REFERENCE_FN_RANGE[0] <= speed*.514444 / math.sqrt(
                    inputs.gravity_m_s2 * inputs.hull_length_m) <= REFERENCE_FN_RANGE[1]
                   for speed in inputs.speeds_knots):
                raise ValueError("screening assessment is outside its actual Froude scope")
            requested = self.resolutions[0]
            if set(requested) != set(REFERENCE_RESOLUTION_FLOOR) or any(
                    requested[key] < minimum for key, minimum in REFERENCE_RESOLUTION_FLOOR.items()):
                raise ValueError("screening assessment is outside its resolution scope")
            n, m, t = (requested[key] for key in ("n_stations", "n_depths", "n_theta"))
            expected = [dict(zip(("n_stations", "n_depths", "n_theta"), level, strict=True))
                        for level in refinement_levels(n, m, t)]
            if self.resolutions != expected or tuple(o.stations for o in self.surface_observations) != SURFACE_STATIONS:
                raise ValueError("screening observations do not follow the published refinement policy")
            for index in range(len(self.speeds_knots)):
                total_error, viscous_error = achieved_uncertainty(
                    [o.total_resistance_N[index] for o in self.observations],
                    [o.viscous_resistance_N[index] for o in self.surface_observations],
                )
                if (not math.isclose(self.absolute_uncertainty_N[index], total_error, rel_tol=1e-12, abs_tol=0)
                        or not math.isclose(self.viscous_uncertainty_N[index], viscous_error, rel_tol=1e-12, abs_tol=0)):
                    raise ValueError("screening uncertainty contradicts retained policy observations")
        return self


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
    numerical_quality: NumericalQuality = Field(default_factory=NumericalQuality)
    model_family: str = "raw_ittc_michell"
    numerical_method_version: str | None = None
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

    @model_validator(mode="after")
    def _numerical_evidence_covers_speed_grid(self) -> "ResistanceCurve":
        quality = self.metadata.numerical_quality
        if quality.status != "unknown" and len(quality.relative_changes) != len(self.V_knots):
            raise ValueError("numerical assessment must cover every requested speed")
        if quality.speeds_knots and quality.speeds_knots != self.V_knots:
            raise ValueError("numerical assessment must bind the exact requested speed grid")
        if quality.policy_version == "michell_linear_depth_screening_v1" and quality.status != "unknown":
            inputs = quality.comparison_inputs
            assert inputs is not None  # NumericalQuality enforces policy evidence.
            constants = self.metadata.constants
            if (inputs.numerical_method_version != self.metadata.numerical_method_version
                    or inputs.model_family != self.metadata.model_family
                    or inputs.calibration_model_version != self.metadata.model_version
                    or inputs.density_kg_m3 != constants.get("seawater_density_kg_m3")
                    or inputs.kinematic_viscosity_m2_s != constants.get("seawater_kinematic_viscosity_m2_s")
                    or inputs.gravity_m_s2 != constants.get("gravity_m_s2")):
                raise ValueError("numerical assessment input metadata changed")
            if (self.metadata.quadrature != quality.observations[0].resolution
                    or self.Rt_N != quality.observations[0].total_resistance_N
                    or self.Rv_N != quality.surface_observations[0].viscous_resistance_N):
                raise ValueError("numerical assessment requested observations changed")
            count = len(self.V_knots)
            if any(len(values) != count for values in (self.Fn, self.Rv_N, self.Rw_N, self.Rt_N)):
                raise ValueError("assessed resistance vectors must cover the requested speed grid")
            actual_fn = [v * .514444 / math.sqrt(inputs.gravity_m_s2 * inputs.hull_length_m)
                         for v in self.V_knots]
            if any(not math.isclose(reported, actual, rel_tol=1e-12, abs_tol=0)
                   for reported, actual in zip(self.Fn, actual_fn, strict=True)):
                raise ValueError("numerical assessment Froude numbers changed")
            if any(total != viscous + wave for total, viscous, wave in
                   zip(self.Rt_N, self.Rv_N, self.Rw_N, strict=True)):
                raise ValueError("assessed resistance contributions do not sum to their total")
        return self


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


class LoadComponentSnapshot(LongitudinalLoadComponent):
    """Immutable component owned by an evaluation input snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class LoadCaseSnapshot(LoadCase):
    """Deeply immutable load data; mutable caller records remain independent."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    components: tuple[LoadComponentSnapshot, ...] = ()


class EvaluationContext(BaseModel):
    """Exact, immutable physical and numerical inputs to one evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    schema_version: Literal["1"] = "1"
    hull_record_hash: str
    hull_design_hash: str
    geometry_kind: str
    input_origin: Literal["supplied", "legacy_default"] = "legacy_default"
    load_supplied_fields: tuple[str, ...] = ()
    load_case: LoadCaseSnapshot = Field(default_factory=LoadCaseSnapshot)
    speeds_knots: tuple[float, ...] = tuple(1.0 + .25 * i for i in range(21))
    kinematic_viscosity_m2_s: float = Field(default=1.19e-6, gt=0)
    hydrostatic_stations: int = Field(default=60, ge=3)
    n_stations: int = Field(default=600, ge=3)
    n_depths: int = Field(default=25, ge=3)
    n_theta: int = Field(default=40, ge=3)
    numerical_relative_tolerance: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    equilibrium: bool = False
    equilibrium_tolerance_kg: float = Field(default=1.0, gt=0)
    moment_tolerance_kg_m: float | None = Field(default=None, gt=0)
    equilibrium_max_iterations: int = Field(default=60, ge=1)
    max_trim_angle_deg: float = Field(default=8.0, gt=0, lt=90)
    sinkage_m: float = 0.0
    trim_angle_deg: float = 0.0
    evaluator_versions: tuple[tuple[str, str], ...] = ()

    @field_validator("load_case", mode="before")
    @classmethod
    def _snapshot_load(cls, value: Any) -> Any:
        return value.model_dump(mode="json") if isinstance(value, LoadCase) else value

    @field_validator("speeds_knots")
    @classmethod
    def _physical_speeds(cls, speeds: tuple[float, ...]) -> tuple[float, ...]:
        if not speeds or any(speed <= 0 for speed in speeds):
            raise ValueError("speed grid must contain positive speeds")
        return speeds

    @classmethod
    def for_hull(cls, hull: Any, **settings: Any) -> "EvaluationContext":
        from kayakgen.eval.resistance import NUMERICAL_METHOD_VERSION
        load = settings.get("load_case")
        if load is not None:
            settings.setdefault("input_origin", "supplied")
            load = load if isinstance(load, LoadCase) else LoadCase.model_validate(load)
            paths = list(sorted(load.model_fields_set))
            paths.extend(f"components.{i}.{name}"
                         for i, component in enumerate(load.components)
                         for name in sorted(component.model_fields_set))
            settings.setdefault("load_supplied_fields", tuple(paths))
        settings.setdefault("evaluator_versions", (
            ("hydrostatics", "mesh_integral_v1"),
            ("resistance", NUMERICAL_METHOD_VERSION),
        ))
        return cls(
            hull_record_hash=hull.record_hash(),
            hull_design_hash=hull.design_hash(),
            geometry_kind=hull.geometry_kind,
            **settings,
        )

    def operating_comparison_inputs(self) -> dict[str, Any]:
        """Project shared operating conditions without evaluating or mutating them.

        Resistance refinement has its own achieved uncertainty. Solved operating
        pose error does not, so its solver settings remain comparison conditions.
        Explicit component values retain their distribution, independent of names.
        """
        kg = {key: getattr(self.load_case, key) for key in (
            "kg_above_keel_m", "kg_reference", "kg_reference_value_m",
            "seat_height_above_keel_m",
        )}
        if self.load_case.components:
            components = [{key: getattr(component, key) for key in (
                "mass_kg", "x_m", "kg_above_keel_m",
            )} for component in self.load_case.components]
            components.sort(key=lambda value: json.dumps(value, sort_keys=True))
            load = {"components": components}
            if any(component["kg_above_keel_m"] is None for component in components):
                load["inherited_kg"] = kg
        else:
            load = {key: getattr(self.load_case, key) for key in (
                "paddler_mass_kg", "hull_mass_kg", "cargo_mass_kg",
            )}
            load["kg"] = kg
        operating: dict[str, Any] = {"equilibrium": self.equilibrium}
        if self.equilibrium:
            operating.update({key: getattr(self, key) for key in (
                "hydrostatic_stations", "equilibrium_tolerance_kg",
                "moment_tolerance_kg_m", "equilibrium_max_iterations", "max_trim_angle_deg",
            )})
        else:
            operating.update(sinkage_m=self.sinkage_m, trim_angle_deg=self.trim_angle_deg)
        return {
            "schema_version": "1", "load": load,
            "water_density_kg_m3": self.load_case.seawater_density_kg_m3,
            "kinematic_viscosity_m2_s": self.kinematic_viscosity_m2_s,
            "speeds_knots": list(self.speeds_knots), "operating": operating,
        }

    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class StabilityResult(BaseModel):
    """Initial-stability read model; high-angle GZ remains explicitly reserved."""

    model_config = ConfigDict(extra="forbid")

    load_case: LoadCase = Field(default_factory=LoadCase)
    method: Literal[
        "design_waterline_initial",
        "fixed_operating_pose",
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
    """Per-stage numerical evidence; merely completing a stage is unknown.

    Older explicit flags are retained as historical assertions. Admission uses
    the separate numerical_quality record, so legacy stage-ran flags cannot
    establish numerical adequacy.
    """

    model_config = ConfigDict(extra="forbid")

    stage: str
    status: Literal["unknown", "converged", "not_converged", "iteration_cap"]
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
    if stability.method in ("design_waterline_initial", "fixed_operating_pose"):
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
    context: EvaluationContext | None = None
    context_hash: str | None = None
    hydrostatics: Hydrostatics
    resistance: ResistanceCurve | None = None
    stability: StabilityResult | None = None
    cfd: CfdResult | None = None
    turning_metrics: TurningMetrics | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
    design_validity: DesignValidityReport = Field(default_factory=DesignValidityReport)
    convergence: list[ConvergenceFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bind_context(self) -> "EvaluationResult":
        if self.context is not None:
            if self.hull_hash != self.context.hull_record_hash:
                raise ValueError("evaluation hull and context do not match")
            expected = self.context.fingerprint()
            if self.context_hash is not None and self.context_hash != expected:
                raise ValueError("evaluation context fingerprint does not match")
            self.context_hash = expected
            if self.stability is not None:
                if (self.stability.load_case.model_dump(mode="json") != self.context.load_case.model_dump(mode="json")
                    or self.stability.load_mass_kg != self.context.load_case.total_mass_kg):
                    raise ValueError("stability load does not match evaluation context")
            if self.resistance is not None:
                curve = self.resistance
                if tuple(curve.V_knots) != self.context.speeds_knots:
                    raise ValueError("resistance speed grid does not match evaluation context")
                expected_grid = {key: getattr(self.context, key)
                                 for key in ("n_stations", "n_depths", "n_theta")}
                if curve.metadata.quadrature != expected_grid:
                    raise ValueError("resistance quadrature does not match evaluation context")
                if curve.metadata.numerical_quality.relative_tolerance != self.context.numerical_relative_tolerance:
                    raise ValueError("resistance numerical budget does not match evaluation context")
                constants = curve.metadata.constants
                if (constants.get("seawater_density_kg_m3") != self.context.load_case.seawater_density_kg_m3
                    or constants.get("seawater_kinematic_viscosity_m2_s") != self.context.kinematic_viscosity_m2_s):
                    raise ValueError("resistance fluid does not match evaluation context")
        elif self.context_hash is not None:
            raise ValueError("evaluation context fingerprint requires its context")
        return self

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
            ConvergenceFlag(stage="hydrostatics", status="unknown", residual=None)
        ]
        if self.resistance is not None:
            flags.append(
                ConvergenceFlag(
                    stage="resistance",
                    status=self.resistance.metadata.numerical_quality.status,
                    residual=None,
                )
            )
        if self.stability is not None:
            flags.extend(_flags_from_stability(self.stability))
        # ``mesh_diagnostics`` is reported as a single converged entry whenever
        # an EvaluationResult is materialized with a mesh-bearing CFD record.
        # The default ``kayakgen evaluate`` flow does not attach mesh
        # diagnostics, so this entry only appears when the consumer wires it.
        self.convergence = flags
        return self
