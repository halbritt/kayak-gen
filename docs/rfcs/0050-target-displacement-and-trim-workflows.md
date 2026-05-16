# RFC 0050: Target-Displacement and Target-Trim Design Workflows

Status: proposed
Date: 2026-05-16
Context: Phase 8 item 1 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Today's evaluators
take a fully-specified `Hull` plus an explicit draft and return
hydrostatics; designers asking "what draft does this hull need to
carry 95 kg of paddler + cargo?" must run a search by hand. This RFC
scopes two paired workflows that solve the inverse problem.

## Problem

A designer's natural design loop is target-load-first: they know the
all-up weight (paddler + hull + cargo) and want kayakgen to tell them
the resulting draft, trim, sinkage, and freeboard at that load. Today
they iterate `kayakgen evaluate` manually, adjusting `draft_m` until
`displaced_mass_kg` matches the target. The trim workflow is even
worse: there is no direct `--target-load load.json` flag on any
existing command.

These workflows already exist *inside* the evaluators:
`evaluate_upright_equilibrium` solves draft from displacement;
`_solve_midship_draft_for_trim` solves draft and trim from a
load case. They are buried behind evaluator boundaries.

## Goals

- Land two new CLI subcommands or flags that expose the inverse
  solvers to operators directly.
- Preserve the existing evaluator surfaces (`kayakgen stability
  --equilibrium`) byte-stably.
- Honor every claim/no-claim rule already in force.

## Non-Goals

- No change to the underlying solvers.
- No optimization over multiple hulls; this RFC solves *one* hull at
  a time. Multi-hull search is RFC 0044 / RFC 0047.
- No structural claim about whether the load is *carriable*; the
  workflow reports the resulting state, the operator decides.
- No safety / seaworthiness wording.

## Proposal

Two new entry points:

1. **`kayakgen target-draft <hull.json> --load <load.json> --out <out>`**
   solves upright sinkage for the given load and writes an extended
   `EvaluationResult` whose `equilibrium` block carries the solved
   draft, residuals, iterations, and the resulting hydrostatics.
2. **`kayakgen target-trim <hull.json> --load <load.json> --out <out>`**
   solves draft + trim for a load case with a non-zero longitudinal
   component (paddler offset, cargo aft, etc.) and writes the trim
   result plus per-station displacement decomposition.

Both reuse the existing solvers via `kayakgen.services.evaluation`.

Output records reuse the existing `StabilityResult` and trim-result
contracts; no new schema. The two new CLI subcommands are thin
wrappers, not a new service surface.

## Acceptance Criteria

- `kayakgen target-draft default.json --load day-trip.json` returns
  a draft within 1 mm of the converged value the existing
  `evaluate_upright_equilibrium` would compute for the same hull +
  load.
- `kayakgen target-trim default.json --load offset-paddler.json`
  produces a converged trim equilibrium with residuals below the
  default tolerance.
- Default `kayakgen stability --equilibrium` output unchanged.
- New tests pin: load JSON round-trip; the new commands fail
  gracefully when the load is unphysical (>2× max displaced mass).

## Open Questions

- Should the inverse solvers also write the trim metadata into the
  base `kayakgen evaluate` output when an `--target-load` flag is
  added to that command? Or are the two new subcommands enough?
- Does `target-trim` need a separate `--initial-draft` hint when the
  solver fails to converge, or is the existing bracketed search good
  enough?
- Should the load-mismatch reporting path (given a draft, report
  the load mismatch) be a third subcommand, or just a `--report-only`
  flag on `target-draft`?

## Implementation Path

1. Define a `TargetDraftRequest` / `TargetTrimRequest` value object
   in `kayakgen/services/evaluation.py`.
2. Land `solve_target_draft(hull, load_case) -> StabilityResult`
   and `solve_target_trim(hull, load_case) -> StabilityResult` in
   the same module; both reuse existing evaluator helpers.
3. Add `kayakgen target-draft` and `kayakgen target-trim` Typer
   subcommands in `kayakgen/cli/main.py`.
4. Update `docs/USER_GUIDE.md` with the new CLI surface.
5. +6-8 focused tests.

## Domain Modeling

Boundary clarification. The workflows are *use-cases* over the
existing stability aggregate. They add no new aggregate root,
no new value object beyond two thin request records, and no new
domain event. The Hull aggregate, load-case value object, and
StabilityResult schemas are unchanged.
