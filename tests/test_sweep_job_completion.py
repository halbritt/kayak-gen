"""Job success requires completed requested sweep execution, not just a return."""

import json
from pathlib import Path
from threading import Event

import pytest

from kayakgen.search.sweep import CandidateRecord
from kayakgen.services.generative_jobs import InProcessGenerativeJobManager, SubprocessGenerativeJobManager
from kayakgen.services.generative_jobs_runner import _run as run_subprocess_entry


@pytest.mark.parametrize("backend", ["inprocess", "subprocess_entry"])
def test_job_keeps_incomplete_sweep_resumable(tmp_path: Path, monkeypatch, backend: str) -> None:
    def deferred_candidate(**request) -> CandidateRecord:
        return CandidateRecord(
            candidate_index=request["index"], candidate_key=request["candidate_key"],
            parameters=request["params"], attempted_hull=request["attempted"], status="pending",
        )

    monkeypatch.setattr("kayakgen.search.sweep._evaluate_candidate", deferred_candidate)
    if backend == "inprocess":
        manager = InProcessGenerativeJobManager(jobs_root=tmp_path)
    else:
        manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)

        def inline_spawn(job_id: str, *, resume: bool) -> None:
            assert run_subprocess_entry(tmp_path, job_id, resume=resume) == 0

        monkeypatch.setattr(manager, "_spawn", inline_spawn)
    job = manager.start(spec_payload={
        "name": "incomplete-scope", "base_hull": {"beam_oa_m": 0.6},
        "variables": {"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    }, job_kind="sweep")
    manager.join(job.job_id, timeout=30)
    final = manager.get(job.job_id)
    run = json.loads((Path(final.output_dir) / "run.json").read_text())
    assert run["execution_state"] == "incomplete"
    assert run["requested_candidate_count"] == run["processed_candidate_count"] == 2
    assert run["pending_count"] == 2
    assert final.state == "resumable"
    assert final.resumable_from_checkpoint
    assert final.error is not None
    assert final.error.kind == "internal_error"
    assert "sweep execution incomplete" in final.error.message


def test_inprocess_public_resume_counts_each_requested_outcome_once(tmp_path: Path, monkeypatch) -> None:
    from kayakgen.search import sweep

    entered, release = Event(), Event()
    evaluate = sweep._evaluate_candidate

    def gated_evaluation(**request) -> CandidateRecord:
        entered.set()
        assert release.wait(timeout=10)
        return evaluate(**request)

    monkeypatch.setattr(sweep, "_evaluate_candidate", gated_evaluation)
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload={
        "name": "resume-progress", "base_hull": {"beam_oa_m": 0.6},
        "variables": {"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    }, job_kind="sweep")
    try:
        assert entered.wait(timeout=10)
        manager.cancel(job.job_id)
    finally:
        release.set()
        manager.join(job.job_id, timeout=30)
    partial = manager.get(job.job_id)
    assert partial.state == "resumable"
    assert partial.progress.completed_count == partial.progress.realized_evaluations == 1

    manager.resume(job.job_id)
    manager.join(job.job_id, timeout=30)
    final = manager.get(job.job_id)
    run = json.loads((Path(final.output_dir) / "run.json").read_text())
    assert final.state == "succeeded"
    assert final.progress.completed_count == final.progress.realized_evaluations == 2
    assert final.progress.failed_count == final.progress.pending_count == 0
    assert run["reused_count"] == 1
    assert run["completed_count"] == run["requested_candidate_count"] == run["processed_candidate_count"] == 2
