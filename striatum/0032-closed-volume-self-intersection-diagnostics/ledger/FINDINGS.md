author: operator [self-declared: operator-0032-ledger]

# Workflow 0032 Findings Ledger

## Gate result

Gate result: accept_with_findings for the conservative RFC 0021 diagnostic
safe slice.

The accepted slice is limited to closed-volume self-intersection diagnostics
for explicit synthetic closed bodies and future named closed bodies. It may
add diagnostic schema, policy/profile identity, deterministic fixtures,
algorithm limits, and readiness gating for closed-volume diagnostics. It must
not build generated hull-plus-deck closed bodies, repair geometry, reinterpret
display STL overlap as physical readiness, or promote any artifact to
`cfd_ready`.

## Consolidated findings

### F-001 - RFC 0021 needs explicit serialized self-intersection evidence

Sources: T-001, O-001.

Accepted finding: the current RFC 0016 diagnostic model can report
`closed_volume` without any self-intersection record. Any profile that adopts
RFC 0021 must serialize the check result instead of letting the absence of a
check pass silently.

Required action: add explicit diagnostic fields for
`self_intersection_status`, `self_intersection_algorithm`,
`self_intersection_tolerance_m`, `self_intersection_pair_count`, and bounded
example triangle-pair references. Preserve `explicit_synthetic_closed_volume_v1`
honestly as the RFC 0016 compatibility profile, where existing fixtures may
record `not_checked`. Introduce or name a new RFC 0021 profile whose
`closed_volume` readiness requires `self_intersection_status == "passed"`.
Missing, `not_checked`, `failed`, or `inconclusive` evidence must not satisfy
that new profile.

### F-002 - Self-intersection authority must be body-level and assembled

Sources: T-002, D-002, O-002.

Accepted finding: self-intersection readiness is a property of the assembled
closed body, not of independent parts. Cross-part penetration must fail the
body even when each part is locally manifold.

Required action: run self-intersection diagnostics on the same assembled body
used for closure, manifold, and signed-volume diagnostics. Per-part summaries
may remain explanatory only. Define self-intersection adjacency from the
assembled closed-body topology after the serialized vertex-weld tolerance is
applied, so legitimate welded seams can be skipped only when the body graph
declares them neighbors. Add fixtures for a valid non-self-intersecting body,
a closed edge-manifold self-intersecting body, and at least one body-level
cross-part failure.

### F-003 - Vertex-only adjacency and pinches must not be skipped blindly

Sources: D-001, D-002.

Accepted finding: skipping every triangle pair that shares a vertex can hide
pinched point-contact bodies that still pass edge-manifold checks. Those
bodies are not valid volume boundaries for displacement, high-angle stability,
or future solid meshing.

Required action: narrow the first algorithm's adjacency exclusion to
policy-declared manifold neighbors, preferably shared-edge neighbors in the
assembled graph. Vertex-only contact between otherwise non-adjacent triangles
must be reported as `failed` or `inconclusive`, unless a vertex-manifold
diagnostic proves the faces belong to one local manifold fan. Add regression
coverage for vertex-only pinches or record an explicit deferral that blocks
readiness for such cases.

### F-004 - Tolerance and ambiguous-contact semantics must be blocking

Sources: D-003, O-003.

Accepted finding: RFC 0021 serializes a self-intersection tolerance but leaves
near-contact and coplanar cases underspecified. For a closed-volume readiness
gate, within-tolerance non-adjacent contact cannot mean pass.

Required action: define `self_intersection_tolerance_m` before coding the
readiness gate. The policy must state whether the tolerance inflates triangle
bounds, measures minimum separation, or only classifies numerical ambiguity
after a crossing test. Non-adjacent coplanar overlap, coplanar touch,
edge/point touch, near-contact, and numerically ambiguous cases must be
serialized as `failed` or `inconclusive`, and both outcomes must block the RFC
0021 closed-volume profile. Add tests proving `failed` and `inconclusive`
cannot satisfy readiness even if the first implementation does not naturally
produce `inconclusive`.

### F-005 - The intersection search needs deterministic bounds

Sources: O-002, O-004, T-005.

Accepted finding: all-pairs triangle checks are enough for tiny fixtures but
too loose as a project-owned diagnostic boundary. Diagnostics also need stable
debug evidence without unbounded output.

Required action: implement a deterministic broad phase before exact or
conservative triangle-pair checks, keep output ordering stable, and cap
serialized example pairs. Count all detected pairs when available, but retain
only the bounded examples required for debugging. Add a focused stress-style
test with many non-overlapping triangles or components to prove the broad
phase returns zero intersections without material runtime growth, and assert
the example list cap.

### F-006 - Passing diagnostics must not become solver readiness

Sources: T-004, O-005.

Accepted finding: RFC 0021 success is necessary future closed-body evidence,
not solver-readiness evidence. The existing contract correctly keeps
`cfd_ready: false` and rejects forged watertight dispatch evidence.

Required action: keep `ClosedVolumePolicy.cfd_readiness_policy` at
`never_claim_cfd_ready`, keep closed-volume diagnostics serialized with
`cfd_ready: false`, and keep watertight dispatch evidence-based. Add a
regression where a valid RFC 0021 diagnostic with
`self_intersection_status == "passed"` still cannot satisfy a
`cfd_ready` watertight solver profile. If a CLI surface is added, generated
open-surface packages and display STL output must remain below
`closed_volume` and `cfd_ready`.

### F-007 - Documentation must describe diagnostics, not repair

Sources: T-005, D-003.

Accepted finding: user-facing and status documentation currently explain the
RFC 0016 synthetic boundary but do not yet describe RFC 0021 status values,
algorithm limits, tolerance semantics, or ambiguous-case behavior.

Required action: update documentation when implementation lands to describe
`not_checked`, `passed`, `failed`, and `inconclusive`; the algorithm identity;
the serialized tolerance; bounded example-pair reporting; and the rule that
`failed` or `inconclusive` blocks only the relevant closed-volume diagnostic
profile. The docs must also state that the diagnostic does not repair
geometry, generate closed hull-plus-deck bodies, or create solver-readiness
evidence.

### F-008 - Generated closed bodies remain outside workflow 0032

Sources: T-003, T-004, O-005.

Accepted finding: the current code correctly has no generated `Hull` to
`ClosedVolumeBody` builder, and generated mesh packages remain open-surface
artifacts. Workflow 0032 must preserve that boundary.

Required action: keep changes inside diagnostic models, policy/profile
metadata, self-intersection algorithms, explicit synthetic fixtures, tests,
and documentation. Do not add generated hull-plus-deck construction, do not
change mesh package classification, do not treat visual display overlap as
physical-body readiness, and do not relax watertight dispatch rejection.

## Safe-now implementation scope

- Add RFC 0021 self-intersection fields, status values, algorithm identity,
  tolerance metadata, pair counts, and bounded example pairs to closed-volume
  diagnostics.
- Preserve an honest RFC 0016 compatibility profile with `not_checked`, and
  gate a new RFC 0021 closed-volume diagnostic profile on `passed`.
- Run diagnostics at assembled-body level, with cross-part failures counted as
  body failures and per-part summaries used only for debugging.
- Define conservative adjacency, vertex-only contact, coplanar, near-contact,
  and ambiguous-case semantics before the readiness gate can pass.
- Add deterministic valid, failed, cross-part, inconclusive/blocking, output
  cap, performance-envelope, serialization, and `cfd_ready` rejection tests.
- Update documentation to distinguish diagnostics from repair, generated
  closed-body construction, and solver readiness.

## Explicitly deferred work

- Generated hull-plus-deck closed-body construction, including bow/stern caps,
  deck/shear joins, waterline cut semantics, and exact plumb-stem/end-cap
  decisions from RFC 0004 and RFC 0016.
- Geometry repair, automatic healing, remeshing, or volume-meshing.
- Any promotion of generated hulls, explicit synthetic diagnostics, display
  STL output, or mesh packages to `cfd_ready`.
- Real CFD adapters, calibrated drag, final design fitness, validated solver
  output, and high-angle `GZ` handoff.
- Exact computational-geometry completeness for every degenerate triangle
  arrangement beyond the conservative status/algorithm/tolerance policy
  implemented for this diagnostic slice.
