author: operator [self-declared: operator-0027-ledger]

# Workflow 0027 Findings Ledger

## Gate result

Gate result: needs_revision for generated closed-volume implementation and any
`cfd_ready` handoff.

The operator override to `accept_with_findings` is only a consolidation
mechanism for this ledger. It does not downgrade the domain/geometry and
ops/test blockers. RFC 0016 may proceed only for contract scaffolding,
serialization boundaries, diagnostics, and synthetic fixtures that do not claim
generated hull-plus-deck closure or solver readiness.

## Consolidated findings

### F-001 - RFC 0016 must name the first closed body before implementation

Sources: T-001, D-001, D-006.

Required RFC 0016 policy amendment before implementation: record a single
initial closed-body policy. It must state whether the accepted body is
`hull_plus_deck_closed` or `hull_only_capped`, name every included surface, and
declare whether the design waterline is metadata only or a geometric cut
boundary. Downstream signed-volume, high-angle stability, and readiness
consumers may only consume that named body.

### F-002 - Bow and stern cap semantics remain a hard policy gate

Sources: T-001, D-002.

Required RFC 0016 policy amendment before implementation: define canonical bow
and stern cap construction, including plumb-stem behavior. The policy must say
whether caps are vertical planar stem faces, fan caps from the final
non-degenerate station, zero-area parametric closure points plus separate caps,
or another deterministic polygon. It must also define how `bow_rake = 0.0`,
`bow_rake = 1.0`, intermediate values, and exact `x = +/-L/2` stations are
handled.

### F-003 - Sheerline, deck join, and beam mismatch need explicit geometry

Sources: D-003.

Required RFC 0016 policy amendment before implementation: define the closure
rule that joins hull and deck. At minimum it must identify source curves,
state whether `beam_wl_m != beam_oa_m` creates topside side panels, set join
tolerances, and make unmatched join vertices a deterministic diagnostic result
instead of implicit mesh behavior.

### F-004 - Closed-body diagnostics must be body-level, oriented, and policy-owned

Sources: D-004, D-005, D-007, O-003.

Required RFC 0016 policy amendment before implementation: define outward normal
orientation, signed-volume acceptance, body-level manifold checks, and
serialized closure tolerances. Diagnostics must echo the exact tolerances used,
including vertex welding, degenerate face area, cap/join matching,
self-intersection availability/status, and signed-volume tolerance.

Safe-now implementation requirement: when diagnostics are added, report both
individual `ClosedSurfacePart` checks and authoritative assembled
`ClosedVolumeBody` checks. Include raw and tolerance-welded boundary-edge
counts, nonmanifold-edge counts, part attribution for failed edges, positive
signed volume for outward normals, and profile identity in serialized
diagnostics.

### F-005 - Closed-volume artifacts must stay separate from display STL packages

Sources: T-002, D-008, O-001.

Safe-now implementation requirement: introduce a distinct closed-volume
body/manifest/diagnostics boundary. Do not satisfy RFC 0016 by relabeling
current `hull.stl` plus `deck.stl`, changing `write_mesh_package()` to mark
existing open surfaces as `cfd_ready`, or reinterpreting solver case
directories as the closed source of truth. A later mesh package may reference a
closed-body artifact only through an explicit manifest boundary.

### F-006 - RFC 0006 validity/advisory status must be visible in closed-body metadata

Sources: T-003.

Safe-now implementation requirement: closed-volume metadata or diagnostics must
record enforced model checks, advisory RFC 0006 range warnings, unsupported
shape parameters, and whether displacement/system-weight matching was evaluated
or left to a caller-supplied load case. The contract should not reject every
out-of-class exploratory hull, but it must not hide constraint status.

### F-007 - Dispatch readiness must be evidence-based for watertight profiles

Sources: T-004, O-002, O-003.

Safe-now implementation requirement: any successful closed-volume diagnostic
handoff into mesh or dispatch readiness must use a named profile transition
backed by tests. Dispatch preparation for watertight profiles must parse
referenced quality or closed-volume diagnostics and reject forged or
hand-edited manifests whose boundary, nonmanifold, closure-policy, profile, or
readiness evidence does not satisfy the selected solver profile. Add a
regression fixture where a forged `cfd_ready`
`watertight_solid_resistance_v1` manifest over current open artifacts is
rejected.

### F-008 - Contract scaffolding and synthetic diagnostics may land now

Sources: T-005, O-001.

Safe-now implementation requirement: RFC 0016 can land serializable closed-body
types, closure-policy metadata fields, manifests, diagnostics that reject open
and nonmanifold bodies, and deterministic synthetic fixtures for valid, open,
and nonmanifold bodies. This evidence must be reported separately from any
generated hull-plus-deck success claim.

### F-009 - CLI and status surfaces need broader rejection coverage

Sources: O-004, T-004.

Safe-now implementation requirement: add CLI regression coverage for unknown
mesh and CFD solver profiles, missing `manifest.json`, missing referenced
artifacts, malformed manifests, invalid CFD numeric inputs, and closed-volume
diagnostic rejection wording. Existing and new CLI/status wording must continue
to describe CFD job output as raw and unvalidated.

### F-010 - Generated-body success and readiness handoff are explicitly deferred

Sources: T-004, T-005, D-001 through D-007, O-001.

Explicitly deferred work: do not claim a valid default generated
closed-volume body, `cfd_ready` readiness, high-angle `GZ` enablement, real CFD
solver readiness, calibrated drag, final design fitness, volume meshing, or
validated solver output until the RFC 0016 policy amendments above are recorded
and tests prove generated geometry closure against them.

## A. Safe-now implementation requirements

- F-004: add body-level, oriented, profile-scoped diagnostics once the
  diagnostic artifact exists.
- F-005: keep closed-volume artifacts separate from display STL packages and
  solver case directories.
- F-006: record RFC 0006 enforced/advisory/unsupported validity status.
- F-007: make watertight dispatch readiness evidence-based and reject forged
  readiness manifests.
- F-008: land serializable contract scaffolding and synthetic valid/open/
  nonmanifold diagnostics without generated-body success claims.
- F-009: broaden CLI failure-mode and rejection-wording coverage.

## B. Required RFC 0016 policy amendments before generated-body implementation

- F-001: name the initial closed body and waterline semantics.
- F-002: define bow/stern cap construction and plumb endpoint handling.
- F-003: define sheerline/deck join behavior, including `beam_wl_m !=
  beam_oa_m`.
- F-004: define normal orientation, signed-volume acceptance, body-level
  manifold authority, and serialized closure tolerances.

## C. Explicitly deferred work

- F-010: generated default hull-plus-deck closed-body success.
- F-010: any `cfd_ready` handoff based on generated geometry.
- F-010: high-angle `GZ` or secondary-stability enablement from the generated
  body.
- F-010: real CFD adapters, calibrated drag, final design fitness, volume
  meshing, or validated solver-output claims.
