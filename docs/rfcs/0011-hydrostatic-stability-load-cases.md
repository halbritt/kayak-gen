# RFC 0011: Hydrostatic Stability and Load Cases

Status: proposed
Date: 2026-05-13
Context: `kayakgen.eval.hydrostatics` computes integrated hydrostatics and
`GM0_m`; `kayakgen.eval.contract.GZCurve` is reserved for stability.

## Problem

The current hydrostatics evaluator computes `GM0_m` with a hard-coded
placeholder center of gravity. That is useful as a rough signal, but the
generative pipeline needs explicit load cases: paddler, hull, cargo, and the
reference point for vertical center of gravity.

The project also reserves a `GZCurve`, but it does not yet define what volume is
used for heeled stability, how load displacement is solved, or which outputs are
safe to compare.

## Goals

- Replace hidden `KG` assumptions with explicit, serializable load cases.
- Keep default behavior numerically compatible until load cases are adopted by
  callers.
- Define a stability result contract for `GM0`, `GZ`, righting moment, maximum
  `GZ`, and range of positive stability.
- Make stability output usable by CLI, web, desktop, and sweep runs.
- Clearly distinguish design-waterline initial stability that can be estimated
  today from high-angle `GZ` behavior and equilibrium load solving that require
  further decisions.

## Non-Goals

- Active paddler bracing, seakeeping, wave response, cockpit ergonomics, or
  capsize recovery.
- Changing STL export into a watertight hull/deck solid.
- Claiming validated high-angle stability before the volume semantics are
  decided.
- Optimizing hulls directly.

## Proposal

Add `kayakgen.eval.stability` with:

- `LoadCase`
- `StabilityResult`
- `evaluate_initial_stability(hull, load_case)`
- reserved `evaluate_gz_curve(...)` that raises a clear not-implemented error
  until the heeled-volume decision is made.

Default load case fields:

```python
name: str = "default"
paddler_mass_kg: float = 85.0
hull_mass_kg: float = 18.0
cargo_mass_kg: float = 0.0
kg_above_keel_m: float = 0.25
seawater_density_kg_m3: float = 1025.0
```

The initial implementation should allow `Hydrostatics.GM0_m` to remain
available and make its baseline/keel-referenced `KG` source explicit. Full
`GZ` and load-equilibrium waterline solving remain reserved until humans choose
the heeled-volume and sinkage/trim semantics.

CLI:

```text
kayakgen stability hull.json --load-case load-case.json --out stability.json
```

## Acceptance Criteria

- `LoadCase` serializes and round-trips.
- Default initial `GM0` remains populated and is tied to an explicit load case.
- Raising `kg_above_keel_m` lowers initial `GM0`.
- Increasing `beam_wl_m` increases initial `GM0` for otherwise equal hulls.
- `StabilityResult` includes `load_mass_kg`, `displaced_mass_kg`,
  `displacement_error_kg`, method/status fields, and warnings when the result
  is design-waterline-only rather than equilibrium-solved.
- `EvaluationResult.stability` is `StabilityResult | None`, with `GZCurve`
  nested as an optional value.
- Full `GZ` curve calls are explicit about not being implemented, not silently
  fake.

## Open Questions

- Should high-angle stability use hull-body-only volume, hull-plus-deck volume,
  or a new evaluation-only closed volume?
- Should future load cases reference KG from keel, seat, or design waterline?
- What default paddler/hull/cargo masses should be canonical?

## Implementation Path

- Step 1 - Add load-case and stability result models.
- Step 2 - Refactor initial GM calculation to accept an explicit load case
  without changing default output.
- Step 3 - Add CLI and JSON helpers.
- Step 4 - Keep full `GZ` curve reserved with tests proving it does not claim
  computed output.
- Step 5 - Revisit full `GZ` after RFC 0010 mesh/volume decisions.

## Domain Modeling

`LoadCase` is a value object. `StabilityResult` is an evaluator read model
derived from the `Hull` aggregate and a load case.
