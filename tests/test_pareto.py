"""Pure Pareto-frontier utilities."""

from __future__ import annotations

import pytest

from kayakgen.search.pareto import (
    HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS,
    HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
    CandidatePoint,
    HighAngleGzObjectiveRefusedError,
    Objective,
    dominates,
    ensure_objectives_not_high_angle_gz,
    pareto_front,
)


def test_dominates_requires_no_worse_and_one_strictly_better() -> None:
    objectives = [
        Objective(metric="drag_N", direction="min"),
        Objective(metric="gm0_m", direction="max"),
    ]
    efficient = CandidatePoint(id="efficient", metrics={"drag_N": 10.0, "gm0_m": 0.32})
    dominated = CandidatePoint(id="dominated", metrics={"drag_N": 12.0, "gm0_m": 0.32})
    tradeoff = CandidatePoint(id="tradeoff", metrics={"drag_N": 9.0, "gm0_m": 0.25})
    tied = CandidatePoint(id="tied", metrics={"drag_N": 10.0, "gm0_m": 0.32})

    assert dominates(efficient, dominated, objectives)
    assert not dominates(dominated, efficient, objectives)
    assert not dominates(efficient, tradeoff, objectives)
    assert not dominates(efficient, tied, objectives)


def test_pareto_front_keeps_only_non_dominated_candidates_in_input_order() -> None:
    objectives = [
        Objective(metric="drag_N", direction="min"),
        Objective(metric="gm0_m", direction="max"),
    ]
    candidates = [
        CandidatePoint(id="fast-stable", metrics={"drag_N": 10.0, "gm0_m": 0.35}),
        CandidatePoint(id="slow-unstable", metrics={"drag_N": 12.0, "gm0_m": 0.30}),
        CandidatePoint(id="fast-tippy", metrics={"drag_N": 9.0, "gm0_m": 0.25}),
    ]

    front = pareto_front(candidates, objectives)

    assert [candidate.id for candidate in front] == ["fast-stable", "fast-tippy"]


def test_missing_metrics_are_non_dominating_and_return_warning_copy() -> None:
    objectives = [
        Objective(metric="drag_N", direction="min"),
        Objective(metric="gm0_m", direction="max"),
    ]
    complete = CandidatePoint(id="complete", metrics={"drag_N": 10.0, "gm0_m": 0.30})
    incomplete = CandidatePoint(id="incomplete", metrics={"drag_N": 9.0})

    assert not dominates(incomplete, complete, objectives)
    assert not dominates(complete, incomplete, objectives)

    front = pareto_front([complete, incomplete], objectives)

    assert [candidate.id for candidate in front] == ["complete", "incomplete"]
    assert front[1].warnings == ("missing metric: gm0_m",)
    assert incomplete.warnings == ()


def test_existing_candidate_warnings_are_preserved_when_missing_metrics_are_added() -> None:
    objectives = [Objective(metric="gm0_m", direction="max")]
    candidate = CandidatePoint(
        id="candidate",
        metrics={},
        warnings=("mesh diagnostic pending",),
    )

    front = pareto_front([candidate], objectives)

    assert front[0].warnings == ("mesh diagnostic pending", "missing metric: gm0_m")


def test_exploratory_resistance_requires_explicit_accepted_use_provenance() -> None:
    objectives = [
        Objective(metric="gm0_m", direction="max"),
        Objective(metric="resistance_N", direction="min", accepted_use_required=True),
    ]
    accepted = CandidatePoint(
        id="accepted",
        metrics={"gm0_m": 0.35, "resistance_N": 11.0},
        provenance={"accepted_use": {"resistance_N": True}},
    )
    exploratory = CandidatePoint(
        id="exploratory",
        metrics={"gm0_m": 0.30, "resistance_N": 10.0},
    )

    assert not dominates(exploratory, accepted, objectives)
    assert not dominates(accepted, exploratory, objectives)

    front = pareto_front([accepted, exploratory], objectives)

    assert [candidate.id for candidate in front] == ["accepted", "exploratory"]
    assert front[1].warnings == ("metric requires accepted-use provenance: resistance_N",)


def test_accepted_use_can_be_attached_to_metric_provenance() -> None:
    objectives = [Objective(metric="resistance_N", direction="min", accepted_use_required=True)]
    faster = CandidatePoint(
        id="faster",
        metrics={"resistance_N": 10.0},
        provenance={"resistance_N": {"accepted_use": True}},
    )
    slower = CandidatePoint(
        id="slower",
        metrics={"resistance_N": 12.0},
        provenance={"resistance_N": {"accepted_use": True}},
    )

    assert dominates(faster, slower, objectives)
    assert [candidate.id for candidate in pareto_front([faster, slower], objectives)] == ["faster"]


@pytest.mark.parametrize("metric", sorted(HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS))
def test_high_angle_gz_metrics_are_refused_as_objectives(metric: str) -> None:
    """RFC 0043 stage 3: high-angle GZ keys cannot drive Pareto ranking."""
    with pytest.raises(HighAngleGzObjectiveRefusedError) as exc:
        ensure_objectives_not_high_angle_gz([Objective(metric=metric, direction="max")])

    assert exc.value.metric == metric
    assert exc.value.reason["token"] == HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN
    assert exc.value.reason["code"] == "high_angle_gz_display_only"


def test_ensure_objectives_not_high_angle_gz_allows_normal_metrics() -> None:
    """The gate is a no-op for every non-display-only metric."""
    ensure_objectives_not_high_angle_gz(
        [
            Objective(metric="GM0_m", direction="max"),
            Objective(metric="displacement_error_kg", direction="min"),
            Objective(metric="mesh_problem_count", direction="min"),
        ]
    )
