"""Deterministic sweep records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kayakgen.io.stl import write_stl
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.objectives import DEFAULT_OBJECTIVE_METRICS
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


def _stl_spec() -> SweepSpec:
    return SweepSpec(
        name="stl",
        base_hull={"beam_oa_m": 0.60},
        variables={
            "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]},
            "Cp": {"kind": "values", "values": [0.54]},
        },
        evaluators={"hydrostatics": True, "resistance": False, "stl": True},
    )


def test_sweep_stl_off_does_not_write_stl_files(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for record in run.candidates:
        assert record.stl_artifacts is None
        candidate_dir = tmp_path / "candidates" / record.candidate_key
        assert not (candidate_dir / "hull.stl").exists()
        assert not (candidate_dir / "deck.stl").exists()
        assert "stl_hull" not in record.artifacts
        assert "stl_deck" not in record.artifacts
    # Ensure no stray .stl files anywhere under candidates/
    assert list((tmp_path / "candidates").rglob("*.stl")) == []


def test_sweep_stl_on_writes_hull_and_deck_per_candidate(tmp_path: Path) -> None:
    run = run_sweep(_stl_spec(), tmp_path)
    assert run.completed_count == 2
    for record in run.candidates:
        assert record.status == "complete"
        assert record.stl_artifacts is not None
        hull_rel = record.stl_artifacts.hull.path
        deck_rel = record.stl_artifacts.deck.path
        assert hull_rel == f"candidates/{record.candidate_key}/hull.stl"
        assert deck_rel == f"candidates/{record.candidate_key}/deck.stl"
        hull_path = tmp_path / hull_rel
        deck_path = tmp_path / deck_rel
        assert hull_path.exists()
        assert deck_path.exists()
        # Byte-equivalent to the `kayakgen generate` STL path for the
        # triangle payload (the 80-byte binary STL header includes a numpy-stl
        # timestamp, so we compare the geometry payload after the header).
        reference_hull = tmp_path / "reference_hull.stl"
        reference_deck = tmp_path / "reference_deck.stl"
        write_stl(Hull(**record.attempted_hull), "hull", reference_hull)
        write_stl(Hull(**record.attempted_hull), "deck", reference_deck)
        assert hull_path.read_bytes()[80:] == reference_hull.read_bytes()[80:]
        assert deck_path.read_bytes()[80:] == reference_deck.read_bytes()[80:]
        reference_hull.unlink()
        reference_deck.unlink()


def test_sweep_stl_records_artifact_hashes(tmp_path: Path) -> None:
    run = run_sweep(_stl_spec(), tmp_path)
    for record in run.candidates:
        assert record.stl_artifacts is not None
        for kind, artifact in (
            ("hull", record.stl_artifacts.hull),
            ("deck", record.stl_artifacts.deck),
        ):
            path = tmp_path / artifact.path
            data = path.read_bytes()
            assert artifact.bytes == len(data)
            assert artifact.sha256 == hashlib.sha256(data).hexdigest()
            assert len(artifact.sha256) == 64
            assert kind in artifact.path


def test_sweep_stl_failed_candidate_skips_artifacts(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="failed-stl",
        base_hull={"beam_oa_m": 0.55},
        variables={"beam_wl_m": {"kind": "values", "values": [0.60]}},
        evaluators={"hydrostatics": True, "resistance": False, "stl": True},
    )
    run = run_sweep(spec, tmp_path)
    assert run.failed_count == 1
    record = run.candidates[0]
    assert record.status == "failed"
    assert record.stl_artifacts is None
    candidate_dir = tmp_path / "candidates" / record.candidate_key
    assert not (candidate_dir / "hull.stl").exists()
    assert not (candidate_dir / "deck.stl").exists()


def test_sweep_stl_pending_candidate_skips_artifacts(tmp_path: Path) -> None:
    spec = _stl_spec()
    run = run_sweep(spec, tmp_path)
    target = run.candidates[0]
    record_path = tmp_path / "candidates" / f"{target.candidate_key}.record.json"
    candidate_dir = tmp_path / "candidates" / target.candidate_key
    # Force the candidate back into the pending state and clear its STL artifacts
    # so we can prove the resume path does not emit any STLs for pending records.
    if candidate_dir.exists():
        for stl in candidate_dir.glob("*.stl"):
            stl.unlink()
    pending = target.model_copy(update={"status": "pending", "stl_artifacts": None})
    record_path.write_text(pending.model_dump_json(indent=2))

    resumed = run_sweep(spec, tmp_path, resume=True)

    pending_record = next(r for r in resumed.candidates if r.candidate_key == target.candidate_key)
    assert pending_record.status == "pending"
    assert pending_record.stl_artifacts is None
    assert not (candidate_dir / "hull.stl").exists()
    assert not (candidate_dir / "deck.stl").exists()


def _high_angle_gz_spec(*, heel_grid_deg: list[float] | None = None) -> SweepSpec:
    evaluators: dict[str, object] = {
        "hydrostatics": True,
        "resistance": False,
        "stl": False,
        "high_angle_gz": True,
    }
    if heel_grid_deg is not None:
        evaluators["high_angle_gz_heel_grid_deg"] = heel_grid_deg
    return SweepSpec(
        name="hagz",
        base_hull={"beam_oa_m": 0.60},
        variables={
            "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]},
            "Cp": {"kind": "values", "values": [0.54]},
        },
        evaluators=evaluators,
    )


def test_sweep_high_angle_gz_off_writes_no_artifact(tmp_path: Path) -> None:
    run = run_sweep(_spec(), tmp_path)
    for record in run.candidates:
        assert record.high_angle_gz_artifact is None
        candidate_dir = tmp_path / "candidates" / record.candidate_key
        assert not (candidate_dir / "high_angle_gz.json").exists()
        assert "high_angle_gz" not in record.artifacts
    assert list((tmp_path / "candidates").rglob("high_angle_gz.json")) == []


def test_sweep_high_angle_gz_on_writes_per_candidate_artifact(tmp_path: Path) -> None:
    run = run_sweep(_high_angle_gz_spec(), tmp_path)
    assert run.completed_count == 2
    for record in run.candidates:
        assert record.status == "complete"
        assert record.high_angle_gz_artifact is not None
        rel = record.high_angle_gz_artifact.path
        assert rel == f"candidates/{record.candidate_key}/high_angle_gz.json"
        artifact_path = tmp_path / rel
        assert artifact_path.exists()
        payload = json.loads(artifact_path.read_text())
        # Block shape matches the CLI surface (RFC 0043 stage 1).
        for key in (
            "available",
            "result_semantics",
            "body_profile",
            "heel_grid_deg",
            "heel_points",
            "summary",
            "assumptions",
            "warnings",
        ):
            assert key in payload
        assert payload["heel_grid_deg"][0] == 0.0
        assert payload["heel_grid_deg"][-1] == 90.0
        assert len(payload["heel_grid_deg"]) == 19


def test_sweep_high_angle_gz_records_artifact_hashes(tmp_path: Path) -> None:
    run = run_sweep(_high_angle_gz_spec(), tmp_path)
    for record in run.candidates:
        artifact = record.high_angle_gz_artifact
        assert artifact is not None
        path = tmp_path / artifact.path
        data = path.read_bytes()
        assert artifact.bytes == len(data)
        assert artifact.sha256 == hashlib.sha256(data).hexdigest()
        assert len(artifact.sha256) == 64
        assert artifact.path.endswith("high_angle_gz.json")


def test_sweep_high_angle_gz_failed_candidate_skips_artifact(tmp_path: Path) -> None:
    spec = SweepSpec(
        name="failed-hagz",
        base_hull={"beam_oa_m": 0.55},
        variables={"beam_wl_m": {"kind": "values", "values": [0.60]}},
        evaluators={"hydrostatics": True, "resistance": False, "high_angle_gz": True},
    )
    run = run_sweep(spec, tmp_path)
    assert run.failed_count == 1
    record = run.candidates[0]
    assert record.status == "failed"
    assert record.high_angle_gz_artifact is None
    candidate_dir = tmp_path / "candidates" / record.candidate_key
    assert not (candidate_dir / "high_angle_gz.json").exists()


def test_sweep_high_angle_gz_pending_candidate_skips_artifact(tmp_path: Path) -> None:
    spec = _high_angle_gz_spec()
    run = run_sweep(spec, tmp_path)
    target = run.candidates[0]
    record_path = tmp_path / "candidates" / f"{target.candidate_key}.record.json"
    candidate_dir = tmp_path / "candidates" / target.candidate_key
    if candidate_dir.exists():
        for stale in candidate_dir.glob("high_angle_gz.json"):
            stale.unlink()
    pending = target.model_copy(update={"status": "pending", "high_angle_gz_artifact": None})
    record_path.write_text(pending.model_dump_json(indent=2))

    resumed = run_sweep(spec, tmp_path, resume=True)

    pending_record = next(r for r in resumed.candidates if r.candidate_key == target.candidate_key)
    assert pending_record.status == "pending"
    assert pending_record.high_angle_gz_artifact is None
    assert not (candidate_dir / "high_angle_gz.json").exists()


def test_sweep_high_angle_gz_resume_preserves_existing_artifact(tmp_path: Path) -> None:
    spec = _high_angle_gz_spec()
    run = run_sweep(spec, tmp_path)
    fingerprints: dict[str, tuple[bytes, float]] = {}
    for record in run.candidates:
        assert record.high_angle_gz_artifact is not None
        artifact_path = tmp_path / record.high_angle_gz_artifact.path
        fingerprints[record.candidate_key] = (
            artifact_path.read_bytes(),
            artifact_path.stat().st_mtime,
        )

    resumed = run_sweep(spec, tmp_path, resume=True)
    assert resumed.skipped_count == 2
    assert resumed.completed_count == 0
    for record in resumed.candidates:
        assert record.status == "skipped"
        assert record.high_angle_gz_artifact is not None
        artifact_path = tmp_path / record.high_angle_gz_artifact.path
        prior_bytes, prior_mtime = fingerprints[record.candidate_key]
        assert artifact_path.read_bytes() == prior_bytes
        # Byte-for-byte preserved; no regeneration.
        assert artifact_path.stat().st_mtime == prior_mtime


def test_sweep_high_angle_gz_does_not_appear_in_summary_csv_columns(tmp_path: Path) -> None:
    run = run_sweep(_high_angle_gz_spec(), tmp_path)
    assert run.completed_count == 2
    summary_text = (tmp_path / "summary.csv").read_text()
    header = summary_text.splitlines()[0]
    forbidden = (
        "high_angle_gz",
        "max_gz",
        "heel_at_max_gz",
        "range_positive_stability_deg",
    )
    for token in forbidden:
        assert token not in header
    # And no high-angle keys leak into the candidate summary scoring fields.
    for record in run.candidates:
        for key in record.summary:
            assert "high_angle" not in key
            assert "gz" not in key.lower() or key in {"GM0_m", "initial_GM0_m"}


def test_sweep_high_angle_gz_is_not_in_default_pareto_objectives() -> None:
    # RFC 0043 stage 2 must not change the default Pareto objectives.
    assert DEFAULT_OBJECTIVE_METRICS == (
        "GM0_m",
        "displacement_error_kg",
        "mesh_problem_count",
    )
    assert "high_angle_gz" not in DEFAULT_OBJECTIVE_METRICS
    assert not any("gz" in metric.lower() and metric != "GM0_m" for metric in DEFAULT_OBJECTIVE_METRICS)


def test_sweep_stl_resume_preserves_existing_artifacts(tmp_path: Path) -> None:
    spec = _stl_spec()
    run = run_sweep(spec, tmp_path)
    fingerprints: dict[str, tuple[bytes, bytes, float, float]] = {}
    for record in run.candidates:
        assert record.stl_artifacts is not None
        hull_path = tmp_path / record.stl_artifacts.hull.path
        deck_path = tmp_path / record.stl_artifacts.deck.path
        fingerprints[record.candidate_key] = (
            hull_path.read_bytes(),
            deck_path.read_bytes(),
            hull_path.stat().st_mtime,
            deck_path.stat().st_mtime,
        )

    resumed = run_sweep(spec, tmp_path, resume=True)
    assert resumed.skipped_count == 2
    assert resumed.completed_count == 0
    for record in resumed.candidates:
        assert record.status == "skipped"
        # The completed-run record carried stl_artifacts forward; the skipped
        # resume copy must preserve them rather than dropping them.
        assert record.stl_artifacts is not None
        hull_path = tmp_path / record.stl_artifacts.hull.path
        deck_path = tmp_path / record.stl_artifacts.deck.path
        prior_hull, prior_deck, prior_hull_mtime, prior_deck_mtime = fingerprints[record.candidate_key]
        assert hull_path.read_bytes() == prior_hull
        assert deck_path.read_bytes() == prior_deck
        # File untouched on disk — no regeneration on resume.
        assert hull_path.stat().st_mtime == prior_hull_mtime
        assert deck_path.stat().st_mtime == prior_deck_mtime
