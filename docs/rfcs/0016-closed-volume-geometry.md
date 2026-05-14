# RFC 0016: Closed-Volume Geometry

Status: landed synthetic-contract safe-slice
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

Add a closed-volume geometry layer distinct from the display mesh. Workflow
0027 may land only the ledger-constrained safe slice: serializable explicit
synthetic triangle-mesh bodies, diagnostics for valid/open/nonmanifold
synthetic fixtures, and evidence-based dispatch rejection for forged
watertight readiness. It must not claim generated hull-plus-deck closure or
`cfd_ready` handoff.

The safe-slice body type is explicitly synthetic:

```python
ClosedVolumeBody(
    body_id: str,
    body_type: Literal["explicit_synthetic_triangle_mesh"],
    policy: ClosedVolumePolicy,
    parts: tuple[ClosedSurfacePart, ...],
)
```

The synthetic policy records `profile_name =
"explicit_synthetic_closed_volume_v1"`, `waterline_semantics =
"metadata_only"`, `cap_policy = "not_applicable_explicit_mesh"`,
`deck_join_policy = "not_applicable_explicit_mesh"`, `normal_orientation =
"outward_positive_signed_volume"`, and `cfd_readiness_policy =
"never_claim_cfd_ready"`. Diagnostics are serializable and authoritative only
for the assembled synthetic body. Acceptance as `closed_volume` requires zero
body-level raw or tolerance-welded boundary edges, zero body-level raw or
tolerance-welded nonmanifold edges, no nonfinite/invalid/degenerate geometry,
and positive signed volume above the serialized signed-volume tolerance.

The future generated-body contract remains separate:

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

The eventual generated evaluation body must be derived from the parametric hull
and deck definitions, not a solver-specific case directory. It may later feed a
mesh package, but it must stand on its own as the named body used for volume and
heel integration. That generated body is deferred until the policy decisions
below are fully specified.

Closure policy records:

- whether the deck is included;
- how bow and stern are capped;
- how the sheerline join is constructed;
- whether the waterline is only metadata or a cut boundary;
- tolerances for vertex welding, face degeneracy, and signed volume checks.

Diagnostics report signed volume, boundary edges, nonmanifold edges,
self-intersection checks when available, part list, and coordinate bounds.
Diagnostics must echo the exact tolerances used, including vertex welding,
degenerate face area, cap/join matching when applicable, self-intersection
availability/status, and signed-volume tolerance. A body may be available for
closed-volume diagnostics before any future solver profile consumes it, but the
workflow 0027 safe slice never promotes a body to `cfd_ready`.

Generated hull-plus-deck closed bodies and any `cfd_ready` handoff are
explicitly deferred until all of the following are specified and tested:

- bow and stern cap policy;
- exact plumb endpoint semantics;
- sheerline and deck-join behavior, including `beam_wl_m != beam_oa_m`;
- waterline semantics as metadata or geometric cut boundary;
- outward normal orientation;
- positive signed-volume acceptance;
- body-level manifold checks as the only readiness authority;
- serialized closure tolerances for welding, degeneracy, joins/caps, and
  signed volume.

## Acceptance Criteria

- A closed-volume body format and manifest are documented and serializable.
- Diagnostics reject open surfaces and report closure failures explicitly.
- The closed-volume body is separate from current display meshes and mesh
  package surfaces.
- The synthetic safe slice records explicit non-applicable cap/deck policies
  and `never_claim_cfd_ready` metadata.
- Synthetic diagnostics require zero body-level boundary/nonmanifold edges and
  positive signed volume for `closed_volume` readiness.
- Generated mesh packages remain open-surface artifacts and are not relabeled
  as closed-volume or `cfd_ready` outputs.
- Dispatch preparation rejects forged or hand-edited watertight manifests whose
  readiness evidence does not satisfy the selected solver profile.
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

- Step 1 - Land serializable synthetic closed-volume body, part, policy, and
  diagnostics data models.
- Step 2 - Add synthetic validation fixtures for valid, open, and nonmanifold
  explicit triangle meshes.
- Step 3 - Add evidence-based dispatch rejection for forged watertight
  readiness manifests.
- Step 4 - Record the generated-body closure policy decision for bow, stern,
  deck join, sheerline, waterline, normals, signed volume, body-level manifold
  authority, and serialized tolerances.
- Step 5 - Add a deterministic generated-body builder only after Step 4 is
  complete.
- Step 6 - Wire successful generated-body diagnostics into future high-angle
  stability and watertight CFD work only by explicit dependency.

## Domain Modeling

`ClosedVolumeBody` is a value object derived from the `Hull` aggregate for
evaluation and solver boundaries. It clarifies the boundary between authored
hull parameters, display geometry, and downstream physical calculations.
