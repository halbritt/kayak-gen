"""Deterministic sweep records."""

from __future__ import annotations

import json
from pathlib import Path

from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.sweep import CandidateRecord, SweepSpec, expand_candidates, run_sweep


def _spec() -> SweepSpec:
    return SweepSpec(
        name="tiny",
        base_hull={"beam_oa_m": 0.60},
        variables={
            "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]},
            "Cp": {"kind": "values", "values": [0.54]},
        },
    )


def test_expand_candidates_is_deterministic() -> None:
    spec = _spec()
    first = expand_candidates(spec)
    second = expand_candidates(spec)
    assert first == second
    assert [row[0] for row in first] == [0, 1]
    assert first[0][2] == {"beam_wl_m": 0.50, "Cp": 0.54}
    assert first[0][1] != first[1][1]


def test_run_sweep_writes_records_and_summary(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    summary_header = (tmp_path / "summary.csv").read_text().splitlines()[0]
    assert run.completed_count == 2
    assert run.pending_count == 0
    assert run.failed_count == 0
    assert (tmp_path / "run.json").exists()
    assert (tmp_path / "spec.json").exists()
    assert summary_header.startswith("candidate_index")
    assert "param_beam_wl_m" in summary_header
    assert "param_Cp" in summary_header
    for record in run.candidates:
        assert record.hull_hash
        assert (tmp_path / record.artifacts["hull"]).exists()
        assert (tmp_path / record.artifacts["evaluation"]).exists()


def test_resume_marks_completed_records_as_skipped(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)
    resumed = run_sweep(_spec(), tmp_path, resume=True)
    assert resumed.completed_count == 0
    assert resumed.skipped_count == 2


def test_resume_preserves_pending_records(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    record_path = tmp_path / "candidates" / f"{run.candidates[0].candidate_key}.record.json"
    record = CandidateRecord.model_validate_json(record_path.read_text())
    record_path.write_text(record.model_copy(update={"status": "pending"}).model_dump_json(indent=2))

    resumed = run_sweep(_spec(), tmp_path, resume=True)

    assert resumed.pending_count == 1
    assert resumed.completed_count == 0
    assert resumed.skipped_count == 1
    assert resumed.candidates[0].status == "pending"
    assert CandidateRecord.model_validate_json(record_path.read_text()).status == "pending"


def test_invalid_candidate_is_recorded_as_failed(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="invalid",
        base_hull={"beam_oa_m": 0.55},
        variables={"beam_wl_m": {"kind": "values", "values": [0.60]}},
    )
    run = run_sweep(spec, tmp_path)
    assert run.failed_count == 1
    record = run.candidates[0]
    assert record.status == "failed"
    assert record.hull_hash is None
    assert record.error
    assert record.design_validity.findings == []
    assert record.design_warning_count == 0
    loaded = CandidateRecord.model_validate_json(
        (tmp_path / "candidates" / f"{record.candidate_key}.record.json").read_text()
    )
    assert loaded.attempted_hull["beam_wl_m"] == 0.60


def test_completed_candidate_records_design_validity_without_failure(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="advisory",
        base_hull={"length_m": 4.0, "beam_oa_m": 0.70},
        variables={"beam_wl_m": {"kind": "values", "values": [0.65]}},
    )

    run = run_sweep(spec, tmp_path)
    record = run.candidates[0]
    evaluation = json.loads((tmp_path / record.artifacts["evaluation"]).read_text())

    assert run.completed_count == 1
    assert run.failed_count == 0
    assert record.status == "complete"
    assert record.design_warning_count == 1
    assert record.design_validity.findings[0].code == CODE_L_BWL_LOW
    assert "design_warning_count" not in record.summary
    assert evaluation["design_validity"]["findings"][0]["code"] == CODE_L_BWL_LOW


def test_mesh_diagnostics_are_optional_candidate_artifacts(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="mesh",
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
        evaluators={"hydrostatics": True, "resistance": False, "mesh_diagnostics": True, "stl": False},
    )
    run = run_sweep(spec, tmp_path)
    record = run.candidates[0]
    assert "mesh_diagnostics" in record.artifacts
    assert (tmp_path / record.artifacts["mesh_diagnostics"]).exists()
    assert "mesh has boundary edges" in ",".join(record.warnings)


def test_stability_is_optional_candidate_artifact_and_summary(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="stability",
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
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
            "stability_moment_tolerance_kg_m": 0.2,
            "mesh_diagnostics": False,
            "stl": False,
        },
    )

    run = run_sweep(spec, tmp_path)
    record = run.candidates[0]
    evaluation = json.loads((tmp_path / record.artifacts["evaluation"]).read_text())
    summary_header = (tmp_path / "summary.csv").read_text().splitlines()[0]

    assert evaluation["stability"]["method"] == "equilibrium_trim"
    assert evaluation["stability"]["trim_angle_deg"] > 0.0
    assert record.summary["stability_status"] == "converged"
    assert record.summary["trim_angle_deg"] > 0.0
    assert abs(record.summary["moment_error_kg_m"]) <= 0.2
    assert "trim_angle_deg" in summary_header
    assert "moment_error_kg_m" in summary_header
    forbidden_gz = {
        "max_gz_m",
        "heel_at_max_gz_deg",
        "righting_moment_nm",
        "range_positive_stability_deg",
        "area_under_positive_gz_m_deg",
    }
    assert forbidden_gz.isdisjoint(record.summary)
    assert not any(field in summary_header for field in forbidden_gz)
