# Domain review - watertight solid mesh profile

author: operator [self-declared: operator-domain-review]
run: run_877488bcf83244479df1d95d7b420a65
job: review_domain
date: 2026-05-13
verdict: accept_with_findings

## Findings

### D-001 - Current hull and deck meshes are separate open surfaces

`LoftedHullGeometry.mesh()` creates longitudinal strips between station slices
for either `hull` or `deck`. It does not generate end-cap polygons, a seam
joining hull to deck, or a single closed body. Existing diagnostics report
boundary edges for both hull and deck. Therefore current output cannot be
classified as watertight or `cfd_ready`.

Required action: keep readiness below `cfd_ready` for current hull/deck
packages.

### D-002 - Exact end-cap and plumb-stem semantics remain deferred

RFC 0004 still defers exact non-zero endpoint area, explicit end caps, and
watertight hull-plus-deck solid readiness. A watertight solid generator would
have to resolve end caps at `x = +/-L/2`, waterline/deck seams, and normal
orientation for a combined body.

Required action: do not implement synthetic closure in this workflow.

### D-003 - A named blocked profile is domain-safe

A watertight-required profile can encode the future contract:
closed volume required, hull/deck accepted as source parts, consistent outward
normals required, no open waterline boundary allowed. For current packages, that
profile should emit blockers rather than success.

Required action: implement a profile boundary and explicit blocked reasons.

## Recommendation

Accept a validation/readiness slice: named watertight-solid profile, explicit
blocked package readiness, tests proving current geometry does not pass. Defer
geometry closure.
