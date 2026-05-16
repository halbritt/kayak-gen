# RFC 0047: Active Search v2 — Successor Algorithms

Status: proposed
Date: 2026-05-16
Context: successor to RFC 0044 v1 (vendored NSGA-II), which landed in
the cowboy 2026-05-16 session under D024. The v1 surface is multi-
objective only, evolutionary (NSGA-II with SBX crossover and polynomial
mutation), and seeded-deterministic. This RFC scopes which algorithm
family lands next.

## Problem

NSGA-II is well-suited to noisy, hard-to-differentiate evaluation
landscapes, which describes kayakgen's analytical resistance + hydro
+ mesh-diagnostics evaluator stack. It is less efficient when:

- the objective evaluator is expensive (real OpenFOAM interFoam runs
  per RFC 0041 / D012 / D022 are seconds-to-minutes each, not
  milliseconds; an NSGA-II run with 12 population × 4 generations × 3
  metrics × interFoam = 90+ s wall-clock minimum, often 10× more);
- the operator wants to find a *single* best design under explicit
  constraints (NSGA-II returns a Pareto front, not a singleton);
- the operator wants probabilistic uncertainty on the trade-off shape
  (NSGA-II returns no surrogate that can be queried after the run).

Three v2 algorithm candidates address those gaps:

- **GP-Bayesian optimization** (single-objective, GP surrogate, EI/UCB
  acquisition) — best for cost-bounded single-objective design.
- **EHVI** (Expected Hypervolume Improvement, multi-objective GP) —
  best for cost-bounded Pareto-front exploration where each evaluation
  is expensive.
- **MOEA/D** (decomposition-based multi-objective evolutionary
  algorithm) — best when the operator wants many uniformly-spread
  Pareto points but cost-per-eval is moderate.

Picking only one v2 algorithm is appropriate; trying to ship all three
duplicates engineering effort and confuses the CLI surface.

## Goals

- Pick one v2 algorithm family that complements (not replaces) v1
  NSGA-II.
- Preserve the additive opt-in surface from RFC 0044: a new
  `algorithm.kind` value on `SearchAlgorithmSpec` selects the v2
  algorithm without changing v1 behavior.
- Reuse RFC 0044's claim-admissibility gate
  (`ensure_objectives_claim_admissible_for_search`) — the v2 algorithm
  must obey the same `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`
  refusal rules and the RFC 0043 high-angle-GZ display-only refusal.
- Preserve seeded determinism: a seeded v2 run reproduces byte-identical
  candidate records.
- Preserve the RFC 0009 candidate-record schema and the `pending`
  lifecycle.

## Non-Goals

- No external optimization-library dependency. The v2 algorithm ships
  pure-Python, like v1.
- No new objective metric, no new claim state.
- No surrogate-emitted result wording: surrogate-informed *candidate
  selection* is in scope; surrogate-emitted numeric drag/GM₀/etc. is
  out. Surrogates are not allowed to fabricate evaluation values.
- No cross-run model reuse, no transfer learning, no persisted
  surrogate weights.
- No web/desktop UI for v2 algorithm output. v2 results surface through
  the existing comparison report's display-only path.
- No hosted/distributed execution.

## Algorithm choice

The recommendation is **EHVI (Expected Hypervolume Improvement) over a
multi-output Gaussian-process surrogate**, for these reasons:

- The most expensive evaluator path (real OpenFOAM-v2512 interFoam) is
  seconds-to-minutes per evaluation. Expected-cost optimization wins
  here.
- The default kayakgen objective set is multi-objective (GM₀,
  displacement_error_kg, mesh_problem_count). EHVI is the canonical
  multi-objective Bayesian-optimization acquisition function.
- A GP surrogate gives the operator a query-after-the-run interface
  ("given my final population, where would the next best candidate
  be?") that NSGA-II cannot.
- The decomposition story (MOEA/D) is more useful when the operator
  knows the Pareto direction of interest in advance; kayakgen
  operators rarely do.
- Pure-Python EHVI is implementable in ~600-1200 lines (Cholesky-
  factorized GP, EHVI calculator, sub-region decomposition for the
  hypervolume gradient).

GP-Bayesian (single-objective) is then a natural sub-case: a 1-objective
EHVI run with a degenerate hypervolume calculation reduces to expected
improvement (EI). The same code path admits both.

MOEA/D is rejected for v2 because the use case overlaps NSGA-II
(both return Pareto fronts) without solving the high-cost-per-eval
problem.

## Proposal

### Surface

`SearchAlgorithmSpec.kind` admits a new literal: `"ehvi"`. Spec shape:

```json
"algorithm": {
  "kind": "ehvi",
  "initial_population_size": 16,
  "iteration_budget": 32,
  "seed": 1234,
  "gp_kernel": "matern_5_2",
  "gp_noise_floor": 1.0e-6,
  "reference_point": "auto",
  "candidate_pool_size": 256
}
```

- `initial_population_size`: Latin-hypercube initial sample.
- `iteration_budget`: number of acquired candidates after the initial
  sample.
- `gp_kernel`: starting with `matern_5_2` and `rbf`; defaults to
  `matern_5_2`. No external GP library; ship a minimal Cholesky-
  factorized GP.
- `gp_noise_floor`: minimum diagonal jitter for numerical stability.
- `reference_point`: hypervolume reference, either `"auto"` (worst
  per-objective values in the initial sample + 10% margin) or an
  explicit tuple.
- `candidate_pool_size`: number of EHVI-evaluated candidates per
  iteration (acquired via Sobol or LHS sample, scored by EHVI, best
  one evaluated).

### Vendored GP + EHVI

Implementation lives at:

- `kayakgen/search/active/gp.py` — minimal Cholesky-factorized GP with
  Matern 5/2 and RBF kernels, marginal-likelihood maximization via
  Nelder-Mead from `scipy.optimize`. Avoids any third-party GP library.
- `kayakgen/search/active/ehvi.py` — multi-objective EHVI calculator
  via sub-region decomposition (Couckuyt 2014 algorithm), pure Python,
  no external dependency.

### Determinism

Seeded as in v1: a single `random.Random(seed)` plus
`numpy.random.default_rng(seed)` thread through every sampling step
(LHS, candidate pool, tie-breaking). GP hyperparameter optimization
starts from a fixed seed-derived initialization to keep the marginal-
likelihood fit deterministic.

### Resume

EHVI is naturally checkpoint-friendly: after each iteration, the
surrogate's training data is the previously-evaluated candidate set.
Resume rebuilds the GP from disk and continues. The `pending` lifecycle
from RFC 0009 applies unchanged.

### What lands and what does not

Lands:
- `kayakgen/search/active/gp.py` and `kayakgen/search/active/ehvi.py`.
- `EhviAlgorithmSpec` (subset of `SearchAlgorithmSpec`).
- New v2 algorithm path in `runner.py` triggered by
  `algorithm.kind == "ehvi"`.
- A new objective-admissibility test: EHVI honors the same claim-state
  gates as NSGA-II.
- Tests for: seeded determinism, GP marginal-likelihood reproducibility,
  EHVI hypervolume improvement strictly nonnegative, EHVI vs random
  candidate selection (EHVI must improve hypervolume over the run for
  a seeded synthetic case), constraint enforcement parity with v1,
  exploratory-mode tagging parity.

Does not land:
- No MOEA/D.
- No GP-Bayesian-only (single-objective) path; that's expressed as
  EHVI with 1 objective.
- No web UI.
- No surrogate-emitted numeric values exposed in run.json or
  comparison output. The surrogate is internal to the algorithm.
- No external optimization library, no GP library.

## Acceptance Criteria

- `SearchAlgorithmSpec.kind == "ehvi"` is accepted by spec validation.
- Default behavior (no v2 spec) is byte-identical to RFC 0044 v1.
- Two independent invocations of an EHVI spec with the same seed
  produce byte-identical `candidates/<key>/record.json`.
- The GP marginal-likelihood fit is deterministic across reseeded
  runs.
- An EHVI run on a seeded synthetic objective landscape achieves at
  least 10x hypervolume improvement vs random candidate selection at
  the same budget (regression test).
- Constraints fire identically to v1 (constraint_failed status).
- The claim-admissibility gate refuses raw_unvalidated and
  uncalibrated_comparative objectives unless exploratory.
- The RFC 0043 high-angle-GZ refusal still wins.
- No external Python dependency added beyond what RFC 0044 used.

## Open Questions

- Should the GP marginal-likelihood optimizer be Nelder-Mead (vendored)
  or L-BFGS-B (depends on `scipy.optimize`)? Both are pure-Python
  available in `scipy`, which is not currently a dependency. Vendoring
  Nelder-Mead avoids the new dep.
- Should `reference_point: "auto"` recompute every iteration (typical)
  or only after the initial sample (cheaper)?
- For 1-objective runs, should the spec be allowed to declare
  `algorithm.kind = "bo"` as a convenience alias for `"ehvi"`?
- Should the surrogate's predicted variance be surfaced in the
  candidate record (purely informational, never as an evaluation
  value)?

## Implementation Path

1. Land `kayakgen/search/active/gp.py` with a minimal Cholesky GP and
   Nelder-Mead marginal-likelihood optimization. Test seeded
   determinism.
2. Land `kayakgen/search/active/ehvi.py` with the sub-region
   decomposition algorithm. Test against a known-Pareto-front
   synthetic problem.
3. Extend `SearchAlgorithmSpec` to admit `kind = "ehvi"` and a new
   `EhviAlgorithmConfig` block.
4. Extend `runner.py` to dispatch v1 NSGA-II vs v2 EHVI on
   `algorithm.kind`.
5. Add the acceptance-criteria tests.
6. Update `docs/USER_GUIDE.md` `kayakgen search` section with the new
   algorithm option.

## Domain Modeling

Boundary clarification. v2 EHVI is an *algorithm strategy* added to the
existing `kayakgen.search.active` use-case. No new aggregate root, no
new domain event. The GP surrogate is a transient model local to one
run; it is not persisted as a domain artifact.

Cite `DDD.md § "Adding to the model"`: this is a *strategy* refinement
over the existing search service.
