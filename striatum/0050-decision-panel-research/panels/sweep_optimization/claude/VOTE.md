---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-001
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_ea0ed42a425c4954b87902f879b98da5
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_sweep_optimization_claude
lease: lease_999e53a330514c85905c19ca2b767997

# Panel Vote - Sweep, Comparison, And Optimization Admissibility

## Vote

Option A (Conservative Default Whitelist) now, with Option B (Explicit
Objective Registry Before Search) as a hard prerequisite for any future
optimizer/search RFC, and Options C and D adopted as the standing
promotion and scalar-fitness rules.

Confidence: high.

## Decision Sentence For `docs/DECISION_LOG.md`

Adopt the current sweep and comparison admissibility split as the
project's standing policy: default Pareto objectives are limited to
`GM0_m:max`, `displacement_error_kg:min`, and `mesh_problem_count:min`
when present; raw analytical resistance is admissible only as an
explicitly requested `exploratory_frontier` objective with accepted-use
warnings; raw CFD, advisory validity scores, unavailable high-angle
stability, and scalar `design_fitness` are inadmissible; and any future
optimizer/search RFC is blocked behind reconciling RFC 0009 status,
publishing an explicit objective metadata registry, and the
evidence-gated promotion rules listed below.

## Evidence

### Local code, tests, and RFC citations (verified 2026-05-14)

- `kayakgen/search/compare.py:24-28` defines
  `DEFAULT_OBJECTIVE_CANDIDATES = (GM0_m:max, displacement_error_kg:min,
  mesh_problem_count:min)`; `:313-324` filters them to metrics actually
  present on `complete` candidates. The current default whitelist is
  exactly the one this vote proposes to ratify.
- `kayakgen/search/compare.py:119-128` flips `report_kind` to
  `exploratory_frontier` whenever a selected objective is claim-gated;
  `:175-178` adds explicit warnings for resistance and final-design-
  fitness objectives. The "exploratory unless claim-gate passes"
  behavior is already wired and tested.
- `kayakgen/search/compare.py:327-349` promotes any claim-gated objective
  to `accepted_use_required` and warns when accepted-use provenance is
  missing. Optimization code that ignored these gates would silently
  re-derive admissibility, which Option B prevents.
- `kayakgen/search/pareto.py:64-93` and `:116-154` enforce that missing
  metrics, or claim-gated metrics without accepted-use provenance, make
  pairs non-dominating rather than silently comparable. This is the
  load-bearing guarantee that lets us admit raw resistance as
  exploratory without it implicitly dominating other candidates.
- `kayakgen/eval/claims.py:195-227` defines
  `claim_allows_calibrated_prediction` and
  `claim_allows_final_design_fitness`. Both require a calibrated model
  state, accepted-use tag, calibration fixture IDs, model version,
  passing fit status, fit metrics, and a validity envelope; the
  final-design-fitness gate additionally requires the
  `validated_design_fitness` state that no current output satisfies.
  These are the gates Option C references for future promotion.
- `kayakgen/eval/resistance.py` confirms current raw resistance is the
  "fast filter tier" and absolute values "should be treated as fit for
  sweep/Pareto filtering, not for final performance prediction"
  (`:19-29`). The downstream metadata path keeps the result
  `uncalibrated_comparative` with no calibration fixtures, no fit, and
  uncalibrated warnings.
- `kayakgen/search/sweep.py:25` defines
  `CandidateStatus = Literal["complete", "failed", "skipped"]`, with no
  `pending`. RFC 0009 still names `pending` (`docs/rfcs/0009-sweep-run-records.md:105`)
  and the `stl` evaluator option exists at `kayakgen/search/sweep.py:69`
  but the runner never produces a `stl` artifact. These two deltas are
  the RFC 0009 reconciliation items.
- `tests/test_compare.py:113-173`, `:193-209`, and `:274-445` already
  enforce the admissibility split this vote codifies: defaults use
  `GM0_m`, exclude raw `Rt_N_last`, preserve design validity without
  scoring warnings, mark raw resistance exploratory and provenance-
  gated, reject forged or incomplete calibrated metadata, and reject
  calibrated resistance as final design fitness.
- `tests/test_sweep.py:23-106` and `:120-155` enforce sweep determinism,
  resume behavior, failure preservation, optional mesh diagnostics,
  optional stability summaries, and absence of high-angle `GZ` summary
  fields.
- `docs/rfcs/0013-pareto-frontier-comparison-ui.md:8-16, :53-63, :87-90`
  reads exactly as the current code: default reports exclude raw
  uncalibrated resistance; explicit resistance objectives become
  exploratory frontiers; calibrated provenance plus RFC 0012 is the
  promotion gate.
- `docs/rfcs/0009-sweep-run-records.md:20-37` explicitly excludes
  optimization and automatic best-kayak selection as non-goals and
  keeps resistance as comparative filter only. Option D is the
  RFC-level position.
- `docs/ROADMAP.md:34-59` (the "No-Claims Rules") and `:209-222` (Batch
  H) state the governing rule verbatim: comparison can use only metrics
  whose claim state and availability are explicit, and optimization
  must not silently treat raw resistance, raw CFD, advisory validity,
  or unavailable stability as final design fitness. This vote ratifies
  Batch H.

### Independent external check (access date 2026-05-14)

I sampled the external citations in the research packet and accepted
them; they remain the right sources for this decision. Two observations
strengthen the vote:

- NASA's V&V tutorial and `Uncertainty and Error in CFD Simulations`
  (grc.nasa.gov/www/wind/valid/tutorial/) say conceptual-stage CFD use
  may trade accuracy for speed only when the accuracy level is
  understood by the consumer. That argument transfers directly to raw
  analytical resistance and to any future raw CFD - both are admissible
  as explicit exploratory filters, not as silent ranking inputs.
- ITTC 7.5-02-02-01 (resistance test procedure) and 7.5-02-02-02
  (resistance uncertainty example) require documented procedure, bias
  and precision limits, total uncertainty, and benchmark validation
  before a resistance number stands on its own. RFC 0027 / `claims.py`
  already require the equivalent provenance bundle; that is the right
  shape for the future promotion gate in Option C.
- pymoo and OpenMDAO documentation both separate variables, objectives,
  and constraints and assume the application supplies trustworthy
  metric definitions. They support project-owned objective metadata
  (Option B) rather than letting an optimizer infer admissibility from
  numeric availability.

## Why Rejected Alternatives Lose

- **Option B alone (registry without ratifying Option A defaults).**
  Building the metric registry is necessary but insufficient; without
  ratifying the current default whitelist as the decision, a future
  workflow could ship an "objective registry" that re-admits raw
  resistance or warning counts. The decision needs to lock the current
  defaults as the answer, with the registry as the implementation
  vehicle. So Options A and B must travel together; B alone loses.
- **Option C alone (only evidence-gated promotion).** Promotion rules
  matter, but they describe the *future* admissibility transition, not
  today's policy. Without Option A, the project would leave the current
  default set as informal code-only convention. Option C is therefore
  adopted *with* Option A, not instead of it.
- **Option D alone (only scalar-fitness postponement).** Postponing
  scalar `design_fitness` is correct but addresses only one risk
  (overclaiming a single best kayak). It does not handle exploratory
  resistance, raw CFD, advisory validity, or unavailable high-angle
  stability. Adopted only as a supporting rule.
- **A broader default whitelist (admit `wetted_surface_m2`,
  `Cp_actual`, or raw `Rt_N_last` by default).** Each has a defensible
  expert-use story, but admitting them as defaults makes the project
  responsible for direction-by-class semantics (Cp), target form
  (mass/displacement), or speed-indexed naming (resistance) that have
  not been settled. Better to keep them user-selected and explicit, per
  Option B's `default_objective` vs `explicit_exploratory_objective`
  split.
- **A scalar `design_fitness` now (or any "best kayak" auto-pick).**
  Forbidden by `docs/ROADMAP.md:34-59` and unsupported by
  `claim_allows_final_design_fitness` in `kayakgen/eval/claims.py`. No
  current output satisfies `validated_design_fitness`.
- **Admit raw CFD or advisory-validity counts as objectives.** Roadmap
  No-Claims Rules and current tests forbid both. Optimizing a warning
  count hides severity and domain meaning; admitting raw CFD without a
  real solver success path violates `docs/ROADMAP.md:34-59`.
- **Treat RFC 0009 as still "proposed" rather than reconciling its
  status.** The runner already implements the acceptance backbone
  (`kayakgen/search/sweep.py:56-93, 96-137, 144-220, 237-323, 327-370`).
  Leaving RFC 0009 indexed `proposed` invites a future workflow to
  re-litigate sweep-record semantics; reconciliation is cheap and is a
  precondition for any optimizer RFC.

## Implementation Gates (must hold before any optimizer/search RFC)

These are gates, not deliverables of this decision. The vote forbids
starting optimizer work without them.

1. Reconcile RFC 0009 status to "landed partial / run-record safe
   slice" in `docs/rfcs/README.md` and roadmap text, and record the
   three deltas: `pending` is not a serialized status, `stl` is an
   evaluator option without a runner artifact, and mesh diagnostics
   have landed as an optional artifact.
2. Either implement `stl` sweep artifacts or mark `stl` as reserved /
   no-op in docs and `CandidateRecord`/`SweepSpec` text.
3. Add objective metadata for comparison and any future search,
   classifying every metric as `default_objective`,
   `explicit_exploratory_objective`, `constraint_or_filter`,
   `display_only`, `unavailable`, or `forbidden_until_claim_gate`, and
   carrying unit, direction, source evaluator, claim-state
   requirement, availability rule, and warning text.
4. Preserve current behavior: missing or provenance-failed metrics
   produce warnings and never silently dominate; failed/skipped
   candidates remain visible but ineligible for frontier membership.
5. Before promoting calibrated resistance to a non-exploratory
   objective: require accepted fit, calibration fixture IDs, model
   version, fit metrics, validity envelope, in-envelope evaluation,
   and an explicit speed-indexed metric name (e.g.,
   `Rt_N_at_target` or `Rt_N_fn_0_40`). `Rt_N_last` must not be
   promoted - it depends on the final speed in the curve, not a
   target.
6. Before promoting CFD-derived metrics: a real-solver success path
   (RFC 0041), validated/accepted output semantics, and per-metric
   accepted-use provenance must exist.
7. Before promoting high-angle stability metrics: RFC 0043 generated-
   body and heeled-integration gates must have landed.
8. Add tests that any future optimizer/search defaults cannot include
   raw resistance, raw CFD, advisory validity, unavailable high-angle
   stability, or scalar `design_fitness`.
9. Defer any scalar "best kayak" or `design_fitness` axis to a future
   RFC that defines `validated_design_fitness` semantics, weights,
   validity envelope, and residual-risk wording.

## No-Claims Language That Must Remain In Force

The following sentences are load-bearing and must not be softened by
any successor RFC, comparison report, or optimizer:

- Raw analytical resistance is `uncalibrated_comparative`, a comparative
  filter, not a calibrated model, final prediction, design-fitness
  score, or default optimization objective.
- CFD output is local-dispatch raw/unvalidated or fixture-only; no
  accepted real-solver success path exists.
- Class validity, advisory badges, and design warnings are not proof of
  seaworthiness, calibrated performance, final design fitness, or
  solver readiness.
- High-angle `GZ`, `GZ_max`, range-of-positive-stability, capsize
  range, and secondary-stability metrics are unavailable for real
  generated kayaks until RFC 0043 gates land.
- No current output satisfies `validated_design_fitness`. Calibrated
  resistance, even when admitted, is a calibrated prediction objective,
  not final design fitness.
- Failed and skipped candidates remain visible but never enter the
  Pareto frontier.

## Revisit Conditions

Reopen this decision when:

- RFC 0042 produces an accepted calibration fixture with fit, validity
  envelope, and speed-indexed metric; or
- RFC 0041 lands a real external solver with validated outputs and
  documented accepted use; or
- RFC 0043 lands real high-angle stability with accepted heeled
  integration; or
- A future RFC defines `validated_design_fitness` semantics.

Until then, the default Pareto objective set stays exactly as it is in
`kayakgen/search/compare.py:24-28`.
