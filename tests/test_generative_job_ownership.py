"""Real child lifetime, reattachment and one-writer acceptance scenarios."""

from __future__ import annotations

import time
from pathlib import Path

from kayakgen.services.generative_jobs import SubprocessGenerativeJobManager


def long_sweep() -> dict:
    return {
        "schema_version": "1", "name": "owned-sweep",
        "base_hull": {"length_m": 4.5, "beam_oa_m": 0.55, "draft_m": 0.12, "Cp": 0.55},
        "variables": {"beam_wl_m": {"kind": "values", "values": [0.46 + i * 0.000001 for i in range(2000)]}},
        "evaluators": {"hydrostatics": True}, "limits": {"max_candidates": 2000},
    }


def wait_for_running(manager: SubprocessGenerativeJobManager, job_id: str):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        job = manager.get(job_id)
        if job.state == "running":
            return job
        assert job.state == "queued", job
        time.sleep(0.01)
    raise AssertionError("owned child did not enter running")


def test_new_manager_reattaches_to_live_child_without_forging_resumability(tmp_path: Path) -> None:
    first = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = first.start(spec_payload=long_sweep(), job_kind="sweep")
    try:
        wait_for_running(first, job.job_id)
        fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path)
        observed = fresh.get(job.job_id)
        assert first._processes[job.job_id].poll() is None
        assert observed.state == "running"
        fresh.cancel(job.job_id)
        first.join(job.job_id, timeout=30)
        cancelled = fresh.get(job.job_id)
        assert cancelled.state == "resumable"
        assert cancelled.cancellation_requested_at is not None
    finally:
        first.cancel(job.job_id)
        first.join(job.job_id, timeout=30)
        assert first._processes[job.job_id].poll() is not None


def test_dead_child_gets_one_successor_and_stale_publication_is_fenced(tmp_path: Path) -> None:
    import json
    import os
    import signal
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    import pytest

    from kayakgen.services.generative_job_ownership import JobOwnershipError
    from kayakgen.services.generative_jobs import persist_job_to_dir, read_job_from_dir

    original = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = original.start(spec_payload=long_sweep(), job_kind="sweep")
    old = wait_for_running(original, job.job_id)
    child = original._processes[job.job_id]
    os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=10)
    first = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    second = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    assert first.get(job.job_id).state == "resumable"
    barrier = Barrier(2)

    def resume(manager):
        barrier.wait(timeout=5)
        try:
            return manager, manager.resume(job.job_id)
        except ValueError:
            return manager, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(resume, [first, second]))
    winners = [(manager, resumed) for manager, resumed in outcomes if resumed is not None]
    assert len(winners) == 1
    owner, resumed = winners[0]
    try:
        assert resumed.attempt_id != old.attempt_id
        assert len(list((tmp_path / job.job_id / "attempts").iterdir())) == 2
        with pytest.raises(JobOwnershipError, match="stale|unowned"):
            persist_job_to_dir(tmp_path, old.model_copy(update={"state": "succeeded"}))
        assert read_job_from_dir(tmp_path, job.job_id).attempt_id == resumed.attempt_id
        assert json.loads((tmp_path / job.job_id / "owner.json").read_text())["attempt_id"] == resumed.attempt_id
    finally:
        owner.cancel(job.job_id)
        owner.join(job.job_id, timeout=30)
        assert owner._processes[job.job_id].poll() is not None
    assert owner.get(job.job_id).state == "resumable"


def test_legacy_active_namespace_is_observed_without_reassignment(tmp_path: Path) -> None:
    import pytest

    from kayakgen.services.generative_jobs import initialize_job_dir, persist_job_to_dir

    job = initialize_job_dir(tmp_path, spec_payload=long_sweep(), job_kind="sweep")
    job = job.model_copy(update={"state": "running"})
    persist_job_to_dir(tmp_path, job)
    path = tmp_path / job.job_id / "job.json"
    before = path.read_bytes()
    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    assert manager.get(job.job_id).state == "running"
    assert "ownership unknown" in manager.get(job.job_id).error.message
    with pytest.raises(ValueError, match="ownership unknown"):
        manager.resume(job.job_id)
    assert path.read_bytes() == before
    assert not (tmp_path / job.job_id / "attempts").exists()


def test_pid_reuse_is_not_mistaken_for_the_prior_owner(tmp_path: Path) -> None:
    import json
    import os

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    payload = long_sweep()
    payload["variables"]["beam_wl_m"]["values"] = [0.46]
    job = manager.start(spec_payload=payload, job_kind="sweep")
    manager.join(job.job_id, timeout=30)
    assert manager.get(job.job_id).state == "succeeded"
    owner_path = tmp_path / job.job_id / "owner.json"
    old_identity = json.loads(owner_path.read_text())
    # The old worker's numeric start time remains. This still-live test
    # process now occupies the PID, modelling reuse by a different process.
    old_identity["pid"] = os.getpid()
    owner_path.write_text(json.dumps(old_identity))
    job_path = tmp_path / job.job_id / "job.json"
    stale = json.loads(job_path.read_text())
    stale["state"] = "running"
    job_path.write_text(json.dumps(stale))
    fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    assert fresh.get(job.job_id).state == "resumable"


def test_missing_owner_evidence_blocks_automatic_recovery_without_an_operator(tmp_path: Path) -> None:
    import json

    import pytest

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    payload = long_sweep()
    payload["variables"]["beam_wl_m"]["values"] = [0.46]
    job = manager.start(spec_payload=payload, job_kind="sweep")
    manager.join(job.job_id, timeout=30)
    owner_path = tmp_path / job.job_id / "owner.json"
    owner_path.unlink()
    job_path = tmp_path / job.job_id / "job.json"
    stale = json.loads(job_path.read_text())
    stale["state"] = "running"
    job_path.write_text(json.dumps(stale))
    before = job_path.read_bytes()
    fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    assert "ownership unknown" in fresh.get(job.job_id).error.message
    with pytest.raises(ValueError, match="not resumable|unknown"):
        fresh.resume(job.job_id)
    assert job_path.read_bytes() == before
    from kayakgen.services.generative_job_ownership import JobOwnershipError
    from kayakgen.services.generative_jobs import persist_job_to_dir, read_job_from_dir

    unowned = read_job_from_dir(tmp_path, job.job_id).model_copy(update={"attempt_id": None})
    with pytest.raises(JobOwnershipError):
        persist_job_to_dir(tmp_path, unowned)
    assert job_path.read_bytes() == before


def test_malformed_or_foreign_owner_record_is_not_treated_as_dead(tmp_path: Path) -> None:
    import json

    import pytest

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    payload = long_sweep()
    payload["variables"]["beam_wl_m"]["values"] = [0.46]
    job = manager.start(spec_payload=payload, job_kind="sweep")
    manager.join(job.job_id, timeout=30)
    owner_path = tmp_path / job.job_id / "owner.json"
    owner = json.loads(owner_path.read_text())
    job_path = tmp_path / job.job_id / "job.json"
    stale = json.loads(job_path.read_text())
    stale["state"] = "running"
    job_path.write_text(json.dumps(stale))
    before = job_path.read_bytes()
    for wrong in [dict(owner, process_start="not-a-process-start"), dict(owner, host_id="0" * 32)]:
        owner_path.write_text(json.dumps(wrong))
        fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path)
        assert "ownership unknown" in fresh.get(job.job_id).error.message
        with pytest.raises(ValueError, match="not resumable|unknown"):
            fresh.resume(job.job_id)
        assert job_path.read_bytes() == before


def test_resume_does_not_admit_a_changed_request_or_switch_to_threads(tmp_path: Path) -> None:
    import json

    import pytest

    from kayakgen.services.generative_jobs import InProcessGenerativeJobManager

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload=long_sweep(), job_kind="sweep")
    wait_for_running(manager, job.job_id)
    manager.cancel(job.job_id)
    manager.join(job.job_id, timeout=30)
    assert manager.get(job.job_id).state == "resumable"
    with pytest.raises(ValueError, match="ownership-aware"):
        InProcessGenerativeJobManager(jobs_root=tmp_path).resume(job.job_id)
    spec_path = tmp_path / job.job_id / "spec.json"
    spec = json.loads(spec_path.read_text())
    spec["name"] = "changed-request"
    spec_path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="persisted spec"):
        manager.resume(job.job_id)
    assert len(list((tmp_path / job.job_id / "attempts").iterdir())) == 1


def test_failed_launch_retains_attempt_and_allows_a_proven_successor(tmp_path: Path) -> None:
    import pytest

    broken = SubprocessGenerativeJobManager(jobs_root=tmp_path, python_executable="/no-such-python")
    with pytest.raises(FileNotFoundError):
        broken.start(spec_payload=long_sweep(), job_kind="sweep")
    summary = broken.list()[0]
    assert summary.state == "failed"
    original = broken.get(summary.job_id)
    fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    fresh.resume(summary.job_id)
    try:
        assert fresh.get(summary.job_id).attempt_id != original.attempt_id
        assert (tmp_path / summary.job_id / "attempts" / original.attempt_id / "job.json").is_file()
    finally:
        fresh.cancel(summary.job_id)
        fresh.join(summary.job_id, timeout=30)
        assert fresh._processes[summary.job_id].poll() is not None


def test_worker_keeps_ownership_after_its_manager_process_dies(tmp_path: Path) -> None:
    import json
    import os
    import select
    import signal
    import subprocess
    import sys

    from kayakgen.services.generative_job_ownership import owner_state, process_identity

    spec = tmp_path / "request.json"
    spec.write_text(json.dumps(long_sweep()))
    launcher_code = """
import json,sys,time
from pathlib import Path
from kayakgen.services.generative_jobs import SubprocessGenerativeJobManager
m=SubprocessGenerativeJobManager(jobs_root=Path(sys.argv[1]))
j=m.start(spec_payload=json.loads(Path(sys.argv[2]).read_text()),job_kind='sweep')
print(j.job_id,flush=True)
time.sleep(60)
"""
    launcher = subprocess.Popen(
        [sys.executable, "-c", launcher_code, str(tmp_path / "jobs"), str(spec)],
        stdout=subprocess.PIPE, text=True, start_new_session=True,
    )
    job_id = None
    child_identity = None
    child_pid = None
    try:
        assert select.select([launcher.stdout], [], [], 15)[0]
        job_id = launcher.stdout.readline().strip()
        assert job_id
        fresh = SubprocessGenerativeJobManager(jobs_root=tmp_path / "jobs")
        job = wait_for_running(fresh, job_id)
        owner = json.loads((tmp_path / "jobs" / job_id / "owner.json").read_text())
        child_pid = owner["pid"]
        child_identity = process_identity(child_pid)
        launcher.kill()
        launcher.wait(timeout=10)
        assert fresh.get(job_id).state == "running"
        assert owner_state(tmp_path / "jobs" / job_id, job.attempt_id) == "live"
        fresh.cancel(job_id)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            final = fresh.get(job_id)
            if final.state == "resumable" and owner_state(tmp_path / "jobs" / job_id, job.attempt_id) == "dead":
                break
            time.sleep(0.01)
        else:
            raise AssertionError("reattached orphan worker did not cooperatively terminate")
    finally:
        if launcher.poll() is None:
            launcher.kill()
            launcher.wait(timeout=10)
        remaining = None if child_pid is None else process_identity(child_pid)
        if (remaining is not None and child_identity is not None
                and remaining[:2] == child_identity[:2] and remaining[2] != "Z"):
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_thread_backend_cannot_adopt_a_legacy_resumable_namespace(tmp_path: Path) -> None:
    import pytest

    from kayakgen.services.generative_jobs import (
        InProcessGenerativeJobManager, initialize_job_dir, persist_job_to_dir,
    )

    job = initialize_job_dir(tmp_path, spec_payload=long_sweep(), job_kind="sweep")
    persist_job_to_dir(tmp_path, job.model_copy(update={"state": "resumable"}))
    with pytest.raises(ValueError, match="ownership.*unknown"):
        InProcessGenerativeJobManager(jobs_root=tmp_path).resume(job.job_id)
