"""Deterministic sweep records."""

from __future__ import annotations

from pathlib import Path

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
    assert run.completed_count == 2
    assert run.failed_count == 0
    assert (tmp_path / "run.json").exists()
    assert (tmp_path / "spec.json").exists()
    assert (tmp_path / "summary.csv").read_text().startswith("candidate_index")
    for record in run.candidates:
        assert record.hull_hash
        assert (tmp_path / record.artifacts["hull"]).exists()
        assert (tmp_path / record.artifacts["evaluation"]).exists()


def test_resume_marks_completed_records_as_skipped(tmp_path: Path) -> None:
    run_sweep(_spec(), tmp_path)
    resumed = run_sweep(_spec(), tmp_path, resume=True)
    assert resumed.completed_count == 0
    assert resumed.skipped_count == 2


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
    loaded = CandidateRecord.model_validate_json(
        (tmp_path / "candidates" / f"{record.candidate_key}.record.json").read_text()
    )
    assert loaded.attempted_hull["beam_wl_m"] == 0.60


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
