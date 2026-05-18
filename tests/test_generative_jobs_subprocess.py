"""SubprocessGenerativeJobManager + crash-survival tests (RFC 0057 stage 3)."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import pytest

from kayakgen.services.generative_jobs import (
    CANCEL_FLAG_FILENAME,
    SubprocessGenerativeJobManager,
)


def _sweep_payload(values: list[float] | None = None) -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "subprocess-sweep",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {
                "kind": "values",
                "values": values if values is not None else [0.48, 0.50, 0.52],
            },
        },
        "evaluators": {"hydrostatics": True},
    }


def _search_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "subprocess-search",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "search_space": {
            "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.54},
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 4,
            "generations": 2,
            "seed": 7,
        },
        "objectives": [
            {"metric": "GM0_m", "direction": "max"},
            {"metric": "displaced_mass_kg", "direction": "min"},
        ],
        "constraints": [],
        "evaluators": {"hydrostatics": True},
        "budget": {"max_evaluations": 999},
    }


def test_subprocess_manager_runs_sweep_to_succeeded(tmp_path: Path) -> None:
    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload=_sweep_payload(), job_kind="sweep")
    assert job.state == "queued"
    assert (tmp_path / job.job_id / "spec.json").exists()

    manager.join(job.job_id, timeout=180.0)

    final = manager.get(job.job_id)
    assert final.state == "succeeded"
    assert final.progress.realized_evaluations == 3
    assert final.completed_at is not None
    assert (Path(final.output_dir) / "run.json").exists()


def test_subprocess_manager_runs_search_to_succeeded(tmp_path: Path) -> None:
    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload=_search_payload(), job_kind="search")

    manager.join(job.job_id, timeout=180.0)

    final = manager.get(job.job_id)
    assert final.state == "succeeded"
    assert final.progress.realized_evaluations >= 1
    assert (Path(final.output_dir) / "run.json").exists()


def test_subprocess_manager_cancel_via_flag(tmp_path: Path) -> None:
    """Cancel writes a flag file the subprocess polls; job ends ``resumable``."""

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    # Big-enough sweep so the cancel arrives mid-flight.
    values = [0.46 + 0.005 * i for i in range(40)]
    job = manager.start(
        spec_payload=_sweep_payload(values=values), job_kind="sweep"
    )

    # Give the subprocess a moment to begin emitting candidates.
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        current = manager.get(job.job_id)
        if current.progress.realized_evaluations >= 1:
            break
        time.sleep(0.1)

    cancel_result = manager.cancel(job.job_id)
    assert cancel_result.cancellation_requested_at is not None
    assert (tmp_path / job.job_id / CANCEL_FLAG_FILENAME).exists()

    manager.join(job.job_id, timeout=180.0)
    final = manager.get(job.job_id)
    assert final.state in ("resumable", "succeeded")
    if final.state == "resumable":
        assert final.error is not None
        assert final.error.kind == "cancelled_by_operator"
        # Subprocess runner cleans up the flag on terminal write so a
        # subsequent resume doesn't immediately re-cancel.
        assert not (tmp_path / job.job_id / CANCEL_FLAG_FILENAME).exists()


def test_subprocess_manager_resume_after_cancel(tmp_path: Path) -> None:
    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    values = [0.46 + 0.005 * i for i in range(30)]
    job = manager.start(
        spec_payload=_sweep_payload(values=values), job_kind="sweep"
    )
    manager.cancel(job.job_id)
    manager.join(job.job_id, timeout=180.0)

    intermediate = manager.get(job.job_id)
    if intermediate.state != "resumable":
        pytest.skip("job completed before cancel landed; nothing to resume")

    manager.resume(job.job_id)
    manager.join(job.job_id, timeout=180.0)

    final = manager.get(job.job_id)
    assert final.state in ("succeeded", "resumable")


def test_subprocess_manager_crash_survival(tmp_path: Path) -> None:
    """SIGKILL the runner mid-flight; manager.get reconciles to ``resumable``.

    A subsequent :meth:`resume` should re-spawn a fresh subprocess that
    picks up from the persisted ``state.json`` checkpoint and reaches a
    terminal state.
    """

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    values = [0.46 + 0.005 * i for i in range(40)]
    job = manager.start(
        spec_payload=_sweep_payload(values=values), job_kind="sweep"
    )

    # Wait for the child to emit at least one candidate so state.json
    # has something to resume from.
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        current = manager.get(job.job_id)
        if current.progress.realized_evaluations >= 1:
            break
        time.sleep(0.1)

    proc = manager._processes.get(job.job_id)
    assert proc is not None
    if proc.poll() is not None:
        pytest.skip("subprocess already exited before SIGKILL")

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except ProcessLookupError:
        pytest.skip("subprocess vanished before SIGKILL")
    proc.wait(timeout=30.0)

    reconciled = manager.get(job.job_id)
    assert reconciled.state == "resumable", (
        f"crashed subprocess should reconcile to 'resumable', got {reconciled.state!r}"
    )
    assert reconciled.error is not None

    manager.resume(job.job_id)
    manager.join(job.job_id, timeout=180.0)
    final = manager.get(job.job_id)
    assert final.state in ("succeeded", "resumable")


def test_subprocess_manager_list_reconciles_dead_running_jobs(
    tmp_path: Path,
) -> None:
    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload=_sweep_payload(), job_kind="sweep")

    # Forcibly clobber on-disk state to "running" while subprocess is alive
    # would race; instead, wait for it to finish then mutate the file to
    # simulate a stale "running" entry from a prior crash.
    manager.join(job.job_id, timeout=180.0)
    final_path = tmp_path / job.job_id / "job.json"
    text = final_path.read_text()
    text = text.replace('"state":"succeeded"', '"state":"running"', 1)
    final_path.write_text(text)
    manager._processes.pop(job.job_id, None)

    summaries = manager.list()
    assert any(s.state == "resumable" for s in summaries), summaries


def test_subprocess_manager_resume_running_dead_job_directly(
    tmp_path: Path,
) -> None:
    """Stale 'running' state with no live process resumes cleanly via resume()."""

    manager = SubprocessGenerativeJobManager(jobs_root=tmp_path)
    job = manager.start(spec_payload=_sweep_payload(), job_kind="sweep")
    manager.join(job.job_id, timeout=180.0)

    # Simulate a prior crash by rewriting state to 'running' and forgetting
    # the process handle.
    final_path = tmp_path / job.job_id / "job.json"
    text = final_path.read_text()
    text = text.replace('"state":"succeeded"', '"state":"running"', 1)
    final_path.write_text(text)
    manager._processes.pop(job.job_id, None)

    manager.resume(job.job_id)
    manager.join(job.job_id, timeout=180.0)
    assert manager.get(job.job_id).state == "succeeded"
