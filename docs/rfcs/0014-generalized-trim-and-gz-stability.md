# RFC 0014: Generalized Trim and GZ Stability

Status: superseded by RFC 0043 (closed by RFC 0064)
Date: 2026-05-13
Context: RFC 0011 landed explicit load cases and equilibrium sinkage, but left
generalized trim and high-angle stability open. Workflow 0022 landed compatible
longitudinal load components, additive trim result fields, and bounded
fixed-body upright trim equilibrium for explicit component load cases. It still
does not claim a computed high-angle `GZCurve`.

## Problem

The current stability implementation can answer whether a centered load case
floats at an equilibrium draft. It cannot answer whether the same hull trims bow
down or stern down under a real paddler/cargo layout, and it cannot produce a
righting-arm curve over heel.

Those outputs are load-bearing for kayak comparison. They are also easy to fake
if the project does not define coordinate references, moment balance,
closed-volume semantics, and warning behavior before implementation.

## Goals

- Add explicit longitudinal load inputs for paddler, hull, and cargo masses.
- Solve upright equilibrium for sinkage and trim by matching total
  displacement and longitudinal moment.
- Preserve the stern-positive coordinate convention from RFC 0010:
  `+x` points toward the stern and `-x` points toward the bow.
- Define when a `GZCurve` may be emitted and what volume model it uses.
- Keep fixed-paddler-CG assumptions visible in result metadata and warnings.
- Make results serializable for CLI, web, desktop, and sweep records.

## Non-Goals

- Dynamic stability, bracing, waves, surf launches, or capsize recovery.
- Validating the stability model against measured kayak test data.
- Replacing the mesh contract or solving watertight CFD geometry by implication.
- Optimizing load placement automatically.

## Proposal

Extend `LoadCase` with longitudinal load components:

```python
LongitudinalLoadComponent(
    name: str,
    mass_kg: float,
    x_m: float,
    kg_above_keel_m: float | None = None,
)
```

`x_m` uses the RFC 0010 coordinate system. A component with negative `x_m` is
forward of midship toward the bow; a component with positive `x_m` is aft toward
the stern. Existing compact fields such as `paddler_mass_kg` remain accepted as
compatibility helpers, but the normalized computation model is a list of load
components with total mass, LCG, and KG.

Add an upright trim solver that searches for waterplane position and trim angle
until both of these equations are within tolerance:

- displaced mass equals total load mass;
- displaced longitudinal moment equals load longitudinal moment.

The result model adds these fields on `StabilityResult`:

```python
draft_at_midship_m: float | None
sinkage_m: float | None
trim_angle_deg: float | None
load_lcg_m: float | None
buoyancy_lcb_m: float | None
displacement_error_kg: float
moment_error_kg_m: float | None
moment_tolerance_kg_m: float | None
equilibrium_iterations: int | None
warnings: list[str]
```

Workflow 0022 landed the upright trim slice with fixed-body station-area
integration against the current hull shape and a bounded trim search for
explicit component load cases. The implementation preserves compact load-case
fields, normalizes explicit components to total mass, load LCG, and
mass-weighted KG, and defines `trim_angle_deg > 0` as stern-down/bow-up with
`+x` aft toward the stern. Result fields are additive on `StabilityResult`
rather than a separate breaking result model: `draft_at_midship_m`,
`sinkage_m`, `trim_angle_deg`, `load_lcg_m`, `buoyancy_lcb_m`,
`displacement_error_kg`, `moment_error_kg_m`, `moment_tolerance_kg_m`,
`equilibrium_iterations`, and warnings.

CLI equilibrium output and opt-in sweep summaries now carry the same trim
fields. Existing compact centered-load equilibrium behavior remains compatible
and continues to report a zero-trim sinkage solution.

High-angle `GZCurve` output is allowed only when the evaluator can identify the
closed body used for heel-volume integration. The initial accepted body should
be an evaluation-only closed hull volume, not the open display mesh and not a
solver-specific CFD package. Because that body is not defined, high-angle GZ
remains unavailable with the explicit `closed_volume_body_not_defined` boundary
instead of synthetic righting arms.

The target high-angle `GZCurve` contract remains deferred:

```python
GZCurve(
    heel_deg: list[float],
    gz_m: list[float],
    righting_moment_nm: list[float],
    max_gz_m: float | None,
    heel_at_max_gz_deg: float | None,
    range_positive_stability_deg: float | None,
    assumptions: list[str],
    warnings: list[str],
)
```

## Acceptance Criteria

- Landed in workflow 0022: load cases round-trip with explicit longitudinal load
  components.
- Landed in workflow 0022: compact legacy load fields normalize compatibly
  without changing existing default equilibrium-sinkage output.
- Landed in workflow 0022: a forward LCG produces bow-down trim and an aft LCG
  produces stern-down trim under otherwise equal inputs.
- Landed in workflow 0022: trim solve results include displacement and moment
  residuals, convergence status, iteration count, and warnings.
- Landed in workflow 0022: CLI output includes trim fields in equilibrium mode.
- Landed in workflow 0022: sweep/evaluation records can carry trim equilibrium
  output without breaking existing JSON consumers.
- Deferred: `evaluate_gz_curve` emits real `GZ` values only when a named
  closed-volume model is used.
- Landed in workflow 0022: tests prove that unsupported high-angle stability
  remains unavailable rather than producing placeholder curves.

## Open Questions

- Should the first closed-volume body be hull-only, hull plus deck, or a
  stability-specific evaluation body that is distinct from CFD mesh profiles?
- Should the default paddler LCG be a fixed fraction of length, a named cockpit
  station, or user-required input?
- Which heel angle range and spacing should be canonical for comparison runs?
- Should high-angle curves hold paddler CG fixed in world coordinates, fixed to
  the hull, or make the assumption selectable?

## Implementation Path

- Step 1 - Add longitudinal load components and compatibility normalization.
- Step 2 - Add trim equilibrium result fields and JSON/CLI serialization.
- Step 3 - Implement upright sinkage-plus-trim solving with tests for LCG
  direction, residuals, and non-convergence.
- Step 4 - Carry trim fields through opt-in sweep summaries and comparison
  records without breaking existing JSON consumers.
- Step 5 - Keep `GZCurve` unavailable with explicit warnings until a
  closed-volume body is accepted.
- Step 6 - Implement high-angle `GZCurve` only after the volume decision has
  landed.

## Domain Modeling

`LongitudinalLoadComponent` and `LoadCase` are value objects. `StabilityResult`
carries the landed trim-equilibrium read-model fields. `GZCurve` remains a
reserved evaluator read model derived from the `Hull` aggregate and a load case
after the closed-volume decision lands.
