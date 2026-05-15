"""Active-search runner (RFC 0044 v1).

Orchestrates a vendored NSGA-II run, evaluates each proposed candidate via
:func:`kayakgen.search.sweep._evaluate_candidate`, applies hard-rejection
constraints, and writes:

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
import time
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kayakgen.model.hull import Hull
from kayakgen.search.active.constraints import ConstraintViolation, evaluate_constraints
from kayakgen.search.active.nsga2 import (
    Generation,
    Individual,
    initialize_population,
    nsga2_iterations,
    select_next_population,
)
from kayakgen.search.active.spec import (
    GenerationHistoryEntry,
    ObjectiveSpec,
    SearchClass,
    SearchMetadata,
    SearchSpec,
    TerminationReason,
    load_search_spec,
)
from kayakgen.search.objectives import DEFAULT_OBJECTIVE_METRICS, OBJECTIVE_METADATA
from kayakgen.search.pareto import (
    Objective,
    SearchObjectiveRefusedError,
    ensure_objectives_claim_admissible_for_search,
    ensure_objectives_not_high_angle_gz,
)
from kayakgen.search.sweep import (
    CandidateRecord,
    EvaluatorOptions,
    SweepSpec,
    _evaluate_candidate,
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


def _write_record(record: CandidateRecord, out: Path) -> None:
    path = _record_path(out, record.candidate_key)
    path.parent.mkdir(parents=True, exist_ok=True)
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

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates").mkdir(parents=True, exist_ok=True)
    (out / "spec.json").write_text(spec.model_dump_json(indent=2))

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
            _write_record(record, out)
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
            _write_record(record, out)
            return record

        violations = evaluate_constraints(record.summary, spec.constraints)
        if violations:
            record = _build_constraint_failed_record(base=record, violations=violations)
        _write_record(record, out)
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
                _write_record(record, out)
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
    (out / "run.json").write_text(run_record.model_dump_json(indent=2))
    _write_summary(out / "summary.csv", ordered)
    _write_failures(
        out / "failures.jsonl",
        [r for r in ordered if r.status in ("failed", "constraint_failed")],
    )
    _write_state(state, out)

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
