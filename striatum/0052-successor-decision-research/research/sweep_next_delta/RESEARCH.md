---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_04183aa859d540a2badb33ca29b98468
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_sweep_next_delta
lease: lease_a582a2c7636f47d79bd0050f9ec2d375
date: 2026-05-14

# Research - Sweep Next Delta

## Decision Question

Which remaining RFC 0009/search delta should be scheduled next after workflow
0051: `pending` candidate state, sweep-side STL artifacts, optimizer/search, or
additional metadata/claim hardening?

## Local Project Constraints

- Workflow 0052 is design-only. It must not implement runtime behavior, tests,
  solver execution, calibration, watertight-readiness promotion, hosted
  operation, desktop rewrite, or optimizer/search behavior.
- RFC 0009 is now indexed and documented as a partial landed sweep-run-record
  slice. Current `kayakgen sweep` writes deterministic run/spec/summary/failure
  files and per-candidate hull/evaluation/record artifacts, but the planned
  `pending` status and sweep-side `stl` artifact path remain explicit deltas.
- Workflow 0051 already landed an objective metadata registry and comparison
  claim gates. The current code has `kayakgen/search/objectives.py`,
  conservative defaults of `GM0_m`, `displacement_error_kg`, and
  `mesh_problem_count`, explicit exploratory metadata for `Rt_N_last`, and a
  claim-gated reserved `design_fitness` metric.
- Current `CandidateStatus` is only `complete`, `failed`, and `skipped`.
  `compare` keeps non-`complete` candidates visible but frontier-ineligible,
  which is already the right shape for adding `pending`.
- Existing no-claims rules still govern any next delta: raw resistance remains
  `uncalibrated_comparative`, raw CFD is unvalidated or unavailable/failed,
  open hull/deck STLs are inspection surfaces, high-angle real kayak `GZ` is
  not product-surfaced, advisory validity is not design fitness, and no metric
  is a final design-fitness score.

## External Evidence

All external sources were accessed on 2026-05-14.

- Optuna's current trial-state model includes `WAITING`, `RUNNING`,
  `COMPLETE`, `PRUNED`, and `FAIL`; `WAITING` is defined as a trial that is
  waiting and unfinished, and unfinished states include `RUNNING` or `WAITING`.
  This supports an explicit `pending`/waiting state for queued or not-yet-run
  candidates rather than overloading complete/failed/skipped.
  Source: Optuna TrialState documentation,
  https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.TrialState.html
- Optuna's multi-objective guide requires specifying optimization direction
  for each objective; its example uses one minimized metric and one maximized
  metric. This supports keeping metric direction machine-readable before any
  active optimizer consumes comparison data.
  Source: Optuna multi-objective documentation,
  https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/002_multi_objective.html
- pymoo's problem definition docs say optimization problems carry metadata such
  as number of objectives, constraints, and lower/upper design-space bounds.
  This supports treating objective and design-space metadata as a prerequisite
  for optimizer/search rather than an optional UI label.
  Source: pymoo problem definition documentation,
  https://pymoo.org/problems/definition.html
- SciPy's `differential_evolution` is stochastic, minimizes a callable
  objective, requires finite variable bounds, supports constraints, can require
  many function evaluations, and has different behavior for parallel/vectorized
  evaluation. This argues against scheduling active search before candidate
  lifecycle, reproducibility, bounds, constraints, and budget semantics are
  explicit.
  Source: SciPy differential evolution documentation,
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
- W3C PROV describes provenance as information about entities, activities, and
  people involved in producing data or things, supporting assessment of quality,
  reliability, and trustworthiness; its recommendations include reproducibility,
  versioning, procedures, and derivation. This supports explicit run/candidate
  state transitions and artifact provenance before richer search automation.
  Source: W3C PROV Overview, https://www.w3.org/TR/prov-overview/
- GO FAIR's rich-metadata guidance includes context, quality/condition,
  protocol links, units, and parameter-space information. This supports
  artifact sidecars and objective metadata snapshots, especially if sweep-side
  STLs are added.
  Source: GO FAIR F2 principle,
  https://www.go-fair.org/fair-principles/f2-data-described-rich-metadata/
- The Library of Congress STL format note describes STL as a triangular surface
  mesh format and highlights limited functionality, including no standard color
  or texture support and common defect/repair concerns. This supports treating
  sweep-side STLs as inspection artifacts with explicit sidecar metadata and
  checksums, not as self-describing solver-ready evidence.
  Source: Library of Congress STL format family,
  https://www.loc.gov/preservation/digital/formats/fdd/fdd000504.shtml

## Viable Options

### Option A - Schedule `pending` Record State Next

Conservative default.

Implement the smallest remaining run-record lifecycle delta: add `pending` to
`CandidateStatus`, add pending counts to `SweepRunRecord`, write planned
candidate records before or as evaluation begins, and keep pending candidates
visible but frontier-ineligible in comparison reports.

Why this fits now:

- It closes a recorded RFC 0009 delta without adding new physics, geometry
  artifacts, optimizer behavior, or user-facing claims.
- It strengthens provenance and crash/interruption auditability for all later
  work: sweep-side STL generation, parallel execution, queued CFD, and active
  optimizer/search can all reuse the same lifecycle.
- It aligns with common optimizer/job-state practice where waiting/running and
  finished/failed states are distinct.
- Current comparison behavior already handles non-complete candidates as
  ineligible, so the blast radius should be modest.

Minimum gates:

- `pending` records must not carry `hull_hash` or evaluation artifacts before
  validation/evaluation has actually produced them.
- `resume` must define how existing `pending` records behave. Recommended:
  re-evaluate or requeue pending candidates, skip only prior `complete`
  records, and keep `failed` visible unless an explicit rerun flag exists.
- `summary.csv`, `run.json`, and comparison reports must preserve pending rows
  without counting them as completed or frontier-eligible.
- Tests should cover deterministic pending record creation, transition to
  `complete`/`failed`, resume over prior pending records, and comparison
  warnings for `pending`.
- No optimizer loop, no parallel worker queue, and no new artifact type should
  be bundled into this workflow.

### Option B - Schedule Sweep-Side STL Artifacts Next

Implement the reserved `evaluators.stl` flag so a sweep can opt in to
per-candidate hull/deck STL emission and artifact paths.

Why this is viable:

- It closes a user-visible RFC 0009 delta and makes sweep candidates easier to
  inspect outside JSON.
- The project already has `kayakgen generate` and STL writer behavior that can
  be reused.

Why it is not the best next default:

- It creates binary artifact volume and possible disk-budget surprises across
  large sweeps.
- STL is geometry-only and not self-describing enough for this project's claim
  boundaries. It needs sidecar metadata, checksums, source hull hash,
  part/profile labels, and explicit "open inspection surface, not
  `cfd_ready`" wording.
- It benefits from the `pending` lifecycle first, because large binary outputs
  are exactly where interruption and partial-run state matter.

Minimum gates if selected:

- Require explicit `evaluators.stl: true`; keep default false.
- Emit hull and deck only as open inspection surfaces, with artifact keys that
  cannot be confused with mesh-package or volume-mesh readiness evidence.
- Add manifest/checksum/unit/profile metadata or embed equivalent fields in
  candidate records before claiming artifact reproducibility.
- Add disk-budget or candidate-count warnings for large STL-enabled sweeps.

### Option C - Schedule Additional Metadata/Claim Hardening

Add a narrow metadata-hardening workflow instead of a new runtime feature:
snapshot objective metadata into comparison/run reports, define a
search-readiness report, harden unsupported/claim-gated objective roles, and
add artifact manifest conventions for future STLs.

Why this is viable:

- External optimizer frameworks expect objective directions, constraints, and
  bounds to be explicit; data/provenance practice favors rich metadata and
  derivation records.
- It keeps optimizer/search blocked while improving the machine-checkable gate.
- It may be necessary if reviewers think workflow 0051's objective registry is
  too comparison-local for active search.

Why it is not the best standalone next default:

- Workflow 0051 already delivered the highest-risk objective metadata and claim
  gate slice.
- More metadata without a concrete lifecycle or artifact delta risks becoming
  abstract schema churn.

Best use:

- Fold a small amount of metadata hardening into Option A or Option B acceptance
  criteria. Do not let it grow into a broad redesign unless the panel finds a
  specific missing machine-enforced gate.

### Option D - Start Optimizer/Search

Begin an active search loop, such as random/Latin-hypercube sampling,
ask/tell-style optimizer integration, or multi-objective evolutionary search.

Why this is tempting:

- The sweep runner, comparison reports, and objective registry now exist.
- The design problem is naturally multi-objective, and external tools can
  optimize bounded multi-objective problems once objectives and constraints are
  defined.

Why it should not be scheduled next:

- Active optimizers magnify any ambiguous metric. Even with workflow 0051's
  registry, the project still lacks a candidate lifecycle with `pending`,
  search spec/versioning, random seed and sampler provenance, evaluation budget
  semantics, constraint/filter policy, and interruption/resume behavior.
- SciPy and Optuna evidence both imply explicit objective direction, bounds,
  and repeatability/iteration state. Those must be project contracts, not
  assumptions inside the first optimizer implementation.
- It risks reopening forbidden claims by accidentally treating raw resistance,
  advisory validity, or unavailable stability as fitness pressure.

Minimum gates before this becomes viable:

- `pending`/unfinished candidate lifecycle exists and is tested.
- Search spec records algorithm, version, random seed, budget, bounds,
  constraints/filters, selected objective metadata, and forbidden objective
  handling.
- The first optimizer workflow is explicitly exploratory and cannot emit a
  "best design" or final design-fitness score.

## Risks And Unknowns

- `pending` semantics can become misleading if the sequential runner writes
  pending records but never exposes interrupted runs. The implementation should
  make pending useful for auditability, not just expand an enum.
- `resume` semantics need care: skipping only `complete` records is current
  behavior; pending and failed records need explicit requeue/rerun policy.
- Adding `pending_count` to `SweepRunRecord` is a JSON contract change. It
  should be additive and compatibility-tested against existing run records.
- Sweep-side STLs can produce large binary directories. Any STL workflow needs
  opt-in behavior, artifact naming stability, sidecar metadata, checksums, and
  no-claim copy.
- Objective metadata role names in current code are conservative but slightly
  narrower than the roadmap vocabulary. A future search workflow may need a
  compatibility mapping, not a breaking rename.
- Active search will need design-space constraints beyond objective metadata:
  parameter bounds, dependent constraints such as `beam_wl_m <= beam_oa_m`,
  invalid-candidate policy, and deterministic sampler provenance.

## Recommendation

Schedule Option A, `pending` record state, as the next sweep/search delta.

It is the smallest recorded RFC 0009 gap that improves reproducibility and
prepares for both artifact-heavy sweeps and future optimizer/search. It also
preserves all no-claims boundaries because it changes candidate lifecycle
semantics rather than physics, artifacts, solver readiness, or objective
admissibility. The next workflow should explicitly forbid optimizer behavior
and sweep-side STL generation except as tests or fixtures needed to prove
pending-state compatibility.

After `pending` lands, the next choice should be between sweep-side STL
artifacts with manifest/checksum/no-claim gates and a narrowly scoped
search-spec design workflow. Active optimizer/search should remain blocked
until `pending` plus search-spec metadata are in place.
