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

#: Per RFC 0044 v1 active hull-design search: objective metrics whose claim
#: state is ``raw_unvalidated`` or ``uncalibrated_comparative`` may only be
#: selected as search objectives when the spec opts in to exploratory mode.
#: The runner then marks the run as ``search_class: exploratory``. This token
#: stays machine-grep-able so the refusal payload can be matched in tests and
#: comparison report banners.
SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN = (
    "RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY"
)

#: Claim states that are refused as default (conservative) search objectives.
SEARCH_REFUSED_CLAIM_STATES: frozenset[str] = frozenset(
    {
        "raw_unvalidated",
        "uncalibrated_comparative",
    }
)

#: Map the registry's ``role`` field to the source evaluator's current emitted
#: claim state. The registry does not record the live claim state of evaluator
#: outputs directly (it records what claim state the metric *requires* to be
#: usable as a calibrated objective). Active-search admissibility hinges on
#: what today's evaluator actually emits, so the gate maps the role to the
#: claim state name expected by RFC 0044's refusal payload.
_SEARCH_ROLE_TO_CLAIM_STATE: dict[str, str] = {
    "explicit_exploratory": "raw_unvalidated",
    "claim_gated_reserved": "uncalibrated_comparative",
}


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


class SearchObjectiveRefusedError(ValueError):
    """Raised when a search-objective claim state is not admissible by default.

    Carries a structured ``reason`` payload with the offending metric, its
    recorded claim state, and the refusal token so callers can surface a stable,
    machine-readable error.
    """

    def __init__(self, metric: str, claim_state: str | None) -> None:
        self.metric = metric
        self.claim_state = claim_state
        self.reason = {
            "code": "search_objective_claim_not_admissible",
            "token": SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN,
            "metric": metric,
            "claim_state": claim_state,
            "detail": (
                f"objective metric {metric!r} has claim state {claim_state!r}; "
                f"refused as a default search objective per "
                f"{SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN}. Set "
                "objectives_explicit_exploratory=true to opt in as an "
                "exploratory search."
            ),
        }
        super().__init__(self.reason["detail"])


class UnknownSearchObjectiveError(ValueError):
    """Raised when an explicit search objective is not registered.

    Carries the structured rejection payload from
    :func:`kayakgen.search.objectives.is_objective_metric_admissible` so callers
    can render a machine-readable refusal.
    """

    def __init__(self, metric: str, reason: dict[str, str]) -> None:
        self.metric = metric
        self.reason = reason
        super().__init__(reason.get("detail", f"unknown objective metric: {metric!r}"))


def ensure_objectives_claim_admissible_for_search(
    objectives: list["Objective"],
    *,
    explicit_exploratory: bool,
) -> None:
    """Refuse search-objective metrics whose claim states demand exploratory opt-in.

    Reads each objective's recorded claim state from
    :data:`kayakgen.search.objectives.OBJECTIVE_METADATA`. Metrics whose
    claim state is ``raw_unvalidated`` or ``uncalibrated_comparative`` are
    refused unless the caller passes ``explicit_exploratory=True``.

    The existing :func:`ensure_objectives_not_high_angle_gz` gate is always
    invoked first; the RFC 0043 display-only refusal is unconditional and is
    not softened by the exploratory flag.
    """

    # The RFC 0043 display-only gate always wins, even in exploratory mode.
    ensure_objectives_not_high_angle_gz(objectives)

    if explicit_exploratory:
        return

    # Local import to avoid a module-level circular import between
    # ``kayakgen.search.objectives`` (which imports from this module) and this
    # module's runtime path.
    from kayakgen.search.objectives import (
        OBJECTIVE_METADATA,
        is_objective_metric_admissible,
    )

    for objective in objectives:
        metadata = OBJECTIVE_METADATA.get(objective.metric)
        if metadata is None:
            # Unknown metrics are admissible only under explicit exploratory.
            admissible, reason = is_objective_metric_admissible(
                objective.metric, explicit_exploratory=explicit_exploratory
            )
            if not admissible:
                assert reason is not None
                raise UnknownSearchObjectiveError(objective.metric, reason)
            continue
        # ``display_only`` role is owned by the RFC 0043 gate above; we do not
        # double-report here so the existing token wins.
        if metadata.role == "display_only":
            continue
        claim_state = _SEARCH_ROLE_TO_CLAIM_STATE.get(metadata.role)
        if claim_state in SEARCH_REFUSED_CLAIM_STATES:
            raise SearchObjectiveRefusedError(objective.metric, claim_state)


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
