# RFC 0074: Fixed-body operating pose and load equilibrium

Status: landed fixed-body immersion + v2 load equilibrium
Date: 2026-11-07
Context: KAYGEN-14 / W9; RFCs 0048 and 0050, and the explicit evaluation
context in RFC 0073.

## Problem

V2 geometry reads `distribution_v2.draft_profile`. Updating the legacy
`Hull.draft_m` scalar therefore changes neither its physical sections nor
its displaced volume. A target-load bisection over that scalar has an
unchanging bracket. Changing the draft distribution instead would change
the designed hull to represent a different load.

## Goals

- Hold the complete canonical hull-plus-deck body fixed while moving its
  waterplane and trim.
- Use the same realized pose for hydrostatics and wetted resistance sampling.
- Solve feasible lighter/heavier and longitudinally offset load cases;
  retain explicit failure for infeasible loads or unsupported operating bounds.
- Preserve legacy behavior when no operating pose is requested.

## Non-Goals

No measured validation, calibrated resistance, final design fitness or safety
claim is introduced. Pose support does not repair the analytical resistance
integrator's numerical-quality limitations. Geometry and shape identity are
not changed by load solving.

## Proposal

`OperatingPose` is an immutable value object with `sinkage_m` and
`trim_angle_deg`. Model X points sternward, Y starboard and Z upward.
Positive trim is stern-down. Sinkage is the body-frame waterplane intercept:
`z_body = sinkage + x_body * tan(trim)`. Rigidly rotating `(x, z-sinkage)`
puts that plane at world `z=0`:

```
x_world = x_body*cos(trim) + (z_body-sinkage)*sin(trim)
z_world = -x_body*sin(trim) + (z_body-sinkage)*cos(trim)
```

The canonical closed body includes deck surfaces. Physical triangles are
clipped against world Z=0, including exact intersections through crossing
triangles. The virtual waterplane cap contributes zero tetrahedral volume
and first moment because it lies in the plane through the integration
origin. The retained physical facets supply displaced volume, buoyancy
centroid and wetted area. Oriented waterplane edges supply waterplane area
and transverse second moment, without assuming a convex waterplane cap.
Dry and fully submerged states carry explicit notes and no initial GM.

The source mesh is cached for one full Hull record/resolution during repeated
pose evaluations; only its rigid pose changes. Resistance samples a regular
world X/depth grid through the inverse rigid transform and canonical station
rings. Its Froude number continues to use physical `Hull.length_m`; the
sampling extent is the transformed body extent. Numerical-resolution and
uncalibrated-use limits still apply.

The fixed-body equilibrium solver brackets sinkage using actual body vertex
bounds and the requested trim. It uses actual canonical midship keel depth,
not the legacy draft scalar. Optional trim solves the world-frame buoyancy
and load-CG moment, including KG projection. Returned load and buoyancy
centroids use common world X. Loads outside the fixed body's displaced-mass
range, failed mass brackets, failed moment brackets and iteration caps remain
`not_converged`. The legacy no-pose lofted path remains unchanged; explicit
new evaluation contexts may use fixed-body solving for either geometry kind.

## Acceptance Criteria

- Independent rectangular-body tests establish displacement and wetted area
  at several immersions and the `sec(trim)` oblique-waterplane relation.
- Changing a real v2 hull's load moves its waterplane and solves requested
  displacement while its full serialized physical record remains unchanged.
- A longitudinally offset v2 load solves positive stern-down trim and agrees
  with the same posed hydrostatic displacement and moment.
- Posed resistance wetted area matches the independent reference; trimmed
  grid sampling agrees with inverse rigid coordinates.
- Dry/full-body bounds and nonfinite/vertical poses are explicit; infeasible
  loads never acquire successful equilibrium status.
- Shared context and target-workflow services preserve input loads and use
  the same pose in saved results and reports (RFC 0073 integration).
- Legacy hydrostatics, resistance and stability tests pass with no pose.
- Full pinned pytest and Ruff pass before trunk integration.

## Open Questions

Physical applicability and numerical-adequacy policy remain independent gates.
No high-angle or roll equilibrium is added by this pitch/sinkage value object.

## Implementation Path

1. Reproduce the unchanging v2 draft control variable.
2. Add rigid pose and clipped canonical-body integration with independent
   references, then wire hydrostatics and resistance to that pose.
3. Add bounded mass/trim solvers and route v2 equilibrium through them.
4. Integrate target/report evaluation context, retain legacy paths, and run
   actual request/save/report acceptance separately from mathematical tests.

## Domain Modeling

OperatingPose is a value object describing operation of the existing Hull
aggregate. The physical Hull remains the shape authority. Fixed-body
integration and equilibrium are evaluator services, consistent with
`DDD.md`'s model-extension convention.
