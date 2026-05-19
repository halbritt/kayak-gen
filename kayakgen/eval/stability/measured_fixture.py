"""Measured-stability fixture schemas (RFC 0056).

Lands the schema + validator surface for the strain-gauged moment-arm
rig data ingest. Sibling to RFC 0054's resistance-calibration tooling:

- :class:`MeasuredStabilityFixture` aggregates the on-disk manifest for
  a single ``(hull, configuration)`` rig run, the per-row
  ``(θ, GZ)`` data, hull identity, loading configuration, calibration
  trace, free-equilibrium trace, and hysteresis bound.
- Validators enforce the RFC 0056 acceptance gates: ``intended_use``
  enumeration, ``HullIdentityRef`` presence, calibration trace presence,
  free-equilibrium trace presence, and hysteresis bound declaration.
- No fixture is promoted by this module. ``intended_use`` defaults to
  ``"validation_candidate"`` until an operator-run promotion-review
  packet accepts the run as a ``measured_stability_fixture``.

The module is import-safe (no module-level filesystem or network calls)
and contains no claim about a hull's safety, seaworthiness, or
final-prediction fitness. RFC 0043's
``unvalidated_hydrostatic_comparison`` semantics on analytical
``GZCurve`` outputs remain authoritative.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.eval.calibration.rights import RightsChecklist

MeasuredStabilityUse = Literal[
    "validation_candidate",
    "measured_stability_fixture",
    "rejected",
]
"""Lifecycle states for a strain-gauged GZ rig run (RFC 0056).

- ``validation_candidate`` — raw run; the analytical evaluator may
  compare against it but never tune.
- ``measured_stability_fixture`` — promotion-reviewed run. Validation
  use only by default; only an explicit RFC successor (parallel to
  RFC 0027 for resistance) graduates a fixture to calibration use.
- ``rejected`` — review packet refused promotion; the raw data is
  preserved but excluded from analytical comparisons.
"""

MeasuredStabilityConfiguration = Literal["sealed_deck", "flooded_cockpit"]
"""Hull configuration the rig run measured (RFC 0056)."""

PaddlerBallastKind = Literal["absent", "rigid_manikin", "active_paddler"]
"""Paddler-ballast convention pinned on a loading configuration."""

DEFAULT_HYSTERESIS_BOUND_FRACTION = 0.03
"""Default forward/reverse-sweep agreement bound (3% of GZ_max)."""

DEFAULT_CALIBRATION_DRIFT_BOUND = 0.005
"""Default pre/post-run dead-weight drift bound (0.5% of full scale)."""


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class HullIdentityRef(BaseModel):
    """Identity of the physical hull a rig run was made against.

    Manufacturer / model strings alone are insufficient: production-tolerance
    variation between two units of the same model can exceed the rig's
    measurement uncertainty. The ``scan_hash`` field carries the SHA-256 of
    a 3D scan of the tested hull, pinning the surface used.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    manufacturer: str = Field(min_length=1)
    model: str = Field(min_length=1)
    serial_or_year: str | None = None
    scan_hash: str = Field(min_length=64, max_length=64)
    scan_method: str = Field(min_length=1)
    hull_class: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class LoadingConfiguration(BaseModel):
    """Mass, paddler ballast, and configuration of a rig run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    displacement_kg: float = Field(gt=0)
    paddler_state: PaddlerBallastKind
    paddler_mass_kg: float = Field(ge=0)
    paddler_cg_height_m: float = Field(ge=0)
    added_ballast_kg: float = Field(default=0.0, ge=0)
    added_ballast_cg_height_m: float | None = Field(default=None, ge=0)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _paddler_mass_matches_state(self) -> "LoadingConfiguration":
        if self.paddler_state == "absent" and self.paddler_mass_kg != 0.0:
            raise ValueError(
                "paddler_state='absent' requires paddler_mass_kg=0; "
                f"got paddler_mass_kg={self.paddler_mass_kg}"
            )
        if self.paddler_state in ("rigid_manikin", "active_paddler") and self.paddler_mass_kg <= 0:
            raise ValueError(
                f"paddler_state={self.paddler_state!r} requires paddler_mass_kg > 0"
            )
        return self


class CalibrationTrace(BaseModel):
    """Pre/post-run dead-weight calibration sweep summary."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    pre_run_trace_path: str = Field(min_length=1)
    post_run_trace_path: str = Field(min_length=1)
    dead_weight_kg: float = Field(gt=0)
    measured_arm_pre_m: float = Field(gt=0)
    measured_arm_post_m: float = Field(gt=0)
    drift_bound_fraction: float = Field(
        default=DEFAULT_CALIBRATION_DRIFT_BOUND, ge=0
    )

    @property
    def drift_fraction(self) -> float:
        """Fractional drift between pre and post dead-weight readings."""

        if self.measured_arm_pre_m == 0:
            return float("inf")
        return abs(self.measured_arm_post_m - self.measured_arm_pre_m) / self.measured_arm_pre_m

    @model_validator(mode="after")
    def _drift_within_bound(self) -> "CalibrationTrace":
        if self.drift_fraction > self.drift_bound_fraction:
            raise ValueError(
                "calibration_drift_above_bound: pre/post drift "
                f"{self.drift_fraction:.4f} exceeds bound "
                f"{self.drift_bound_fraction:.4f}"
            )
        return self


class FreeEquilibriumPoint(BaseModel):
    """Trim + heave at one heel angle during the sweep."""

    model_config = ConfigDict(extra="forbid")

    theta_deg: float
    trim_deg: float
    heave_m: float


class FreeEquilibriumTrace(BaseModel):
    """Trim + heave traces over the rig sweep.

    Acceptance requires the traces vary smoothly with ``theta_deg`` and
    do not show clamping or oscillation patterns characteristic of rig
    restraint. ``constrained_trim`` or ``constrained_heave`` may be set
    when the rig deliberately fixed one of the DOFs; doing so caps the
    fixture's ``intended_use`` at ``"validation_candidate"`` because the
    measurement is no longer free-hydrostatic.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    points: list[FreeEquilibriumPoint] = Field(min_length=3)
    constrained_trim: bool = False
    constrained_heave: bool = False
    smoothness_failures: list[str] = Field(default_factory=list)


class HysteresisBound(BaseModel):
    """Forward/reverse sweep agreement bound and the observed worst case."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    bound_fraction: float = Field(
        default=DEFAULT_HYSTERESIS_BOUND_FRACTION, ge=0
    )
    observed_max_fraction: float = Field(ge=0)
    observed_at_theta_deg: float

    @model_validator(mode="after")
    def _observed_within_bound(self) -> "HysteresisBound":
        if self.observed_max_fraction > self.bound_fraction:
            raise ValueError(
                "hysteresis_above_bound: observed "
                f"{self.observed_max_fraction:.4f} at theta="
                f"{self.observed_at_theta_deg} exceeds bound "
                f"{self.bound_fraction:.4f}"
            )
        return self


class MeasuredStabilityRow(BaseModel):
    """One ``(theta, gz)`` data point in a measured-stability fixture."""

    model_config = ConfigDict(extra="forbid")

    theta_deg: float
    gz_m: float
    gz_std_m: float | None = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Aggregate root
# ---------------------------------------------------------------------------


class MeasuredStabilityFixture(BaseModel):
    """Aggregate root for one strain-gauged GZ rig run (RFC 0056).

    Acceptance gates (validated below):

    - ``intended_use`` is one of the :data:`MeasuredStabilityUse` values.
    - ``hull_identity`` is present and carries a 64-char SHA-256 scan hash.
    - ``calibration_trace`` is present and its drift is within bound.
    - ``free_equilibrium_trace`` is present.
    - ``hysteresis_bound`` is declared.
    - A constrained free-equilibrium trace caps ``intended_use`` at
      ``"validation_candidate"`` — the fixture cannot promote to
      ``measured_stability_fixture`` while the rig has been clamping
      trim or heave.
    - ``rights`` checklist must be present for any fixture that intends
      to surface in a downstream comparison.

    No fixture is promoted by this aggregate. The default for
    ``intended_use`` is ``"validation_candidate"``; a separate
    operator-run promotion-review packet (sibling to RFC 0019's source
    review for resistance) graduates a run to
    ``"measured_stability_fixture"``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    fixture_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_citation: str = Field(min_length=1)
    source_url: str | None = None
    rights: RightsChecklist
    extraction_method: str = Field(min_length=1)
    hull_identity: HullIdentityRef
    configuration: MeasuredStabilityConfiguration
    loading: LoadingConfiguration
    measured_quantity: Literal["gz_m"] = "gz_m"
    heel_units: Literal["deg"] = "deg"
    arm_units: Literal["m"] = "m"
    valid_heel_range_deg: tuple[float, float]
    rig_design_ref: str = Field(min_length=1)
    geometry_manifest_ref: str = Field(min_length=1)
    calibration_trace: CalibrationTrace
    free_equilibrium_trace: FreeEquilibriumTrace
    hysteresis_bound: HysteresisBound
    rows: list[MeasuredStabilityRow] = Field(min_length=3)
    runs_dir: str | None = None
    intended_use: MeasuredStabilityUse = "validation_candidate"
    non_promotion_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _valid_heel_range_ordered(self) -> "MeasuredStabilityFixture":
        low, high = self.valid_heel_range_deg
        if not low < high:
            raise ValueError(
                "valid_heel_range_deg requires low < high; "
                f"got ({low}, {high})"
            )
        return self

    @model_validator(mode="after")
    def _rows_inside_valid_range(self) -> "MeasuredStabilityFixture":
        low, high = self.valid_heel_range_deg
        out_of_range = [
            row.theta_deg for row in self.rows
            if row.theta_deg < low - 1e-6 or row.theta_deg > high + 1e-6
        ]
        if out_of_range:
            raise ValueError(
                "rows_outside_valid_heel_range: "
                f"theta={out_of_range[:5]} (and {max(0, len(out_of_range) - 5)} more) "
                f"lie outside valid_heel_range_deg={self.valid_heel_range_deg}"
            )
        return self

    @model_validator(mode="after")
    def _intended_use_caps_for_constrained_trace(self) -> "MeasuredStabilityFixture":
        trace = self.free_equilibrium_trace
        if (trace.constrained_trim or trace.constrained_heave) and (
            self.intended_use == "measured_stability_fixture"
        ):
            raise ValueError(
                "constrained_trace_blocks_promotion: a fixture with "
                "constrained trim or heave cannot promote to "
                "measured_stability_fixture; cap intended_use at "
                "validation_candidate and record the constraint in "
                "non_promotion_reasons."
            )
        return self

    @model_validator(mode="after")
    def _non_promotion_reasons_required_for_validation_candidate(
        self,
    ) -> "MeasuredStabilityFixture":
        if (
            self.intended_use == "validation_candidate"
            and not self.non_promotion_reasons
        ):
            self.warnings.append("validation_candidate_without_recorded_reasons")
        return self

    def is_promoted(self) -> bool:
        """Whether the fixture is currently promoted to ``measured_stability_fixture``."""

        return self.intended_use == "measured_stability_fixture"

    def gz_max_m(self) -> float:
        """Observed peak ``GZ`` over the binned rows."""

        return max(row.gz_m for row in self.rows)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def validate_measured_stability_fixture_path(path: str | "PathLike[str]") -> MeasuredStabilityFixture:
    """Load and validate a fixture manifest from disk.

    The on-disk shape is the canonical JSON dump of
    :class:`MeasuredStabilityFixture`. Raises a Pydantic
    ``ValidationError`` on any acceptance-gate failure.
    """

    import json
    from pathlib import Path as _Path

    text = _Path(path).expanduser().read_text(encoding="utf-8")
    payload = json.loads(text)
    return MeasuredStabilityFixture.model_validate(payload)


__all__ = [
    "DEFAULT_CALIBRATION_DRIFT_BOUND",
    "DEFAULT_HYSTERESIS_BOUND_FRACTION",
    "CalibrationTrace",
    "FreeEquilibriumPoint",
    "FreeEquilibriumTrace",
    "HullIdentityRef",
    "HysteresisBound",
    "LoadingConfiguration",
    "MeasuredStabilityConfiguration",
    "MeasuredStabilityFixture",
    "MeasuredStabilityRow",
    "MeasuredStabilityUse",
    "PaddlerBallastKind",
    "validate_measured_stability_fixture_path",
]


# Local type alias so the module imports nothing from ``os`` at the top.
from os import PathLike  # noqa: E402,F401
