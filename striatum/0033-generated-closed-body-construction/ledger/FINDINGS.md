# FINDINGS - workflow 0033 generated closed-body construction

Verdict intent: accept_with_findings

This ledger consolidates the three review artifacts for workflow 0033 and
defines the conservative implementation slice for RFC 0022 generated
closed-body construction. It preserves the boundary between closed-volume
evaluation evidence and solver-specific CFD readiness.

## Inputs read

- `AGENTS.md`
- `docs/workflows/0033-generated-closed-body-construction/SOURCES.md`
- `docs/workflows/0033-generated-closed-body-construction/roles/ledger.md`
- `docs/workflows/0033-generated-closed-body-construction/prompts/findings_ledger.md`
- `striatum/0033-generated-closed-body-construction/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0033-generated-closed-body-construction/domain/REVIEW_DOMAIN.md`
- `striatum/0033-generated-closed-body-construction/ops/REVIEW_OPS_TEST.md`
- The RFCs and source/test files listed by `SOURCES.md`, with live-path
  correction where the workflow metadata is stale.

No project implementation source, tests, RFCs, changelog, root operator report,
or Striatum state was changed by this ledger role.

## Sub-agent help used

Four read-only explorer sub-agents were used with disjoint scopes:

- Volta extracted traceability findings from `REVIEW_TRACEABILITY.md`.
- Pascal extracted domain geometry findings from `REVIEW_DOMAIN.md`.
- Kant extracted ops/test findings from `REVIEW_OPS_TEST.md`.
- Mill performed a cross-review consistency and wording-risk pass.

The sub-agents were instructed not to edit files, not to call `striatum`, not to
publish or complete jobs, and not to push branches. Their outputs were used as
independent extraction and deduplication inputs; this ledger was written in the
main ledger role.

## Deduplicated findings

### L1 - High - Workflow source and write-scope metadata are stale

`docs/workflows/0033-generated-closed-body-construction/SOURCES.md` and
`workflow.json` still point to `kayakgen/geometry/lofted_hull.py`,
`kayakgen/domain/hull.py`, and `tests/test_geometry.py`. Those paths do not
exist in this checkout. The live equivalents are `kayakgen/model/geometry.py`,
`kayakgen/model/hull.py`, and `tests/test_geometry_lofted.py`.

The implementation job write scope also allows `kayakgen/domain/` and
`kayakgen/geometry/` but not the live `kayakgen/model/` package. This is a
workflow metadata blocker: implementation should not be forced into duplicate
packages. The ledger role is not authorized to edit those files, so the next
operator/implementation step should repair the workflow metadata before code
work starts.

Review sources: traceability T1, ops/test F1, consistency sub-agent.

### L2 - High - RFC 0022 generated body profile and builder are absent

`generated_hull_plus_deck_closed_body_v1` is currently RFC-only. The current
closed-volume module still accepts only `explicit_synthetic_triangle_mesh`,
keeps synthetic/not-applicable cap and deck policy metadata, and rejects other
body types in `diagnose_closed_volume_body`.

This is expected for the pre-implementation review, but it is the primary
implementation item. The generated profile literal, policy/serialization, body
builder, RFC 0021 self-intersection wiring, and acceptance tests should land
together. Do not add a profile literal as inert scaffolding ahead of the
builder and tests.

Review sources: traceability T2, domain DOM-001/DOM-004, ops/test F2.

### L3 - High - Endpoint rings and bow/stern caps are missing

Current lofted display geometry tapers each open part across stations and does
not produce explicit bow or stern cap surfaces. RFC 0004 deliberately deferred
exact endpoint non-zero area and watertight end-cap semantics; RFC 0022 now
owns that decision.

The generated closed-body builder must own endpoint ring construction rather
than infer closure from display mesh tapering. For plumb or near-plumb
`bow_rake`, it must preserve the nonzero near-end section implied by the plumb
transition and cap it with nondegenerate triangles where geometry supports
that. Cap degeneracy may be reported by tolerance, but if it leaves boundary
edges the body must remain below closed-volume readiness.

Review sources: domain findings 1-2, traceability T4, RFC 0022 caps policy.

### L4 - High - Sheerline/topside/deck join is missing

The current lofted geometry uses `beam_wl_m` for the hull part and
`beam_oa_m` for the deck part. When `beam_wl_m != beam_oa_m`, that creates an
intentional modeling gap between the waterline hull edge and the overall-beam
deck edge in the display surfaces.

The generated closed body must add the missing topside surface from waterline
beam to overall beam and then join the deck at the actual outer sheerline. The
join policy should serialize whether the builder uses exact shared vertices or
tolerance welding, and body-level diagnostics must remain the readiness
authority.

Review sources: domain finding 3, ops/test F2-F3, RFC 0022 sheerline policy.

### L5 - High - Generated diagnostics and policy wiring must be added without CFD promotion

The existing RFC 0016/RFC 0021 diagnostic machinery can be reused, but it is
currently guarded to the explicit synthetic body type. The generated profile
must run body-level boundary, nonmanifold, invalid-index, nonfinite,
degenerate-face, positive signed-volume, outward-normal, and self-intersection
diagnostics.

For the generated profile, `closed_volume` readiness must require a passed RFC
0021 self-intersection result. A negative signed volume is an orientation
failure, not a value to absolutize. `cfd_ready` must remain false, and dispatch
evidence must continue to reject `watertight_solid_resistance_v1` or any
solver profile that requires `cfd_ready`.

Review sources: traceability RFC 0021 matrix, domain DOM-004/DOM-006,
ops/test positive checks.

### L6 - Medium - Generated-body acceptance tests are missing

The implementation needs tests that build generated closed bodies from valid
`Hull` parameters and assert:

- deterministic construction without reading display STL output;
- serialized `generated_hull_plus_deck_closed_body_v1` policy and tolerances;
- default and non-default `bow_rake` endpoint/cap behavior;
- `beam_wl_m != beam_oa_m` topside and sheerline/deck join behavior;
- waterline recorded as metadata only, not a geometric cut;
- outward face orientation and positive signed volume;
- closure, manifoldness, degenerate geometry, and RFC 0021 self-intersection
  diagnostics at body level;
- current display STL and mesh package outputs remain open inspection/export
  artifacts;
- no generated hull is promoted to `cfd_ready`.

Review sources: traceability T3, domain DOM-005, ops/test F3.

### L7 - Medium-Low - Synthetic diagnostic hardening tests remain thin

The closed-volume code reports nonfinite vertices/faces, out-of-range indices,
degenerate faces, boundary edges, nonmanifold edges, signed volume, and
self-intersection status. Current tests cover open, nonmanifold, reversed
orientation, out-of-range indices, and self-intersection cases, but do not
directly test nonfinite closed-volume input, degenerate-face rejection, or exact
custom tolerance preservation after JSON serialization.

This is not part of generated-body construction itself, but it is a low-risk
hardening addition because the generated profile will reuse the same diagnostic
surface.

Review sources: ops/test F4, traceability RFC 0016 matrix.

## Conservative implementation slice

The next implementation should stay inside this slice:

1. Repair workflow-local metadata so required context and write scope point at
   the live `kayakgen/model/` package and `tests/test_geometry_lofted.py`.
2. Add generated closed-body policy/model support for
   `generated_hull_plus_deck_closed_body_v1`, including source hull hash,
   coordinate system, units, waterline metadata, cap policy, join policy,
   tolerances, and `never_claim_cfd_ready` semantics.
3. Build the generated evaluation body deterministically from `Hull` and the
   parametric geometry, not from display STL files or solver case directories.
4. Construct hull, topside, deck, explicit bow/stern caps, and join strips as
   one assembled body with outward-oriented faces.
5. Run RFC 0016 closure/manifold/signed-volume diagnostics and RFC 0021
   self-intersection diagnostics for the generated profile.
6. Add generated-body acceptance tests and the small synthetic diagnostic
   hardening tests listed above.
7. Preserve current display STL and mesh-package behavior as separate open
   surfaces.
8. Preserve dispatch rejection and keep every generated closed-body result
   below `cfd_ready`.

## Explicit deferrals

The following work remains outside workflow 0033's conservative slice:

- solver-specific surface meshing or volume meshing;
- `watertight_solid_resistance_v1` handoff;
- any `cfd_ready` promotion or solver dispatch evidence;
- high-angle stability physics or `GZ` enablement;
- resistance validation or calibrated drag claims;
- geometry repair/healing workflows;
- cockpit openings, flooding, paddler volume, hatches, appendages, or deck
  cutouts;
- changing current display mesh defaults;
- asymmetric bow/stern rake controls.

Safe wording for implementation artifacts is "generated closed-volume
evaluation body", "closed-volume diagnostics passed", or "eligible for
closed-volume evaluation". Avoid "CFD-ready", "solver-ready", "dispatchable",
or "watertight-solid ready" for RFC 0022 results.

## Positive constraints to preserve

- RFC 0022 supersedes only RFC 0016's unresolved generated-body portion. The
  explicit synthetic closed-volume safe slice remains valid.
- Current display STL and mesh package outputs are correctly classified as open
  surfaces or candidates, not generated closed bodies.
- Current closed-volume diagnostics and CFD dispatch paths do not overclaim
  `cfd_ready`.
- RFC 0021 self-intersection diagnostics are diagnostic evidence for
  closed-volume readiness only; they are not repair or solver-readiness logic.

## Handoff

Proceed to implementation only after the operator validates this ledger and
repairs or explicitly authorizes repair of the stale workflow metadata. The
implementation gate should require generated-body tests before accepting the
profile as closed-volume evidence.
