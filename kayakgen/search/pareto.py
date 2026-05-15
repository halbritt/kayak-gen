"""Pure Pareto-frontier utilities for candidate comparison."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Direction = Literal["min", "max"]

#: Per RFC 0043 stage 3 (workflow 0052 staged surfacing): high-angle GZ values
#: are display-only. Until a future RFC explicitly promotes them to objectives,
#: any caller that tries to drive Pareto comparison from these keys is rejected
#: with this token so the refusal stays machine-grep-able.
HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN = "RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY"

#: Metric keys that mirror the high-angle GZ artifact summary. These are
#: surfaced as display columns by the comparison report but MUST NOT be
#: selectable as Pareto objectives.
HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS: frozenset[str] = frozenset(
    {
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
    }
)


class HighAngleGzObjectiveRefusedError(ValueError):
    """Raised when a caller selects a high-angle GZ key as a Pareto objective.

    Carries a structured ``reason`` payload with the offending metric and the
    refusal token so callers can surface a stable, machine-readable error.
    """

    def __init__(self, metric: str) -> None:
        self.metric = metric
        self.reason = {
            "code": "high_angle_gz_display_only",
            "token": HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
            "metric": metric,
            "detail": (
                f"high-angle GZ metric {metric!r} is display-only per "
                f"{HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN}; not selectable as a Pareto objective"
            ),
        }
        super().__init__(self.reason["detail"])


def ensure_objectives_not_high_angle_gz(objectives: list["Objective"]) -> None:
    """Refuse high-angle GZ display-only metrics as Pareto objectives.

    Raises :class:`HighAngleGzObjectiveRefusedError` for the first offending
    objective. Callers wanting to soften this gate must land a future, explicit
    RFC that supersedes :data:`HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN`.
    """

    for objective in objectives:
        if objective.metric in HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS:
            raise HighAngleGzObjectiveRefusedError(objective.metric)


class Objective(BaseModel):
    """A metric and its optimisation direction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric: str
    direction: Direction
    accepted_use_required: bool = False

    @field_validator("metric")
    @classmethod
    def _metric_must_not_be_blank(cls, value: str) -> str:
        metric = value.strip()
        if not metric:
            raise ValueError("metric must not be blank")
        return metric


class CandidatePoint(BaseModel):
    """A scored design candidate.

    ``metrics`` are the only values used for Pareto comparison. ``warnings``
    and ``provenance`` travel with the point so upstream exploratory evaluators
    can keep their caveats attached without becoming hard-coded objectives.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    metrics: dict[str, float]
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _id_must_not_be_blank(cls, value: str) -> str:
        candidate_id = value.strip()
        if not candidate_id:
            raise ValueError("id must not be blank")
        return candidate_id

    @field_validator("metrics")
    @classmethod
    def _metrics_must_be_finite(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, score in value.items():
            if not math.isfinite(score):
                raise ValueError(f"metric {metric!r} must be finite")
        return value


def dominates(left: CandidatePoint, right: CandidatePoint, objectives: list[Objective]) -> bool:
    """Return whether ``left`` Pareto-dominates ``right``.

    Dominance requires both candidates to be comparable for every objective,
    and at least one objective must be strictly better. Missing metrics, or
    exploratory metrics without accepted-use provenance, make the pair
    non-dominating rather than raising.
    """

    if not objectives:
        return False

    strictly_better = False
    for objective in objectives:
        if not _has_usable_metric(left, objective) or not _has_usable_metric(right, objective):
            return False

        left_value = left.metrics[objective.metric]
        right_value = right.metrics[objective.metric]

        if objective.direction == "min":
            if left_value > right_value:
                return False
            strictly_better = strictly_better or left_value < right_value
        else:
            if left_value < right_value:
                return False
            strictly_better = strictly_better or left_value > right_value

    return strictly_better


def pareto_front(
    candidates: list[CandidatePoint], objectives: list[Objective]
) -> list[CandidatePoint]:
    """Return non-dominated candidates in input order.

    Returned candidates are copies annotated with objective-related warnings.
    The input objects are not mutated.
    """

    annotated = [_with_objective_warnings(candidate, objectives) for candidate in candidates]
    front: list[CandidatePoint] = []
    for index, candidate in enumerate(annotated):
        if not any(
            other_index != index and dominates(other, candidate, objectives)
            for other_index, other in enumerate(annotated)
        ):
            front.append(candidate)
    return front


def _has_usable_metric(candidate: CandidatePoint, objective: Objective) -> bool:
    if objective.metric not in candidate.metrics:
        return False
    if objective.accepted_use_required and not _has_accepted_use(candidate, objective.metric):
        return False
    return True


def _has_accepted_use(candidate: CandidatePoint, metric: str) -> bool:
    accepted_use = candidate.provenance.get("accepted_use")
    if isinstance(accepted_use, dict) and accepted_use.get(metric) is True:
        return True

    metric_provenance = candidate.provenance.get(metric)
    if isinstance(metric_provenance, dict) and metric_provenance.get("accepted_use") is True:
        return True

    return False


def _with_objective_warnings(
    candidate: CandidatePoint, objectives: list[Objective]
) -> CandidatePoint:
    warnings = list(candidate.warnings)
    seen = set(warnings)

    for objective in objectives:
        if objective.metric not in candidate.metrics:
            warning = f"missing metric: {objective.metric}"
        elif objective.accepted_use_required and not _has_accepted_use(candidate, objective.metric):
            warning = f"metric requires accepted-use provenance: {objective.metric}"
        else:
            continue

        if warning not in seen:
            warnings.append(warning)
            seen.add(warning)

    return candidate.model_copy(update={"warnings": tuple(warnings)})
