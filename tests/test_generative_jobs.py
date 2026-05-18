"""Round-trip + summary projection tests for GenerativeJob records (RFC 0057)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from kayakgen.services.generative_jobs import (
    GenerativeJob,
    GenerativeJobError,
    GenerativeJobProgress,
    GenerativeJobSummary,
    canonical_job_json,
    summarize_job,
)


def _baseline_job(**overrides: object) -> GenerativeJob:
    defaults: dict[str, object] = {
        "job_id": "9f1c0e",
        "job_kind": "search",
        "spec_ref": "_store/spec.json",
        "spec_hash": "a" * 64,
        "output_dir": "runs/search-1",
        "log_tail_ref": "log.txt",
    }
    defaults.update(overrides)
    return GenerativeJob(**defaults)


def test_generative_job_round_trip_preserves_canonical_bytes() -> None:
    job = _baseline_job(
        state="running",
        started_at=1_700_000_000.0,
        progress=GenerativeJobProgress(
            realized_evaluations=12,
            budget_max_evaluations=64,
            generation=2,
            completed_count=10,
            failed_count=2,
            wall_clock_seconds=4.5,
            last_candidate_key="abc-0011",
            last_update_at=1_700_000_004.5,
        ),
    )

    canonical = canonical_job_json(job)
    restored = GenerativeJob.model_validate_json(canonical)
    assert canonical_job_json(restored) == canonical
    assert restored == job


def test_canonical_job_json_is_sorted_and_compact() -> None:
    canonical = canonical_job_json(_baseline_job())
    assert " " not in canonical
    assert ", " not in canonical
    # Sorted-key invariant: ``job_id`` precedes ``job_kind`` precedes
    # ``log_tail_ref`` precedes ``output_dir`` precedes ``progress``.
    indices = [canonical.index(f'"{key}"') for key in (
        "job_id",
        "job_kind",
        "log_tail_ref",
        "output_dir",
        "progress",
    )]
    assert indices == sorted(indices)


def test_generative_job_rejects_unknown_state() -> None:
    with pytest.raises(ValidationError):
        _baseline_job(state="archived")  # type: ignore[arg-type]


def test_generative_job_error_round_trips() -> None:
    err = GenerativeJobError(
        kind="ehvi_dimension_unsupported",
        message="EHVI rejects 4+ objectives",
    )
    restored = GenerativeJobError.model_validate_json(err.model_dump_json())
    assert restored == err


def test_generative_job_error_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        GenerativeJobError(kind="oops", message="...")  # type: ignore[arg-type]


def test_generative_job_progress_defaults_are_zero_or_none() -> None:
    progress = GenerativeJobProgress()
    assert progress.schema_version == "1"
    assert progress.realized_evaluations == 0
    assert progress.budget_max_evaluations is None
    assert progress.generation is None
    assert progress.iteration is None
    assert progress.last_candidate_key is None


def test_summarize_job_projects_progress_counters() -> None:
    job = _baseline_job(
        state="succeeded",
        progress=GenerativeJobProgress(
            realized_evaluations=42,
            completed_count=40,
            failed_count=1,
            constraint_failed_count=1,
            pending_count=0,
        ),
    )

    summary = summarize_job(job)

    assert isinstance(summary, GenerativeJobSummary)
    assert summary.job_id == job.job_id
    assert summary.spec_hash == job.spec_hash
    assert summary.state == "succeeded"
    assert summary.realized_evaluations == 42
    assert summary.completed_count == 40
    assert summary.failed_count == 1
    assert summary.constraint_failed_count == 1
    assert summary.pending_count == 0


def test_generative_job_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        _baseline_job(unexpected="oops")


def test_canonical_job_json_is_byte_stable_across_progress_field_orders() -> None:
    progress_payload = {
        "schema_version": "1",
        "realized_evaluations": 3,
        "completed_count": 3,
        "failed_count": 0,
        "constraint_failed_count": 0,
        "pending_count": 0,
        "wall_clock_seconds": 1.25,
        "last_update_at": 1_700_000_001.25,
    }
    reordered = dict(reversed(list(progress_payload.items())))

    a = GenerativeJobProgress.model_validate(progress_payload)
    b = GenerativeJobProgress.model_validate(reordered)
    assert a == b
    a_canonical = json.dumps(a.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    b_canonical = json.dumps(b.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    assert a_canonical == b_canonical
