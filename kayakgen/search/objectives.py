"""Objective metadata for sweep comparison and future search gates."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from kayakgen.eval.claims import (
    ACCEPTED_USE_FINAL_DESIGN_FITNESS,
    ACCEPTED_USE_FINAL_PREDICTION,
    CALIBRATED_MODEL,
    VALIDATED_DESIGN_FITNESS,
)
from kayakgen.search.pareto import (
    Direction,
    HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS,
    HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
    Objective,
)

ObjectiveRole = Literal[
    "default_conservative",
    "explicit_exploratory",
    "claim_gated_reserved",
    "display_only",
    "unsupported",
]


class ObjectiveMetadata(BaseModel):
    """Machine-readable admissibility metadata for one comparison objective."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str
    label: str
    unit: str
    direction: Direction
    source_evaluator: str
    availability_rule: str
    claim_state_required: str | None = None
    accepted_use_required: str | None = None
    role: ObjectiveRole
    display_format: str = "{value:.3f}"
    availability_conditions: list[str] = []
    default_objective_eligible: bool = False

    @field_validator("metric", "label", "unit", "source_evaluator", "availability_rule")
    @classmethod
    def _text_must_not_be_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("objective metadata text fields must not be blank")
        return text

    @field_validator("display_format")
    @classmethod
    def _display_format_must_format(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("display_format must not be blank")
        # Smoke-test the format string against a representative float so a
        # malformed format spec fails at registration time, not at render time.
        try:
            text.format(value=1.0)
        except (KeyError, IndexError, ValueError) as exc:
            raise ValueError(
                f"display_format must accept a 'value' placeholder: {exc}"
            ) from exc
        return text


OBJECTIVE_METADATA: dict[str, ObjectiveMetadata] = {
    "GM0_m": ObjectiveMetadata(
        metric="GM0_m",
        label="Initial metacentric height",
        unit="m",
        direction="max",
        source_evaluator="hydrostatics",
        availability_rule="present when hydrostatics evaluation completes",
        role="default_conservative",
        display_format="{value:.3f}",
        availability_conditions=["hydrostatics_evaluated"],
        default_objective_eligible=True,
    ),
    "displacement_error_kg": ObjectiveMetadata(
        metric="displacement_error_kg",
        label="Displacement error",
        unit="kg",
        direction="min",
        source_evaluator="stability",
        availability_rule="present when the stability evaluator runs",
        role="default_conservative",
        display_format="{value:.3f}",
        availability_conditions=["stability_evaluator_ran"],
        default_objective_eligible=True,
    ),
    "displaced_mass_kg": ObjectiveMetadata(
        metric="displaced_mass_kg",
        label="Displaced mass",
        unit="kg",
        direction="min",
        source_evaluator="hydrostatics",
        availability_rule="present when hydrostatics evaluation completes",
        role="default_conservative",
        display_format="{value:.3f}",
        availability_conditions=["hydrostatics_evaluated"],
        default_objective_eligible=False,
    ),
    "wetted_surface_m2": ObjectiveMetadata(
        metric="wetted_surface_m2",
        label="Wetted surface",
        unit="m^2",
        direction="min",
        source_evaluator="hydrostatics",
        availability_rule="present when hydrostatics evaluation completes",
        role="default_conservative",
        display_format="{value:.3f}",
        availability_conditions=["hydrostatics_evaluated"],
        default_objective_eligible=False,
    ),
    "Cp_actual": ObjectiveMetadata(
        metric="Cp_actual",
        label="Prismatic coefficient (actual)",
        unit="dimensionless",
        direction="max",
        source_evaluator="hydrostatics",
        availability_rule="present when hydrostatics evaluation completes",
        role="default_conservative",
        display_format="{value:.3f}",
        availability_conditions=["hydrostatics_evaluated"],
        default_objective_eligible=False,
    ),
    "mesh_problem_count": ObjectiveMetadata(
        metric="mesh_problem_count",
        label="Mesh problem count",
        unit="count",
        direction="min",
        source_evaluator="mesh_diagnostics",
        availability_rule="derived from a mesh diagnostics artifact when enabled",
        role="default_conservative",
        display_format="{value:.0f}",
        availability_conditions=["mesh_diagnostics_artifact_present"],
        default_objective_eligible=True,
    ),
    "Rt_N_last": ObjectiveMetadata(
        metric="Rt_N_last",
        label="Total resistance at last sweep speed",
        unit="N",
        direction="min",
        source_evaluator="resistance",
        availability_rule="present when raw analytical resistance evaluation runs",
        claim_state_required=CALIBRATED_MODEL,
        accepted_use_required=ACCEPTED_USE_FINAL_PREDICTION,
        role="explicit_exploratory",
        display_format="{value:.3f}",
        availability_conditions=["resistance_evaluator_ran"],
        default_objective_eligible=False,
    ),
    "design_fitness": ObjectiveMetadata(
        metric="design_fitness",
        label="Validated design fitness",
        unit="score",
        direction="max",
        source_evaluator="reserved_claim_gate",
        availability_rule="reserved until a validated design-fitness evaluator exists",
        claim_state_required=VALIDATED_DESIGN_FITNESS,
        accepted_use_required=ACCEPTED_USE_FINAL_DESIGN_FITNESS,
        role="claim_gated_reserved",
        display_format="{value:.3f}",
        availability_conditions=["validated_design_fitness_evaluator_present"],
        default_objective_eligible=False,
    ),
    "max_gz_m": ObjectiveMetadata(
        metric="max_gz_m",
        label="Max GZ (m)",
        unit="m",
        direction="max",
        source_evaluator="high_angle_gz",
        availability_rule="present when high-angle GZ artifact is computed",
        role="display_only",
        display_format="{value:.3f}",
        availability_conditions=["high_angle_gz_artifact_present"],
        default_objective_eligible=False,
    ),
    "heel_at_max_gz_deg": ObjectiveMetadata(
        metric="heel_at_max_gz_deg",
        label="Heel at max GZ (deg)",
        unit="deg",
        direction="max",
        source_evaluator="high_angle_gz",
        availability_rule="present when high-angle GZ artifact is computed",
        role="display_only",
        display_format="{value:.3f}",
        availability_conditions=["high_angle_gz_artifact_present"],
        default_objective_eligible=False,
    ),
    "range_positive_stability_deg": ObjectiveMetadata(
        metric="range_positive_stability_deg",
        label="Range positive stability (deg)",
        unit="deg",
        direction="max",
        source_evaluator="high_angle_gz",
        availability_rule="present when high-angle GZ artifact is computed",
        role="display_only",
        display_format="{value:.3f}",
        availability_conditions=["high_angle_gz_artifact_present"],
        default_objective_eligible=False,
    ),
}

DEFAULT_OBJECTIVE_METRICS: tuple[str, ...] = (
    "GM0_m",
    "displacement_error_kg",
    "mesh_problem_count",
)

# Structured rejection codes for `is_objective_metric_admissible` so callers
# can branch on a token rather than parsing free-form text.
OBJECTIVE_REJECTION_UNKNOWN_METRIC = "objective_metric_unknown"
OBJECTIVE_REJECTION_DISPLAY_ONLY = "high_angle_gz_display_only"
OBJECTIVE_REJECTION_CLAIM_GATED = "objective_claim_state_not_admissible"


def register_objective_metadata(metadata: ObjectiveMetadata) -> None:
    """Register a new ObjectiveMetadata entry.

    Raises :class:`ValueError` if a metric with the same key already exists so
    tests and downstream callers can detect accidental redefinition.
    """

    if metadata.metric in OBJECTIVE_METADATA:
        raise ValueError(
            f"objective metric {metadata.metric!r} is already registered"
        )
    OBJECTIVE_METADATA[metadata.metric] = metadata


def default_objectives() -> tuple[Objective, ...]:
    """Return conservative default objective candidates in registry order."""
    return tuple(
        Objective(
            metric=metadata.metric,
            direction=metadata.direction,
            accepted_use_required=metadata.accepted_use_required is not None,
        )
        for metric in DEFAULT_OBJECTIVE_METRICS
        for metadata in (OBJECTIVE_METADATA[metric],)
    )


def objective_metadata_for(objective: Objective) -> ObjectiveMetadata:
    """Return selected-objective metadata, including an unsupported fallback."""
    metadata = OBJECTIVE_METADATA.get(objective.metric)
    if metadata is None:
        return ObjectiveMetadata(
            metric=objective.metric,
            label=objective.metric,
            unit="unknown",
            direction=objective.direction,
            source_evaluator="unknown",
            availability_rule="unsupported metric is not emitted by current sweep records",
            role="unsupported",
        )
    if metadata.direction == objective.direction:
        return metadata
    return metadata.model_copy(update={"direction": objective.direction})


def objective_requires_accepted_use(objective: Objective) -> bool:
    """Return whether objective dominance needs accepted-use provenance."""
    metadata = OBJECTIVE_METADATA.get(objective.metric)
    if metadata is not None and metadata.accepted_use_required is not None:
        return True
    return objective.accepted_use_required


def is_objective_metric_admissible(
    metric: str, *, explicit_exploratory: bool
) -> tuple[bool, dict[str, str] | None]:
    """Decide whether a metric is admissible as an explicit objective.

    Returns ``(True, None)`` when admissible, or ``(False, reason)`` with a
    structured rejection payload. The payload always carries a ``code`` token
    so callers can branch on a machine-grep-able key.

    Rejection codes (constants on this module):

    * :data:`OBJECTIVE_REJECTION_DISPLAY_ONLY` -- the metric is registered as
      a display-only mirror of the high-angle GZ artifact (RFC 0043). The
      display-only refusal wins even when ``explicit_exploratory`` is True.
    * :data:`OBJECTIVE_REJECTION_CLAIM_GATED` -- the metric is registered
      under an ``explicit_exploratory`` or ``claim_gated_reserved`` role and
      the caller did not opt in via ``explicit_exploratory=True``.
    * :data:`OBJECTIVE_REJECTION_UNKNOWN_METRIC` -- the metric is not in the
      registry; unknown metrics are admissible only under the exploratory
      opt-in.
    """

    # High-angle GZ refusal token always wins (defense in depth even when the
    # metric is not yet registered as a display-only entry).
    if metric in HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS:
        return False, {
            "code": OBJECTIVE_REJECTION_DISPLAY_ONLY,
            "token": HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
            "metric": metric,
            "detail": (
                f"objective metric {metric!r} is display-only per "
                f"{HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN}; not selectable as an objective"
            ),
        }

    metadata = OBJECTIVE_METADATA.get(metric)
    if metadata is None:
        if explicit_exploratory:
            return True, None
        return False, {
            "code": OBJECTIVE_REJECTION_UNKNOWN_METRIC,
            "metric": metric,
            "detail": (
                f"objective metric {metric!r} is not registered; "
                "explicit objectives must be registered or marked exploratory"
            ),
        }

    if metadata.role == "display_only":
        return False, {
            "code": OBJECTIVE_REJECTION_DISPLAY_ONLY,
            "token": HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
            "metric": metric,
            "detail": (
                f"objective metric {metric!r} is display-only per "
                f"{HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN}; not selectable as an objective"
            ),
        }

    if explicit_exploratory:
        return True, None

    if metadata.role in ("explicit_exploratory", "claim_gated_reserved"):
        return False, {
            "code": OBJECTIVE_REJECTION_CLAIM_GATED,
            "metric": metric,
            "role": metadata.role,
            "claim_state_required": metadata.claim_state_required,
            "detail": (
                f"objective metric {metric!r} requires explicit exploratory "
                f"opt-in (role={metadata.role!r})"
            ),
        }

    return True, None
