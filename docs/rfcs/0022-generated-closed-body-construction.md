# RFC 0022: Generated Hull-Plus-Deck Closed-Body Construction

Status: landed generated-body safe-slice
Date: 2026-05-13
Context: supersedes the unresolved generated-body portion of RFC 0016.

## Problem

RFC 0016 deliberately landed only an explicit synthetic closed-volume safe
slice. It deferred the generated hull-plus-deck body because bow and stern
caps, plumb endpoint behavior, deck joins, waterline policy, normals, signed
volume, and tolerances were not yet specified.

The project now needs one deterministic generated closed body for hydrostatic
and stability evaluation. It must be separate from display STL output and must
not claim CFD readiness.

## Goals

- Define generated hull-plus-deck construction as the next closed-volume body
  profile.
- Resolve bow and stern cap policy, including plumb endpoint semantics.
- Define sheerline and deck-join behavior when `beam_wl_m != beam_oa_m`.
- Record waterline metadata and make the first generated body an uncut full
  hull-plus-deck body.
- Require outward normals, positive signed volume, body-level manifold checks,
  self-intersection diagnostics, and serialized closure tolerances.
- Keep display STL export separate from evaluation-body construction.

## Non-Goals

- Promoting generated bodies to `cfd_ready`.
- Producing solver-specific surface or volume meshes.
- Modeling cockpit openings, paddler body volume, flooding, hatches, or
  appendages.
- Changing current display mesh defaults.
- Validating resistance or high-angle stability physics.

## Supersession

This RFC supersedes the unresolved generated-body portion of RFC 0016. RFC 0016
continues to define the explicit synthetic closed-volume safe slice and its
diagnostics. Generated-body construction should reference this RFC rather than
the deferred bullet list in RFC 0016.

## Proposal

Introduce a generated closed-volume profile named
`generated_hull_plus_deck_closed_body_v1`. The body is derived from the
parametric `Hull` and geometry settings, not from a display STL file or solver
case directory.

The generated body contains:

- a hull surface from keel and waterline station geometry;
- a deck surface from sheerline to deck centerline;
- bow and stern cap surfaces;
- explicit join strips between hull sheer edges and deck sheer edges;
- serialized policy, source hull hash, coordinate system, units, tolerances,
  waterline metadata, and diagnostics.

### Bow and Stern Caps

Caps are generated as explicit surfaces at the forward and aft endpoints of
the body. They close the hull, deck, and sheerline rings into one watertight
body. For `bow_rake = 1.0`, the cap may collapse toward the existing fine end
if the station ring degenerates within tolerance. For near-plumb values, the
cap must preserve the nonzero near-end section implied by the plumb transition
and close it with nondegenerate triangles where geometry supports that.

Exact endpoint semantics are:

- the generated closed body owns its endpoint ring construction;
- endpoint closure is not inferred from display mesh tapering;
- cap triangles may be rejected as degenerate by tolerance, but rejection must
  be reported and must block readiness if it leaves the body open;
- bow and stern use the same policy until a future RFC introduces asymmetric
  endpoint controls.

### Sheerline and Deck Join

The closed body must join the hull and deck at the actual outer sheerline, not
at the waterline. When `beam_wl_m != beam_oa_m`, the builder must construct
the topside surface from waterline beam to overall beam and then join the deck
to the overall-beam sheer edge.

The join policy records whether vertices are shared exactly or welded within
tolerance. Body-level manifold diagnostics, not per-part intent, are the
authority for readiness.

### Waterline Policy

For `generated_hull_plus_deck_closed_body_v1`, the waterline is metadata only.
It records the design/load waterline used by hydrostatic evaluation, but it is
not a geometric cut boundary and does not truncate the closed body. Future
flooded or sliced bodies require a separate profile.

### Normals and Signed Volume

All generated faces must be oriented outward. Readiness requires positive
signed volume greater than the serialized signed-volume tolerance. A negative
volume is an orientation failure, not a value to be absolutized.

### Tolerances

The profile serializes tolerances for vertex welding, degenerate face area,
cap and join matching, self-intersection classification, and signed-volume
acceptance. Diagnostics must echo the exact tolerances used.

### Display STL Separation

Display STL output remains a visual/export artifact. It may share helper code
with generated-body construction, but it is not the source of truth for the
closed evaluation body. Display STL success is not evidence of
`closed_volume`, `generated_closed_body`, or `cfd_ready` readiness.

## Diagnostics

Generated bodies must run the closed-volume diagnostics from RFC 0016 plus the
self-intersection policy from RFC 0021. Acceptance requires:

- zero body-level raw and welded boundary edges;
- zero body-level raw and welded nonmanifold edges;
- zero invalid, nonfinite, or degenerate geometry after policy tolerances;
- no failed or inconclusive self-intersection result;
- positive signed volume with outward normals;
- serialized cap, join, waterline, and tolerance policy metadata.

## Readiness Policy

Successful generated closed-body diagnostics may satisfy a generated
closed-volume readiness level for evaluation workflows. They do not satisfy
`cfd_ready`, `watertight_solid_resistance_v1`, or any solver dispatch profile.
Any CFD handoff must be added by a later RFC with solver-specific evidence and
tests.

## Acceptance Criteria

- A generated closed body can be built deterministically from a valid `Hull`
  without reading display STL output.
- Bow and stern cap construction is explicit and serialized in policy
  metadata.
- Plumb endpoint behavior is tested for default and non-default `bow_rake`
  values.
- The sheerline/deck join works when `beam_wl_m != beam_oa_m`.
- Waterline metadata is recorded without cutting the body.
- Generated faces are outward-oriented and signed volume is positive.
- Body-level diagnostics enforce closure, manifoldness, self-intersection,
  degenerate geometry, and serialized tolerance policy.
- Display STL export remains separate and is not relabeled as closed-body or
  CFD evidence.
- No generated hull is promoted to `cfd_ready`.

## Open Questions

- Should generated bodies retain station-curve provenance in addition to the
  triangle mesh for future hydrostatic integration?
- What default station and circumferential resolution should the generated
  closed-body builder use independently of display mesh resolution?
- Should exact endpoint rings be exposed for review plots before they become
  implementation details?

## Implementation Path

1. Add generated-body policy models and serialization without changing display
   STL defaults.
2. Build hull, topside, deck, join, and endpoint cap surfaces from parametric
   geometry.
3. Add body-level diagnostics, including RFC 0021 self-intersection checks.
4. Add tests for default rake, plumb rake, `beam_wl_m != beam_oa_m`, outward
   normals, positive volume, and display STL separation.
5. Expose generated closed-body diagnostics to evaluation code only as
   closed-volume evidence, not CFD evidence.
