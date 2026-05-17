"""Active-search runner (RFC 0044 v1 NSGA-II + RFC 0047 v2 EHVI).

Orchestrates a vendored NSGA-II or EHVI run, evaluates each proposed
candidate via :func:`kayakgen.search.sweep._evaluate_candidate`, applies
hard-rejection constraints, and writes:

  - ``runs/<name>/spec.json``        — input spec, persisted byte-for-byte
  - ``runs/<name>/candidates/<key>.record.json`` — per-candidate record
  - ``runs/<name>/summary.csv``       — reused sweep writer
  - ``runs/<name>/failures.jsonl``    — reused sweep writer
  - ``runs/<name>/run.json``          — top-level run record with
                                        ``search_metadata`` header
  - ``runs/<name>/state.json``        — algorithm checkpoint (seed,
                                        generation index, queued population)

Determinism: the entire run uses ``random.Random(spec.algorithm.seed)``. No
calls to the global ``random`` state are made anywhere on this path. Resume
reuses the persisted state checkpoint to replay queued candidates in the same
order before continuing the algorithm.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Iterable, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kayakgen.model.hull import Hull
from kayakgen.search.active.constraints import ConstraintViolation, evaluate_constraints
from kayakgen.search.active.ehvi import EhviDimensionError, compute_ehvi
from kayakgen.search.active.gp import GaussianProcess, kernel_by_name
from kayakgen.search.active.nsga2 import (
    Generation,
    Individual,
    nsga2_iterations,
)
from kayakgen.search.active.spec import (
    ChoiceVariable,
    EhviAlgorithmConfig,
    EhviHistoryEntry,
    GenerationHistoryEntry,
    ObjectiveSpec,
    SearchClass,
    SearchMetadata,
    SearchSpec,
    SearchVariable,
    TerminationReason,
    UniformVariable,
    load_search_spec,
)
from kayakgen.search.objectives import DEFAULT_OBJECTIVE_METRICS, OBJECTIVE_METADATA
from kayakgen.search.pareto import (
    Objective,
    ensure_objectives_claim_admissible_for_search,
    ensure_objectives_not_high_angle_gz,
)
from kayakgen.search.sweep import (
    CandidateRecord,
    SweepSpec,
    _evaluate_candidate,
    _index_row_for_candidate,
    _write_failures,
    _write_summary,
)


class SearchRunResult(BaseModel):
    """Top-level summary returned by :func:`run_search`."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str
    run_dir: str
    search_class: SearchClass
    search_metadata: SearchMetadata
    final_frontier_keys: list[str] = Field(default_factory=list)
    candidate_count: int
    completed_count: int
    failed_count: int
    constraint_failed_count: int
    pending_count: int


class SearchRunRecord(BaseModel):
    """Top-level ``run.json`` payload for an active-search run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    name: str
    spec_hash: str
    search_class: SearchClass
    search_metadata: SearchMetadata
    candidate_count: int
    pending_count: int
    completed_count: int
    failed_count: int
    constraint_failed_count: int
    final_frontier_keys: list[str]
    candidates: list[CandidateRecord]


# ---------------------------------------------------------------------------
# Spec helpers
# ---------------------------------------------------------------------------


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def spec_hash(spec: SearchSpec) -> str:
    return hashlib.sha256(
        _canonical_json(spec.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()


def resolve_objectives(spec: SearchSpec) -> list[ObjectiveSpec]:
    if spec.objectives is not None:
        return list(spec.objectives)
    return [
        ObjectiveSpec(
            metric=metric,
            direction=OBJECTIVE_METADATA[metric].direction,
        )
        for metric in DEFAULT_OBJECTIVE_METRICS
    ]


def _candidate_key(spec_h: str, genome: dict[str, Any]) -> str:
    payload = {"spec_hash": spec_h, "parameters": genome}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _make_sweep_spec_shim(search: SearchSpec) -> SweepSpec:
    """Build a one-row-variable SweepSpec carrying the same evaluator options.

    ``_evaluate_candidate`` only consults the ``evaluators`` attribute on its
    ``spec`` argument; we still satisfy the validator by stuffing a single
    no-op ``values`` variable so SweepSpec's ``variables`` invariant holds.
    """
    return SweepSpec(
        name=search.name,
        base_hull=dict(search.base_hull),
        variables={"_search_placeholder": {"kind": "values", "values": [0.0]}},
        evaluators=search.evaluators,
    )


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _hull_from_genome(spec: SearchSpec, genome: dict[str, Any]) -> tuple[Hull, dict[str, Any]]:
    attempted = dict(spec.base_hull) | dict(genome)
    hull = Hull.model_validate(attempted)
    return hull, attempted


def _record_path(out: Path, candidate_key: str) -> Path:
    return out / "candidates" / f"{candidate_key}.record.json"


def _write_record(record: CandidateRecord, out: Path, *, store: Any | None = None) -> None:
    path = _record_path(out, record.candidate_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    if store is not None:
        store.put_json(
            "candidate_record",
            record,
            candidate_key=record.candidate_key,
            canonical_path=path,
        )
        return
    path.write_text(record.model_dump_json(indent=2))


def _build_failed_record(
    *,
    spec: SearchSpec,
    index: int,
    candidate_key: str,
    genome: dict[str, Any],
    attempted: dict[str, Any],
    error: str,
) -> CandidateRecord:
    return CandidateRecord(
        candidate_index=index,
        candidate_key=candidate_key,
        parameters=genome,
        attempted_hull=attempted,
        status="failed",
        evaluator_settings=spec.evaluators.model_dump(mode="json"),
        evaluator_versions={"search_schema": "1"},
        error=error,
    )


def _build_constraint_failed_record(
    *,
    base: CandidateRecord,
    violations: list[ConstraintViolation],
) -> CandidateRecord:
    updates: dict[str, Any] = {
        "status": "constraint_failed",
        "error": json.dumps(
            {"violations": [v.model_dump(mode="json") for v in violations]}
        ),
    }
    summary = dict(base.summary)
    summary["constraint_violations"] = [v.model_dump(mode="json") for v in violations]
    updates["summary"] = summary
    return base.model_copy(update=updates)


def _build_pending_record(
    *,
    spec: SearchSpec,
    index: int,
    candidate_key: str,
    genome: dict[str, Any],
    generation_index: int,
) -> CandidateRecord:
    attempted = dict(spec.base_hull) | dict(genome)
    summary = {"queued_in_generation": generation_index}
    return CandidateRecord(
        candidate_index=index,
        candidate_key=candidate_key,
        parameters=genome,
        attempted_hull=attempted,
        status="pending",
        evaluator_settings=spec.evaluators.model_dump(mode="json"),
        evaluator_versions={"search_schema": "1"},
        summary=summary,
    )


def _objective_value(record: CandidateRecord, metric: str) -> float | None:
    if metric in record.summary:
        value = record.summary.get(metric)
    elif metric in record.parameters:
        value = record.parameters.get(metric)
    else:
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _signed_objective(
    record: CandidateRecord, objectives: list[ObjectiveSpec]
) -> tuple[float, ...]:
    """Return objectives as minimize-direction floats; inf for missing."""
    out: list[float] = []
    for obj in objectives:
        val = _objective_value(record, obj.metric)
        if val is None:
            out.append(math.inf)
        elif obj.direction == "max":
            out.append(-val)
        else:
            out.append(val)
    return tuple(out)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


CandidateStatus = Literal["pending", "complete", "failed", "skipped", "constraint_failed"]


class _PendingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_index: int
    candidate_key: str
    genome: dict[str, Any]
    generation_index: int


class _RunnerState(BaseModel):
    """Persisted algorithm checkpoint (``state.json``)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    seed: int
    next_candidate_index: int = 0
    next_generation_index: int = 0
    pending_queue: list[_PendingEntry] = Field(default_factory=list)
    history: list[GenerationHistoryEntry] = Field(default_factory=list)
    finished_generations: int = 0


def _state_path(out: Path) -> Path:
    return out / "state.json"


def _load_state(out: Path) -> _RunnerState | None:
    path = _state_path(out)
    if not path.exists():
        return None
    return _RunnerState.model_validate_json(path.read_text())


def _write_state(state: _RunnerState, out: Path) -> None:
    _state_path(out).write_text(state.model_dump_json(indent=2))


def _budget_remaining(
    spec: SearchSpec, evaluations: int, started_at: float
) -> TerminationReason | None:
    """Return a termination reason if budget exhausted, else None."""
    if (
        spec.budget.max_evaluations is not None
        and evaluations >= spec.budget.max_evaluations
    ):
        return "budget_exhausted"
    if spec.budget.wall_clock_seconds is not None:
        elapsed = time.monotonic() - started_at
        if elapsed >= spec.budget.wall_clock_seconds:
            return "wall_clock_exhausted"
    return None


def run_search(
    spec_path: str | Path,
    out_dir: str | Path,
    *,
    resume: bool = False,
) -> SearchRunResult:
    """Run an active-search session.

    On budget or wall-clock exhaustion, queued-but-unrun individuals are
    persisted as ``pending`` candidate records so a follow-up
    ``run_search(..., resume=True)`` can replay them in the same order before
    continuing the algorithm.
    """

    if isinstance(spec_path, Path):
        spec_path_p = spec_path
    else:
        spec_path_p = Path(spec_path)
    spec = load_search_spec(spec_path_p)

    from kayakgen import __version__ as kayakgen_version
    from kayakgen.services.artifact_store import (
        FilesystemArtifactStore,
        index_candidates,
        index_run_directory,
    )
    from kayakgen.services.identity import run_hash as compute_run_hash

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates").mkdir(parents=True, exist_ok=True)
    spec_h_pre = spec_hash(spec)
    run_id = f"search-{spec_h_pre[:16]}-{out.name}"
    store = FilesystemArtifactStore(out, run_id=run_id)
    run_hash_value = compute_run_hash(spec.model_dump(mode="json"), kayakgen_version)
    index_run_directory(
        out,
        run_id=run_id,
        kind="search",
        spec_hash=spec_h_pre,
        run_hash_value=run_hash_value,
        index=store.index,
    )
    store.put_json("search_run_record", spec, canonical_path=out / "spec.json")

    objectives = resolve_objectives(spec)
    objective_models = [
        Objective(metric=obj.metric, direction=obj.direction) for obj in objectives
    ]

    ensure_objectives_not_high_angle_gz(objective_models)
    ensure_objectives_claim_admissible_for_search(
        objective_models,
        explicit_exploratory=spec.objectives_explicit_exploratory,
    )

    search_class: SearchClass = (
        "exploratory" if spec.objectives_explicit_exploratory else "conservative"
    )

    if isinstance(spec.algorithm, EhviAlgorithmConfig):
        return _run_ehvi_search(
            spec=spec,
            out=out,
            objectives=objectives,
            search_class=search_class,
            resume=resume,
            store=store,
            run_id=run_id,
        )

    sweep_shim = _make_sweep_spec_shim(spec)
    spec_h = spec_hash(spec)
    started_at = time.monotonic()

    state = _load_state(out) if resume else None
    if state is None:
        state = _RunnerState(seed=spec.algorithm.seed)

    records_by_key: dict[str, CandidateRecord] = {}
    # If resuming, pre-load existing records that were already finalised.
    if resume:
        for path in sorted((out / "candidates").glob("*.record.json")):
            try:
                rec = CandidateRecord.model_validate_json(path.read_text())
            except ValidationError:
                continue
            if rec.status in ("complete", "failed", "constraint_failed"):
                records_by_key[rec.candidate_key] = rec

    # ---- Replay pending queue first (resume) -------------------------------
    pending_queue: list[_PendingEntry] = list(state.pending_queue)
    state.pending_queue = []
    evaluations = sum(
        1 for r in records_by_key.values() if r.status != "pending"
    )

    termination_reason: TerminationReason | None = None

    def _evaluate_and_record(
        index: int,
        candidate_key: str,
        genome: dict[str, Any],
        generation_index: int,
    ) -> CandidateRecord:
        try:
            hull, attempted = _hull_from_genome(spec, genome)
        except (ValidationError, ValueError) as exc:
            record = _build_failed_record(
                spec=spec,
                index=index,
                candidate_key=candidate_key,
                genome=genome,
                attempted=dict(spec.base_hull) | dict(genome),
                error=str(exc),
            )
            _write_record(record, out, store=store)
            return record

        try:
            record = _evaluate_candidate(
                hull=hull,
                spec=sweep_shim,
                index=index,
                candidate_key=candidate_key,
                params=dict(genome),
                attempted=attempted,
                out=out,
                store=store,
            )
        except (ValidationError, ValueError) as exc:
            record = _build_failed_record(
                spec=spec,
                index=index,
                candidate_key=candidate_key,
                genome=genome,
                attempted=attempted,
                error=str(exc),
            )
            _write_record(record, out, store=store)
            return record

        violations = evaluate_constraints(record.summary, spec.constraints)
        if violations:
            record = _build_constraint_failed_record(base=record, violations=violations)
        _write_record(record, out, store=store)
        return record

    for entry in pending_queue:
        if termination_reason is not None:
            # We did not get to it; re-queue.
            state.pending_queue.append(entry)
            continue
        # Skip already-finalised candidates from prior runs.
        existing = records_by_key.get(entry.candidate_key)
        if existing is not None and existing.status != "pending":
            evaluations = sum(
                1 for r in records_by_key.values() if r.status != "pending"
            )
            continue
        record = _evaluate_and_record(
            entry.candidate_index,
            entry.candidate_key,
            entry.genome,
            entry.generation_index,
        )
        records_by_key[entry.candidate_key] = record
        evaluations += 1
        reason = _budget_remaining(spec, evaluations, started_at)
        if reason is not None:
            termination_reason = reason

    # ---- Algorithm iteration ----------------------------------------------
    history: list[GenerationHistoryEntry] = list(state.history)

    if termination_reason is None:

        def _objective_evaluator(individual: Individual) -> Individual:
            nonlocal evaluations, termination_reason
            if termination_reason is not None:
                # Mark as infeasible placeholder so dominance sort ignores it;
                # the runner ignores these post-hoc.
                return individual.model_copy(
                    update={
                        "objectives": tuple(math.inf for _ in objectives),
                        "feasible": False,
                    }
                )
            candidate_index = state.next_candidate_index
            state.next_candidate_index += 1
            candidate_key = _candidate_key(spec_h, individual.genome)
            existing = records_by_key.get(candidate_key)
            if existing is None or existing.status == "pending":
                record = _evaluate_and_record(
                    candidate_index,
                    candidate_key,
                    individual.genome,
                    state.next_generation_index,
                )
                records_by_key[candidate_key] = record
                evaluations += 1
            else:
                record = existing
            reason = _budget_remaining(spec, evaluations, started_at)
            if reason is not None:
                termination_reason = reason
            obj = _signed_objective(record, objectives)
            feasible = record.status == "complete"
            return individual.model_copy(
                update={"objectives": obj, "feasible": feasible}
            )

        iterator = nsga2_iterations(
            spec.algorithm,
            spec.search_space,
            _objective_evaluator,
        )
        try:
            for generation in iterator:
                state.next_generation_index = generation.index + 1
                history_entry = _build_generation_history(
                    generation, records_by_key, objectives, spec_h
                )
                history.append(history_entry)
                state.history = history
                state.finished_generations = generation.index + 1
                _write_state(state, out)
                if termination_reason is not None:
                    # Queue any in-flight unevaluated members of the *next*
                    # generation for resume.
                    break
        except StopIteration:  # pragma: no cover - defensive
            pass

    if termination_reason is None:
        termination_reason = "completed"

    # ---- Pending records for queued-but-unrun individuals ------------------
    # If the budget ran out mid-evaluation, any genome in the algorithm's
    # "next generation" queue that hasn't been evaluated is enumerated here.
    # The current implementation does not pre-queue offspring before
    # evaluation; instead we surface any individuals that the evaluator marked
    # infeasible because the budget had already tripped.
    # (Their records-by-key entries don't exist; we add pending entries for
    # them so resume picks them up.)
    if termination_reason in ("budget_exhausted", "wall_clock_exhausted"):
        # Anything still in state.pending_queue stays pending.
        for entry in list(state.pending_queue):
            existing = records_by_key.get(entry.candidate_key)
            if existing is None or existing.status == "pending":
                record = _build_pending_record(
                    spec=spec,
                    index=entry.candidate_index,
                    candidate_key=entry.candidate_key,
                    genome=entry.genome,
                    generation_index=entry.generation_index,
                )
                _write_record(record, out, store=store)
                records_by_key[entry.candidate_key] = record

    # ---- Build final records, frontier, summary, run.json ------------------
    ordered = sorted(records_by_key.values(), key=lambda r: r.candidate_index)
    final_frontier_keys = _final_frontier_keys(
        ordered, objectives, exploratory=spec.objectives_explicit_exploratory
    )

    pending_count = sum(1 for r in ordered if r.status == "pending")
    completed_count = sum(1 for r in ordered if r.status == "complete")
    failed_count = sum(1 for r in ordered if r.status == "failed")
    constraint_failed_count = sum(
        1 for r in ordered if r.status == "constraint_failed"
    )

    metadata = SearchMetadata(
        seed=spec.algorithm.seed,
        population_size=spec.algorithm.population_size,
        generations=spec.algorithm.generations,
        objectives=objectives,
        constraints=list(spec.constraints),
        realized_max_evaluations=spec.budget.max_evaluations,
        realized_wall_clock_seconds=spec.budget.wall_clock_seconds,
        realized_evaluations=evaluations,
        termination_reason=termination_reason,
        history=history,
    )

    run_record = SearchRunRecord(
        name=spec.name,
        spec_hash=spec_h,
        search_class=search_class,
        search_metadata=metadata,
        candidate_count=len(ordered),
        pending_count=pending_count,
        completed_count=completed_count,
        failed_count=failed_count,
        constraint_failed_count=constraint_failed_count,
        final_frontier_keys=final_frontier_keys,
        candidates=ordered,
    )
    store.put_json("search_run_record", run_record, canonical_path=out / "run.json")
    _write_summary(out / "summary.csv", ordered)
    store.put_file("sweep_summary_csv", out / "summary.csv")
    _write_failures(
        out / "failures.jsonl",
        [r for r in ordered if r.status in ("failed", "constraint_failed")],
    )
    store.put_file("sweep_failures_jsonl", out / "failures.jsonl")
    _write_state(state, out)
    index_candidates(
        run_id=run_id,
        candidate_rows=[_index_row_for_candidate(rec) for rec in ordered],
        index=store.index,
    )

    return SearchRunResult(
        name=spec.name,
        run_dir=str(out),
        search_class=search_class,
        search_metadata=metadata,
        final_frontier_keys=final_frontier_keys,
        candidate_count=len(ordered),
        completed_count=completed_count,
        failed_count=failed_count,
        constraint_failed_count=constraint_failed_count,
        pending_count=pending_count,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_generation_history(
    generation: Generation,
    records_by_key: dict[str, CandidateRecord],
    objectives: list[ObjectiveSpec],
    spec_h: str,
) -> GenerationHistoryEntry:
    population_records: list[CandidateRecord] = []
    for individual in generation.population:
        key = _candidate_key(spec_h, individual.genome)
        rec = records_by_key.get(key)
        if rec is not None:
            population_records.append(rec)

    evaluated = [r for r in population_records if r.status == "complete"]
    constraint_failed = [
        r for r in population_records if r.status == "constraint_failed"
    ]
    failed = [r for r in population_records if r.status == "failed"]
    frontier_size = len(generation.fronts[0]) if generation.fronts else 0

    summary: dict[str, dict[str, float]] = {}
    for obj in objectives:
        values: list[float] = []
        for rec in evaluated:
            val = _objective_value(rec, obj.metric)
            if val is None:
                continue
            values.append(val)
        if not values:
            continue
        values_sorted = sorted(values)
        summary[obj.metric] = {
            "best": values_sorted[0] if obj.direction == "min" else values_sorted[-1],
            "worst": values_sorted[-1] if obj.direction == "min" else values_sorted[0],
            "median": values_sorted[len(values_sorted) // 2],
        }
    return GenerationHistoryEntry(
        generation=generation.index,
        evaluated_count=len(evaluated),
        constraint_failed_count=len(constraint_failed),
        failed_count=len(failed),
        frontier_size=frontier_size,
        objective_summary=summary,
    )


# ---------------------------------------------------------------------------
# EHVI runner (RFC 0047)
# ---------------------------------------------------------------------------


_EHVI_AUTO_REFERENCE_MARGIN = 0.10


def _continuous_variable_names(
    search_space: dict[str, SearchVariable],
) -> list[str]:
    return [name for name, var in search_space.items() if isinstance(var, UniformVariable)]


def _featureise_genome(
    genome: dict[str, Any], names: list[str], search_space: dict[str, SearchVariable]
) -> np.ndarray:
    out = np.empty(len(names), dtype=float)
    for i, name in enumerate(names):
        var = search_space[name]
        if isinstance(var, UniformVariable):
            out[i] = (float(genome[name]) - var.min) / max(var.max - var.min, 1.0e-12)
        else:  # pragma: no cover - filtered by names
            out[i] = 0.0
    return out


def _latin_hypercube_unit(
    rng: np.random.Generator, n_samples: int, n_dim: int
) -> np.ndarray:
    """Return ``(n_samples, n_dim)`` LHS draws in [0, 1)."""
    if n_samples <= 0 or n_dim <= 0:
        return np.empty((max(n_samples, 0), max(n_dim, 0)), dtype=float)
    cuts = np.arange(n_samples, dtype=float) / float(n_samples)
    u = rng.uniform(size=(n_samples, n_dim))
    columns = []
    for d in range(n_dim):
        perm = rng.permutation(n_samples)
        columns.append((cuts + u[:, d] / float(n_samples))[perm])
    return np.stack(columns, axis=1)


def _sample_genome_from_unit(
    unit: np.ndarray,
    search_space: dict[str, SearchVariable],
    py_rng: random.Random,
) -> dict[str, Any]:
    """Map a [0,1) unit vector to a genome dict.

    Continuous variables come from ``unit`` (LHS draws); choice variables use
    the seeded ``random.Random`` to keep parity with v1's stochastic surface.
    """
    genome: dict[str, Any] = {}
    cont_index = 0
    for name, var in search_space.items():
        if isinstance(var, UniformVariable):
            u = float(unit[cont_index])
            cont_index += 1
            genome[name] = var.min + u * (var.max - var.min)
        elif isinstance(var, ChoiceVariable):
            genome[name] = py_rng.choice(var.values)
        else:  # pragma: no cover - guarded by spec
            raise TypeError(f"unsupported search variable: {var!r}")
    return genome


def _signed_value(value: float, direction: Literal["min", "max"]) -> float:
    return -value if direction == "max" else value


def _ehvi_pareto_front(
    records: Iterable[CandidateRecord], objectives: list[ObjectiveSpec]
) -> np.ndarray:
    """Return the non-dominated front (minimisation space) of evaluated records."""
    pts: list[list[float]] = []
    for rec in records:
        if rec.status != "complete":
            continue
        row: list[float] = []
        ok = True
        for obj in objectives:
            v = _objective_value(rec, obj.metric)
            if v is None:
                ok = False
                break
            row.append(_signed_value(v, obj.direction))
        if ok:
            pts.append(row)
    if not pts:
        return np.empty((0, len(objectives)), dtype=float)
    arr = np.asarray(pts, dtype=float)
    # Filter to non-dominated.
    keep: list[int] = []
    for i in range(arr.shape[0]):
        dominated = False
        for j in range(arr.shape[0]):
            if i == j:
                continue
            if np.all(arr[j] <= arr[i]) and np.any(arr[j] < arr[i]):
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return arr[np.array(keep, dtype=int)]


def _ehvi_reference_point(
    algorithm: EhviAlgorithmConfig,
    evaluated_points: np.ndarray,
    n_obj: int,
) -> np.ndarray:
    if algorithm.reference_point == "auto":
        if evaluated_points.shape[0] == 0:
            return np.zeros(n_obj, dtype=float) + 1.0
        worst = np.max(evaluated_points, axis=0)
        span = np.maximum(
            np.max(evaluated_points, axis=0) - np.min(evaluated_points, axis=0), 1.0
        )
        return worst + _EHVI_AUTO_REFERENCE_MARGIN * span
    ref = np.asarray(algorithm.reference_point, dtype=float)
    if ref.shape[0] != n_obj:
        raise ValueError(
            f"reference_point dimensionality {ref.shape[0]} does not match "
            f"objective count {n_obj}"
        )
    return ref


def _run_ehvi_search(
    *,
    spec: SearchSpec,
    out: Path,
    objectives: list[ObjectiveSpec],
    search_class: SearchClass,
    resume: bool,
    store: Any | None = None,
    run_id: str | None = None,
) -> SearchRunResult:
    """RFC 0047 v2: Latin-hypercube initialisation + EHVI acquisition loop."""

    algorithm = spec.algorithm
    assert isinstance(algorithm, EhviAlgorithmConfig)

    if len(objectives) > 3:
        raise EhviDimensionError(
            f"EHVI v1 supports 1-3 objectives; spec declares {len(objectives)}"
        )

    cont_names = _continuous_variable_names(spec.search_space)
    if not cont_names:
        raise ValueError(
            "EHVI requires at least one uniform variable in search_space"
        )

    sweep_shim = _make_sweep_spec_shim(spec)
    spec_h = spec_hash(spec)
    started_at = time.monotonic()

    state = _load_state(out) if resume else None
    if state is None:
        state = _RunnerState(seed=algorithm.seed)

    py_rng = random.Random(algorithm.seed)
    np_rng = np.random.default_rng(algorithm.seed)

    records_by_key: dict[str, CandidateRecord] = {}
    if resume:
        for path in sorted((out / "candidates").glob("*.record.json")):
            try:
                rec = CandidateRecord.model_validate_json(path.read_text())
            except ValidationError:
                continue
            if rec.status in ("complete", "failed", "constraint_failed"):
                records_by_key[rec.candidate_key] = rec

    evaluations = sum(1 for r in records_by_key.values() if r.status != "pending")
    termination_reason: TerminationReason | None = None
    ehvi_history: list[EhviHistoryEntry] = []

    def _evaluate_and_record(
        index: int,
        candidate_key: str,
        genome: dict[str, Any],
    ) -> CandidateRecord:
        try:
            hull, attempted = _hull_from_genome(spec, genome)
        except (ValidationError, ValueError) as exc:
            record = _build_failed_record(
                spec=spec,
                index=index,
                candidate_key=candidate_key,
                genome=genome,
                attempted=dict(spec.base_hull) | dict(genome),
                error=str(exc),
            )
            _write_record(record, out, store=store)
            return record
        try:
            record = _evaluate_candidate(
                hull=hull,
                spec=sweep_shim,
                index=index,
                candidate_key=candidate_key,
                params=dict(genome),
                attempted=attempted,
                out=out,
                store=store,
            )
        except (ValidationError, ValueError) as exc:
            record = _build_failed_record(
                spec=spec,
                index=index,
                candidate_key=candidate_key,
                genome=genome,
                attempted=attempted,
                error=str(exc),
            )
            _write_record(record, out, store=store)
            return record
        violations = evaluate_constraints(record.summary, spec.constraints)
        if violations:
            record = _build_constraint_failed_record(base=record, violations=violations)
        _write_record(record, out, store=store)
        return record

    def _append_history(iteration: int, ehvi_score: float) -> None:
        evaluated = [r for r in records_by_key.values() if r.status == "complete"]
        constraint_failed = [
            r for r in records_by_key.values() if r.status == "constraint_failed"
        ]
        failed = [r for r in records_by_key.values() if r.status == "failed"]
        pareto = _ehvi_pareto_front(records_by_key.values(), objectives)
        summary: dict[str, dict[str, float]] = {}
        for obj in objectives:
            values: list[float] = []
            for rec in evaluated:
                val = _objective_value(rec, obj.metric)
                if val is None:
                    continue
                values.append(val)
            if not values:
                continue
            values_sorted = sorted(values)
            summary[obj.metric] = {
                "best": values_sorted[0] if obj.direction == "min" else values_sorted[-1],
                "worst": values_sorted[-1] if obj.direction == "min" else values_sorted[0],
                "median": values_sorted[len(values_sorted) // 2],
            }
        ehvi_history.append(
            EhviHistoryEntry(
                iteration=iteration,
                evaluated_count=len(evaluated),
                constraint_failed_count=len(constraint_failed),
                failed_count=len(failed),
                frontier_size=int(pareto.shape[0]),
                ehvi_score=float(ehvi_score),
                objective_summary=summary,
            )
        )

    # ---- Initial Latin-hypercube draw ------------------------------------
    initial_unit = _latin_hypercube_unit(
        np_rng, algorithm.initial_population_size, len(cont_names)
    )

    for i in range(algorithm.initial_population_size):
        if termination_reason is not None:
            break
        # Build genome with the LHS row, mapping back to variable bounds.
        # Iterate search_space in declaration order so continuous indices line
        # up with the LHS row.
        genome: dict[str, Any] = {}
        cont_idx = 0
        for name, var in spec.search_space.items():
            if isinstance(var, UniformVariable):
                u = float(initial_unit[i, cont_idx])
                cont_idx += 1
                genome[name] = var.min + u * (var.max - var.min)
            elif isinstance(var, ChoiceVariable):
                genome[name] = py_rng.choice(var.values)
            else:  # pragma: no cover
                raise TypeError(f"unsupported variable: {var!r}")
        candidate_key = _candidate_key(spec_h, genome)
        existing = records_by_key.get(candidate_key)
        if existing is None or existing.status == "pending":
            record = _evaluate_and_record(state.next_candidate_index, candidate_key, genome)
            state.next_candidate_index += 1
            records_by_key[candidate_key] = record
            evaluations += 1
        _append_history(iteration=i, ehvi_score=0.0)
        reason = _budget_remaining(spec, evaluations, started_at)
        if reason is not None:
            termination_reason = reason

    # ---- EHVI acquisition loop ------------------------------------------
    for iteration_idx in range(algorithm.iteration_budget):
        if termination_reason is not None:
            break

        observed = [r for r in records_by_key.values() if r.status == "complete"]
        if not observed:
            # Fall back to a pure random draw if the LHS phase yielded no
            # feasible point.
            unit = np_rng.uniform(size=len(cont_names))
            genome = _sample_genome_from_unit(unit, spec.search_space, py_rng)
            candidate_key = _candidate_key(spec_h, genome)
            existing = records_by_key.get(candidate_key)
            if existing is None or existing.status == "pending":
                record = _evaluate_and_record(
                    state.next_candidate_index, candidate_key, genome
                )
                state.next_candidate_index += 1
                records_by_key[candidate_key] = record
                evaluations += 1
            _append_history(
                iteration=algorithm.initial_population_size + iteration_idx,
                ehvi_score=0.0,
            )
            reason = _budget_remaining(spec, evaluations, started_at)
            if reason is not None:
                termination_reason = reason
            continue

        # Build training set.
        X_rows: list[np.ndarray] = []
        Y_rows: list[list[float]] = []
        for rec in observed:
            X_rows.append(_featureise_genome(rec.parameters, cont_names, spec.search_space))
            y_row: list[float] = []
            ok = True
            for obj in objectives:
                v = _objective_value(rec, obj.metric)
                if v is None:
                    ok = False
                    break
                y_row.append(_signed_value(v, obj.direction))
            if ok:
                Y_rows.append(y_row)
            else:
                X_rows.pop()
        if not X_rows:
            unit = np_rng.uniform(size=len(cont_names))
            genome = _sample_genome_from_unit(unit, spec.search_space, py_rng)
            candidate_key = _candidate_key(spec_h, genome)
            existing = records_by_key.get(candidate_key)
            if existing is None or existing.status == "pending":
                record = _evaluate_and_record(
                    state.next_candidate_index, candidate_key, genome
                )
                state.next_candidate_index += 1
                records_by_key[candidate_key] = record
                evaluations += 1
            _append_history(
                iteration=algorithm.initial_population_size + iteration_idx,
                ehvi_score=0.0,
            )
            reason = _budget_remaining(spec, evaluations, started_at)
            if reason is not None:
                termination_reason = reason
            continue

        X = np.stack(X_rows, axis=0)
        Y = np.asarray(Y_rows, dtype=float)

        # Fit one GP per objective with a *fresh* deterministic RNG anchored
        # in the spec seed so reseeded runs are byte-identical.
        gps: list[GaussianProcess] = []
        for obj_idx in range(len(objectives)):
            gp_rng = np.random.default_rng(
                algorithm.seed + 1000 * (iteration_idx + 1) + obj_idx
            )
            kernel = kernel_by_name(algorithm.gp_kernel)
            gp = GaussianProcess(kernel, noise_floor=algorithm.gp_noise_floor)
            gp.fit(X, Y[:, obj_idx], rng=gp_rng)
            gps.append(gp)

        # Sample the candidate pool via LHS in unit space.
        pool_unit = _latin_hypercube_unit(
            np_rng, algorithm.candidate_pool_size, len(cont_names)
        )
        pareto = _ehvi_pareto_front(records_by_key.values(), objectives)
        ref_point = _ehvi_reference_point(algorithm, Y, len(objectives))

        best_score = -1.0
        best_genome: dict[str, Any] | None = None
        for cand_i in range(pool_unit.shape[0]):
            unit = pool_unit[cand_i]
            genome = _sample_genome_from_unit(unit, spec.search_space, py_rng)
            x_feat = _featureise_genome(genome, cont_names, spec.search_space).reshape(1, -1)
            mu = np.empty(len(objectives), dtype=float)
            sigma = np.empty(len(objectives), dtype=float)
            for obj_idx, gp in enumerate(gps):
                m, v = gp.predict(x_feat)
                mu[obj_idx] = float(m[0])
                sigma[obj_idx] = math.sqrt(max(float(v[0]), 1.0e-12))
            score = compute_ehvi(mu, sigma, pareto, ref_point)
            # Stable tie-break: prefer earlier draws on equal score.
            if score > best_score:
                best_score = score
                best_genome = genome

        assert best_genome is not None
        candidate_key = _candidate_key(spec_h, best_genome)
        existing = records_by_key.get(candidate_key)
        if existing is None or existing.status == "pending":
            record = _evaluate_and_record(
                state.next_candidate_index, candidate_key, best_genome
            )
            state.next_candidate_index += 1
            records_by_key[candidate_key] = record
            evaluations += 1
        _append_history(
            iteration=algorithm.initial_population_size + iteration_idx,
            ehvi_score=best_score,
        )
        reason = _budget_remaining(spec, evaluations, started_at)
        if reason is not None:
            termination_reason = reason

    if termination_reason is None:
        termination_reason = "completed"

    # ---- Finalise ----------------------------------------------------------
    ordered = sorted(records_by_key.values(), key=lambda r: r.candidate_index)
    final_frontier_keys = _final_frontier_keys(
        ordered, objectives, exploratory=spec.objectives_explicit_exploratory
    )
    pending_count = sum(1 for r in ordered if r.status == "pending")
    completed_count = sum(1 for r in ordered if r.status == "complete")
    failed_count = sum(1 for r in ordered if r.status == "failed")
    constraint_failed_count = sum(
        1 for r in ordered if r.status == "constraint_failed"
    )

    metadata = SearchMetadata(
        algorithm_kind="ehvi",
        seed=algorithm.seed,
        population_size=None,
        generations=None,
        initial_population_size=algorithm.initial_population_size,
        iteration_budget=algorithm.iteration_budget,
        gp_kernel=algorithm.gp_kernel,
        objectives=objectives,
        constraints=list(spec.constraints),
        realized_max_evaluations=spec.budget.max_evaluations,
        realized_wall_clock_seconds=spec.budget.wall_clock_seconds,
        realized_evaluations=evaluations,
        termination_reason=termination_reason,
        history=[],
        ehvi_history=ehvi_history,
    )

    run_record = SearchRunRecord(
        name=spec.name,
        spec_hash=spec_h,
        search_class=search_class,
        search_metadata=metadata,
        candidate_count=len(ordered),
        pending_count=pending_count,
        completed_count=completed_count,
        failed_count=failed_count,
        constraint_failed_count=constraint_failed_count,
        final_frontier_keys=final_frontier_keys,
        candidates=ordered,
    )
    if store is not None:
        store.put_json("search_run_record", run_record, canonical_path=out / "run.json")
    else:
        (out / "run.json").write_text(run_record.model_dump_json(indent=2))
    _write_summary(out / "summary.csv", ordered)
    if store is not None:
        store.put_file("sweep_summary_csv", out / "summary.csv")
    _write_failures(
        out / "failures.jsonl",
        [r for r in ordered if r.status in ("failed", "constraint_failed")],
    )
    if store is not None:
        store.put_file("sweep_failures_jsonl", out / "failures.jsonl")
    _write_state(state, out)
    if store is not None and run_id is not None:
        from kayakgen.services.artifact_store import index_candidates as _index_candidates

        _index_candidates(
            run_id=run_id,
            candidate_rows=[_index_row_for_candidate(rec) for rec in ordered],
            index=store.index,
        )
    return SearchRunResult(
        name=spec.name,
        run_dir=str(out),
        search_class=search_class,
        search_metadata=metadata,
        final_frontier_keys=final_frontier_keys,
        candidate_count=len(ordered),
        completed_count=completed_count,
        failed_count=failed_count,
        constraint_failed_count=constraint_failed_count,
        pending_count=pending_count,
    )


def _final_frontier_keys(
    records: Iterable[CandidateRecord],
    objectives: list[ObjectiveSpec],
    *,
    exploratory: bool,
) -> list[str]:
    eligible = [r for r in records if r.status == "complete"]
    if not eligible:
        return []
    # Build minimize-direction tuples.
    tuples: list[tuple[float, ...]] = []
    for rec in eligible:
        tuples.append(_signed_objective(rec, objectives))
    frontier: list[str] = []
    for i, point in enumerate(tuples):
        dominated = False
        for j, other in enumerate(tuples):
            if i == j:
                continue
            better_in_any = False
            worse_in_any = False
            for pv, ov in zip(point, other):
                if math.isinf(pv) or math.isinf(ov):
                    worse_in_any = True
                    break
                if ov < pv:
                    better_in_any = True
                elif ov > pv:
                    worse_in_any = True
            if better_in_any and not worse_in_any:
                dominated = True
                break
        if not dominated:
            frontier.append(eligible[i].candidate_key)
    if exploratory:
        # Exploratory frontier rows are surfaced but flagged elsewhere as
        # frontier-ineligible under the conservative view.
        return frontier
    return frontier
