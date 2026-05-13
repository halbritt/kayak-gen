author: operator [self-declared: operator-0032-domain]
run: run_04735e0767704843a93cb507c202231f
job: review_domain
date: 2026-05-13

# Domain Review - Workflow 0032 Closed-Volume Self-Intersection Diagnostics

## Verdict Intent

accept_with_findings

RFC 0021 is directionally honest for closed-volume kayak bodies. It correctly
treats self-intersection as body-level evidence, keeps it separate from display
mesh quality and CFD readiness, and says detected or inconclusive
self-intersections block any new closed-volume profile that adopts the RFC.

The remaining domain risk is not the high-level boundary. It is the exact
geometry policy for exclusions and tolerances. Those details decide whether a
pinched, self-touching, or cross-part-intersecting kayak body can be incorrectly
accepted as a closed volume.

## Findings

### D-001 - Vertex-sharing exclusions can hide non-manifold pinches

RFC 0021 allows the first algorithm to "skip adjacent triangles that share an
edge or vertex" (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:62`).
Skipping edge-adjacent triangles is necessary for an ordinary triangle mesh, but
skipping every vertex-sharing pair is too broad unless the implementation also
checks vertex-manifold topology.

The existing RFC 0016 safe slice and implementation only make edge-manifold
authority explicit: body readiness requires zero raw or welded boundary and
nonmanifold edges (`docs/rfcs/0016-closed-volume-geometry.md:71`), and the
current diagnostic code counts edge multiplicity only
(`kayakgen/eval/closed_volume.py:364`). A closed triangle mesh can still be
edge-manifold while pinching at a single vertex. For a kayak closed body, that
point-contact shape is not a valid volume boundary for displacement, high-angle
stability, or future solid meshing.

Required action: before implementation, narrow the adjacency exclusion or add a
vertex-manifold diagnostic. The policy should either exclude only shared-edge
face pairs, or exclude vertex-sharing pairs only when they belong to a single
local manifold vertex fan. Vertex-only body contacts outside that local fan must
be reported as `failed` or `inconclusive`, and must block closed-volume
readiness.

### D-002 - Cross-part adjacency must use assembled-body topology

RFC 0021 correctly says self-intersection diagnostics must treat all parts as
one assembled body, and that a deck triangle intersecting a hull triangle is a
body failure even if each part is locally manifold
(`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:68`). That rule
needs one more domain constraint: the intersection checker must derive its
adjacency exclusions from the same assembled-body topology used for closure
diagnostics, not from per-part local indices.

Today, explicit synthetic parts are assembled by offsetting each part's vertex
indices (`kayakgen/eval/closed_volume.py:159`), and body closure is evaluated
both raw and tolerance-welded (`kayakgen/eval/closed_volume.py:197`). Future
hull/deck joins may be represented by separate parts whose seam vertices are
coincident or welded by policy, not literally shared before assembly. If the
self-intersection checker uses raw per-part sharing alone, it can misclassify a
valid welded seam as an intersection. If it skips too much cross-part contact,
it can miss a real deck/hull penetration.

Required action: define adjacency for self-intersection checks on the assembled
body after applying the serialized closure/weld tolerance. Cross-part triangle
pairs should be skipped only when the closed-body graph declares them legitimate
neighbors; otherwise cross-part overlap, crossing, or non-adjacent contact must
be `failed` or `inconclusive`.

### D-003 - Near-contact and coplanar tolerance semantics are underspecified

RFC 0021 adds `self_intersection_tolerance_m` as the tolerance used to classify
near-contact (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:49`)
and says ambiguous cases may be `inconclusive`
(`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:63`). It also
leaves touching-but-not-crossing coplanar triangles as an open question
(`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:105`).

For a closed-volume readiness gate, "within tolerance" cannot mean "pass." A
near-contact between non-adjacent hull/deck panels, a coplanar overlap, or a
non-adjacent edge/point touch can make signed volume and downstream solid
meshing ambiguous even when edge counts and signed volume look acceptable.

Required action: define `self_intersection_tolerance_m` before coding the gate.
The policy should state whether tolerance inflates triangle bounds, measures
minimum triangle separation, or only classifies numerical ambiguity after an
exact crossing test. It should also define outcomes for coplanar overlap,
coplanar touch, edge/point touch, and near-miss cases. For non-adjacent
triangles, these cases should block readiness as `failed` or `inconclusive`,
not pass silently.

## Domain-Safe Boundaries To Preserve

- Keep self-intersection diagnostics authoritative only at assembled body level;
  per-part summaries are explanatory, not readiness authority.
- Preserve RFC 0016's separation between explicit synthetic closed bodies,
  future generated closed bodies, display STL/open-surface mesh packages, and
  CFD readiness.
- Keep generated hull-plus-deck construction and all `cfd_ready` claims out of
  this workflow.
