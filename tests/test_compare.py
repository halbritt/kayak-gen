"""Comparison reports over sweep runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.eval.contract import EvaluationResult, ResistanceCurve, ResistanceMetadata
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.compare import (
    ComparisonReport,
    build_comparison_report,
    write_comparison_report,
)
from kayakgen.search.pareto import Objective
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord, SweepSpec, run_sweep


def _spec() -> SweepSpec:
    return SweepSpec(
        name="compare-tiny",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )


def _write_run_with_resistance_metadata(
    root: Path,
    metadata: ResistanceMetadata,
    *,
    summary_extra: dict[str, float] | None = None,
) -> None:
    candidates = root / "candidates"
    candidates.mkdir(parents=True)
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)
    evaluation = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        resistance=ResistanceCurve(
            V_knots=[3.5],
            Fn=[0.27],
            Rv_N=[6.0],
            Rw_N=[3.0],
            Rt_N=[9.0],
            metadata=metadata,
        ),
    )
    eval_path = candidates / "candidate-a.eval.json"
    eval_path.write_text(evaluation.model_dump_json(indent=2))
    summary = {
        "GM0_m": hydro.GM0_m,
        "Rt_N_last": 9.0,
    }
    summary.update(summary_extra or {})
    record = CandidateRecord(
        candidate_index=0,
        candidate_key="candidate-a",
        parameters={},
        attempted_hull=hull.model_dump(mode="json"),
        status="complete",
        hull_hash=hull.hash(),
        artifacts={"evaluation": str(eval_path.relative_to(root))},
        summary=summary,
    )
    run = SweepRunRecord(
        name="claim-gate",
        spec_hash="claim-gate",
        candidate_count=1,
        completed_count=1,
        failed_count=0,
        skipped_count=0,
        candidates=[record],
    )
    (root / "run.json").write_text(run.model_dump_json(indent=2))


def _complete_calibrated_resistance_metadata(
    *,
    fit_status: str = "accepted_fit",
    calibration_fixture_ids: list[str] | None = None,
    validation_fixture_ids: list[str] | None = None,
) -> ResistanceMetadata:
    return ResistanceMetadata(
        claim_state="calibrated_model",
        calibration_status="calibrated",
        accepted_uses=["final_prediction"],
        calibration_fixture_ids=(
            ["accepted-fixture-001"]
            if calibration_fixture_ids is None
            else calibration_fixture_ids
        ),
        validation_fixture_ids=(
            ["validation-fixture-001"]
            if validation_fixture_ids is None
            else validation_fixture_ids
        ),
        model_version="resistance-test-v1",
        fit_status=fit_status,
        fit_metrics={
            "force_rmse_N": 0.42,
            "mean_absolute_percentage_error": 2.5,
        },
        validity_envelope={"Fn": [0.25, 0.50], "L_B": [8.0, 12.0]},
        warnings=[],
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


def test_default_comparison_uses_stability_displacement_error_when_available(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="compare-stability",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
        evaluators={
            "hydrostatics": True,
            "resistance": False,
            "stability": True,
            "stability_equilibrium": True,
            "stability_load_case": {
                "components": [
                    {
                        "name": "test-load",
                        "mass_kg": 90.0,
                        "x_m": 0.20,
                        "kg_above_keel_m": 0.25,
                    }
                ]
            },
            "stability_tolerance_kg": 0.2,
            "stability_moment_tolerance_kg_m": 0.3,
            "mesh_diagnostics": False,
            "stl": False,
        },
    )
    run_sweep(spec, tmp_path)

    report = build_comparison_report(tmp_path)

    assert "displacement_error_kg" in [objective.metric for objective in report.objectives]
    assert all(
        "displacement_error_kg" in summary.metrics
        for summary in report.candidate_summaries
    )


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


def test_comparison_preserves_design_validity_without_changing_frontier(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="compare-advisory",
        base_hull={"length_m": 4.0, "beam_oa_m": 0.70},
        variables={"beam_wl_m": {"kind": "values", "values": [0.65]}},
    )
    run_sweep(spec, tmp_path)

    report = build_comparison_report(tmp_path)
    summary = report.candidate_summaries[0]

    assert report.pareto_front_keys == [summary.candidate_key]
    assert summary.design_warning_count == 1
    assert report.design_warning_count == 1
    assert summary.design_validity.findings[0].code == CODE_L_BWL_LOW
    assert report.design_validity[summary.candidate_key].findings[0].code == CODE_L_BWL_LOW
    assert "design_warning_count" not in summary.metrics


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


def test_forged_legacy_final_prediction_metadata_is_not_accepted(tmp_path: Path) -> None:
    _write_run_with_resistance_metadata(
        tmp_path,
        ResistanceMetadata(
            calibration_status="calibrated",
            accepted_use=["final_prediction"],
        ),
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    summary = report.candidate_summaries[0]

    assert summary.provenance["Rt_N_last"]["accepted_use"] is False
    assert summary.provenance["Rt_N_last"]["claim_state"] == "uncalibrated_comparative"
    assert "metric requires accepted-use provenance: Rt_N_last" in summary.warnings


def test_complete_accepted_fit_contract_allows_resistance_objective(
    tmp_path: Path,
) -> None:
    _write_run_with_resistance_metadata(
        tmp_path,
        _complete_calibrated_resistance_metadata(),
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    summary = report.candidate_summaries[0]

    assert summary.provenance["Rt_N_last"]["accepted_use"] is True
    assert summary.provenance["Rt_N_last"]["fit_status"] == "accepted_fit"
    assert summary.provenance["Rt_N_last"]["fit_metrics"]
    assert "metric requires accepted-use provenance: Rt_N_last" not in summary.warnings


@pytest.mark.parametrize("fit_status", ["candidate_fit", "rejected_fit"])
def test_comparison_rejects_candidate_or_rejected_fit_with_metrics(
    tmp_path: Path,
    fit_status: str,
) -> None:
    _write_run_with_resistance_metadata(
        tmp_path,
        _complete_calibrated_resistance_metadata(fit_status=fit_status),
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    summary = report.candidate_summaries[0]

    assert summary.provenance["Rt_N_last"]["accepted_use"] is False
    assert summary.provenance["Rt_N_last"]["fit_status"] == fit_status
    assert summary.provenance["Rt_N_last"]["fit_metrics"]
    assert "metric requires accepted-use provenance: Rt_N_last" in summary.warnings


def test_comparison_rejects_validation_only_resistance_metadata(
    tmp_path: Path,
) -> None:
    _write_run_with_resistance_metadata(
        tmp_path,
        _complete_calibrated_resistance_metadata(
            calibration_fixture_ids=[],
            validation_fixture_ids=["validation-fixture-001"],
        ),
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    summary = report.candidate_summaries[0]

    assert summary.provenance["Rt_N_last"]["accepted_use"] is False
    assert summary.provenance["Rt_N_last"]["calibration_fixture_ids"] == []
    assert summary.provenance["Rt_N_last"]["validation_fixture_ids"] == [
        "validation-fixture-001"
    ]
    assert "metric requires accepted-use provenance: Rt_N_last" in summary.warnings


@pytest.mark.parametrize(
    ("metadata_update", "expected_missing"),
    [
        ({"calibration_fixture_ids": []}, "calibration_fixture_ids"),
        ({"model_version": None}, "model_version"),
        ({"fit_status": None, "fit_metrics": {}}, "fit_status"),
        ({"fit_metrics": {}}, "fit_metrics"),
        ({"validity_envelope": None}, "validity_envelope"),
    ],
)
def test_calibrated_prediction_requires_full_claim_contract(
    tmp_path: Path,
    metadata_update: dict[str, object],
    expected_missing: str,
) -> None:
    metadata_values = {
        "claim_state": "calibrated_model",
        "calibration_status": "calibrated",
        "accepted_uses": ["final_prediction"],
        "calibration_fixture_ids": ["accepted-fixture-001"],
        "validation_fixture_ids": ["validation-fixture-001"],
        "model_version": "resistance-test-v1",
        "fit_status": "accepted_fit",
        "fit_metrics": {
            "force_rmse_N": 0.42,
            "mean_absolute_percentage_error": 2.5,
        },
        "validity_envelope": {"Fn": [0.25, 0.50]},
        "warnings": [],
    } | metadata_update
    _write_run_with_resistance_metadata(
        tmp_path,
        ResistanceMetadata.model_validate(metadata_values),
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
    )
    summary = report.candidate_summaries[0]

    assert summary.provenance["Rt_N_last"]["accepted_use"] is False
    assert summary.provenance["Rt_N_last"][expected_missing] in (None, [], {})
    assert "metric requires accepted-use provenance: Rt_N_last" in summary.warnings


def test_calibrated_resistance_is_not_final_design_fitness(tmp_path: Path) -> None:
    _write_run_with_resistance_metadata(
        tmp_path,
        _complete_calibrated_resistance_metadata(),
        summary_extra={"design_fitness": 0.75},
    )

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="design_fitness", direction="max")],
    )
    summary = report.candidate_summaries[0]

    assert report.objectives[0].accepted_use_required is True
    assert summary.provenance["design_fitness"]["accepted_use"] is False
    assert summary.provenance["design_fitness"]["claim_state"] == "calibrated_model"
    assert "metric requires accepted-use provenance: design_fitness" in summary.warnings
    assert "exploratory frontier includes final design-fitness objective" in report.warnings


def test_write_comparison_report_round_trips(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path / "run")
    out = tmp_path / "comparison.json"

    report = write_comparison_report(tmp_path / "run", out)
    loaded = ComparisonReport.model_validate_json(out.read_text())

    assert loaded == report
    assert loaded.run_name == "compare-tiny"
