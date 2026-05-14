# RFC 0021: Closed-Volume Self-Intersection Diagnostics

Status: landed synthetic-diagnostic
Date: 2026-05-13
Context: follows RFC 0016 closed-volume geometry and workflow 0027 findings.

Implementation note (workflow 0032, 2026-05-13): the explicit synthetic safe
slice has landed as
`explicit_synthetic_closed_volume_self_intersection_v1`. It remains
diagnostic-only: no generated hull-plus-deck closed body, geometry repair,
volume mesh, high-angle `GZ` handoff, or `cfd_ready` promotion landed.

## Problem

RFC 0016 landed a conservative closed-volume safe slice for explicit synthetic
triangle meshes. The current diagnostics can reject open, nonmanifold,
degenerate, nonfinite, and negative-volume bodies, but they do not define what
to do when a closed manifold intersects itself.

A self-intersecting body can pass edge-manifold checks while still being
unsuitable for displaced-volume integration, high-angle stability, or future
solid meshing. The project needs a clear diagnostic policy before generated
hull-plus-deck bodies are introduced.

## Goals

- Define a project-owned policy for reporting closed-body self-intersections.
- Apply the policy to explicit synthetic closed bodies and future generated
  closed bodies.
- Keep self-intersection diagnostics separate from CFD readiness claims.
- Make diagnostic availability, algorithm limits, and tolerances explicit in
  serialized output.
- Preserve RFC 0016's rule that generated open-surface mesh packages are not
  relabeled as closed-volume or `cfd_ready` artifacts.

## Non-Goals

- Implementing generated hull-plus-deck closed-body construction.
- Promoting any generated hull to `cfd_ready`.
- Implementing a real CFD solver adapter, volume mesher, or repair tool.
- Guaranteeing exact computational-geometry completeness for all degenerate
  triangle arrangements in the first implementation.
- Treating visual overlap in display STL output as physical-body readiness.

## Proposal

Add self-intersection status to closed-volume diagnostics. The status is
body-level evidence, not a display hint and not a solver-readiness override.

The serialized diagnostic result records:

- `self_intersection_status`: `not_checked`, `passed`, `failed`, or
  `inconclusive`;
- `self_intersection_algorithm`: a stable implementation identifier;
- `self_intersection_tolerance_m`: the tolerance used to classify near-contact;
- `self_intersection_pair_count`: the number of intersecting triangle pairs
  when available;
- optional bounded examples of intersecting triangle references for debugging.

`closed_volume` readiness requires a successful self-intersection check once
the check is available for the body type under evaluation. Until then,
diagnostics may remain `invalid` or a narrower implementation-specific
candidate status, but they must not silently pass a body as ready while
omitting the check. Explicit synthetic fixtures may keep existing behavior only
if the diagnostic record says `not_checked` and the policy version remains the
older RFC 0016 profile.

The first algorithm is conservative: it uses deterministic broad-phase
bounding boxes and triangle-pair checks. Adjacency exclusions come from the
assembled body after the vertex-weld tolerance is applied. Shared-edge
neighbors are skipped. Vertex-only pairs are skipped only when the welded
assembled topology proves the faces belong to the same local vertex fan;
disconnected vertex-only pinches are reported as blocking contact. `failed`
and `inconclusive` both block closed-volume readiness for any new profile that
requires this RFC.

The serialized `self_intersection_tolerance_m` is used to expand broad-phase
boxes and classify close non-adjacent pairs after exact contact/crossing
checks. Non-adjacent coplanar overlap, coplanar touch, edge/point touch, and
crossing classify as `failed`. Non-adjacent pairs closer than the tolerance
without detected contact classify as `inconclusive`.

Self-intersection diagnostics must treat parts as one assembled body. A deck
triangle intersecting a hull triangle is a body failure even if each individual
part is locally manifold. The report should still include per-part summaries
when they help identify the source of the failure.

## Readiness Policy

This RFC does not create `cfd_ready` evidence. A body that passes closure,
positive signed volume, and self-intersection checks is only eligible for the
closed-volume readiness level defined by the relevant closed-body profile.

Generated hulls remain unavailable for CFD handoff until a later workflow
defines and verifies generated closed-body construction, solver-specific mesh
requirements, and dispatch evidence. Self-intersection success is necessary
future evidence, not sufficient evidence.

## Acceptance Criteria

- Closed-volume diagnostics serialize self-intersection status, algorithm
  identity, tolerance, and intersection counts.
- Tests cover a valid non-self-intersecting synthetic closed body and a closed
  synthetic body with a deliberate self-intersection.
- A detected or inconclusive self-intersection blocks readiness for any new
  closed-volume diagnostic profile that adopts this RFC.
- Existing synthetic RFC 0016 fixtures remain honest about whether
  self-intersections were checked.
- Generated open-surface packages and display STL output are not promoted to
  `closed_volume` or `cfd_ready`.
- Documentation distinguishes self-intersection diagnostics from geometric
  repair and from solver readiness.

## Open Questions

- Should the first implementation depend on a geometry library, or keep a
  small local triangle-intersection implementation for deterministic tests?
  Workflow 0032 chose a small local implementation.
- How many intersecting triangle examples should diagnostics retain before
  truncating the report? Workflow 0032 retained up to eight example pairs.
- Should touching-but-not-crossing coplanar triangles be classified as
  `failed` or `inconclusive` for the first policy version? Workflow 0032
  classifies non-adjacent coplanar touch as `failed`.

## Implementation Path

1. Add self-intersection fields and tolerance metadata to closed-volume
   diagnostics without changing generated hull behavior.
2. Add deterministic explicit synthetic fixtures for pass and fail cases.
3. Gate new-profile closed-volume readiness on the self-intersection result.
4. Document algorithm limits and make ambiguous cases block readiness.
5. Leave generated hull-plus-deck construction and all CFD handoff work to
   RFC 0022 and later solver-profile workflows.
