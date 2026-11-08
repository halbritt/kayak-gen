"""Verified reuse is execution metadata, not a new scientific outcome."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from kayakgen.search.compare import build_comparison_report
from kayakgen.search.sweep import EvaluatorOptions, SweepReuseUnavailable, SweepRunRecord, SweepSpec, run_sweep
from kayakgen.services.artifact_store import ArtifactIntegrityError, FilesystemArtifactStore


def tiny_spec() -> SweepSpec:
    return SweepSpec.model_validate({
        "name": "recovery", "base_hull": {"beam_oa_m": 0.6},
        "variables": {"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    })


def test_noop_resume_preserves_scientific_outcomes_and_frontier(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    before = build_comparison_report(tmp_path)
    originals = {p.name: p.read_bytes() for p in (tmp_path / "candidates").glob("*.record.json")}
    resumed = run_sweep(tiny_spec(), tmp_path, resume=True)
    after = build_comparison_report(tmp_path)
    assert resumed.completed_count == first.completed_count == 2
    assert {r.status for r in resumed.candidates} == {"complete"}
    assert before.pareto_front_keys == after.pareto_front_keys
    assert resumed.reused_count == 2
    assert resumed.execution_state == "complete"
    assert resumed.requested_candidate_count == resumed.processed_candidate_count == 2
    assert originals == {p.name: p.read_bytes() for p in (tmp_path / "candidates").glob("*.record.json")}


def test_resume_restores_missing_canonical_evaluation_from_verified_content(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    evaluation_path = tmp_path / first.candidates[0].artifacts["evaluation"]
    before = evaluation_path.read_bytes()
    evaluation_path.unlink()
    resumed = run_sweep(tiny_spec(), tmp_path, resume=True)
    assert evaluation_path.is_file()
    assert evaluation_path.read_bytes() == before
    assert resumed.reused_count == 2
    assert {r.status for r in resumed.candidates} == {"complete"}


class CancelAfterOne:
    def candidate_completed(self, **kwargs) -> None:
        pass

    def should_cancel(self) -> bool:
        return True


def test_cancelled_subset_records_scope_and_resumes_to_the_same_frontier(tmp_path: Path) -> None:
    partial = run_sweep(tiny_spec(), tmp_path, progress_sink=CancelAfterOne())
    assert partial.execution_state == "cancelled"
    assert partial.requested_candidate_count == 2
    assert partial.processed_candidate_count == partial.completed_count == 1
    assert any("cancelled: 1/2" in warning for warning in build_comparison_report(tmp_path).warnings)
    complete = run_sweep(tiny_spec(), tmp_path, resume=True)
    assert complete.execution_state == "complete"
    assert complete.requested_candidate_count == complete.processed_candidate_count == 2
    assert complete.reused_count == 1
    assert {r.status for r in complete.candidates} == {"complete"}


def test_missing_all_evaluation_copies_prevents_reuse_and_marks_incomplete(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    relative = first.candidates[0].artifacts["evaluation"]
    store = FilesystemArtifactStore(tmp_path)
    ref = store.ref_for_relative_path(relative)
    (tmp_path / relative).unlink()
    for blob in store.store_dir.glob(ref.artifact_hash + ".*"):
        blob.unlink()
    with pytest.raises(SweepReuseUnavailable, match="reuse unavailable"):
        run_sweep(tiny_spec(), tmp_path, resume=True)
    recorded = json.loads((tmp_path / "run.json").read_text())
    assert recorded["execution_state"] == "incomplete"
    assert recorded["requested_candidate_count"] == 2
    assert recorded["processed_candidate_count"] == 0
    assert recorded["execution_errors"]
    assert first.candidates[0].status == "complete"
    assert not (tmp_path / relative).exists()


def test_corrupt_required_bytes_are_never_reused_as_summary_only_results(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    (tmp_path / first.candidates[0].artifacts["evaluation"]).write_text("corrupt")
    with pytest.raises(ArtifactIntegrityError):
        build_comparison_report(tmp_path)
    with pytest.raises(SweepReuseUnavailable, match="integrity"):
        run_sweep(tiny_spec(), tmp_path, resume=True)


def test_comparison_reads_known_content_when_canonical_evaluation_is_missing(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    expected = build_comparison_report(tmp_path)
    (tmp_path / first.candidates[0].artifacts["evaluation"]).unlink()
    observed = build_comparison_report(tmp_path)
    assert observed.pareto_front_keys == expected.pareto_front_keys
    assert [s.metrics for s in observed.candidate_summaries] == [s.metrics for s in expected.candidate_summaries]


def test_resume_restores_every_named_artifact_and_missing_candidate_records(tmp_path: Path) -> None:
    spec = tiny_spec().model_copy(update={"evaluators": EvaluatorOptions(stl=True, mesh_diagnostics=True)})
    first = run_sweep(spec, tmp_path)
    paths = [tmp_path / relative for record in first.candidates for relative in record.artifacts.values()]
    paths.extend((tmp_path / "candidates").glob("*.record.json"))
    originals = {path: path.read_bytes() for path in paths}
    for path in paths:
        path.unlink()
    resumed = run_sweep(spec, tmp_path, resume=True)
    assert resumed.reused_count == 2
    assert {path: path.read_bytes() for path in paths} == originals


def test_missing_all_evaluation_copies_refuses_comparison(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    relative = first.candidates[0].artifacts["evaluation"]
    store = FilesystemArtifactStore(tmp_path)
    ref = store.ref_for_relative_path(relative)
    (tmp_path / relative).unlink()
    for blob in store.store_dir.glob(ref.artifact_hash + ".*"):
        blob.unlink()
    with pytest.raises(FileNotFoundError, match="artifact"):
        build_comparison_report(tmp_path)


def test_cancel_is_polled_when_every_outcome_is_reused(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    original = {p.name: p.read_bytes() for p in (tmp_path / "candidates").glob("*.record.json")}
    partial = run_sweep(tiny_spec(), tmp_path, resume=True, progress_sink=CancelAfterOne())
    assert partial.execution_state == "cancelled"
    assert partial.processed_candidate_count == partial.completed_count == partial.reused_count == 1
    assert partial.requested_candidate_count == first.candidate_count == 2
    assert original == {p.name: p.read_bytes() for p in (tmp_path / "candidates").glob("*.record.json")}


def test_required_bundle_failure_leaves_explicit_incomplete_scope(tmp_path: Path, monkeypatch) -> None:
    from kayakgen.search import sweep

    def fail_summary(*args) -> None:
        raise OSError("summary publication failed")

    monkeypatch.setattr(sweep, "_write_summary", fail_summary)
    with pytest.raises(OSError, match="summary publication failed"):
        run_sweep(tiny_spec(), tmp_path)
    recorded = SweepRunRecord.model_validate_json((tmp_path / "run.json").read_bytes())
    assert recorded.execution_state == "incomplete"
    assert recorded.processed_candidate_count == recorded.requested_candidate_count == 2
    assert recorded.execution_errors == ["summary publication failed"]


def test_legacy_unknown_run_is_preserved_without_invented_provenance(tmp_path: Path) -> None:
    originals = {"run.json": b'{"legacy":true}', "spec.json": b'{"old-spec":true}'}
    for relative, data in originals.items():
        (tmp_path / relative).write_bytes(data)
    with pytest.raises(SweepReuseUnavailable, match="legacy run provenance is unknown"):
        run_sweep(tiny_spec(), tmp_path, resume=True)
    assert {relative: (tmp_path / relative).read_bytes() for relative in originals} == originals
    store = FilesystemArtifactStore(tmp_path)
    assert not store.manifest.provenance_complete
    assert store.manifest.artifacts == {}


def test_manifest_spec_conflict_precedes_any_output_replacement(tmp_path: Path) -> None:
    run_sweep(tiny_spec(), tmp_path)
    originals = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    changed = tiny_spec().model_copy(update={"name": "different"})
    with pytest.raises(ValueError, match="descriptor conflicts"):
        run_sweep(changed, tmp_path, resume=True)
    assert {p: p.read_bytes() for p in originals} == originals


def test_modern_complete_scope_cannot_contradict_processed_count(tmp_path: Path) -> None:
    complete = run_sweep(tiny_spec(), tmp_path).model_dump(mode="json")
    with pytest.raises(ValidationError, match="execution scope"):
        SweepRunRecord.model_validate({**complete, "processed_candidate_count": 1})
    with pytest.raises(ValidationError, match="entire requested scope"):
        SweepRunRecord.model_validate({**complete, "requested_candidate_count": 3})
    legacy_fields = {"execution_state", "requested_candidate_count", "processed_candidate_count",
                     "reused_count", "reused_candidate_keys", "execution_errors", "previous_run_artifact_hash"}
    legacy = SweepRunRecord.model_validate({k: v for k, v in complete.items() if k not in legacy_fields})
    assert legacy.execution_state is None
    assert legacy.requested_candidate_count is None


def test_current_canonical_bytes_cannot_replace_a_missing_trusted_binding(tmp_path: Path) -> None:
    first = run_sweep(tiny_spec(), tmp_path)
    relative = first.candidates[0].artifacts["evaluation"]
    manifest_path = tmp_path / "_store" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    del manifest["artifacts"][relative]
    manifest_path.write_text(json.dumps(manifest))
    expected = (tmp_path / relative).read_bytes()
    with pytest.raises(SweepReuseUnavailable, match="provenance missing"):
        run_sweep(tiny_spec(), tmp_path, resume=True)
    assert (tmp_path / relative).read_bytes() == expected
    assert relative not in FilesystemArtifactStore(tmp_path).manifest.artifacts


def test_reuse_refuses_conflicting_artifact_metadata(tmp_path: Path) -> None:
    spec = tiny_spec().model_copy(update={"evaluators": EvaluatorOptions(stl=True)})
    first = run_sweep(spec, tmp_path)
    target = first.candidates[0]
    stls = target.stl_artifacts
    changed = target.model_copy(update={"stl_artifacts": stls.model_copy(update={
        "hull": stls.hull.model_copy(update={"sha256": "0" * 64})
    })})
    FilesystemArtifactStore(tmp_path).put_json(
        "candidate_record", changed, candidate_key=target.candidate_key,
        canonical_path=tmp_path / "candidates" / f"{target.candidate_key}.record.json",
    )
    with pytest.raises(SweepReuseUnavailable, match="metadata disagrees"):
        run_sweep(spec, tmp_path, resume=True)


def test_reuse_requires_artifacts_enabled_by_the_admitted_request(tmp_path: Path) -> None:
    spec = tiny_spec().model_copy(update={"evaluators": EvaluatorOptions(stl=True)})
    first = run_sweep(spec, tmp_path)
    target = first.candidates[0]
    changed = target.model_copy(update={
        "stl_artifacts": None,
        "artifacts": {role: path for role, path in target.artifacts.items() if not role.startswith("stl_")},
    })
    FilesystemArtifactStore(tmp_path).put_json(
        "candidate_record", changed, candidate_key=target.candidate_key,
        canonical_path=tmp_path / "candidates" / f"{target.candidate_key}.record.json",
    )
    with pytest.raises(SweepReuseUnavailable, match="requested stl artifacts"):
        run_sweep(spec, tmp_path, resume=True)
