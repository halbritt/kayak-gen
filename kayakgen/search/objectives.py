"""Objective metadata for sweep comparison and future search gates."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from kayakgen.eval.claims import (
    ACCEPTED_USE_FINAL_DESIGN_FITNESS,
    ACCEPTED_USE_FINAL_PREDICTION,
    CALIBRATED_MODEL,
    VALIDATED_DESIGN_FITNESS,
)
from kayakgen.search.pareto import Direction, Objective

ObjectiveRole = Literal[
    "default_conservative",
    "explicit_exploratory",
    "claim_gated_reserved",
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

    @field_validator("metric", "label", "unit", "source_evaluator", "availability_rule")
    @classmethod
    def _text_must_not_be_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("objective metadata text fields must not be blank")
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
    ),
    "displacement_error_kg": ObjectiveMetadata(
        metric="displacement_error_kg",
        label="Displacement error",
        unit="kg",
        direction="min",
        source_evaluator="stability",
        availability_rule="present when the stability evaluator runs",
        role="default_conservative",
    ),
    "mesh_problem_count": ObjectiveMetadata(
        metric="mesh_problem_count",
        label="Mesh problem count",
        unit="count",
        direction="min",
        source_evaluator="mesh_diagnostics",
        availability_rule="derived from a mesh diagnostics artifact when enabled",
        role="default_conservative",
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
    ),
}

DEFAULT_OBJECTIVE_METRICS: tuple[str, ...] = (
    "GM0_m",
    "displacement_error_kg",
    "mesh_problem_count",
)


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
