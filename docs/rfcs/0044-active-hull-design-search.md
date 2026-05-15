# RFC 0044: Active Hull-Design Search

Status: landed v1 NSGA-II + kayakgen search CLI (additive opt-in; defaults unchanged)
Date: 2026-05-16
Context: successor to RFC 0009 (sweep records, `pending` lifecycle, sweep-side
STL and high-angle GZ artifacts) and RFC 0013 (Pareto frontier and comparison
UI). Decisions D010 (sweep/comparison admissibility) and D016 (`pending`
lifecycle before active search) gate this RFC. The objective-metadata
registry in `kayakgen/search/objectives.py` is the load-bearing
infrastructure that this RFC consumes; the
`HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN` gate in `kayakgen/search/pareto.py` is the
display-only boundary that any active-search algorithm must respect.

Disposition of predecessors: RFC 0044 does not supersede RFC 0009 or RFC 0013;
it builds on them. The current `kayakgen sweep` exhaustive-grid behavior
remains the conservative default. Active search is an additive opt-in path.

## Problem

`kayakgen sweep` today walks an explicit JSON-defined parameter grid. That
is reproducible, deterministic, and well-suited to small parameter spaces and
the no-claims posture the project keeps. It is also the wrong tool for two
real questions a designer asks:

- *Single-objective with constraints*: "Minimize drag at `U = 3.5 m/s` subject
  to `GM0_m ≥ 0.05 m` and `displacement_kg ≥ 90 kg`."
- *Multi-objective Pareto frontier*: "What is the achievable trade-off
  between drag, GM0, and mesh quality across the touring sea kayak class
  envelope?"

A grid that resolves the design space densely enough to answer either
question becomes exponentially expensive in dimension count. Even the
conservative seven-parameter sea-kayak envelope produces millions of cells at
useful resolution. Worse, the grid is uninformed: it spends the same budget
in flat regions of the objective landscape as in regions near the Pareto
front.

The current sweep also has no notion of "spend a budget; return the best
results when you stop." Resume support exists for completed cells, but the
sweep can only end early by user interruption — there is no algorithmic stop
condition tied to convergence or budget exhaustion.

Active search closes both gaps. It chooses where to evaluate next based on
prior evaluations, respects an explicit evaluation budget, and converges
toward useful regions of the design space without the operator hand-picking
the resolution.

This RFC does not implement active search. It scopes what an acceptable
implementation must do, and what it must not claim.

## Goals

- Define an opt-in `kayakgen search` CLI surface that is additive to
  `kayakgen sweep` and `kayakgen compare`, not a replacement.
- Settle algorithm admissibility: which class of algorithms is allowed in
  the v1 surface, what their seeding requirements are, and how their
  termination criteria interact with the existing run-record schema.
- Preserve the D010 admissibility rules: raw resistance, raw CFD, advisory
  validity, pending candidates, and high-angle GZ metrics may not become
  default design-fitness signals. The optimizer must surface its
  objective-claim provenance for every recorded run.
- Reuse the RFC 0009 candidate-record schema (with the landed `pending`
  lifecycle and the existing `stl_artifacts` / `high_angle_gz_artifact`
  fields) so an active-search run is a sweep run with extra header metadata.
- Keep the default `kayakgen sweep` and `kayakgen compare` behavior
  byte-identical to today's behavior.

## Non-Goals

- No runtime implementation in this RFC.
- No new objective metric, no new claim state, no new readiness gate.
- No calibrated final-prediction signal, no design-fitness scalar, no
  safety / seaworthiness / capsize claim.
- No promotion of high-angle GZ summary metrics
  (`max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`) out of
  the display-only boundary. `ensure_objectives_not_high_angle_gz` continues
  to refuse them.
- No promotion of `raw_unvalidated` CFD drag, `uncalibrated_comparative`
  resistance, or advisory validity flags into the default objective set.
- No automatic OpenFOAM dispatch from the search runner. If the user wires
  the OpenFOAM `succeeded` path (D012, opt-in env-gated) as an evaluator,
  every drag value still carries `claim_state="raw_unvalidated"`.
- No hosted-execution, parallel worker queue, or distributed-runner work.
- No surrogate model that emits values for hulls it has not been evaluated
  on. Surrogate-informed candidate *selection* is in scope; surrogate-emitted
  numeric results are out.
- No machine-learning training pipeline, no model weight artifact storage,
  no cross-run model reuse without explicit acceptance evidence.
- No new web or desktop UI surfaces. Active-search records may surface
  through the existing comparison report's display-only path.

## Dependencies

- RFC 0009 sweep records and the landed `pending` candidate lifecycle.
- RFC 0013 Pareto frontier comparison rules.
- Decision D010 (conservative sweep admissibility) and D016 (`pending` before
  active search). Both must remain authoritative.
- `kayakgen/search/objectives.py:OBJECTIVE_METADATA` — every objective the
  search uses must have a registry entry, and the registry's claim-state
  field is the truth for objective admissibility.
- `kayakgen/search/pareto.py:ensure_objectives_not_high_angle_gz` — the
  search runner must call this gate on every resolved objective set before
  the first evaluation.

## Proposal

### Surface

A new CLI subcommand `kayakgen search` takes a spec JSON:

```json
{
  "schema_version": "1",
  "name": "touring-sea-kayak-pareto",
  "base_hull": {"length_m": 5.2, "beam_oa_m": 0.55, "draft_m": 0.12},
  "search_space": {
    "length_m":    {"kind": "uniform", "min": 4.4, "max": 5.6},
    "beam_wl_m":   {"kind": "uniform", "min": 0.46, "max": 0.58},
    "Cp":          {"kind": "uniform", "min": 0.50, "max": 0.62}
  },
  "algorithm": {
    "kind": "nsga2",
    "population_size": 24,
    "generations": 8,
    "seed": 1234
  },
  "objectives": [
    {"metric": "GM0_m", "direction": "max"},
    {"metric": "displacement_error_kg", "direction": "min"},
    {"metric": "mesh_problem_count", "direction": "min"}
  ],
  "evaluators": {
    "hydrostatics": true,
    "mesh_diagnostics": true,
    "resistance": false,
    "stability": true,
    "stl": false,
    "high_angle_gz": false
  },
  "constraints": [
    {"metric": "displacement_kg", "min": 85.0},
    {"metric": "L_over_Bwl",      "min": 7.5}
  ],
  "budget": {"max_evaluations": 192, "wall_clock_seconds": 600},
  "limits": {"max_pending": 8}
}
```

The runner writes a single `runs/<name>/` directory with the same shape RFC
0009 already defines: `spec.json`, `run.json`, `summary.csv`,
`failures.jsonl`, `candidates/<key>/record.json`, optional `*.stl` and
`high_angle_gz.json` per the existing evaluator flags.

The difference is in `run.json`'s header. Active-search runs add a
`search_metadata` block recording: algorithm kind, seed, population size,
generation count, objective metadata snapshot, the resolved constraint set,
the realized evaluation budget, the termination reason, and a per-generation
trail of objective summaries (best/median/worst on each objective, frontier
size, frontier-stability indicator).

### v1 algorithm admissibility

Exactly one algorithm family is admitted for v1: **NSGA-II** (or equivalent
explicit dominance-rank + crowding-distance multi-objective evolutionary
algorithm). v1 is multi-objective only. Single-objective use is expressed as
a single-objective NSGA-II run with one objective; this preserves the
frontier-eligibility semantics and avoids a parallel single-objective
pipeline.

Acceptable v1 implementations:
- vendored algorithm in `kayakgen/search/active/nsga2.py` with no external
  optimization-library dependency; OR
- adapter wrapping a single permitted external library (pinned version) so
  long as the library is pure-Python and adds no provider-specific telemetry,
  hidden caching, or non-determinism.

Determinism is required: a seeded run must produce identical evaluations and
identical frontiers byte-for-byte when re-executed against the same
evaluator versions. Resume continues from the last completed generation.

Future algorithm families (Bayesian optimization with GP surrogates, EHVI
expected hypervolume improvement, MOEA/D decomposition) require a successor
RFC that records the same admissibility rules. They are explicitly out of
v1.

### Objective-claim gating

Every objective the search uses must:
- exist in `OBJECTIVE_METADATA` with a recorded claim state,
- pass `ensure_objectives_not_high_angle_gz` (RFC 0043 display-only token),
- pass a new `ensure_objectives_claim_admissible_for_search` gate that
  refuses `raw_unvalidated`, `uncalibrated_comparative`, and any
  advisory-only metric unless the spec sets
  `objectives_explicit_exploratory: true` AND the run is marked
  `search_class: exploratory` in `run.json`.

Default objective set when the spec omits the `objectives` block remains
`(GM0_m, displacement_error_kg, mesh_problem_count)`.

A search run that uses `raw_unvalidated` drag from the OpenFOAM `succeeded`
path is admissible only as `search_class: exploratory` with a banner warning
in the report and in stdout. The frontier rows for exploratory runs stay
visible but are tagged `exploratory: true` and remain frontier-ineligible
under the conservative comparison view, mirroring the pending-row treatment.

### Constraints

`constraints[]` is the v1 surface for "must hold" filters. Each entry has a
`metric` (registry-resolved), optional `min`, optional `max`, and an optional
`reason` string. A candidate that fails any constraint is recorded with
`status="constraint_failed"` and is excluded from the frontier; the
`record.json` lists the failing constraints and current values for each. This
is additive to the existing `failed` and `pending` statuses.

NSGA-II penalization for soft constraints is not in scope; constraints are
hard rejections in v1.

### Resume and `pending` interaction

A search run that exits before its budget records every queued-but-unrun
candidate as `pending` with a fully-resolved hull spec and the generation
index that proposed it. Resume replays `pending` rows first, then continues
the algorithm from the last completed generation. The seed contract is
preserved: resume must produce the same evaluations the original run would
have produced.

`pending_count` and the frontier-ineligibility rule for pending rows are
unchanged. The comparison report's `high_angle_gz_columns` boolean is also
unchanged; high-angle GZ artifacts written by the search evaluator are
display-only via the RFC 0043 stage 3 path.

### What lands and what does not

Lands:
- new `kayakgen search` CLI subcommand and runner.
- `kayakgen/search/active/` subpackage with NSGA-II implementation.
- `SearchSpec`, `SearchAlgorithmSpec`, `SearchConstraint`, and
  `SearchMetadata` Pydantic records.
- `ensure_objectives_claim_admissible_for_search` gate in
  `kayakgen/search/pareto.py` (or a new sibling module).
- Frontier-eligibility tagging for exploratory runs.
- Resume support that preserves seed determinism.
- Unit tests for algorithm determinism, constraint enforcement, objective
  admissibility refusal, exploratory-mode tagging, and resume seed
  preservation.

Does not land:
- No new objective metric.
- No new evaluator flag beyond what RFC 0009 already exposes.
- No web or desktop UI changes. The comparison report displays
  active-search results through the existing display-only path.
- No surrogate model or learned cost surface.
- No external service / hosted execution.
- No `raw_unvalidated` -> validated promotion path, regardless of how many
  evaluations the search records.

## Acceptance Criteria

- `kayakgen sweep` JSON output and per-candidate record shape are unchanged
  when the operator does not invoke `kayakgen search`.
- `kayakgen compare` Pareto frontier rules, default objectives, and
  display-only high-angle GZ surface are unchanged.
- A seeded `kayakgen search` run produces byte-identical
  `candidates/<key>/record.json` content across two independent invocations
  with the same evaluator versions and the same spec.
- A search spec that names `max_gz_m` (or any
  `HIGH_ANGLE_GZ_DISPLAY_ONLY_METRICS`) as an objective is rejected at parse
  time with a structured reason that cites
  `HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN`.
- A search spec that names a `raw_unvalidated` or
  `uncalibrated_comparative` metric without
  `objectives_explicit_exploratory: true` is rejected with a structured
  reason that names the offending claim state.
- A run with `objectives_explicit_exploratory: true` records
  `search_class: exploratory` in `run.json` and emits an exploratory banner
  in the stdout summary and the comparison report.
- Resume after partial completion preserves seed determinism: the resumed
  run reaches the same final frontier as a never-interrupted run with the
  same spec.
- Constraint violations produce `constraint_failed` candidate rows
  (frontier-ineligible) and never coexist with `complete` status on the
  same candidate.
- All new test cases pass under both stable and random pytest ordering.

## Open Questions

- Should the v1 surface expose a hypervolume metric for convergence
  diagnostics, or is generation count plus frontier size enough?
- For the vendored NSGA-II, what is the v1 crossover/mutation default
  (SBX + polynomial mutation is the obvious choice but should be confirmed
  against deterministic-reproducibility constraints)?
- Should the runner produce an additional `search/<generation>/frontier.json`
  artifact per generation, or is the run-level history block sufficient?
- Should `constraint_failed` rows feed back into the algorithm as a
  population-level signal, or stay outside the algorithm entirely?
- Should objective metadata include a `search_admissible` boolean directly,
  or is the existing claim-state field the right pivot?

## Implementation Path

1. Land the spec schema (`SearchSpec`, `SearchAlgorithmSpec`,
   `SearchConstraint`, `SearchMetadata`) with strict Pydantic validation and
   no algorithm execution. Round-trip tests only.
2. Add the new claim-admissibility gate
   (`ensure_objectives_claim_admissible_for_search`) and refuse
   `raw_unvalidated` / `uncalibrated_comparative` objectives unless
   `objectives_explicit_exploratory` is set. Pin the refusal token.
3. Implement vendored NSGA-II in `kayakgen/search/active/nsga2.py` with no
   external library dependency. Pin determinism with seeded unit tests.
4. Wire the runner into `kayakgen search` CLI; the runner reuses the RFC
   0009 candidate-record writer.
5. Add resume support with seed-preserving determinism tests.
6. Add constraint enforcement and `constraint_failed` status tests.
7. Add exploratory-mode tagging and banner-copy tests.
8. Update `docs/USER_GUIDE.md` to describe the new subcommand. No web or
   desktop UI changes.

## Domain Modeling

Boundary clarification. Active search adds a new **policy** layer that sits
above the existing sweep aggregate root (RFC 0009) and the comparison
read-model (RFC 0013). It introduces no new aggregate root, no new value
object beyond `SearchSpec` and its helpers, and no new domain event. The
candidate-record contract from RFC 0009 remains the authority; active
search is a different *driver* of the same aggregate.

The new admissibility gate
(`ensure_objectives_claim_admissible_for_search`) is a domain-service-level
predicate that consumes `OBJECTIVE_METADATA` claim-state and the
`HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN` registry. It does not add new claim
states; it interprets existing ones.

The search runner's per-generation history block is an append-only event
log local to one run; it is not a cross-run domain event stream. Cross-run
learning (surrogate reuse, transfer learning, library-level model
artifacts) is explicitly out of v1 and remains a successor-RFC concern.

Cite `DDD.md § "Adding to the model"`: this RFC is a *use-case* over
existing aggregates, not a structural change to them.
