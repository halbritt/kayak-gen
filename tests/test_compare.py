"""Comparison reports over sweep runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kayakgen.cli.high_angle_gz import build_high_angle_gz_block
from kayakgen.eval.contract import EvaluationResult, LoadCase, ResistanceCurve, ResistanceMetadata
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.sweep_artifacts import HighAngleGzArtifact
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.compare import (
    ComparisonReport,
    build_comparison_report,
    write_comparison_report,
)
from kayakgen.search.pareto import (
    HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
    SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN,
    HighAngleGzObjectiveRefusedError,
    Objective,
    SearchObjectiveRefusedError,
)
from kayakgen.search.sweep import CandidateRecord, SweepRunRecord, SweepSpec, run_sweep
from kayakgen.services.artifact_store import ArtifactIntegrityError, FilesystemArtifactStore


def _spec() -> SweepSpec:
    return SweepSpec(
        name="compare-tiny",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )


def _store_backed_write_run(root: Path, run: SweepRunRecord) -> None:
    store = FilesystemArtifactStore(
        root,
        run_id=f"sweep-{run.spec_hash[:16]}-{root.name}",
    )
    store.put_json("sweep_run_record", run, canonical_path=root / "run.json")


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
        pending_count=0,
        completed_count=1,
        failed_count=0,
        skipped_count=0,
        candidates=[record],
    )
    (root / "run.json").write_text(run.model_dump_json(indent=2))


def _write_run_with_pending_candidate(root: Path) -> None:
    candidates = root / "candidates"
    candidates.mkdir(parents=True)
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)
    complete_eval = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydro,
        resistance=ResistanceCurve(
            V_knots=[3.5],
            Fn=[0.27],
            Rv_N=[6.0],
            Rw_N=[3.0],
            Rt_N=[9.0],
            metadata=_complete_calibrated_resistance_metadata(),
        ),
    )
    complete_eval_path = candidates / "candidate-complete.eval.json"
    complete_eval_path.write_text(complete_eval.model_dump_json(indent=2))
    complete_record = CandidateRecord(
        candidate_index=0,
        candidate_key="candidate-complete",
        parameters={},
        attempted_hull=hull.model_dump(mode="json"),
        status="complete",
        hull_hash=hull.hash(),
        artifacts={"evaluation": str(complete_eval_path.relative_to(root))},
        summary={
            "GM0_m": hydro.GM0_m,
            "Rt_N_last": 9.0,
        },
    )
    pending_record = CandidateRecord(
        candidate_index=1,
        candidate_key="candidate-pending",
        parameters={"beam_wl_m": 0.54},
        attempted_hull={"beam_oa_m": 0.60, "beam_wl_m": 0.54},
        status="pending",
        evaluator_settings={"hydrostatics": True, "resistance": False},
        evaluator_versions={"sweep_schema": "1"},
    )
    run = SweepRunRecord(
        name="pending-gate",
        spec_hash="pending-gate",
        candidate_count=2,
        pending_count=1,
        completed_count=1,
        failed_count=0,
        skipped_count=0,
        candidates=[complete_record, pending_record],
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


def test_default_objective_metadata_is_conservative(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)

    report = build_comparison_report(tmp_path)

    metadata = report.objective_metadata["GM0_m"]
    assert metadata.label == "Initial metacentric height"
    assert metadata.unit == "m"
    assert metadata.direction == "max"
    assert metadata.source_evaluator == "hydrostatics"
    assert metadata.claim_state_required is None
    assert metadata.accepted_use_required is None
    assert metadata.role == "default_conservative"
    assert "Rt_N_last" not in report.objective_metadata


def test_default_comparison_excludes_raw_resistance_metric(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for record in run.candidates:
        record.summary["Rt_N_last"] = 12.0
        record.summary["resistance_use"] = "comparative_filter"
    _store_backed_write_run(tmp_path, run)

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


def test_pending_candidates_remain_visible_but_not_frontier_members(tmp_path: Path) -> None:
    _write_run_with_pending_candidate(tmp_path)

    report = build_comparison_report(tmp_path)

    assert report.pareto_front_keys == ["candidate-complete"]
    pending = next(summary for summary in report.candidate_summaries if summary.status == "pending")
    assert pending.objective_values["GM0_m"] is None
    assert "candidate status not eligible for pareto: pending" in pending.warnings


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
    # D048: unknown metrics are admissible only under the exploratory opt-in
    # (the RFC 0044 gate refuses unregistered objectives by default), so the
    # unsupported-objective warning behavior is pinned behind the flag.
    run_sweep(_spec(), tmp_path)

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="not_a_metric", direction="min")],
        explicit_exploratory=True,
    )

    assert "unsupported objective: not_a_metric" in report.warnings
    assert all(
        "missing metric: not_a_metric" in summary.warnings
        for summary in report.candidate_summaries
    )


def test_raw_resistance_objective_without_opt_in_is_refused(tmp_path: Path) -> None:
    """D048 / RFC 0044: raw_unvalidated objectives REFUSE without the opt-in.

    The previous auto-downgrade to a labeled ``exploratory_frontier`` was a
    contract violation of the RELEASE_DISCIPLINE no-claim invariant; the
    labeled behavior survives only behind ``explicit_exploratory=True``.
    """
    run = run_sweep(_spec(), tmp_path)
    for index, record in enumerate(run.candidates):
        record.summary["Rt_N_last"] = float(10 + index)
        record.summary["resistance_use"] = "comparative_filter"
    _store_backed_write_run(tmp_path, run)

    with pytest.raises(SearchObjectiveRefusedError) as exc:
        build_comparison_report(
            tmp_path,
            objectives=[Objective(metric="Rt_N_last", direction="min")],
        )

    assert exc.value.metric == "Rt_N_last"
    assert exc.value.reason["code"] == "search_objective_claim_not_admissible"
    assert exc.value.reason["token"] == SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN
    assert exc.value.reason["claim_state"] == "raw_unvalidated"
    assert SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN in str(exc.value)


def test_design_fitness_objective_without_opt_in_is_refused(tmp_path: Path) -> None:
    """D048: uncalibrated_comparative (claim_gated_reserved) refuses too."""
    _write_run_with_resistance_metadata(
        tmp_path,
        _complete_calibrated_resistance_metadata(),
        summary_extra={"design_fitness": 0.75},
    )

    with pytest.raises(SearchObjectiveRefusedError) as exc:
        build_comparison_report(
            tmp_path,
            objectives=[Objective(metric="design_fitness", direction="max")],
        )

    assert exc.value.metric == "design_fitness"
    assert exc.value.reason["token"] == SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN
    assert exc.value.reason["claim_state"] == "uncalibrated_comparative"


def test_raw_resistance_objective_is_exploratory_and_requires_provenance(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for index, record in enumerate(run.candidates):
        record.summary["Rt_N_last"] = float(10 + index)
        record.summary["resistance_use"] = "comparative_filter"
    _store_backed_write_run(tmp_path, run)

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="Rt_N_last", direction="min")],
        explicit_exploratory=True,
    )

    assert report.report_kind == "exploratory_frontier"
    assert report.objectives[0].accepted_use_required is True
    assert "exploratory frontier includes resistance objective" in report.warnings
    assert all(
        "metric requires accepted-use provenance: Rt_N_last" in summary.warnings
        for summary in report.candidate_summaries
    )
    metadata = report.objective_metadata["Rt_N_last"]
    assert metadata.label == "Total resistance at last sweep speed"
    assert metadata.unit == "N"
    assert metadata.source_evaluator == "resistance"
    assert metadata.claim_state_required == "calibrated_model"
    assert metadata.accepted_use_required == "final_prediction"
    assert metadata.role == "explicit_exploratory"


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
        explicit_exploratory=True,
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
        explicit_exploratory=True,
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
        explicit_exploratory=True,
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
        explicit_exploratory=True,
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
        explicit_exploratory=True,
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
        explicit_exploratory=True,
    )
    summary = report.candidate_summaries[0]

    assert report.objectives[0].accepted_use_required is True
    assert summary.provenance["design_fitness"]["accepted_use"] is False
    assert summary.provenance["design_fitness"]["claim_state"] == "calibrated_model"
    assert "metric requires accepted-use provenance: design_fitness" in summary.warnings
    assert "exploratory frontier includes final design-fitness objective" in report.warnings
    metadata = report.objective_metadata["design_fitness"]
    assert metadata.source_evaluator == "reserved_claim_gate"
    assert metadata.claim_state_required == "validated_design_fitness"
    assert metadata.accepted_use_required == "final_design_fitness"
    assert metadata.role == "claim_gated_reserved"


def test_unsupported_objective_metadata_is_explicit(tmp_path: Path) -> None:
    # D048: unknown metrics need the exploratory opt-in (see comment above).
    run_sweep(_spec(), tmp_path)

    report = build_comparison_report(
        tmp_path,
        objectives=[Objective(metric="not_a_metric", direction="min")],
        explicit_exploratory=True,
    )

    metadata = report.objective_metadata["not_a_metric"]
    assert metadata.label == "not_a_metric"
    assert metadata.unit == "unknown"
    assert metadata.direction == "min"
    assert metadata.source_evaluator == "unknown"
    assert metadata.role == "unsupported"


def test_write_comparison_report_round_trips(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path / "run")
    out = tmp_path / "comparison.json"

    report = write_comparison_report(tmp_path / "run", out)
    loaded = ComparisonReport.model_validate_json(out.read_text())

    assert loaded == report
    assert loaded.run_name == "compare-tiny"


# ---------------------------------------------------------------------------
# RFC 0043 stage 3 (display-only) high-angle GZ comparison surfacing.
# ---------------------------------------------------------------------------


HIGH_ANGLE_KEYS = (
    "max_gz_m",
    "heel_at_max_gz_deg",
    "range_positive_stability_deg",
)


def _build_two_candidate_run(
    root: Path,
    *,
    attach_high_angle_to: set[str] | None = None,
    high_angle_blocks: dict[str, dict] | None = None,
) -> SweepRunRecord:
    """Build a minimal sweep run with two completed candidates.

    When ``attach_high_angle_to`` includes a candidate key, a per-candidate
    ``high_angle_gz.json`` artifact is written under ``candidates/<key>/``
    and the candidate record is updated to point at it. Callers may pass
    ``high_angle_blocks`` to override the artifact JSON for a specific key
    (e.g. to fabricate an "unavailable" block).
    """

    attach_high_angle_to = attach_high_angle_to or set()
    high_angle_blocks = high_angle_blocks or {}
    candidates_dir = root / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)

    records: list[CandidateRecord] = []
    for index, key in enumerate(("candidate-a", "candidate-b")):
        evaluation = EvaluationResult(hull_hash=hull.hash(), hydrostatics=hydro)
        eval_path = candidates_dir / f"{key}.eval.json"
        eval_path.write_text(evaluation.model_dump_json(indent=2))

        artifacts = {"evaluation": str(eval_path.relative_to(root))}
        high_angle_artifact: HighAngleGzArtifact | None = None

        if key in attach_high_angle_to:
            candidate_dir = candidates_dir / key
            candidate_dir.mkdir(parents=True, exist_ok=True)
            block = high_angle_blocks.get(key)
            if block is None:
                block = build_high_angle_gz_block(
                    hull,
                    LoadCase(),
                    heel_grid_deg=[0.0, 5.0, 10.0, 15.0, 20.0],
                )
            artifact_path = candidate_dir / "high_angle_gz.json"
            artifact_path.write_text(json.dumps(block, indent=2))
            data = artifact_path.read_bytes()
            high_angle_artifact = HighAngleGzArtifact(
                path=str(artifact_path.relative_to(root)),
                bytes=len(data),
                sha256=__import__("hashlib").sha256(data).hexdigest(),
            )
            artifacts["high_angle_gz"] = high_angle_artifact.path

        record = CandidateRecord(
            candidate_index=index,
            candidate_key=key,
            parameters={},
            attempted_hull=hull.model_dump(mode="json"),
            status="complete",
            hull_hash=hull.hash(),
            artifacts=artifacts,
            summary={
                "GM0_m": hydro.GM0_m,
                "displaced_mass_kg": hydro.displaced_mass_kg,
            },
            high_angle_gz_artifact=high_angle_artifact,
        )
        records.append(record)

    run = SweepRunRecord(
        name="stage3-fixture",
        spec_hash="stage3-fixture",
        candidate_count=len(records),
        pending_count=0,
        completed_count=len(records),
        failed_count=0,
        skipped_count=0,
        candidates=records,
    )
    (root / "run.json").write_text(run.model_dump_json(indent=2))
    return run


def _unavailable_block_fixture() -> dict:
    return {
        "available": False,
        "result_semantics": "unvalidated_hydrostatic_comparison",
        "body_profile": "generated_hull_plus_deck_closed_body_v1",
        "heel_grid_deg": [0.0, 5.0, 10.0],
        "unavailable_reason": {
            "code": "synthetic_body_not_allowed_for_real_gz",
            "detail": "evaluate_gz_curve returned status != computed",
        },
        "heel_points": [],
        "summary": None,
        "assumptions": ["fixture_assumption"],
        "warnings": [
            "deck_immersion_assumption",
            "flooding_not_modeled",
            "not_safety_or_seaworthiness_claim",
            "active_paddler_not_modeled",
            "sealed_body_assumption",
        ],
    }


def test_compare_omits_high_angle_keys_when_no_artifacts(tmp_path: Path) -> None:
    """No high-angle artifacts means no high-angle keys appear (additive shape)."""
    _build_two_candidate_run(tmp_path)

    report = build_comparison_report(tmp_path)

    assert report.high_angle_gz_columns is False
    for summary in report.candidate_summaries:
        assert summary.high_angle_gz_display is None

    # Defaults remain unchanged: no high-angle key may be a Pareto objective.
    for objective in report.objectives:
        assert objective.metric not in HIGH_ANGLE_KEYS


def test_compare_attaches_high_angle_display_when_artifacts_present(
    tmp_path: Path,
) -> None:
    """Each candidate with an artifact gets a display dict; flag flips on."""
    _build_two_candidate_run(tmp_path, attach_high_angle_to={"candidate-a"})

    report = build_comparison_report(tmp_path)

    assert report.high_angle_gz_columns is True
    by_key = {summary.candidate_key: summary for summary in report.candidate_summaries}
    attached = by_key["candidate-a"].high_angle_gz_display
    other = by_key["candidate-b"].high_angle_gz_display
    assert attached is not None
    assert other is None

    assert attached.body_profile == "generated_hull_plus_deck_closed_body_v1"
    assert attached.result_semantics == "unvalidated_hydrostatic_comparison"
    # Body provenance fields travel adjacent to the value.
    assert attached.method is not None
    assert attached.body_ref is not None
    assert attached.body_type is not None
    # Either fully converged (summary present) or partial (None). Either is
    # legal — the field still exists on the display dict.
    if attached.available:
        # summary may still be None if not every heel point converged.
        pass

    # Frontier ranking is unchanged by display surfacing.
    assert set(report.pareto_front_keys).issubset({"candidate-a", "candidate-b"})


def test_compare_refuses_corrupt_indexed_run_record(tmp_path: Path) -> None:
    """Workflow 0067: store/index-backed run.json reads are rehash-verified."""

    run_sweep(_spec(), tmp_path)
    forged = SweepRunRecord(
        name="forged",
        spec_hash="forged",
        candidate_count=0,
        pending_count=0,
        completed_count=0,
        failed_count=0,
        skipped_count=0,
        candidates=[],
    )
    (tmp_path / "run.json").write_text(forged.model_dump_json(indent=2))

    with pytest.raises(ArtifactIntegrityError):
        build_comparison_report(tmp_path)


def test_compare_refuses_corrupt_hash_recorded_high_angle_artifact(
    tmp_path: Path,
) -> None:
    """Workflow 0067: record-carried high-angle hashes are enforced."""

    _build_two_candidate_run(tmp_path, attach_high_angle_to={"candidate-a"})
    artifact_path = tmp_path / "candidates" / "candidate-a" / "high_angle_gz.json"
    block = json.loads(artifact_path.read_text())
    block["body_profile"] = "tampered-profile"
    artifact_path.write_text(json.dumps(block, indent=2))

    with pytest.raises(ArtifactIntegrityError):
        build_comparison_report(tmp_path)


def test_compare_high_angle_display_carries_warnings_and_assumptions(
    tmp_path: Path,
) -> None:
    """Surface warnings + evaluator assumptions are mirrored verbatim."""
    block = {
        "available": True,
        "result_semantics": "unvalidated_hydrostatic_comparison",
        "body_profile": "generated_hull_plus_deck_closed_body_v1",
        "method": "fixed_trim_generated_body_v1",
        "body_ref": "fixture-body",
        "body_type": "generated_hull_plus_deck_closed_body_v1",
        "body_diagnostic_ref": "fixture-diag",
        "heel_grid_deg": [0.0, 5.0, 10.0],
        "heel_points": [],
        "summary": {
            "max_gz": 0.42,
            "heel_at_max_gz": 25.0,
            "range_positive_stability_deg": 55.0,
        },
        "assumptions": ["fixed_trim_assumption", "load_case_centered"],
        "warnings": [
            "deck_immersion_assumption",
            "flooding_not_modeled",
            "not_safety_or_seaworthiness_claim",
            "active_paddler_not_modeled",
            "sealed_body_assumption",
            "evaluator_emitted_extra_warning",
        ],
    }
    _build_two_candidate_run(
        tmp_path,
        attach_high_angle_to={"candidate-a"},
        high_angle_blocks={"candidate-a": block},
    )

    report = build_comparison_report(tmp_path)

    display = next(
        summary.high_angle_gz_display
        for summary in report.candidate_summaries
        if summary.candidate_key == "candidate-a"
    )
    assert display is not None
    assert display.available is True
    assert display.max_gz_m == pytest.approx(0.42)
    assert display.heel_at_max_gz_deg == pytest.approx(25.0)
    assert display.range_positive_stability_deg == pytest.approx(55.0)
    assert "evaluator_emitted_extra_warning" in display.warnings
    assert "deck_immersion_assumption" in display.warnings
    assert display.assumptions == ["fixed_trim_assumption", "load_case_centered"]
    # body/load/trim provenance lives adjacent on the same display object.
    assert display.body_ref == "fixture-body"
    assert display.body_type == "generated_hull_plus_deck_closed_body_v1"
    assert display.body_diagnostic_ref == "fixture-diag"
    assert display.method == "fixed_trim_generated_body_v1"


def test_compare_high_angle_unavailable_artifact_renders_unavailable_reason(
    tmp_path: Path,
) -> None:
    """Unavailable artifacts mirror ``unavailable_reason`` and null the summary."""
    _build_two_candidate_run(
        tmp_path,
        attach_high_angle_to={"candidate-a"},
        high_angle_blocks={"candidate-a": _unavailable_block_fixture()},
    )

    report = build_comparison_report(tmp_path)

    display = next(
        summary.high_angle_gz_display
        for summary in report.candidate_summaries
        if summary.candidate_key == "candidate-a"
    )
    assert display is not None
    assert display.available is False
    assert display.max_gz_m is None
    assert display.heel_at_max_gz_deg is None
    assert display.range_positive_stability_deg is None
    assert display.unavailable_reason is not None
    assert display.unavailable_reason["code"] == "synthetic_body_not_allowed_for_real_gz"
    assert "sealed_body_assumption" in display.warnings


def test_compare_default_objectives_do_not_include_high_angle_keys(
    tmp_path: Path,
) -> None:
    """Defaults remain unchanged whether or not artifacts are present."""
    _build_two_candidate_run(tmp_path, attach_high_angle_to={"candidate-a"})

    report = build_comparison_report(tmp_path)

    metrics = {objective.metric for objective in report.objectives}
    assert metrics.isdisjoint(HIGH_ANGLE_KEYS)
    for metric in HIGH_ANGLE_KEYS:
        assert metric not in report.objective_metadata


def test_compare_refuses_high_angle_objective(tmp_path: Path) -> None:
    """Caller-supplied ``-o max_gz_m:max`` is rejected with a structured reason."""
    _build_two_candidate_run(tmp_path, attach_high_angle_to={"candidate-a"})

    with pytest.raises(HighAngleGzObjectiveRefusedError) as exc:
        build_comparison_report(
            tmp_path,
            objectives=[Objective(metric="max_gz_m", direction="max")],
        )

    assert exc.value.metric == "max_gz_m"
    assert exc.value.reason["code"] == "high_angle_gz_display_only"
    assert exc.value.reason["token"] == HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN
    assert exc.value.reason["metric"] == "max_gz_m"
    assert HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN in str(exc.value)


def test_compare_frontier_membership_independent_of_high_angle_artifacts(
    tmp_path: Path,
) -> None:
    """Pareto frontier ranks identically whether or not the artifact is attached."""
    bare_root = tmp_path / "bare"
    attached_root = tmp_path / "attached"
    bare_root.mkdir()
    attached_root.mkdir()
    _build_two_candidate_run(bare_root)
    _build_two_candidate_run(
        attached_root, attach_high_angle_to={"candidate-a", "candidate-b"}
    )

    bare_report = build_comparison_report(bare_root)
    attached_report = build_comparison_report(attached_root)

    assert bare_report.pareto_front_keys == attached_report.pareto_front_keys
    assert [obj.metric for obj in bare_report.objectives] == [
        obj.metric for obj in attached_report.objectives
    ]
    # Display surfacing does NOT mutate frontier eligibility.
    assert attached_report.high_angle_gz_columns is True
    assert bare_report.high_angle_gz_columns is False
