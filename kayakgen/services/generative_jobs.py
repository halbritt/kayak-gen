"""Long-lived generative-job records, progress sink, in-process manager (RFC 0057).

This module owns:

- The Pydantic records describing a long-lived ``sweep`` or ``search``
  job (:class:`GenerativeJob`, :class:`GenerativeJobProgress`,
  :class:`GenerativeJobError`, :class:`GenerativeJobSummary`).
- The :class:`GenerativeJobProgressSink` protocol the runner calls.
- The :class:`InProcessGenerativeJobManager` reference implementation
  that runs each job in a background ``threading.Thread`` inside the
  same process.

A :class:`GenerativeJob` is an *application-services* aggregate, not a
hull-domain entity. Its only durable artifacts are ``job.json``, the
frozen ``spec.json`` copy, and a bounded ``log.txt`` ring buffer; the
hull-domain output stays in the run directory's existing
``candidates/`` + ``state.json`` + ``run.json`` files.

Canonical JSON serialization is sorted keys + no insignificant
whitespace, matching :mod:`kayakgen.services.identity`. Round-trip
tests live in ``tests/test_generative_jobs.py``.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

JobKind = Literal["sweep", "search"]

JobState = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    "resumable",
]

JobErrorKind = Literal[
    "spec_validation_failed",
    "evaluator_error",
    "ehvi_dimension_unsupported",
    "objective_claim_state_inadmissible",
    "high_angle_gz_display_only",
    "cancelled_by_operator",
    "internal_error",
]


class GenerativeJobError(BaseModel):
    """Structured error captured when a job transitions to ``failed``."""

    model_config = ConfigDict(extra="forbid")

    kind: JobErrorKind
    message: str
    candidate_key: str | None = None


class GenerativeJobProgress(BaseModel):
    """Read-model view of in-flight job progress.

    Persisted on ``job.json`` after each candidate emission. Reads from
    the candidate-record stream are authoritative for byte-stable output;
    this record is a denormalization for fast list/watch queries on the
    CLI and web surfaces.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    realized_evaluations: int = 0
    budget_max_evaluations: int | None = None
    generation: int | None = None
    iteration: int | None = None
    pending_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    constraint_failed_count: int = 0
    wall_clock_seconds: float = 0.0
    last_candidate_key: str | None = None
    last_update_at: float = Field(default_factory=lambda: float(time.time()))


class GenerativeJob(BaseModel):
    """The long-lived job aggregate (RFC 0057)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    job_kind: JobKind
    spec_ref: str
    spec_hash: str
    output_dir: str
    state: JobState = "queued"
    progress: GenerativeJobProgress = Field(default_factory=GenerativeJobProgress)
    started_at: float | None = None
    completed_at: float | None = None
    cancellation_requested_at: float | None = None
    error: GenerativeJobError | None = None
    log_tail_ref: str
    resumable_from_checkpoint: bool = False


class GenerativeJobSummary(BaseModel):
    """List-view projection of :class:`GenerativeJob` for index queries."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    job_id: str
    job_kind: JobKind
    spec_hash: str
    state: JobState
    output_dir: str
    started_at: float | None = None
    completed_at: float | None = None
    realized_evaluations: int = 0
    completed_count: int = 0
    failed_count: int = 0
    constraint_failed_count: int = 0
    pending_count: int = 0


def summarize_job(job: GenerativeJob) -> GenerativeJobSummary:
    """Project a full :class:`GenerativeJob` to its index-view summary."""

    return GenerativeJobSummary(
        job_id=job.job_id,
        job_kind=job.job_kind,
        spec_hash=job.spec_hash,
        state=job.state,
        output_dir=job.output_dir,
        started_at=job.started_at,
        completed_at=job.completed_at,
        realized_evaluations=job.progress.realized_evaluations,
        completed_count=job.progress.completed_count,
        failed_count=job.progress.failed_count,
        constraint_failed_count=job.progress.constraint_failed_count,
        pending_count=job.progress.pending_count,
    )


def canonical_job_json(job: GenerativeJob) -> str:
    """Canonical JSON encoding of a :class:`GenerativeJob`.

    Sorted keys, no insignificant whitespace; matches the canonical-JSON
    contract :mod:`kayakgen.services.identity` uses for content hashes.
    """

    payload = job.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class GenerativeJobProgressSink(Protocol):
    """Runner-side hook for emitting per-candidate and checkpoint events.

    :func:`kayakgen.search.active.runner.run_search` and
    :func:`kayakgen.search.sweep.run_sweep` accept an optional
    ``progress_sink: GenerativeJobProgressSink | None``. When ``None``
    (the default) the runner is byte-equal to today; when present it
    calls :meth:`candidate_completed` after every candidate-record
    write and :meth:`checkpoint` after every ``state.json`` write.

    Implementations are expected to be thread-safe: the runner holds no
    lock around these calls.
    """

    def candidate_completed(
        self,
        *,
        candidate_key: str,
        status: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        """Called once per persisted candidate record."""

        ...

    def checkpoint(
        self,
        *,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        """Called after every runner ``state.json`` write."""

        ...

    def should_cancel(self) -> bool:
        """Return ``True`` if the runner should shut down at the next safe point.

        The runner checks this between candidate emissions. When it
        returns ``True`` the runner persists its checkpoint and exits;
        no in-flight evaluation is interrupted.
        """

        ...


# ---------------------------------------------------------------------------
# Job manager
# ---------------------------------------------------------------------------


JOB_LOG_MAX_BYTES = 256 * 1024
"""Bounded ring-buffer size for ``log.txt``. Older lines are truncated."""


def _hash_spec_payload(payload: dict[str, Any]) -> str:
    """Canonical sha256 of a spec dict for ``GenerativeJob.spec_hash``."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _new_job_id() -> str:
    """Generate a 12-char hex job id (uuid4 prefix)."""

    return uuid.uuid4().hex[:12]


class GenerativeJobManager(Protocol):
    """Manager-protocol for long-lived generative jobs (RFC 0057)."""

    def start(
        self,
        *,
        spec_payload: dict[str, Any],
        job_kind: JobKind,
    ) -> GenerativeJob:
        """Create and start a new job; return its initial record."""

        ...

    def get(self, job_id: str) -> GenerativeJob:
        """Load the persisted ``job.json`` for ``job_id``."""

        ...

    def list(
        self,
        *,
        state: JobState | None = None,
        job_kind: JobKind | None = None,
    ) -> list[GenerativeJobSummary]:
        """Return summaries of every job under the jobs root."""

        ...

    def cancel(self, job_id: str) -> GenerativeJob:
        """Signal cancellation; the runner shuts down at the next safe point."""

        ...

    def resume(self, job_id: str) -> GenerativeJob:
        """Resume a ``resumable`` job from its persisted ``state.json``."""

        ...

    def tail_log(self, job_id: str, *, since_byte: int = 0) -> tuple[str, int]:
        """Return the log tail and the byte cursor of the file's current end."""

        ...


class _ManagedSink:
    """Bridge :class:`GenerativeJobProgressSink` to a manager-owned job."""

    def __init__(
        self,
        *,
        manager: "InProcessGenerativeJobManager",
        job_id: str,
    ) -> None:
        self._manager = manager
        self._job_id = job_id

    def candidate_completed(
        self,
        *,
        candidate_key: str,
        status: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        self._manager._on_candidate(
            job_id=self._job_id,
            candidate_key=candidate_key,
            status=status,
            generation=generation,
            iteration=iteration,
            realized_evaluations=realized_evaluations,
        )

    def checkpoint(
        self,
        *,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        self._manager._on_checkpoint(
            job_id=self._job_id,
            generation=generation,
            iteration=iteration,
            realized_evaluations=realized_evaluations,
        )

    def should_cancel(self) -> bool:
        return self._manager._should_cancel(self._job_id)


class InProcessGenerativeJobManager:
    """Run generative jobs in background threads inside the same process.

    Jobs persist under ``<jobs_root>/<job_id>/`` with:

    - ``job.json``  — :class:`GenerativeJob` (canonical JSON)
    - ``spec.json`` — frozen sweep/search spec body
    - ``log.txt``   — bounded ring-buffer log
    - ``output/``   — run directory consumed by ``run_search`` /
                      ``run_sweep``; the runner's own
                      ``candidates/`` + ``state.json`` + ``run.json``
                      live inside.

    Threads are non-daemon; cancellation is cooperative via the
    :meth:`GenerativeJobProgressSink.should_cancel` hook.
    """

    def __init__(
        self,
        *,
        jobs_root: Path | str,
        index: Any | None = None,
    ) -> None:
        self.jobs_root = Path(jobs_root).expanduser().resolve()
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self._index = index
        self._cancel_events: dict[str, threading.Event] = {}
        self._job_locks: dict[str, threading.Lock] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._global_lock = threading.Lock()

    # -- public --------------------------------------------------------------

    def start(
        self,
        *,
        spec_payload: dict[str, Any],
        job_kind: JobKind,
    ) -> GenerativeJob:
        job_id = _new_job_id()
        job_dir = self.jobs_root / job_id
        job_dir.mkdir(parents=True)
        output_dir = job_dir / "output"
        output_dir.mkdir()

        spec_path = job_dir / "spec.json"
        spec_path.write_text(
            json.dumps(spec_payload, sort_keys=True, separators=(",", ":")) + "\n"
        )
        log_path = job_dir / "log.txt"
        log_path.write_text("")

        job = GenerativeJob(
            job_id=job_id,
            job_kind=job_kind,
            spec_ref=str(spec_path.relative_to(self.jobs_root)),
            spec_hash=_hash_spec_payload(spec_payload),
            output_dir=str(output_dir),
            state="queued",
            log_tail_ref=str(log_path.relative_to(self.jobs_root)),
        )
        self._persist_job(job)

        cancel_event = threading.Event()
        with self._global_lock:
            self._cancel_events[job_id] = cancel_event
            self._job_locks[job_id] = threading.Lock()

        thread = threading.Thread(
            target=self._run_job,
            name=f"generative-job-{job_id}",
            kwargs={"job_id": job_id, "resume": False},
            daemon=False,
        )
        with self._global_lock:
            self._threads[job_id] = thread
        thread.start()
        return job

    def get(self, job_id: str) -> GenerativeJob:
        path = self._job_dir(job_id) / "job.json"
        if not path.exists():
            raise FileNotFoundError(f"job.json missing for job_id={job_id}")
        return GenerativeJob.model_validate_json(path.read_text())

    def list(
        self,
        *,
        state: JobState | None = None,
        job_kind: JobKind | None = None,
    ) -> list[GenerativeJobSummary]:
        summaries: list[GenerativeJobSummary] = []
        if not self.jobs_root.is_dir():
            return summaries
        for entry in sorted(self.jobs_root.iterdir()):
            job_json = entry / "job.json"
            if not job_json.is_file():
                continue
            try:
                job = GenerativeJob.model_validate_json(job_json.read_text())
            except (ValidationError, ValueError):
                continue
            if state is not None and job.state != state:
                continue
            if job_kind is not None and job.job_kind != job_kind:
                continue
            summaries.append(summarize_job(job))
        return summaries

    def cancel(self, job_id: str) -> GenerativeJob:
        event = self._cancel_events.get(job_id)
        if event is not None:
            event.set()
        with self._lock_for(job_id):
            job = self.get(job_id)
            if job.cancellation_requested_at is None:
                job = job.model_copy(
                    update={"cancellation_requested_at": float(time.time())}
                )
                self._persist_job(job)
        return job

    def resume(self, job_id: str) -> GenerativeJob:
        job = self.get(job_id)
        if job.state not in ("resumable", "failed", "cancelled"):
            raise ValueError(
                f"job_id={job_id} state={job.state!r} is not resumable"
            )
        cancel_event = threading.Event()
        with self._global_lock:
            self._cancel_events[job_id] = cancel_event
            self._job_locks.setdefault(job_id, threading.Lock())
        thread = threading.Thread(
            target=self._run_job,
            name=f"generative-job-{job_id}",
            kwargs={"job_id": job_id, "resume": True},
            daemon=False,
        )
        with self._global_lock:
            self._threads[job_id] = thread
        thread.start()
        return self.get(job_id)

    def tail_log(self, job_id: str, *, since_byte: int = 0) -> tuple[str, int]:
        path = self._job_dir(job_id) / "log.txt"
        if not path.exists():
            return "", 0
        data = path.read_bytes()
        if since_byte < 0:
            since_byte = 0
        return data[since_byte:].decode("utf-8", errors="replace"), len(data)

    def join(self, job_id: str, *, timeout: float | None = None) -> None:
        """Block until the named job's thread exits. Test helper."""

        thread = self._threads.get(job_id)
        if thread is not None:
            thread.join(timeout=timeout)

    # -- internal ------------------------------------------------------------

    def _job_dir(self, job_id: str) -> Path:
        return self.jobs_root / job_id

    def _lock_for(self, job_id: str) -> threading.Lock:
        with self._global_lock:
            return self._job_locks.setdefault(job_id, threading.Lock())

    def _persist_job(self, job: GenerativeJob) -> None:
        path = self._job_dir(job.job_id) / "job.json"
        path.write_text(canonical_job_json(job) + "\n")
        if self._index is not None:
            run_hash = None
            run_id_in_store = None
            try:
                self._index.upsert_generative_job(
                    job_id=job.job_id,
                    job_kind=job.job_kind,
                    spec_hash=job.spec_hash,
                    state=job.state,
                    output_dir=job.output_dir,
                    run_id=run_id_in_store,
                    run_hash=run_hash,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    realized_evaluations=job.progress.realized_evaluations,
                    completed_count=job.progress.completed_count,
                    failed_count=job.progress.failed_count,
                    constraint_failed_count=job.progress.constraint_failed_count,
                    pending_count=job.progress.pending_count,
                )
            except Exception:  # pragma: no cover - index errors are non-fatal
                pass

    def _append_log(self, job_id: str, line: str) -> None:
        path = self._job_dir(job_id) / "log.txt"
        with self._lock_for(job_id):
            existing = path.read_bytes() if path.exists() else b""
            new_bytes = (line.rstrip("\n") + "\n").encode("utf-8")
            buffer = existing + new_bytes
            if len(buffer) > JOB_LOG_MAX_BYTES:
                buffer = buffer[-JOB_LOG_MAX_BYTES:]
            path.write_bytes(buffer)

    def _should_cancel(self, job_id: str) -> bool:
        event = self._cancel_events.get(job_id)
        return event is not None and event.is_set()

    def _on_candidate(
        self,
        *,
        job_id: str,
        candidate_key: str,
        status: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        with self._lock_for(job_id):
            job = self.get(job_id)
            progress = job.progress.model_copy(
                update={
                    "realized_evaluations": realized_evaluations,
                    "generation": generation,
                    "iteration": iteration,
                    "last_candidate_key": candidate_key,
                    "last_update_at": float(time.time()),
                    "completed_count": job.progress.completed_count
                    + (1 if status == "complete" else 0),
                    "failed_count": job.progress.failed_count
                    + (1 if status == "failed" else 0),
                    "constraint_failed_count": job.progress.constraint_failed_count
                    + (1 if status == "constraint_failed" else 0),
                    "pending_count": job.progress.pending_count
                    + (1 if status == "pending" else 0),
                    "wall_clock_seconds": float(time.time())
                    - (job.started_at or float(time.time())),
                }
            )
            updated = job.model_copy(update={"progress": progress})
            self._persist_job(updated)
        self._append_log(
            job_id,
            f"candidate {candidate_key} status={status} eval={realized_evaluations}",
        )

    def _on_checkpoint(
        self,
        *,
        job_id: str,
        generation: int | None,
        iteration: int | None,
        realized_evaluations: int,
    ) -> None:
        self._append_log(
            job_id,
            f"checkpoint generation={generation} iteration={iteration} "
            f"eval={realized_evaluations}",
        )

    def _run_job(self, *, job_id: str, resume: bool) -> None:
        # Local imports to avoid module-load-time cycles.
        from kayakgen.search.active.runner import run_search
        from kayakgen.search.active.spec import SearchSpec
        from kayakgen.search.sweep import SweepSpec, run_sweep

        sink = _ManagedSink(manager=self, job_id=job_id)
        with self._lock_for(job_id):
            job = self.get(job_id)
            started_at = job.started_at if resume else float(time.time())
            running = job.model_copy(
                update={
                    "state": "running",
                    "started_at": started_at,
                }
            )
            self._persist_job(running)
        self._append_log(
            job_id, f"job {job_id} state=running resume={resume}"
        )

        spec_payload = json.loads(
            (self._job_dir(job_id) / "spec.json").read_text()
        )
        job_kind = self.get(job_id).job_kind
        output_dir = Path(self.get(job_id).output_dir)
        error: GenerativeJobError | None = None
        try:
            if job_kind == "search":
                spec_in = output_dir / "spec.in.json"
                spec_in.write_text(json.dumps(spec_payload, sort_keys=True))
                SearchSpec.model_validate(spec_payload)
                run_search(
                    spec_in,
                    output_dir,
                    resume=resume,
                    progress_sink=sink,
                )
            elif job_kind == "sweep":
                sweep_spec = SweepSpec.model_validate(spec_payload)
                run_sweep(
                    sweep_spec,
                    output_dir,
                    resume=resume,
                    progress_sink=sink,
                )
            else:  # pragma: no cover - JobKind is a Literal
                raise ValueError(f"unknown job_kind={job_kind!r}")
        except ValidationError as exc:
            error = GenerativeJobError(
                kind="spec_validation_failed",
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 - re-classify at boundary
            kind: JobErrorKind = "internal_error"
            message = str(exc)
            exc_name = type(exc).__name__
            if exc_name == "EhviDimensionError":
                kind = "ehvi_dimension_unsupported"
            elif exc_name == "HighAngleGzObjectiveRefusedError":
                kind = "high_angle_gz_display_only"
            elif "claim_state" in message and "admissible" in message:
                kind = "objective_claim_state_inadmissible"
            error = GenerativeJobError(kind=kind, message=message)

        terminal_state: JobState
        if error is not None:
            terminal_state = "failed"
        elif self._should_cancel(job_id):
            terminal_state = "resumable"
            error = GenerativeJobError(
                kind="cancelled_by_operator",
                message="cancellation requested via manager",
            )
        else:
            terminal_state = "succeeded"

        with self._lock_for(job_id):
            job = self.get(job_id)
            final = job.model_copy(
                update={
                    "state": terminal_state,
                    "completed_at": float(time.time()),
                    "error": error,
                    "resumable_from_checkpoint": terminal_state == "resumable",
                }
            )
            self._persist_job(final)
        self._append_log(
            job_id,
            f"job {job_id} state={terminal_state}"
            + (f" error={error.kind}" if error else ""),
        )
        with self._global_lock:
            with contextlib.suppress(KeyError):
                del self._cancel_events[job_id]


__all__ = [
    "GenerativeJob",
    "GenerativeJobError",
    "GenerativeJobManager",
    "GenerativeJobProgress",
    "GenerativeJobProgressSink",
    "GenerativeJobSummary",
    "InProcessGenerativeJobManager",
    "JOB_LOG_MAX_BYTES",
    "JobErrorKind",
    "JobKind",
    "JobState",
    "canonical_job_json",
    "summarize_job",
]
