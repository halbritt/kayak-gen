"""Subprocess entry-point for SubprocessGenerativeJobManager (RFC 0057 stage 3).

Invoke as::

    python -m kayakgen.services.generative_jobs_runner <job_id> <jobs_root> [--resume]

The child process reads ``<jobs_root>/<job_id>/spec.json`` + ``job.json``,
transitions the job to ``running``, invokes
:func:`kayakgen.search.active.runner.run_search` or
:func:`kayakgen.search.sweep.run_sweep` with a file-backed cancel sink,
and writes terminal state (``succeeded`` / ``failed`` / ``resumable``)
back to ``job.json`` on exit. Cancellation is signalled by the parent
manager touching ``<job_dir>/cancel.flag``.

The runner is intentionally tiny and import-light; it is not used by the
in-process manager (which threads inside the parent process and uses a
``threading.Event`` instead of a flag file).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from kayakgen.services.generative_job_ownership import (
    JobOwnershipError, begin_attempt, locked_job, protocol_is_current, record_running, runner_lease, save_attempt_state,
)

from kayakgen.services.generative_jobs import (
    CANCEL_FLAG_FILENAME,
    _hash_spec_payload,
    GenerativeJobError,
    GenerativeJobProgress,
    JobState,
    append_log_to_file,
    classify_runner_error,
    persist_job_to_dir,
    read_job_from_dir,
)


class _FileBackedSink:
    """Progress sink that persists to ``job.json`` and polls ``cancel.flag``."""

    def __init__(self, *, jobs_root: Path, job_id: str) -> None:
        self._jobs_root = jobs_root
        self._job_id = job_id
        self._cancel_flag = jobs_root / job_id / CANCEL_FLAG_FILENAME
        self._completed = 0
        self._failed = 0
        self._constraint_failed = 0
        self._pending = 0

    def candidate_completed(
        self,
        *,
        candidate_key: str,
        status: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        if status == "complete":
            self._completed += 1
        elif status == "failed":
            self._failed += 1
        elif status == "constraint_failed":
            self._constraint_failed += 1
        elif status == "pending":
            self._pending += 1
        job = read_job_from_dir(self._jobs_root, self._job_id)
        progress = job.progress.model_copy(
            update={
                "realized_evaluations": realized_evaluations,
                "generation": generation,
                "iteration": iteration,
                "last_candidate_key": candidate_key,
                "last_update_at": float(time.time()),
                "completed_count": self._completed,
                "failed_count": self._failed,
                "constraint_failed_count": self._constraint_failed,
                "pending_count": self._pending,
                "wall_clock_seconds": float(time.time())
                - (job.started_at or float(time.time())),
            }
        )
        persist_job_to_dir(
            self._jobs_root,
            job.model_copy(update={"progress": progress}),
        )
        append_log_to_file(
            self._jobs_root,
            self._job_id,
            f"candidate {candidate_key} status={status} eval={realized_evaluations}",
        )

    def checkpoint(
        self,
        *,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        append_log_to_file(
            self._jobs_root,
            self._job_id,
            f"checkpoint generation={generation} iteration={iteration} "
            f"eval={realized_evaluations}",
        )

    def should_cancel(self) -> bool:
        return self._cancel_flag.exists()


def _run(
    jobs_root: Path, job_id: str, *, resume: bool,
    inherited_ownership: tuple[str, int] | None = None,
) -> int:
    job_dir = jobs_root / job_id
    if not protocol_is_current(job_dir):
        raise JobOwnershipError("legacy job namespace has no ownership proof")
    if inherited_ownership is not None:
        attempt_id, ownership_fd = inherited_ownership
        with runner_lease(job_dir, attempt_id, ownership_fd):
            return _run_owned(jobs_root, job_id, resume=resume)
    # Direct entry is allowed only for a newly marked queued job, before
    # any attempt exists. Existing attempts must use manager admission.
    with locked_job(job_dir) as lease:
        job = read_job_from_dir(jobs_root, job_id)
        if job.attempt_id is not None or job.state != "queued" or resume:
            raise JobOwnershipError("existing attempt requires ownership-aware manager admission")
        token = begin_attempt(lease)
        job = job.model_copy(update={"attempt_id": token})
        persist_job_to_dir(jobs_root, job)
        record_running(lease)
        return _run_owned(jobs_root, job_id, resume=resume)


def _run_owned(jobs_root: Path, job_id: str, *, resume: bool) -> int:
    job_dir = jobs_root / job_id
    if not (job_dir / "spec.json").exists():
        sys.stderr.write(
            f"generative_jobs_runner: spec.json missing under {job_dir}\n"
        )
        return 2

    spec_payload = json.loads((job_dir / "spec.json").read_text())
    job = read_job_from_dir(jobs_root, job_id)
    cancel_flag = job_dir / CANCEL_FLAG_FILENAME
    if cancel_flag.exists():
        job = job.model_copy(update={"cancellation_requested_at": cancel_flag.stat().st_mtime})
    started_at = job.started_at if (resume and job.started_at is not None) else float(time.time())
    running = job.model_copy(
        update={
            "state": "running",
            "started_at": started_at,
            "error": None,
        }
    )
    # On resume, zero the progress counters; the runner re-emits them.
    if resume:
        running = running.model_copy(
            update={"progress": GenerativeJobProgress(last_update_at=float(time.time()))}
        )
    persist_job_to_dir(jobs_root, running)
    append_log_to_file(
        jobs_root, job_id, f"job {job_id} attempt={running.attempt_id} state=running resume={resume} subprocess"
    )

    output_dir = Path(running.output_dir)
    sink = _FileBackedSink(jobs_root=jobs_root, job_id=job_id)
    error: GenerativeJobError | None = None
    sweep_result = None
    try:
        if _hash_spec_payload(spec_payload) != running.spec_hash:
            raise ValueError("persisted spec differs from the admitted job request")
        if running.job_kind == "search":
            from kayakgen.search.active.runner import run_search
            from kayakgen.search.active.spec import SearchSpec

            spec_in = output_dir / "spec.in.json"
            spec_in.write_text(json.dumps(spec_payload, sort_keys=True))
            SearchSpec.model_validate(spec_payload)
            run_search(spec_in, output_dir, resume=resume, progress_sink=sink)
        elif running.job_kind == "sweep":
            from kayakgen.search.sweep import SweepSpec, run_sweep

            sweep_spec = SweepSpec.model_validate(spec_payload)
            sweep_result = run_sweep(sweep_spec, output_dir, resume=resume, progress_sink=sink)
        else:  # pragma: no cover - JobKind is a Literal
            raise ValueError(f"unknown job_kind={running.job_kind!r}")
    except Exception as exc:  # noqa: BLE001 - re-classify at boundary
        error = classify_runner_error(exc)

    terminal_state: JobState
    if error is not None:
        terminal_state = "failed"
    elif sink.should_cancel():
        terminal_state = "resumable"
        error = GenerativeJobError(
            kind="cancelled_by_operator",
            message="cancellation requested via subprocess manager flag",
        )
    elif sweep_result is not None and sweep_result.execution_state != "complete":
        terminal_state = "resumable"
        error = GenerativeJobError(
            kind="internal_error",
            message=f"sweep execution incomplete: {sweep_result.processed_candidate_count}/"
            f"{sweep_result.requested_candidate_count} processed, {sweep_result.pending_count} pending",
        )
    else:
        terminal_state = "succeeded"

    current = read_job_from_dir(jobs_root, job_id)
    cancellation_time = current.cancellation_requested_at
    if sink.should_cancel():
        cancellation_time = (job_dir / CANCEL_FLAG_FILENAME).stat().st_mtime
    final = current.model_copy(
        update={
            "cancellation_requested_at": cancellation_time,
            "state": terminal_state,
            "completed_at": float(time.time()),
            "error": error,
            "resumable_from_checkpoint": terminal_state == "resumable",
        }
    )
    persist_job_to_dir(jobs_root, final)
    save_attempt_state(job_dir, final.model_dump(mode="json"))
    append_log_to_file(
        jobs_root,
        job_id,
        f"job {job_id} attempt={final.attempt_id} state={terminal_state}"
        + (f" error={error.kind}" if error else ""),
    )

    # Clean up the cancel flag so a subsequent resume doesn't immediately
    # re-cancel.
    cancel_flag = jobs_root / job_id / CANCEL_FLAG_FILENAME
    if cancel_flag.exists():
        try:
            cancel_flag.unlink()
        except OSError:  # pragma: no cover - best-effort cleanup
            pass
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m kayakgen.services.generative_jobs_runner",
        description="Subprocess entry-point for RFC 0057 generative jobs.",
    )
    parser.add_argument("job_id", help="generative job id (dir name under jobs_root)")
    parser.add_argument(
        "jobs_root", help="filesystem root that owns <job_id>/{spec,job,log}.* "
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="resume from a previously persisted state.json checkpoint",
    )
    parser.add_argument("--attempt-id")
    parser.add_argument("--ownership-fd", type=int)
    args = parser.parse_args(argv)
    if (args.attempt_id is None) != (args.ownership_fd is None):
        parser.error("attempt identity and ownership descriptor must be supplied together")
    inherited = None if args.attempt_id is None else (args.attempt_id, args.ownership_fd)
    return _run(
        Path(args.jobs_root).expanduser().resolve(),
        args.job_id,
        resume=bool(args.resume),
        inherited_ownership=inherited,
    )


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess only
    sys.exit(main())


__all__ = ["main"]
