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

CFDInLoopEvaluatorStatus = Literal["opt_in_only", "first_class"]

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


def cfd_in_loop_evaluator_status(
    *,
    registry: Any,
    hull_scope: Any,
    persistent_opt_in: bool | None = None,
) -> CFDInLoopEvaluatorStatus:
    """Return whether CFD-in-loop has graduated from opt-in-only status.

    RFC 0058 stage 2 intentionally uses a structural registry: records are
    considered only when they expose ``kind`` as either ``"analytical"`` or
    ``"cfd_in_loop"`` and carry an accepted ``hull_family_scope`` covering
    the requested scope. Per D049,
    :class:`~kayakgen.eval.stability.accepted_fit.StabilityFitRecord` carries
    that ``kind`` discriminator (default ``"analytical"``), so graduation is
    reachable with real records.
    """

    if persistent_opt_in is False:
        return "opt_in_only"

    has_analytical_fit = False
    has_cfd_in_loop_fit = False
    for record in registry:
        if getattr(record, "acceptance_verdict", None) != "accepted":
            continue
        record_scope = getattr(record, "hull_family_scope", None)
        if not _stability_scope_covers(record_scope, hull_scope):
            continue
        kind = getattr(record, "kind", None)
        if kind == "analytical":
            has_analytical_fit = True
        elif kind == "cfd_in_loop":
            has_cfd_in_loop_fit = True

    if has_analytical_fit and has_cfd_in_loop_fit:
        return "first_class"
    return "opt_in_only"


def _stability_scope_covers(record_scope: Any, hull_scope: Any) -> bool:
    if record_scope is None or hull_scope is None:
        return False
    if getattr(record_scope, "hull_class", None) != getattr(hull_scope, "hull_class", None):
        return False

    record_hashes = set(getattr(record_scope, "design_hash_envelope", ()) or ())
    hull_hashes = set(getattr(hull_scope, "design_hash_envelope", ()) or ())
    if not record_hashes or not hull_hashes:
        return False
    return hull_hashes.issubset(record_hashes)


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
    forked_from: str | None = None


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


# ---------------------------------------------------------------------------
# Shared file-based job-store helpers used by both managers and the
# subprocess runner entry.
# ---------------------------------------------------------------------------


def read_job_from_dir(jobs_root: Path, job_id: str) -> GenerativeJob:
    """Load and validate the persisted ``job.json`` for ``job_id``."""

    path = jobs_root / job_id / "job.json"
    if not path.exists():
        raise FileNotFoundError(f"job.json missing for job_id={job_id}")
    return GenerativeJob.model_validate_json(path.read_text())


def list_jobs_in_dir(
    jobs_root: Path,
    *,
    state: JobState | None = None,
    job_kind: JobKind | None = None,
) -> list[GenerativeJobSummary]:
    """List every job whose ``job.json`` parses under ``jobs_root``."""

    summaries: list[GenerativeJobSummary] = []
    if not jobs_root.is_dir():
        return summaries
    for entry in sorted(jobs_root.iterdir()):
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


def tail_log_file(
    jobs_root: Path, job_id: str, *, since_byte: int = 0
) -> tuple[str, int]:
    """Return the (text, cursor) tail of a job's ``log.txt``."""

    path = jobs_root / job_id / "log.txt"
    if not path.exists():
        return "", 0
    data = path.read_bytes()
    if since_byte < 0:
        since_byte = 0
    return data[since_byte:].decode("utf-8", errors="replace"), len(data)


def append_log_to_file(jobs_root: Path, job_id: str, line: str) -> None:
    """Append a line to ``log.txt``, truncating to :data:`JOB_LOG_MAX_BYTES`."""

    path = jobs_root / job_id / "log.txt"
    existing = path.read_bytes() if path.exists() else b""
    new_bytes = (line.rstrip("\n") + "\n").encode("utf-8")
    buffer = existing + new_bytes
    if len(buffer) > JOB_LOG_MAX_BYTES:
        buffer = buffer[-JOB_LOG_MAX_BYTES:]
    path.write_bytes(buffer)


def persist_job_to_dir(
    jobs_root: Path,
    job: GenerativeJob,
    *,
    index: Any | None = None,
) -> None:
    """Write canonical ``job.json`` and (optionally) upsert to SqliteIndex.

    Uses an atomic temp-file + ``os.replace`` swap so concurrent readers
    never observe a half-written or truncated ``job.json``.
    """

    import os as _os

    path = jobs_root / job.job_id / "job.json"
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(canonical_job_json(job) + "\n")
    _os.replace(tmp_path, path)
    if index is not None:
        try:
            index.upsert_generative_job(
                job_id=job.job_id,
                job_kind=job.job_kind,
                spec_hash=job.spec_hash,
                state=job.state,
                output_dir=job.output_dir,
                run_id=None,
                run_hash=None,
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


def initialize_job_dir(
    jobs_root: Path,
    *,
    spec_payload: dict[str, Any],
    job_kind: JobKind,
) -> GenerativeJob:
    """Allocate a job_id and persist the initial ``queued`` :class:`GenerativeJob`.

    Creates the per-job directory layout (``spec.json``, ``log.txt``,
    ``output/``) and returns the initial :class:`GenerativeJob` record.
    The caller is responsible for actually starting the worker (thread
    or subprocess).
    """

    job_id = _new_job_id()
    job_dir = jobs_root / job_id
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
        spec_ref=str(spec_path.relative_to(jobs_root)),
        spec_hash=_hash_spec_payload(spec_payload),
        output_dir=str(output_dir),
        state="queued",
        log_tail_ref=str(log_path.relative_to(jobs_root)),
    )
    return job


def classify_runner_error(exc: Exception) -> GenerativeJobError:
    """Map a runner exception onto a structured :class:`GenerativeJobError`.

    Shared by both the in-process and subprocess paths so terminal-state
    error classification is identical regardless of which manager ran the
    job.
    """

    if isinstance(exc, ValidationError):
        return GenerativeJobError(
            kind="spec_validation_failed",
            message=str(exc),
        )
    message = str(exc)
    exc_name = type(exc).__name__
    kind: JobErrorKind = "internal_error"
    if exc_name == "EhviDimensionError":
        kind = "ehvi_dimension_unsupported"
    elif exc_name == "HighAngleGzObjectiveRefusedError":
        kind = "high_angle_gz_display_only"
    elif "claim_state" in message and "admissible" in message:
        kind = "objective_claim_state_inadmissible"
    return GenerativeJobError(kind=kind, message=message)


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
        job = initialize_job_dir(
            self.jobs_root, spec_payload=spec_payload, job_kind=job_kind
        )
        self._persist_job(job)

        cancel_event = threading.Event()
        with self._global_lock:
            self._cancel_events[job.job_id] = cancel_event
            self._job_locks[job.job_id] = threading.Lock()

        thread = threading.Thread(
            target=self._run_job,
            name=f"generative-job-{job.job_id}",
            kwargs={"job_id": job.job_id, "resume": False},
            daemon=False,
        )
        with self._global_lock:
            self._threads[job.job_id] = thread
        thread.start()
        return job

    def get(self, job_id: str) -> GenerativeJob:
        return read_job_from_dir(self.jobs_root, job_id)

    def list(
        self,
        *,
        state: JobState | None = None,
        job_kind: JobKind | None = None,
    ) -> list[GenerativeJobSummary]:
        return list_jobs_in_dir(self.jobs_root, state=state, job_kind=job_kind)

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
        return tail_log_file(self.jobs_root, job_id, since_byte=since_byte)

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
        persist_job_to_dir(self.jobs_root, job, index=self._index)

    def _append_log(self, job_id: str, line: str) -> None:
        with self._lock_for(job_id):
            append_log_to_file(self.jobs_root, job_id, line)

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
        except Exception as exc:  # noqa: BLE001 - re-classify at boundary
            error = classify_runner_error(exc)

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


# ---------------------------------------------------------------------------
# Subprocess manager (RFC 0057 stage 3)
# ---------------------------------------------------------------------------


class SubprocessGenerativeJobManager:
    """Run generative jobs as detached subprocesses (RFC 0057 stage 3).

    Each ``start`` allocates a job directory and spawns a child Python
    process invoking
    :mod:`kayakgen.services.generative_jobs_runner`. The child writes
    ``job.json`` updates directly to disk via the same helpers the
    in-process manager uses; the parent's ``get/list/tail_log`` only
    read from disk and never need IPC.

    Cancellation is signalled by touching ``<job_dir>/cancel.flag``.
    The child polls the flag between candidate emissions and shuts down
    cleanly to ``state="resumable"`` when it sees the file.

    Crash survival: if the child is ``SIGKILL``'d, the parent's
    :meth:`get` detects that the process handle is no longer alive and
    transitions the stale ``running`` state to ``resumable`` on disk so
    subsequent :meth:`resume` calls work. Re-resume spawns a fresh
    child with ``--resume`` and the runner reuses the persisted
    ``state.json`` checkpoint.
    """

    def __init__(
        self,
        *,
        jobs_root: Path | str,
        index: Any | None = None,
        python_executable: str | None = None,
    ) -> None:
        import subprocess as _subprocess
        import sys as _sys

        self.jobs_root = Path(jobs_root).expanduser().resolve()
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self._index = index
        self._python = python_executable or _sys.executable
        self._processes: dict[str, "_subprocess.Popen[bytes]"] = {}
        self._global_lock = threading.Lock()

    # -- public --------------------------------------------------------------

    def start(
        self,
        *,
        spec_payload: dict[str, Any],
        job_kind: JobKind,
    ) -> GenerativeJob:
        job = initialize_job_dir(
            self.jobs_root, spec_payload=spec_payload, job_kind=job_kind
        )
        persist_job_to_dir(self.jobs_root, job, index=self._index)
        self._spawn(job.job_id, resume=False)
        return job

    def get(self, job_id: str) -> GenerativeJob:
        job = read_job_from_dir(self.jobs_root, job_id)
        # Crash-survival: if the on-disk state says "running" but the
        # child process is no longer alive, reconcile to "resumable".
        if job.state == "running" and not self._is_alive(job_id):
            reconciled = job.model_copy(
                update={
                    "state": "resumable",
                    "resumable_from_checkpoint": True,
                    "completed_at": job.completed_at or float(time.time()),
                    "error": job.error
                    or GenerativeJobError(
                        kind="internal_error",
                        message="subprocess exited without writing terminal state",
                    ),
                }
            )
            persist_job_to_dir(self.jobs_root, reconciled, index=self._index)
            append_log_to_file(
                self.jobs_root,
                job_id,
                f"job {job_id} state=resumable reconciled subprocess_crash",
            )
            return reconciled
        return job

    def list(
        self,
        *,
        state: JobState | None = None,
        job_kind: JobKind | None = None,
    ) -> list[GenerativeJobSummary]:
        # Reconcile any running-but-dead jobs first so the list view is
        # consistent with what :meth:`get` would return for each row.
        if self.jobs_root.is_dir():
            for entry in sorted(self.jobs_root.iterdir()):
                if not (entry / "job.json").is_file():
                    continue
                try:
                    self.get(entry.name)
                except (FileNotFoundError, ValidationError, ValueError):
                    continue
        return list_jobs_in_dir(
            self.jobs_root, state=state, job_kind=job_kind
        )

    def cancel(self, job_id: str) -> GenerativeJob:
        cancel_flag = self.jobs_root / job_id / CANCEL_FLAG_FILENAME
        cancel_flag.touch()
        job = read_job_from_dir(self.jobs_root, job_id)
        if job.cancellation_requested_at is None:
            job = job.model_copy(
                update={"cancellation_requested_at": float(time.time())}
            )
            persist_job_to_dir(self.jobs_root, job, index=self._index)
        return job

    def resume(self, job_id: str) -> GenerativeJob:
        job = self.get(job_id)  # reconcile crashed state first
        if job.state not in ("resumable", "failed", "cancelled"):
            raise ValueError(
                f"job_id={job_id} state={job.state!r} is not resumable"
            )
        # Clear any leftover cancel flag from the previous run.
        cancel_flag = self.jobs_root / job_id / CANCEL_FLAG_FILENAME
        if cancel_flag.exists():
            try:
                cancel_flag.unlink()
            except OSError:  # pragma: no cover
                pass
        self._spawn(job_id, resume=True)
        return self.get(job_id)

    def tail_log(self, job_id: str, *, since_byte: int = 0) -> tuple[str, int]:
        return tail_log_file(self.jobs_root, job_id, since_byte=since_byte)

    def join(self, job_id: str, *, timeout: float | None = None) -> None:
        """Block until the named job's subprocess exits. Test helper."""

        proc = self._processes.get(job_id)
        if proc is None:
            return
        try:
            proc.wait(timeout=timeout)
        except Exception:  # pragma: no cover - best-effort
            pass

    # -- internal ------------------------------------------------------------

    def _spawn(self, job_id: str, *, resume: bool) -> None:
        import subprocess as _subprocess

        argv: list[str] = [
            self._python,
            "-m",
            "kayakgen.services.generative_jobs_runner",
            job_id,
            str(self.jobs_root),
        ]
        if resume:
            argv.append("--resume")
        proc = _subprocess.Popen(
            argv,
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
            cwd=str(self.jobs_root),
            start_new_session=True,
        )
        with self._global_lock:
            self._processes[job_id] = proc

    def _is_alive(self, job_id: str) -> bool:
        proc = self._processes.get(job_id)
        if proc is None:
            # No process handle: either the job was started by a previous
            # parent and we don't know its PID, or it never spawned. The
            # safe assumption is "not alive" so reconciliation kicks in.
            return False
        return proc.poll() is None


CANCEL_FLAG_FILENAME = "cancel.flag"
"""Per-job filename touched by the subprocess manager to request cancellation.

Lives at ``<jobs_root>/<job_id>/<filename>``; the subprocess runner polls
this file between candidate emissions via the file-backed progress sink.
"""


# ---------------------------------------------------------------------------
# Web payload helpers (RFC 0057 stage 2)
# ---------------------------------------------------------------------------


GENERATIVE_JOBS_RESULT_SEMANTICS = "raw_unvalidated"
"""Result-semantics literal carried on every generative-job payload.

The frontier metrics surfaced by the web routes inherit the claim_state of
their underlying candidate records (typically ``raw_unvalidated`` or
``uncalibrated_comparative``). The route envelope publishes the most
conservative state so the panel cannot accidentally elevate the claim.
"""


class GenerativeJobWebError(Exception):
    """Structured generative-job web error (mirrors :class:`CfdWebError`)."""

    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        super().__init__(
            str(payload.get("message", payload.get("error", "generative-job error")))
        )
        self.status = status
        self.payload = payload


def _generative_error_payload(
    error: str,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    """Structured error envelope returned by the route handlers."""

    payload: dict[str, Any] = {
        "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
        "error": error,
        "message": message,
    }
    payload.update(extra)
    return payload


def _serialize_job(job: GenerativeJob) -> dict[str, Any]:
    payload = job.model_dump(mode="json")
    payload["result_semantics"] = GENERATIVE_JOBS_RESULT_SEMANTICS
    return payload


def _serialize_summary(summary: GenerativeJobSummary) -> dict[str, Any]:
    payload = summary.model_dump(mode="json")
    payload["result_semantics"] = GENERATIVE_JOBS_RESULT_SEMANTICS
    return payload


def start_generative_job_payload(
    request_body: dict[str, Any],
    manager: "GenerativeJobManager",
    *,
    job_kind: JobKind,
) -> dict[str, Any]:
    """Validate ``spec`` from the request body and start a new job."""

    if not isinstance(request_body, dict):
        raise GenerativeJobWebError(
            400,
            _generative_error_payload(
                "invalid_request_body",
                "Request body must be a JSON object.",
            ),
        )
    spec_payload = request_body.get("spec")
    if not isinstance(spec_payload, dict):
        raise GenerativeJobWebError(
            400,
            _generative_error_payload(
                "missing_spec",
                "Request body must include a 'spec' object.",
            ),
        )
    try:
        job = manager.start(spec_payload=spec_payload, job_kind=job_kind)
    except ValidationError as exc:
        raise GenerativeJobWebError(
            400,
            _generative_error_payload(
                "spec_validation_failed",
                str(exc),
            ),
        ) from exc
    return _serialize_job(job)


def generative_job_list_payload(
    manager: "GenerativeJobManager",
    *,
    state: JobState | None = None,
    job_kind: JobKind | None = None,
) -> dict[str, Any]:
    """List jobs as a JSON payload (used by ``GET /api/generative-jobs``)."""

    summaries = manager.list(state=state, job_kind=job_kind)
    return {
        "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
        "jobs": [_serialize_summary(summary) for summary in summaries],
    }


def generative_job_full_payload(
    manager: "GenerativeJobManager",
    job_id: str,
) -> dict[str, Any]:
    """Return the full :class:`GenerativeJob` payload."""

    try:
        job = manager.get(job_id)
    except FileNotFoundError as exc:
        raise GenerativeJobWebError(
            404,
            _generative_error_payload(
                "job_not_found",
                f"No generative job recorded for job_id={job_id!r}.",
                job_id=job_id,
            ),
        ) from exc
    return _serialize_job(job)


def cancel_generative_job_payload(
    manager: "GenerativeJobManager",
    job_id: str,
) -> dict[str, Any]:
    """Signal cancellation; return the latest job payload."""

    try:
        job = manager.cancel(job_id)
    except FileNotFoundError as exc:
        raise GenerativeJobWebError(
            404,
            _generative_error_payload(
                "job_not_found",
                f"No generative job recorded for job_id={job_id!r}.",
                job_id=job_id,
            ),
        ) from exc
    return _serialize_job(job)


def resume_generative_job_payload(
    manager: "GenerativeJobManager",
    job_id: str,
) -> dict[str, Any]:
    """Resume a ``resumable`` job; return the post-resume job payload."""

    try:
        job = manager.resume(job_id)
    except FileNotFoundError as exc:
        raise GenerativeJobWebError(
            404,
            _generative_error_payload(
                "job_not_found",
                f"No generative job recorded for job_id={job_id!r}.",
                job_id=job_id,
            ),
        ) from exc
    except ValueError as exc:
        raise GenerativeJobWebError(
            409,
            _generative_error_payload(
                "job_not_resumable",
                str(exc),
                job_id=job_id,
            ),
        ) from exc
    return _serialize_job(job)


def _redact_log_text(
    text: str,
    *,
    home_dir: str | None = None,
    jobs_root: str | None = None,
) -> str:
    """Redact filesystem-disclosing prefixes from a log tail (RFC 0057 / D-11).

    - Replaces any occurrence of ``home_dir`` with ``~``.
    - Replaces any occurrence of ``jobs_root`` with ``<jobs_root>``.

    The substitutions are applied longest-prefix-first so that
    ``jobs_root`` (which often lives under ``home_dir``) is rewritten to
    its ``<jobs_root>`` token *before* the home-dir rewrite touches it.

    Byte-stable for inputs that contain neither prefix.
    """

    if not text:
        return text

    redacted = text

    candidates: list[tuple[str, str]] = []
    if jobs_root:
        candidates.append((str(jobs_root), "<jobs_root>"))
    if home_dir:
        candidates.append((str(home_dir), "~"))

    # Longest replacement target first so that a jobs_root nested inside
    # home_dir is rewritten before the home-dir substitution runs.
    candidates.sort(key=lambda pair: len(pair[0]), reverse=True)
    for needle, replacement in candidates:
        if needle and needle in redacted:
            redacted = redacted.replace(needle, replacement)
    return redacted


def generative_job_log_payload(
    manager: "GenerativeJobManager",
    job_id: str,
    *,
    since_byte: int = 0,
) -> dict[str, Any]:
    """Bounded log tail (RFC 0057). Returns text plus the byte cursor.

    Stage 4 / D-11 redaction: the operator's ``$HOME`` prefix is replaced
    with ``~`` and paths under the manager's resolved ``jobs_root`` are
    rewritten to begin with ``<jobs_root>`` before the payload leaves the
    process. Byte-stable for redaction-free inputs.
    """

    try:
        text, cursor = manager.tail_log(job_id, since_byte=since_byte)
    except FileNotFoundError as exc:
        raise GenerativeJobWebError(
            404,
            _generative_error_payload(
                "job_not_found",
                f"No generative job recorded for job_id={job_id!r}.",
                job_id=job_id,
            ),
        ) from exc

    import os as _os

    jobs_root = getattr(manager, "jobs_root", None)
    redacted_log = _redact_log_text(
        text,
        home_dir=_os.path.expanduser("~"),
        jobs_root=str(jobs_root) if jobs_root is not None else None,
    )
    return {
        "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
        "job_id": job_id,
        "log": redacted_log,
        "cursor": cursor,
    }


def generative_job_frontier_payload(
    manager: "GenerativeJobManager",
    job_id: str,
) -> dict[str, Any]:
    """Resolved Pareto frontier rows from a completed search-job ``run.json``.

    Only ``search`` jobs produce a Pareto frontier; sweep jobs return
    an empty list with an explanatory note. Rows carry candidate_key,
    status, parameters, hull_hash, claim_state, and the candidate-level
    summary dict — no derived ``max_gz_m`` / ``heel_at_max_gz_deg`` /
    ``range_positive_stability_deg`` are projected onto the envelope.
    """

    job = manager.get(job_id)
    run_json_path = Path(job.output_dir) / "run.json"
    if not run_json_path.exists():
        return {
            "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
            "job_id": job_id,
            "frontier": [],
            "frontier_available": False,
            "note": "run.json not yet written",
        }
    try:
        run_payload = json.loads(run_json_path.read_text())
    except (OSError, ValueError):
        return {
            "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
            "job_id": job_id,
            "frontier": [],
            "frontier_available": False,
            "note": "run.json could not be parsed",
        }
    candidates = run_payload.get("candidates") or []
    frontier_keys = set(run_payload.get("final_frontier_keys") or [])
    rows: list[dict[str, Any]] = []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        key = cand.get("candidate_key")
        if key not in frontier_keys:
            continue
        rows.append(
            {
                "candidate_key": key,
                "status": cand.get("status"),
                "parameters": cand.get("parameters", {}),
                "hull_record_hash": cand.get("hull_hash"),
                "summary": cand.get("summary", {}),
            }
        )
    rows.sort(key=lambda r: r.get("candidate_key") or "")
    return {
        "result_semantics": GENERATIVE_JOBS_RESULT_SEMANTICS,
        "job_id": job_id,
        "frontier": rows,
        "frontier_available": bool(rows),
    }


__all__ = [
    "CANCEL_FLAG_FILENAME",
    "GENERATIVE_JOBS_RESULT_SEMANTICS",
    "ForkError",
    "GenerativeJob",
    "GenerativeJobError",
    "GenerativeJobManager",
    "GenerativeJobProgress",
    "GenerativeJobProgressSink",
    "GenerativeJobSummary",
    "GenerativeJobWebError",
    "InProcessGenerativeJobManager",
    "JOB_LOG_MAX_BYTES",
    "JobErrorKind",
    "JobKind",
    "JobState",
    "SubprocessGenerativeJobManager",
    "append_log_to_file",
    "canonical_job_json",
    "cancel_generative_job_payload",
    "classify_runner_error",
    "fork_generative_job",
    "fork_generative_job_payload",
    "generative_job_frontier_payload",
    "generative_job_full_payload",
    "generative_job_list_payload",
    "generative_job_log_payload",
    "initialize_job_dir",
    "list_jobs_in_dir",
    "persist_job_to_dir",
    "read_job_from_dir",
    "resume_generative_job_payload",
    "start_generative_job_payload",
    "summarize_job",
    "tail_log_file",
]


# Re-export the fork helpers at module bottom so the
# ``kayakgen.services.generative_jobs`` surface includes them without
# creating an import cycle at module-load time.
from kayakgen.services.generative_jobs_fork import (  # noqa: E402
    ForkError,
    fork_generative_job,
    fork_generative_job_payload,
)
