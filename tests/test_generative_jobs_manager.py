"""InProcessGenerativeJobManager integration tests (RFC 0057 stage 1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.services.artifact_store import SqliteIndex
from kayakgen.services.generative_jobs import (
    GenerativeJob,
    InProcessGenerativeJobManager,
)


def _sweep_spec_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "manager-sweep",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {
                "kind": "values",
                "values": [0.48, 0.50, 0.52],
            },
        },
        "evaluators": {"hydrostatics": True},
    }


def _search_spec_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "manager-search",
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


def test_manager_runs_sweep_job_to_succeeded(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    job = mgr.start(spec_payload=_sweep_spec_payload(), job_kind="sweep")
    assert job.state == "queued"
    assert job.spec_hash and len(job.spec_hash) == 64
    assert (tmp_path / job.job_id / "spec.json").exists()

    mgr.join(job.job_id, timeout=120.0)

    final = mgr.get(job.job_id)
    assert final.state == "succeeded"
    assert final.completed_at is not None
    assert final.progress.realized_evaluations == 3
    assert final.progress.completed_count >= 1
    assert (Path(final.output_dir) / "run.json").exists()


def test_manager_runs_search_job_to_succeeded(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    job = mgr.start(spec_payload=_search_spec_payload(), job_kind="search")
    mgr.join(job.job_id, timeout=120.0)

    final = mgr.get(job.job_id)
    assert final.state == "succeeded"
    assert final.progress.realized_evaluations >= 1
    assert (Path(final.output_dir) / "run.json").exists()


def test_manager_writes_to_index(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite"
    index = SqliteIndex(db)
    mgr = InProcessGenerativeJobManager(
        jobs_root=tmp_path / "jobs", index=index
    )

    job = mgr.start(spec_payload=_sweep_spec_payload(), job_kind="sweep")
    mgr.join(job.job_id, timeout=120.0)

    rows = index.list_generative_jobs()
    assert len(rows) == 1
    row = rows[0]
    assert row["job_id"] == job.job_id
    assert row["job_kind"] == "sweep"
    assert row["state"] == "succeeded"


def test_manager_cancel_transitions_to_resumable(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    # Use a large sweep so cancel can interrupt mid-flight reliably.
    payload = _sweep_spec_payload()
    values = [0.46 + 0.01 * i for i in range(40)]
    payload["variables"] = {  # type: ignore[index]
        "beam_wl_m": {"kind": "values", "values": values},
    }
    job = mgr.start(spec_payload=payload, job_kind="sweep")
    mgr.cancel(job.job_id)
    mgr.join(job.job_id, timeout=120.0)

    final = mgr.get(job.job_id)
    assert final.cancellation_requested_at is not None
    assert final.state in ("resumable", "succeeded")
    if final.state == "resumable":
        assert final.error is not None
        assert final.error.kind == "cancelled_by_operator"
        assert final.resumable_from_checkpoint is True


def test_manager_list_filters_by_state_and_kind(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    job_a = mgr.start(spec_payload=_sweep_spec_payload(), job_kind="sweep")
    job_b = mgr.start(spec_payload=_search_spec_payload(), job_kind="search")
    mgr.join(job_a.job_id, timeout=120.0)
    mgr.join(job_b.job_id, timeout=120.0)

    sweeps = mgr.list(job_kind="sweep")
    searches = mgr.list(job_kind="search")
    assert {s.job_id for s in sweeps} == {job_a.job_id}
    assert {s.job_id for s in searches} == {job_b.job_id}

    succeeded = mgr.list(state="succeeded")
    assert {s.job_id for s in succeeded} == {job_a.job_id, job_b.job_id}


def test_manager_tail_log_returns_progress_lines(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)
    job = mgr.start(spec_payload=_sweep_spec_payload(), job_kind="sweep")
    mgr.join(job.job_id, timeout=120.0)

    text, cursor = mgr.tail_log(job.job_id)
    assert "candidate" in text
    assert "state=succeeded" in text
    assert cursor == len(text.encode("utf-8"))


def test_manager_rejects_invalid_search_spec(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    bad = _search_spec_payload()
    bad["objectives"] = "not-a-list"  # type: ignore[assignment]

    job = mgr.start(spec_payload=bad, job_kind="search")
    mgr.join(job.job_id, timeout=60.0)

    final = mgr.get(job.job_id)
    assert final.state == "failed"
    assert final.error is not None
    assert final.error.kind == "spec_validation_failed"


def test_manager_persists_job_with_canonical_json(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)
    job = mgr.start(spec_payload=_sweep_spec_payload(), job_kind="sweep")
    mgr.join(job.job_id, timeout=120.0)

    raw = (tmp_path / job.job_id / "job.json").read_text()
    # Round-trip canonical bytes through Pydantic.
    rebuilt = GenerativeJob.model_validate_json(raw)
    assert rebuilt.job_id == job.job_id


@pytest.mark.parametrize("kind", ["sweep", "search"])
def test_manager_resume_after_cancel(tmp_path: Path, kind: str) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)
    if kind == "sweep":
        payload = _sweep_spec_payload()
        values = [0.46 + 0.01 * i for i in range(20)]
        payload["variables"] = {  # type: ignore[index]
            "beam_wl_m": {"kind": "values", "values": values},
        }
    else:
        payload = _search_spec_payload()
        payload["algorithm"] = {  # type: ignore[index]
            "kind": "nsga2",
            "population_size": 4,
            "generations": 30,
            "seed": 7,
        }

    job = mgr.start(spec_payload=payload, job_kind=kind)  # type: ignore[arg-type]
    mgr.cancel(job.job_id)
    mgr.join(job.job_id, timeout=120.0)

    intermediate = mgr.get(job.job_id)
    if intermediate.state != "resumable":
        # Job completed before cancel landed; nothing to resume.
        return

    mgr.resume(job.job_id)
    mgr.join(job.job_id, timeout=120.0)

    final = mgr.get(job.job_id)
    assert final.state in ("succeeded", "resumable")
