"""Fork-with-new-seed primitive for generative jobs (RFC 0057 stage 4, D-12).

This module exposes a small surface that lets the operator clone a
finished search job with a different RNG seed while leaving the source
job's read-model semantics, claim state, and on-disk artifacts
untouched. It deliberately reuses ``InProcessGenerativeJobManager`` /
``SubprocessGenerativeJobManager`` to start the new job so the fork
inherits the parent manager's persistence, indexing, and progress-sink
contracts.

The only structural change to :class:`GenerativeJob` is the optional
``forked_from`` informational field; existing start/cancel/resume code
ignores it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kayakgen.services.generative_jobs import (
    GenerativeJob,
    GenerativeJobManager,
    GenerativeJobWebError,
    _serialize_job,
    persist_job_to_dir,
)


class ForkError(Exception):
    """Raised when a generative-job fork request cannot be honored."""


def _patch_seed(spec_payload: dict[str, Any], new_seed: int) -> dict[str, Any]:
    """Return a copy of ``spec_payload`` with the algorithm seed replaced.

    Supports both NSGA-II (``algorithm.kind == "nsga2"``) and EHVI
    (``algorithm.kind == "ehvi"``) specs. Both store the RNG seed at
    ``algorithm.seed``.
    """

    patched = json.loads(json.dumps(spec_payload))  # deep copy via JSON
    algorithm = patched.get("algorithm")
    if not isinstance(algorithm, dict):
        raise ForkError(
            "spec.json is missing the 'algorithm' block; cannot patch seed"
        )
    kind = algorithm.get("kind")
    if kind not in ("nsga2", "ehvi"):
        raise ForkError(
            f"unsupported algorithm.kind={kind!r}; only 'nsga2' and 'ehvi' are forkable"
        )
    algorithm["seed"] = int(new_seed)
    patched["algorithm"] = algorithm
    return patched


def fork_generative_job(
    manager: GenerativeJobManager,
    source_job_id: str,
    *,
    new_seed: int,
) -> GenerativeJob:
    """Clone ``source_job_id`` as a new generative job with ``new_seed``.

    Reads the source job's persisted ``spec.json``, patches the
    algorithm seed, and starts a new job via ``manager.start``. After
    the new job is registered, the new ``job.json`` is rewritten with
    ``forked_from = source_job_id`` for traceability.

    Raises:
        ForkError: if the source job kind cannot be forked (sweep jobs
            are deterministic and have no RNG seed) or if the source
            spec lacks an algorithm block.
        FileNotFoundError: if the source job_id is unknown to the
            manager (no ``job.json`` exists for it).
    """

    source = manager.get(source_job_id)
    if source.job_kind == "sweep":
        raise ForkError(
            "sweep jobs cannot be forked with a new seed; sweeps are deterministic"
        )

    jobs_root = Path(getattr(manager, "jobs_root"))
    spec_path = jobs_root / source_job_id / "spec.json"
    if not spec_path.exists():
        raise FileNotFoundError(
            f"spec.json missing for source job_id={source_job_id!r}"
        )
    source_spec = json.loads(spec_path.read_text())
    patched = _patch_seed(source_spec, new_seed)

    new_job = manager.start(spec_payload=patched, job_kind=source.job_kind)
    # Annotate ``forked_from`` on the new job. We have to coordinate
    # with the worker thread's own ``job.json`` writers — both share
    # ``<job_id>/job.json.tmp`` as their atomic-rename staging path,
    # so we acquire the manager's per-job lock when it exposes one to
    # serialize against the worker.
    index = getattr(manager, "_index", None)
    lock_for = getattr(manager, "_lock_for", None)
    if callable(lock_for):
        lock = lock_for(new_job.job_id)
        with lock:
            fresh = manager.get(new_job.job_id)
            annotated = fresh.model_copy(update={"forked_from": source_job_id})
            persist_job_to_dir(jobs_root, annotated, index=index)
    else:
        fresh = manager.get(new_job.job_id)
        annotated = fresh.model_copy(update={"forked_from": source_job_id})
        persist_job_to_dir(jobs_root, annotated, index=index)
    return annotated


def fork_generative_job_payload(
    manager: GenerativeJobManager,
    source_job_id: str,
    *,
    new_seed: int,
) -> dict[str, Any]:
    """Web wrapper around :func:`fork_generative_job`.

    Returns the same serialized shape as ``_serialize_job`` so the
    ``POST /api/generative-jobs/{job_id}/fork`` route's response
    matches the rest of the generative-job payload family.

    Maps :class:`ForkError` to HTTP 400 (``cannot_fork_sweep`` /
    ``cannot_fork_spec``) and :class:`FileNotFoundError` to HTTP 404
    (``job_not_found``).
    """

    try:
        forked = fork_generative_job(
            manager, source_job_id, new_seed=new_seed
        )
    except FileNotFoundError as exc:
        raise GenerativeJobWebError(
            404,
            {
                "result_semantics": "raw_unvalidated",
                "error": "job_not_found",
                "message": (
                    f"No generative job recorded for job_id={source_job_id!r}."
                ),
                "job_id": source_job_id,
            },
        ) from exc
    except ForkError as exc:
        message = str(exc)
        if "sweep" in message:
            error_code = "cannot_fork_sweep"
        else:
            error_code = "cannot_fork_spec"
        raise GenerativeJobWebError(
            400,
            {
                "result_semantics": "raw_unvalidated",
                "error": error_code,
                "message": message,
                "job_id": source_job_id,
            },
        ) from exc
    return _serialize_job(forked)


__all__ = [
    "ForkError",
    "fork_generative_job",
    "fork_generative_job_payload",
]
