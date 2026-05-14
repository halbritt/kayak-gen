---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-001
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_461cc5eba71248ad993415314fedaeec
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_sweep_next_delta_claude
lease: lease_144927398dd04cee8366f0cf3af35785
date: 2026-05-14

# Panel Vote - Sweep Next Delta (Claude)

## Vote

**Vote: Option A - Schedule `pending` candidate state next.**

## Decision Sentence

The next workflow after 0051 will close the smallest remaining RFC 0009 /
search lifecycle delta by adding a `pending` value to `CandidateStatus`,
adding `pending_count` to `SweepRunRecord`, writing planned candidate
records before evaluation begins, defining `resume` policy over `pending`
records explicitly, and keeping `pending` candidates visible in
`summary.csv`, `run.json`, and comparison reports as frontier-ineligible.
Sweep-side STL artifact emission, optimizer/search loops, parallel worker
queues, calibrated resistance promotion, real OpenFOAM `succeeded`,
high-angle stability product surfacing, public browser hosting, and any
new objective admissibility remain explicitly out of scope.

## Evidence And Citations

### Research packet alignment

The packet
(`striatum/0052-successor-decision-research/research/sweep_next_delta/RESEARCH.md`)
recommends Option A on the basis that it (a) closes a recorded RFC 0009
delta without new physics, geometry artifacts, optimizer behavior, or
user-facing claims; (b) strengthens provenance and crash/interruption
auditability for all later sweep, STL, queued CFD, and active search work;
(c) aligns with common optimizer/job-state lifecycle practice; and
(d) has modest blast radius because `compare` already treats non-`complete`
candidates as visible-but-frontier-ineligible. I concur on each ground.

### Independent verification of current code state

I confirmed the packet's claims against `kayakgen/search/sweep.py` directly:

- `kayakgen/search/sweep.py:25` defines
  `CandidateStatus = Literal["complete", "failed", "skipped"]` — `pending`
  is genuinely missing.
- `kayakgen/search/sweep.py:125-137` defines `SweepRunRecord` with
  `completed_count`, `failed_count`, and `skipped_count` only; there is
  no `pending_count` slot today.
- `kayakgen/search/sweep.py:69` exposes `EvaluatorOptions.stl: bool = False`
  but the flag is never consumed by `_evaluate_candidate` or `run_sweep`
  (no other `evaluators.stl` / `options.stl` / `stl_path` / `write_stl`
  reference exists in the file). This matches the packet's "reserved but
  unimplemented" framing for Option B.
- `kayakgen/search/sweep.py:176-180` shows that `resume` currently only
  skips records whose prior `status == "complete"`. Failed, skipped, and
  any future `pending` records will be re-attempted on resume unless the
  next workflow defines policy. This is exactly the gap Option A must
  close as part of its acceptance criteria.

### Independent verification of external sources

The packet's external citations are consistent with my background knowledge:
Optuna's `TrialState` includes a `WAITING` state distinct from `RUNNING`,
`COMPLETE`, `PRUNED`, and `FAIL`; W3C PROV defines provenance over entities,
activities, and people supporting reproducibility and trustworthiness; the
Library of Congress STL format note describes STL as a triangular surface
mesh with no standard color/texture and common defect/repair concerns; and
SciPy's `differential_evolution` is documented as stochastic, requiring
finite bounds, and supporting constraints, which is exactly the
prerequisite list Option D would need before scheduling.

### Workflow context alignment

- Decision D010 (workflow 0050 final results,
  `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md:162-176`)
  accepted sweep/search admissibility Option A and explicitly stated that
  "search/optimizer work remains blocked until RFC 0009 status is reconciled
  and objective metadata records metric label, unit, direction, source
  evaluator, availability rule, claim-state requirement, accepted-use
  requirement, and role." Workflow 0051 delivered the objective registry
  slice and reconciled RFC 0009 status as a partial-landed sweep-run-record
  slice
  (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`).
  The candidate-lifecycle pillar is therefore the next gate, not active
  search.
- The workflow 0050 implementation burn-down queue item 11
  (`DECISION_RESULTS.md:267-269`) explicitly names "the `pending` and `stl`
  deltas" as the next sweep/search decision pair — Option A and Option B
  in this research packet — and keeps optimizer work blocked. The panel
  question is precisely which of those two to schedule first.

## Why Rejected Alternatives Lose

### Option B (sweep-side STL artifacts) — close second, schedule next

Option B has real user value (per-candidate hull/deck STLs for outside-JSON
inspection), and `EvaluatorOptions.stl` is already a reserved flag, so the
plumbing is shallow. It loses to Option A on three concrete grounds:

1. **Interruption sensitivity.** Sweep-side STL emission is the workflow
   where partial-run state matters most, because binary outputs can land
   for some candidates and not others. Without a `pending` lifecycle,
   `resume` cannot distinguish "STL planned but not yet emitted" from
   "STL emission attempted and failed" from "STL never asked for." Doing
   Option B first will require re-doing its provenance once Option A
   lands.
2. **Sidecar metadata not yet specified.** The Library of Congress STL
   format note is clear that STL is geometry-only with no color, texture,
   or self-describing metadata, and is prone to defect/repair issues.
   A sweep-side STL workflow needs a manifest/checksum/source-hull-hash/
   part-label sidecar and explicit "open inspection surface, not
   `cfd_ready`" wording before it can be emitted at scale. Specifying that
   sidecar belongs in Option B's own workflow, not bolted onto a `pending`
   workflow.
3. **Disk-budget surprises.** Large sweep matrices with `evaluators.stl:
   true` could produce hundreds or thousands of binary files. That risk
   needs explicit warnings, default-false plus opt-in, and likely a
   candidate-count threshold. Option A has none of those operational
   complications.

After Option A lands, Option B is the recommended successor with the
implementation gates listed in the packet (explicit `evaluators.stl: true`,
hull/deck as open inspection surfaces, manifest/checksum/unit/profile
metadata, disk-budget warnings, no `cfd_ready` confusion).

### Option C (metadata/claim hardening) — fold a small slice into A, not a standalone workflow

Workflow 0051 already delivered the highest-risk objective metadata and
claim-gate slice: `kayakgen/search/objectives.py`, conservative defaults
(`GM0_m`, `displacement_error_kg`, `mesh_problem_count`), explicit
exploratory metadata for `Rt_N_last`, and a claim-gated reserved
`design_fitness` metric. A separate metadata-hardening workflow without a
concrete lifecycle or artifact delta risks becoming abstract schema churn
and would not by itself close any RFC 0009 surface area. The narrow piece
of Option C that is still useful — namely, snapshotting objective metadata
into the `run.json` and confirming `pending` records also snapshot the
objective set in force at planning time — should be folded into Option A's
acceptance criteria, not run as a standalone workflow.

### Option D (optimizer/search) — gate-blocked

Option D is the wrong choice for the next slot for the same reasons D010
recorded: candidate lifecycle (no `pending`), sampler/seed provenance,
budget semantics, design-space constraint policy, and interruption/resume
behavior are not yet project contracts. Optuna's `WAITING`/`RUNNING`
distinction and SciPy's `differential_evolution` requirements both imply
that those contracts must exist before an active loop begins. Even with
0051's objective registry, an optimizer scheduled before `pending` would
either invent a candidate-state model inline (locking in an
implementation-internal lifecycle as the project contract) or magnify any
unresolved metric ambiguity into "best design" pressure. Option D remains
correctly blocked.

## Implementation Gates To Carry Into The Next Workflow

If Option A is accepted by the panel integration, the successor workflow
must enforce, at minimum:

1. **Lifecycle correctness.** `pending` records must not carry `hull_hash`,
   `artifacts`, evaluator-result `summary` fields, or `evaluator_versions`
   beyond `sweep_schema` until validation/evaluation has actually
   produced them. The `CandidateRecord.model_validator` should enforce
   this for `status == "pending"`.
2. **JSON contract is additive.** `SweepRunRecord.pending_count` is a new
   field. Existing `run.json` files written before the change must still
   parse (either via `model_validator` defaulting `pending_count` to 0,
   or via an explicit schema_version bump with a documented compatibility
   path; either way, an additive-compatibility test is required).
3. **`resume` policy is explicit and tested.** Recommended policy:
   `complete` records are skipped as today; `pending` records are
   re-evaluated (treated as planned-but-unrun); `failed` records remain
   visible and are only re-attempted under an explicit `--rerun-failed`
   or equivalent flag. Tests must cover all three branches deterministically.
4. **Reports preserve pending rows.** `summary.csv`, `run.json`, and
   comparison/`compare` reports must show `pending` rows without counting
   them as `completed_count` and must continue to treat them as
   frontier-ineligible. A `compare` regression test should pin this.
5. **Optimizer/search remains blocked.** The next workflow's RUNBOOK must
   explicitly forbid optimizer loops, parallel worker queues, sampler
   integration, and search-spec authoring. Those wait for a later
   workflow once `pending` plus search-spec/objective-metadata snapshots
   are in place.
6. **Sweep-side STL emission remains out of scope.** The reserved
   `evaluators.stl` flag must stay unimplemented except where strictly
   needed as a fixture/test to prove `pending` lifecycle compatibility
   with a planned STL artifact path. If used in fixtures, the artifact
   must remain `fixture_only` and not be surfaced as `cfd_ready`.

## No-Claims Language That Must Remain In Force

The successor workflow lands a lifecycle field, not new physics, geometry,
or solver capability. All no-claims wording from workflows 0050 and 0051
must remain literally unchanged:

- Resistance output remains `uncalibrated_comparative`. No calibrated
  wording, no calibrated comparative-ranking claim, no `design_fitness`
  score, no calibrated prediction default. `SourceUse` still excludes
  `rejected`. `Rt_N_last` remains `explicit_exploratory` with
  `claim_state_required="calibrated_model"` and
  `accepted_use_required="final_prediction"`.
- Real OpenFOAM `succeeded` remains blocked. Parser-readable fake output
  continues to return `error_kind="solver_success_blocked"`. Readiness
  gating (`required_mesh_profile="watertight_solid_resistance_v1"`,
  readiness `cfd_ready`) stays enforced. Ordinary generated packages stay
  below `cfd_ready`.
- Generated-body high-angle GZ remains
  `result_semantics="unvalidated_hydrostatic_comparison"` with
  `summary_semantics="grid_bounded"` and the fixed-trim/sealed-deck
  warnings. No safety, seaworthiness, capsize, or final design-fitness
  claim. No CLI/sweep/comparison/desktop/web surfacing of generated-body
  GZ values.
- No production hosting, hosted CFD, hosted worker queue, account, quota,
  or SLA work. No native desktop rewrite.
- `pending` candidates carry no fitness/eligibility implication beyond
  "planned, not yet completed." A `pending` record cannot be cited as
  partial success, partial failure, or design fitness.

## Risks And Unknowns Carried Forward

- **Sequential-runner trivial case.** Today's runner is sequential, so
  `pending` records would normally appear only across interrupted runs.
  The successor workflow must make sure that the `pending` lifecycle is
  exercised in a way that proves auditability under interruption, not
  just enum expansion. Concrete suggestion: a test that simulates
  interruption (writes pending records then raises) and a resume that
  confirms the same `pending` records are re-evaluated to `complete` or
  `failed`.
- **`pending_count` semantics in mid-run reports.** If `pending` records
  are written before evaluation begins, an interrupted run leaves a
  durable `pending_count > 0` in `run.json`. Downstream consumers
  (comparison reports, web read models, CLI status) must treat that as
  "interrupted/in-progress sweep," not as a fitness or success metric.
- **Compatibility with existing run records.** Existing `run.json` files
  on disk in the project and in test fixtures must continue to parse.
  Recommended: default `pending_count` to `0` rather than requiring it,
  and pin a test that round-trips an older `SweepRunRecord` payload.
- **Objective-metadata snapshot scope creep.** Folding a small piece of
  Option C (objective metadata snapshot in `run.json`) into Option A is
  useful, but the next workflow must guard against expanding Option C
  into broad schema redesign. Any objective-metadata snapshot must be
  derived from the existing `kayakgen/search/objectives.py` registry,
  not new admissibility rules.
- **STL workflow is the recommended successor, not a current scope item.**
  The next-after-`pending` workflow should be Option B (sweep-side STL
  with sidecar/manifest/checksum/disk-budget gates), and active search
  should remain blocked beyond that until a separate search-spec workflow
  defines algorithm, version, random seed, budget, bounds, constraints,
  forbidden objective handling, and exploratory-only result framing.

## Confidence

**High.**

Rationale: Option A is the smallest change that closes a recorded RFC 0009
gap; the current code (`kayakgen/search/sweep.py`) confirms the precise
shape of the gap and that the change is additive; D010 plus the workflow
0050 burn-down queue explicitly position `pending` as one of the two named
next deltas; the external evidence (Optuna `WAITING`, W3C PROV, SciPy
`differential_evolution` prerequisites, STL format notes) lines up with
the packet's framing; and the no-claims surface area is unaffected because
no new physics, artifact, solver, calibration, or admissibility is added.
The only meaningful judgment call is the A-vs-B sequencing, and Option A's
"lifecycle before binary artifacts" ordering is the lower-rework path.
