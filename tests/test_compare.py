"""Comparison reports over sweep runs."""

from __future__ import annotations

from pathlib import Path

from kayakgen.search.compare import (
    ComparisonReport,
    build_comparison_report,
    write_comparison_report,
)
from kayakgen.search.pareto import Objective
from kayakgen.search.sweep import SweepSpec, run_sweep


def _spec() -> SweepSpec:
    return SweepSpec(
        name="compare-tiny",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )


def test_default_comparison_report_is_deterministic(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)

    first = build_comparison_report(tmp_path)
    second = build_comparison_report(tmp_path)

    assert first == second
    assert first.report_kind == "pareto_frontier"
    assert [objective.metric for objective in first.objectives] == ["GM0_m"]
    assert first.pareto_front_keys
    assert all("GM0_m" in summary.objective_values for summary in first.candidate_summaries)


def test_default_comparison_excludes_raw_resistance_metric(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for record in run.candidates:
        record.summary["Rt_N_last"] = 12.0
        record.summary["resistance_use"] = "comparative_filter"
    (tmp_path / "run.json").write_text(run.model_dump_json(indent=2))

    report = build_comparison_report(tmp_path)

    assert report.report_kind == "pareto_frontier"
    assert "Rt_N_last" not in [objective.metric for objective in report.objectives]
    assert all("Rt_N_last" in summary.metrics for summary in report.candidate_summaries)


def test_missing_objective_metrics_are_candidate_warnings(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)

    report = build_comparison_report(
        tmp_path,
        objectives=[
            Objective(metric="GM0_m", direction="max"),
            Objective(metric="mesh_problem_count", direction="min"),
        ],
    )

    assert all(
        "missing metric: mesh_problem_count" in summary.warnings
        for summary in report.candidate_summaries
    )


def test_failed_candidates_remain_visible_but_not_frontier_members(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="invalid",
        base_hull={"beam_oa_m": 0.55},
        variables={"beam_wl_m": {"kind": "values", "values": [0.60]}},
    )
    run_sweep(spec, tmp_path)

    report = build_comparison_report(tmp_path)

    assert report.pareto_front_keys == []
    assert len(report.candidate_summaries) == 1
    summary = report.candidate_summaries[0]
    assert summary.status == "failed"
    assert summary.error
    assert "candidate status not eligible for pareto: failed" in summary.warnings


def test_skipped_candidates_remain_visible_but_not_frontier_members(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)
    run_sweep(_spec(), tmp_path, resume=True)

    report = build_comparison_report(tmp_path)

    assert report.pareto_front_keys == []
    assert {summary.status for summary in report.candidate_summaries} == {"skipped"}
    assert all(
        "candidate status not eligible for pareto: skipped" in summary.warnings
        for summary in report.candidate_summaries
    )


def test_no_usable_default_objectives_is_report_warning(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="invalid",
        base_hull={"beam_oa_m": 0.55},
        variables={"beam_wl_m": {"kind": "values", "values": [0.60]}},
    )
    run_sweep(spec, tmp_path)

    report = build_comparison_report(tmp_path)

    assert report.objectives == []
    assert report.pareto_front_keys == []
    assert "no default objectives available" in report.warnings


def test_unsupported_explicit_objective_is_report_and_candidate_warning(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="not_a_metric", direction="min")],
    )

    assert "unsupported objective: not_a_metric" in report.warnings
    assert all(
        "missing metric: not_a_metric" in summary.warnings
        for summary in report.candidate_summaries
    )


def test_raw_resistance_objective_is_exploratory_and_requires_provenance(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for index, record in enumerate(run.candidates):
        record.summary["Rt_N_last"] = float(10 + index)
        record.summary["resistance_use"] = "comparative_filter"
    (tmp_path / "run.json").write_text(run.model_dump_json(indent=2))

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )

    assert report.report_kind == "exploratory_frontier"
    assert report.objectives[0].accepted_use_required is True
    assert "exploratory frontier includes resistance objective" in report.warnings
    assert all(
        "metric requires accepted-use provenance: Rt_N_last" in summary.warnings
        for summary in report.candidate_summaries
    )


def test_write_comparison_report_round_trips(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path / "run")
    out = tmp_path / "comparison.json"

    report = write_comparison_report(tmp_path / "run", out)
    loaded = ComparisonReport.model_validate_json(out.read_text())

    assert loaded == report
    assert loaded.run_name == "compare-tiny"
