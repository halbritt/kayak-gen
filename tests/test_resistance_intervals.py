"""Strict reported winners use achieved bounds at common physical conditions."""

from __future__ import annotations

import pytest

from numerical_test_cases import assessed_curve
from kayakgen.search.active.runner import _final_frontier_keys
from kayakgen.search.active.spec import ObjectiveSpec
from kayakgen.search.pareto import CandidatePoint, Objective, dominates, pareto_front
from kayakgen.search.sweep import CandidateRecord


def point(key: str, number: int = 6, speed: float = 4.0, rho: float = 1025.0) -> CandidatePoint:
    curve = assessed_curve(number, speed, rho)
    return CandidatePoint(
        id=key,
        metrics={"Rt_N_last": curve.Rt_N[-1]},
        provenance={
            "Rt_N_last": {
                "numerical_quality": curve.metadata.numerical_quality.model_dump(mode="json")
            },
        },
    )


def record(key: str, number: int = 6, speed: float = 4.0) -> CandidateRecord:
    candidate = point(key, number, speed)
    return CandidateRecord(
        candidate_index=0,
        candidate_key=key,
        parameters={},
        attempted_hull={},
        status="complete",
        summary={
            **candidate.metrics,
            "resistance_numerical_quality": candidate.provenance["Rt_N_last"]["numerical_quality"],
        },
    )


def test_overlap_keeps_both_candidates_without_strict_winner() -> None:
    left, right = point("06", 6), point("18", 18)
    objectives = [Objective(metric="Rt_N_last", direction="min")]
    assert not dominates(left, right, objectives)
    assert not dominates(right, left, objectives)
    assert [p.id for p in pareto_front([left, right], objectives)] == ["06", "18"]


def test_separated_intervals_can_resolve_a_larger_gap() -> None:
    assert dominates(
        point("06", 6, 5.0), point("08", 8, 5.0), [Objective(metric="Rt_N_last", direction="min")]
    )


def test_missing_achieved_bounds_cannot_be_treated_as_zero_error() -> None:
    left = point("legacy", 6, 5.0)
    left.provenance["Rt_N_last"]["numerical_quality"].pop("absolute_uncertainty_N")
    assert not dominates(
        left, point("other", 8, 5.0), [Objective(metric="Rt_N_last", direction="min")]
    )


def test_active_final_frontier_uses_intervals_for_both_search_algorithms() -> None:
    objectives = [ObjectiveSpec(metric="Rt_N_last", direction="min")]
    assert _final_frontier_keys(
        [record("06", 6), record("18", 18)], objectives, exploratory=True
    ) == ["06", "18"]
    assert _final_frontier_keys(
        [record("06", 6, 5.0), record("08", 8, 5.0)], objectives, exploratory=True
    ) == ["06"]


def test_other_objective_cannot_hide_unresolved_resistance_order() -> None:
    left, right = point("06", 6), point("18", 18)
    left.metrics["GM0_m"] = 0.2
    right.metrics["GM0_m"] = 0.1
    assert not dominates(
        left,
        right,
        [
            Objective(metric="Rt_N_last", direction="min"),
            Objective(metric="GM0_m", direction="max"),
        ],
    )


def test_nsga_history_front_size_does_not_copy_diagnostic_sort_order() -> None:
    from kayakgen.search.active.nsga2 import Generation, Individual
    from kayakgen.search.active.runner import _build_generation_history, _candidate_key

    genomes = [{"beam_wl_m": 0.46}, {"beam_wl_m": 0.47}]
    keys = [_candidate_key("study", genome) for genome in genomes]
    records = {key: record(key, number) for key, number in zip(keys, [6, 18], strict=True)}
    generation = Generation(
        index=0, population=[Individual(genome=g) for g in genomes], fronts=[[0], [1]]
    )
    history = _build_generation_history(
        generation, records, [ObjectiveSpec(metric="Rt_N_last", direction="min")], "study"
    )
    assert history.frontier_size == 2
    assert history.objective_summary["Rt_N_last"]["point_estimate_min"] == pytest.approx(
        18.66724201599144
    )
    assert "best" not in history.objective_summary["Rt_N_last"]


def test_comparison_advisory_carries_achieved_intervals() -> None:
    from kayakgen.search.compare import CandidateSummary, _numerical_overlap_notes

    a, b = point("06", 6), point("18", 18)
    summaries = [
        CandidateSummary(
            candidate_index=i,
            candidate_key=p.id,
            status="complete",
            metrics=p.metrics,
            provenance=p.provenance,
        )
        for i, p in enumerate([a, b])
    ]
    notes = _numerical_overlap_notes(
        summaries,
        pareto_keys=["06", "18"],
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    assert len(notes) == 1
    assert notes[0].within_numerical_uncertainty
    assert not notes[0].within_evaluator_noise
    intervals = notes[0].numerical_intervals["Rt_N_last"]
    assert max(intervals[0][0], intervals[1][0]) < min(intervals[0][1], intervals[1][1])
    assert intervals[0][0] < a.metrics["Rt_N_last"] < intervals[0][1]


def test_different_comparison_speeds_cannot_establish_dominance() -> None:
    assert not dominates(
        point("4kn", 6, 4.0), point("6kn", 8, 6.0), [Objective(metric="Rt_N_last", direction="min")]
    )


def test_different_comparison_fluids_cannot_establish_dominance() -> None:
    assert not dominates(
        point("fresh", 6, 5.0, 1000.0),
        point("salt", 8, 5.0),
        [Objective(metric="Rt_N_last", direction="min")],
    )


def test_operating_context_must_match_when_present() -> None:
    left, right = point("light", 6, 5.0), point("heavy", 8, 5.0)
    objective = [Objective(metric="Rt_N_last", direction="min")]
    left.provenance["Rt_N_last"]["operating_context"] = {"load_kg": 100.0}
    assert not dominates(left, right, objective)
    right.provenance["Rt_N_last"]["operating_context"] = {"load_kg": 110.0}
    assert not dominates(left, right, objective)
    right.provenance["Rt_N_last"]["operating_context"] = {"load_kg": 100.0}
    assert dominates(left, right, objective)


def test_unavailable_policy_is_readable_but_cannot_join_any_ranked_frontier() -> None:
    from kayakgen.eval.contract import NumericalQuality

    left, right = point("06", 6), point("18", 18)
    for candidate in [left, right]:
        quality = candidate.provenance["Rt_N_last"]["numerical_quality"]
        quality.update(
            policy_version="unavailable_history_v99",
            absolute_uncertainty_N=[0.0],
            relative_changes=[0.0],
        )
        assert NumericalQuality.model_validate(quality).status == "converged"
    objectives = [Objective(metric="Rt_N_last", direction="min")]
    assert not dominates(left, right, objectives)
    assert pareto_front([left], objectives) == []
    assert pareto_front([left, right], objectives) == []
