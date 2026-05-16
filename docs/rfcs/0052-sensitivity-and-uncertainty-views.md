# RFC 0052: Sensitivity and Uncertainty Views

Status: proposed
Date: 2026-05-16
Context: Phase 8 item 3 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Today's evaluator
outputs are point values: one displacement, one GM₀, one resistance
curve. Designers asking "how much would GM₀ change if I bumped beam
by 5 mm?" must run a sweep and inspect the rows by hand.

## Problem

Without local sensitivity numbers a designer cannot tell whether two
candidates are meaningfully different or whether they are within
evaluator noise. With analytical resistance (raw filter), with
hydrostatics computed by triangle integration, and with raw OpenFOAM
output that is `raw_unvalidated`, the "noise floor" is real and not
documented.

Three concrete needs:

1. **Local parameter sensitivity**: for a chosen hull, the partial
   derivative of each metric with respect to each input parameter
   (`length_m`, `beam_oa_m`, `Cp`, etc.).
2. **Evaluator convergence metadata**: did the upright trim solve
   converge? Did the GZ heel point converge? Did the OpenFOAM force
   integral stabilise? Surface those answers explicitly.
3. **Uncertainty warning** when two candidates' summary metrics
   differ by less than the evaluator's quoted tolerance.

## Goals

- Land a `kayakgen sensitivity <hull.json>` subcommand that produces
  a finite-difference Jacobian of summary metrics vs hull parameters.
- Surface evaluator-side convergence flags on existing record
  schemas (additive fields; default None on records without
  convergence data).
- Add a comparison-side advisory: when two candidates'
  default-objective metrics differ by less than a configured
  tolerance, the comparison report flags the pair as
  `within_evaluator_noise`.

## Non-Goals

- No Monte-Carlo uncertainty propagation in v1.
- No covariance matrices.
- No claim that the finite-difference sensitivity is accurate beyond
  the chosen step size (the output is explicitly `local_sensitivity`
  with a recorded step).
- No new claim state.

## Proposal

### Sensitivity subcommand

```bash
kayakgen sensitivity hull.json --metric GM0_m --metric displacement_kg \
    --param length_m --param beam_oa_m --step 0.01 \
    --out build/sensitivity.json
```

Writes a JSON record with:

- `hull_design_hash` (per RFC 0049 vocabulary)
- `step_m_per_param`
- `metric_baseline: dict[str, float]`
- `metric_partials: dict[(metric, param), float]`
- `non_finite_partials: list[(metric, param, reason)]`
- A note that the result is a *local* sensitivity and not a
  reliability claim.

### Convergence metadata

`StabilityResult.equilibrium` already carries
`equilibrium_iterations` and residuals. `evaluate_gz_curve` already
emits per-heel convergence on `GeneratedBodyGZCurve.heel_point_metadata`.
This RFC adds:

- `ConvergenceFlag` value object: `(stage: str, status: Literal["converged", "not_converged", "iteration_cap"], residual: float | None)`.
- A `convergence: list[ConvergenceFlag]` field on `EvaluationResult`
  (additive; default `[]`).
- Evaluator-side writes: hydrostatics, upright equilibrium, trim,
  GZ, mesh diagnostics.

### Comparison-side noise advisory

`build_comparison_report` adds a per-pair check: for any two
candidates on the Pareto frontier, if every default-objective metric
differs by less than `metric_tolerance[metric]` (configurable;
default 1e-3 * baseline-value), the pair is flagged with
`within_evaluator_noise: bool` in the report's `pairwise_notes`
block.

## Acceptance Criteria

- `kayakgen sensitivity` produces a JSON record with the documented
  fields and SHA-256 hashes for hull identity.
- `EvaluationResult.convergence` is populated for the seven existing
  evaluators (hydrostatics, resistance, initial stability, upright
  equilibrium, trim, GZ, mesh diagnostics) on a parametrized test
  matrix.
- Default `kayakgen evaluate`, `compare`, and `search` outputs stay
  byte-stable when the sensitivity feature is not invoked.
- The within-evaluator-noise advisory appears in `compare.json` only
  when at least one pair triggers it.

## Open Questions

- Step-size selection: should sensitivity auto-tune step per
  parameter (e.g. 1e-4 * baseline) or require the operator to set it?
- Should the advisory tolerance map (per-metric thresholds) live in
  the metric registry (RFC 0049 / Phase 5 work) instead of a
  separate config?
- Does sensitivity belong on the Hull aggregate or as a service?

## Implementation Path

1. Define `ConvergenceFlag` in `kayakgen/eval/contract.py` (additive).
2. Wire each evaluator to emit its convergence flag.
3. Land `kayakgen/services/sensitivity.py` with the finite-difference
   loop.
4. Add `kayakgen sensitivity` CLI subcommand.
5. Extend `kayakgen.search.compare.build_comparison_report` with
   the pairwise-noise advisory.
6. Update `docs/USER_GUIDE.md`.

## Domain Modeling

Sensitivity is a *service* over the existing Hull and evaluator
aggregates. `ConvergenceFlag` is a value object attached additively
to `EvaluationResult`. The within-evaluator-noise advisory is a
*read-model* enhancement on the existing `ComparisonReport`.
