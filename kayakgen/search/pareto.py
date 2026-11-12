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


LOAD_CASE_GZ_METRIC_PREFIX = "load_case_gz."


def is_high_angle_gz_display_only_metric(metric: str) -> bool:
    """Whether ``metric`` is a righting-arm value barred from objectives.

    Covers the RFC 0043 single-load mirrors and the RFC 0089 per-load
    keys (``load_case_gz.<name>.gz_m_at_<angle>deg``). Both are the
    same unvalidated hydrostatic comparison. They may bound a search as
    constraints; they may not rank candidates.
    """

    return metric in HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS or metric.startswith(
        LOAD_CASE_GZ_METRIC_PREFIX
    )


def ensure_objectives_not_high_angle_gz(objectives: list["Objective"]) -> None:
    """Refuse high-angle GZ display-only metrics as Pareto objectives.

    Raises :class:`HighAngleGzObjectiveRefusedError` for the first offending
    objective. Callers wanting to soften this gate must land a future, explicit
    RFC that supersedes :data:`HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN`.
    """

    for objective in objectives:
        if is_high_angle_gz_display_only_metric(objective.metric):
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


class DisplayOnlyObjectiveRefusedError(ValueError):
    """A registered display-only metric cannot drive search or comparison."""

    def __init__(self, metric: str, reason: dict[str, str]) -> None:
        self.metric = metric
        self.reason = reason
        super().__init__(reason["detail"])


def ensure_objectives_claim_admissible_for_search(
    objectives: list["Objective"],
    *,
    explicit_exploratory: bool,
) -> None:
    """Apply registry admission policy with compatible structured exceptions.

    Display-only metrics are always refused. Other restricted metrics need
    ``explicit_exploratory=True`` according to the objective registry.

    The existing :func:`ensure_objectives_not_high_angle_gz` gate is always
    invoked first; the RFC 0043 display-only refusal is unconditional and is
    not softened by the exploratory flag.
    """

    # The RFC 0043 display-only gate always wins, even in exploratory mode.
    ensure_objectives_not_high_angle_gz(objectives)

    # Local import to avoid a module-level circular import between
    # ``kayakgen.search.objectives`` (which imports from this module) and this
    # module's runtime path.
    from kayakgen.search.objectives import (
        OBJECTIVE_REJECTION_CLAIM_GATED,
        OBJECTIVE_REJECTION_DISPLAY_ONLY,
        is_objective_metric_admissible,
    )

    for objective in objectives:
        admissible, reason = is_objective_metric_admissible(
            objective.metric, explicit_exploratory=explicit_exploratory
        )
        if admissible:
            continue
        assert reason is not None
        if reason["code"] == OBJECTIVE_REJECTION_DISPLAY_ONLY:
            raise DisplayOnlyObjectiveRefusedError(objective.metric, reason)
        if reason["code"] == OBJECTIVE_REJECTION_CLAIM_GATED:
            claim_state = _SEARCH_ROLE_TO_CLAIM_STATE[reason["role"]]
            raise SearchObjectiveRefusedError(objective.metric, claim_state)
        raise UnknownSearchObjectiveError(objective.metric, reason)


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

    ``metrics`` hold reported values; resistance provenance supplies achieved
    numerical uncertainty for interval comparison. Warnings keep evaluator
    caveats attached to the point.
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

        from kayakgen.search.numerical_intervals import objective_interval

        left_interval = objective_interval(objective.metric, left.metrics[objective.metric], left.provenance)
        right_interval = objective_interval(objective.metric, right.metrics[objective.metric], right.provenance)
        if (left_interval is None or right_interval is None
                or left_interval.comparison_key != right_interval.comparison_key):
            return False
        left_low, left_high = left_interval.bounds
        right_low, right_high = right_interval.bounds

        if objective.direction == "min":
            if left_high > right_low:
                return False
            strictly_better = strictly_better or left_high < right_low
        else:
            if left_low < right_high:
                return False
            strictly_better = strictly_better or left_low > right_high

    return strictly_better


def pareto_front(
    candidates: list[CandidatePoint], objectives: list[Objective]
) -> list[CandidatePoint]:
    """Return non-dominated candidates in input order.

    Returned candidates are copies annotated with objective-related warnings.
    The input objects are not mutated.
    """

    from kayakgen.search.objectives import objective_has_numerical_evidence

    annotated = [
        _with_objective_warnings(candidate, objectives)
        for candidate in candidates
        if all(objective_has_numerical_evidence(obj.metric, candidate.provenance) for obj in objectives)
    ]
    front: list[CandidatePoint] = []
    for index, candidate in enumerate(annotated):
        if not any(
            other_index != index and dominates(other, candidate, objectives)
            for other_index, other in enumerate(annotated)
        ):
            front.append(candidate)
    return front


def _has_usable_metric(candidate: CandidatePoint, objective: Objective) -> bool:
    from kayakgen.search.objectives import objective_has_numerical_evidence

    if not objective_has_numerical_evidence(objective.metric, candidate.provenance):
        return False
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
