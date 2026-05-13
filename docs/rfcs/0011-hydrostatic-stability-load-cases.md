# RFC 0011: Hydrostatic Stability and Load Cases

Status: landed-equilibrium-sinkage-plus-trim-slice
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

## Human Decisions Recorded 2026-05-13

- Stability should support both design-waterline diagnostics and an
  equilibrium-solved mode. The current diagnostic mode remains useful, but it is
  not the final load-case answer.
- The equilibrium mode should solve sinkage and trim together.
- KG inputs should support multiple references and normalize internally for
  computation. Keel/baseline, design waterline, and seat-relative references are
  all useful user-facing inputs.
- Nick Schade's kayak-stability explainer is adopted as non-normative design
  context: stability curves are CG/CB/righting-arm curves over heel angle, the
  fixed-paddler-CG assumption is explicit, waterline shape drives initial
  stability, and seat/CG height materially changes the curve.

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
kg_reference: Literal["keel", "waterline", "seat"] = "keel"
kg_reference_value_m: float | None = None
seat_height_above_keel_m: float | None = None
seawater_density_kg_m3: float = 1025.0
```

Workflow 0022 added compatible longitudinal load components while preserving
the compact fields above. Explicit component load cases normalize to total
mass, load LCG, and mass-weighted KG; compact load cases still round-trip and
retain the centered-load behavior from the equilibrium-sinkage slice.

```python
LongitudinalLoadComponent(
    name: str,
    mass_kg: float,
    x_m: float,
    kg_above_keel_m: float | None = None,
)
```

The initial implementation allows `Hydrostatics.GM0_m` to remain available and
makes its baseline/keel-referenced `KG` source explicit. The current landed
equilibrium-sinkage slice solves compact load-case sinkage by matching displaced
mass to load mass with a bounded tolerance. Workflow 0022 additionally landed a
bounded fixed-body upright trim-equilibrium slice for explicit longitudinal
component load cases. That slice evaluates the current hull shape under a
trimmed upright waterplane, reports additive draft/trim/load-LCG/buoyancy-LCB
and mass/moment residual fields, and carries those fields through CLI and
opt-in sweep summaries.

This trim slice is not a high-angle stability implementation. Full high-angle
`GZ` remains unavailable because the closed-volume body for heeled integration
is not defined.

CLI:

```text
kayakgen stability hull.json --load-case load-case.json --out stability.json
kayakgen stability hull.json --load-case load-case.json --equilibrium --out stability.json
```

## Acceptance Criteria

- `LoadCase` serializes and round-trips.
- `LoadCase` accepts keel, waterline, and seat-relative KG references and
  normalizes them to keel/baseline height for computation.
- `LoadCase` accepts optional longitudinal load components while preserving
  compact legacy fields.
- Default initial `GM0` remains populated and is tied to an explicit load case.
- Raising `kg_above_keel_m` lowers initial `GM0`.
- Increasing `beam_wl_m` increases initial `GM0` for otherwise equal hulls.
- `StabilityResult` includes `load_mass_kg`, `displaced_mass_kg`,
  `displacement_error_kg`, method/status fields, and warnings when the result
  is design-waterline-only rather than equilibrium-solved.
- Equilibrium mode reports solved draft, sinkage, trim assumption, convergence
  tolerance, iteration count, and converged/not-converged status.
- Explicit component-load equilibrium mode reports bounded upright trim,
  signed load LCG, signed buoyancy LCB, moment residuals, and trim warnings.
- Waterline-relative KG references are normalized against the equilibrium draft
  in equilibrium mode.
- Load-case seawater density is used for equilibrium displacement matching.
- `EvaluationResult.stability` is `StabilityResult | None`, with `GZCurve`
  nested as an optional value.
- Full `GZ` curve calls are explicit about not being implemented, not silently
  fake.

## Open Questions

- Should high-angle stability use hull-body-only volume, hull-plus-deck volume,
  or a new evaluation-only closed volume?
- What default paddler/hull/cargo masses should be canonical?
- What default longitudinal component positions should be canonical for paddler,
  hull, and cargo?
- What closed-volume geometry should be used for future high-angle stability?

## Implementation Path

- Step 1 - Add load-case and stability result models.
- Step 2 - Refactor initial GM calculation to accept an explicit load case
  without changing default output.
- Step 3 - Add CLI and JSON helpers.
- Step 4 - Keep full `GZ` curve reserved with tests proving it does not claim
  computed output.
- Step 5 - Add equilibrium sinkage solving with explicit centered/symmetric trim
  assumption.
- Step 6 - Add compatible longitudinal load components and bounded fixed-body
  upright trim equilibrium for explicit component load cases.
- Step 7 - Revisit full `GZ` after RFC 0010 mesh/volume decisions define a
  closed-volume body.

## Domain Modeling

`LongitudinalLoadComponent` and `LoadCase` are value objects.
`StabilityResult` is an evaluator read model derived from the `Hull` aggregate
and a load case.
