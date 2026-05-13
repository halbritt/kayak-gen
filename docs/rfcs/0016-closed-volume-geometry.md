# RFC 0016: Closed-Volume Geometry

Status: proposed
Date: 2026-05-13
Context: builds on RFC 0004 plumb-bow ambiguity, RFC 0010 mesh readiness
profiles, RFC 0014 high-angle stability boundary, and RFC 0015 solver dispatch
gating.

## Problem

The project can generate display and STL surfaces, and it can package open
surface candidates for future CFD work. It does not yet define a single closed
body suitable for displaced-volume integration, high-angle heel analysis, or a
watertight solid solver profile.

Without a closed-volume contract, future code can accidentally treat unrelated
surfaces as a valid solid, hide end-cap assumptions, or produce stability and
CFD results that are not reproducible.

## Goals

- Define the first project-owned closed-volume geometry contract.
- Make end-cap, deck-join, sheerline, and plumb-stem semantics explicit.
- Produce diagnostics that distinguish closed-volume evaluation readiness from
display mesh quality.
- Support future high-angle stability and watertight CFD profiles without
claiming either capability in this RFC.
- Preserve current open-surface export behavior.

## Non-Goals

- Implementing high-angle `GZCurve` output.
- Implementing a real CFD solver adapter or volume meshing.
- Changing existing STL display/export semantics by default.
- Claiming measured accuracy for closed-volume hydrostatics.
- Solving cockpit/coaming flooding, paddler body volume, or deck openings.

## Dependencies

- RFC 0010 for mesh diagnostics, readiness levels, and solver profile naming.
- RFC 0014 for the requirement that high-angle GZ use a named closed body.
- RFC 0015 for dispatch gating against `watertight_solid_resistance_v1`.
- A decision on RFC 0004 plumb-stem and end-cap semantics.

## Proposal

Add a closed-volume geometry layer distinct from the display mesh:

```python
ClosedVolumeBody(
    body_id: str,
    source_hull_hash: str,
    coordinate_system: str,
    units: str,
    surfaces: list[ClosedSurfacePart],
    closure_policy: ClosedVolumeClosurePolicy,
    diagnostics: ClosedVolumeDiagnostics,
)
```

The initial body should be an evaluation body derived from the parametric hull
and deck definitions, not a solver-specific case directory. It may later feed a
mesh package, but it must stand on its own as the named body used for volume and
heel integration.

Closure policy records:

- whether the deck is included;
- how bow and stern are capped;
- how the sheerline join is constructed;
- whether the waterline is only metadata or a cut boundary;
- tolerances for vertex welding, face degeneracy, and signed volume checks.

Diagnostics report signed volume, boundary edges, nonmanifold edges,
self-intersection checks when available, part list, and coordinate bounds. A
body may be available for `closed_volume_candidate` calculations before it is
accepted as `cfd_ready` for any watertight solver profile.

## Acceptance Criteria

- A closed-volume body format and manifest are documented and serializable.
- Diagnostics reject open surfaces and report closure failures explicitly.
- The closed-volume body is separate from current display meshes and mesh
  package surfaces.
- End-cap and sheerline closure choices are recorded in metadata.
- The default generated hull can be evaluated for closure diagnostics without
  changing current STL export behavior.
- Tests cover a valid synthetic closed body, an open body, and a nonmanifold
  body.

## Open Questions

- Should the first accepted body include a deck surface, or be a hull-only
  evaluation body capped at a chosen sheerline?
- What exact plumb-stem policy from RFC 0004 should become canonical?
- Is a triangle-mesh body sufficient, or should the closed body retain station
  curves for more stable hydrostatic integration?
- Should `closed_volume_candidate` be a new readiness level or a named profile
  under the existing mesh-readiness model?

## Implementation Path

- Step 1 - Record the closure policy decision for bow, stern, deck join, and
  sheerline semantics.
- Step 2 - Add closed-volume body, part, policy, and diagnostics data models.
- Step 3 - Add a deterministic body builder behind an opt-in API and CLI check.
- Step 4 - Add synthetic validation fixtures before using generated hulls as
  acceptance evidence.
- Step 5 - Wire successful diagnostics into future high-angle stability and
  watertight CFD work only by explicit dependency.

## Domain Modeling

`ClosedVolumeBody` is a value object derived from the `Hull` aggregate for
evaluation and solver boundaries. It clarifies the boundary between authored
hull parameters, display geometry, and downstream physical calculations.
