Verdict intent: accept_with_findings

# REVIEW_TRACEABILITY — workflow 0033 generated closed-body construction

Role: `reviewer_traceability`
Lane/model: `claude / Claude Opus 4.7`
Artifact path: `striatum/0033-generated-closed-body-construction/traceability/REVIEW_TRACEABILITY.md`
Workflow scope: pre-implementation traceability for RFC 0022 generated `generated_hull_plus_deck_closed_body_v1`, mapped against RFC 0004 (plumb bow), RFC 0016 (closed-volume safe slice), RFC 0021 (self-intersection diagnostics), and the deferral surface left after workflows 0027/0032.

## Sub-agent help used

This CLI invocation performed the review directly without spawning sub-agents. The scope was small and well-bounded — four RFCs against one production module (`kayakgen/eval/closed_volume.py`), one geometry module (`kayakgen/model/geometry.py`), three test modules, and the two peer review artifacts already in this workflow — so an independent main-thread read was the most efficient way to keep verification disjoint from `reviewer_domain_geometry` and `reviewer_ops_test` without duplicating their grep traces. I cross-checked the peer artifacts after independently confirming each claim against source. No project code, no `striatum` calls, no `OPERATOR_REPORT.md` mutations, no artifact publication.

## Supersession check — RFC 0022 vs RFC 0016

RFC 0022 (`docs/rfcs/0022-generated-closed-body-construction.md:3-5,40-44`) declares itself a supersession of only the *unresolved generated-body portion* of RFC 0016, and explicitly leaves the explicit-synthetic safe slice (`explicit_synthetic_closed_volume_v1`) intact. RFC 0016 (`docs/rfcs/0016-closed-volume-geometry.md:46-95,112-124`) lists exactly the deferral set RFC 0022 closes (bow/stern cap policy, plumb endpoints, sheerline/deck join including `beam_wl_m != beam_oa_m`, waterline metadata vs cut, outward normals, signed-volume acceptance, body-level manifold authority, serialized tolerances). The supersession boundary is honest: nothing in RFC 0022 retracts safe-slice contracts, dispatch rejection, or non-applicable cap/deck metadata. RFC 0022 §"Non-Goals" (`:32-38`) and §"Readiness Policy" (`:130-135`) restate that `cfd_ready`, `watertight_solid_resistance_v1`, solver-specific meshing, and high-angle stability stay deferred — matching the workflow 0027 operator-report ledger and the workflow 0032 RFC 0021 status note (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:5-12`).

## Requirements → evidence matrix

### RFC 0004 (plumb-bow `bow_rake`)

| RFC 0004 requirement | Current code | Tests / docs | Status / deferral |
| --- | --- | --- | --- |
| `bow_rake` parameter on hull, default 1.0 (legacy raked behavior preserved) | `kayakgen/model/hull.py:43` (`bow_rake: float = Field(default=1.0, ge=0, le=1, …)`) and shim at `generator.py:26,37` | `tests/test_plumb_bow.py:33-112` and golden tests pin default behavior | Landed (legacy unchanged). |
| Blended end-decay; near-plumb keeps non-zero inboard section through the 5% transition zone | `kayakgen/model/geometry.py:131-171` (`_plumb_transition_decay`, `_end_decay`) | `tests/test_plumb_bow.py:43,55,64` | Landed inside transition zone; exact `x = ±L/2` non-zero closure deferred to RFC 0022 (this workflow). |
| Watertight closed hull-plus-deck STL acceptance | Not implemented. `LoftedHullGeometry.mesh()`/`generate_stl()` (`kayakgen/model/geometry.py:215-244,299-306`) writes one open part at a time. | None. | Deferred — explicitly handed off to RFC 0022 generated closed-body construction. Traceability OK: the deferral is named and owned. |
| Explicit end-cap polygons / nonzero area at endpoints | Not implemented. | None. | Deferred — RFC 0022 §"Bow and Stern Caps" (`:63-78`) takes ownership. Traceability OK. |
| Asymmetric bow/stern rake | Not implemented; RFC 0022 explicitly defers (`:75-78`) | None. | Deferred to a future RFC; consistent across documents. |

### RFC 0016 (closed-volume safe slice)

| RFC 0016 requirement | Current code | Tests / docs | Status / deferral |
| --- | --- | --- | --- |
| Synthetic body model with explicit `body_type`, profile metadata, non-applicable cap/deck policies, `never_claim_cfd_ready` | `kayakgen/eval/closed_volume.py:16-76,104-113` (`ClosedVolumeBody`, `ClosedVolumePolicy` with `not_applicable_explicit_mesh`, `cfd_readiness_policy="never_claim_cfd_ready"`) | `tests/test_closed_volume.py:70-102` asserts every required policy field after JSON round-trip | Landed. |
| Body-level boundary/nonmanifold/welded checks, signed-volume positivity, degenerate/nonfinite rejection | `kayakgen/eval/closed_volume.py:228-304,1074-1099` | `tests/test_closed_volume.py:286-346` (open, nonmanifold, reversed orientation, out-of-range indices) | Landed. **Coverage gap (carry forward from F4 of ops/test peer review):** no direct test of nonfinite-vertex/face or degenerate-face rejection paths, and tolerance preservation after serialization is not asserted. |
| Generated mesh packages remain open-surface, not relabeled as `closed_volume`/`cfd_ready` | `kayakgen/eval/mesh_package.py:90-169` keeps `stl_surface`/`cfd_surface_candidate` only; watertight profile is explicitly rejected with `current package writer emits separate open surfaces` warning (`:154-166`) | `tests/test_mesh_package.py` (per peer review F3) | Landed and honest. |
| Evidence-based dispatch rejection for forged watertight manifests | `kayakgen/eval/closed_volume.py:307-325` (`dispatch_evidence_satisfies_profile` always returns `False`); `kayakgen/eval/cfd/jobs.py:494,522,559-568` wires that into dispatch gating | `tests/test_cfd_jobs.py` (per workflow 0027 ledger and peer review) | Landed. |
| Generated hull-plus-deck closure | Deferred until RFC 0022 + tests land. | None in production. | Deferred — RFC 0022 ownership. Traceability OK. |

### RFC 0021 (self-intersection diagnostics)

| RFC 0021 requirement | Current code | Tests / docs | Status / deferral |
| --- | --- | --- | --- |
| Diagnostics serialize `self_intersection_status`, algorithm id, tolerance, pair count, bounded example pairs | `kayakgen/eval/closed_volume.py:18-37,142-206,265-304` | `tests/test_closed_volume.py:70-258` covers passed, failed (edge-manifold and cross-part), vertex-only pinch, near-contact (inconclusive with capped examples), JSON round-trip, and validator rejection of forged closed-volume readiness without a passed check | Landed. |
| RFC 0021 profile required check; RFC 0016 fixtures stay honest as `not_checked` | `kayakgen/eval/closed_volume.py:62-91,1102-1106` (`_policy_requires_self_intersection`, `explicit_synthetic_self_intersection_policy`); model validator at `:195-206` blocks closed-volume readiness without `passed` when the profile requires it | `tests/test_closed_volume.py:240-258` (`test_rfc0021_profile_rejects_serialized_closed_volume_without_passed_check`) | Landed. |
| Generated hull-plus-deck closed-body construction stays deferred | Body type still locked to `explicit_synthetic_triangle_mesh` (`kayakgen/eval/closed_volume.py:16-17,228-234`) | RFC 0021 §"Implementation Path" item 5 (`:131-133`) explicitly defers to RFC 0022 | Deferred. Consistent. |

### RFC 0022 (generated `generated_hull_plus_deck_closed_body_v1`) — the subject of this workflow

| RFC 0022 requirement | Current code | Tests / docs | Status / deferral |
| --- | --- | --- | --- |
| Generated body profile name `generated_hull_plus_deck_closed_body_v1` | Not present. `ClosedVolumeBodyType` literal accepts only `"explicit_synthetic_triangle_mesh"` (`kayakgen/eval/closed_volume.py:17`) and `diagnose_closed_volume_body` rejects other body types (`:228-234`) | RFC text only | **Open — primary ledger item for the implementation phase.** |
| Deterministic builder from parametric `Hull` (not from display STL) | Not present | None | Open. |
| Explicit bow/stern caps with plumb-endpoint handling | Not present. Geometry still tapers to zero-area station at `±L/2` (`kayakgen/model/geometry.py:248,253,279`) | None | Open (peer domain review F1/F2). |
| Sheerline/deck join when `beam_wl_m != beam_oa_m` | Not present. `_half_beam_for_part` (`kayakgen/model/geometry.py:86-94`) splits hull/deck half-beams but does not construct join strips | None | Open (peer domain review F3). |
| Waterline as metadata only, not a geometric cut | Policy already `waterline_semantics="metadata_only"` on the safe slice (`kayakgen/eval/closed_volume.py:64`); RFC 0022 keeps the same posture | None for generated body | Policy in place; generated profile not yet wired. |
| Outward normals + positive signed volume | Signed-volume sign and outward-normal requirement enforced for any closed-volume body (`kayakgen/eval/closed_volume.py:1065-1094`); reversed-orientation test already pins the rule (`tests/test_closed_volume.py:320-331`) | Reusable for generated profile when builder lands | Mechanism ready; awaits generated builder. |
| Body-level diagnostics including RFC 0021 self-intersection for generated body | Diagnostics pipeline is body-type agnostic at the algorithm level but gated by the body-type guard (`:228-234`); broadening will require widening the literal and the profile policy | None for generated body | Open. |
| Display STL stays separate from evaluation-body construction | Display STL path (`kayakgen/model/geometry.py:215-244,299-306`) and mesh package writer (`kayakgen/eval/mesh_package.py:90-169`) remain open-surface only | `tests/test_mesh_package.py` | Currently honest by virtue of the generated builder not existing yet. The implementation phase must keep this separation explicit. |
| No promotion to `cfd_ready` | `ClosedVolumeDiagnostics.cfd_ready: Literal[False]` (`kayakgen/eval/closed_volume.py:193`); dispatch validator hard-coded to `return False` (`:307-325`); CFD jobs route to the safe-slice validator (`kayakgen/eval/cfd/jobs.py:494-568`) | `tests/test_cfd_jobs.py` (per workflow 0027) | Holds. No accidental solver-readiness expansion observed in this workflow. |
| RFC 0016 safe-slice continues unchanged | Untouched in current diffs | All RFC 0016 tests still pass per peer ops/test review verification (`192 passed`) | Holds. |

## Accidental solver-readiness expansion check

Explicit hunt for backsliding into `cfd_ready`, `watertight_solid_resistance_v1`, or high-angle GZ promotion:

- `ClosedVolumeDiagnostics.cfd_ready` is `Literal[False]` (`kayakgen/eval/closed_volume.py:193`); Pydantic forbids any other value at deserialization time. No alternative serializer constructs the field.
- `dispatch_evidence_satisfies_profile` parses the manifest then *always* returns `False` (`kayakgen/eval/closed_volume.py:307-325`). The function intentionally validates first so dispatch can distinguish contract-aware rejection from blind manifest trust, but it never accepts.
- `kayakgen/eval/cfd/jobs.py:494-568` routes `cfd_ready`-requiring profiles to the closed-volume validator and accepts its `False` verdict.
- `kayakgen/eval/mesh_package.py:127-169` clamps watertight-profile packages to `stl_surface` with explicit `current package writer emits separate open surfaces` reasoning; no promotion path.
- RFC 0022 §"Readiness Policy" (`:130-135`) and §"Non-Goals" (`:32-38`) reinforce in documentation that successful generated closed-body diagnostics are only a *closed-volume* readiness level, never solver dispatch.
- The workflow 0032 status note on RFC 0021 (`:5-12`) explicitly states no generated-body or `cfd_ready` promotion landed.

**No accidental solver-readiness expansion found in this RFC bundle or in the current code.** The new RFC 0022 vocabulary stays inside the closed-volume readiness layer.

## Cross-reference to peer reviews in this workflow

- Domain review (`striatum/0033-generated-closed-body-construction/domain/REVIEW_DOMAIN.md`) accepts the RFC 0022 policy with implementation findings on missing caps, unresolved plumb endpoints, unjoined sheerlines, generated-body test gap, and display-separation enforcement. All five findings map cleanly onto the deferral entries in the matrix above and should be carried into the findings ledger.
- Ops/test review (`striatum/0033-generated-closed-body-construction/ops/REVIEW_OPS_TEST.md`) records four findings: F1 stale workflow `SOURCES.md`/`workflow.json` paths and write-scope, F2 RFC 0022 generated body not yet built, F3 missing generated-body fixture coverage, F4 synthetic diagnostic test-coverage gaps. Independently verified each below.

## Traceability findings to carry into the ledger

### T1 — Stale workflow `SOURCES.md` and write scope (High)

`docs/workflows/0033-generated-closed-body-construction/SOURCES.md:9-12` lists `kayakgen/eval/closed_volume.py`, `kayakgen/geometry/lofted_hull.py`, `kayakgen/domain/hull.py`, `generator.py`, `tests/test_closed_volume.py`, `tests/test_geometry.py`, `tests/test_mesh_package.py`. Three of these do not exist in the current checkout: `kayakgen/geometry/lofted_hull.py` is now `kayakgen/model/geometry.py`, `kayakgen/domain/hull.py` is now `kayakgen/model/hull.py`, and `tests/test_geometry.py` is now `tests/test_geometry_lofted.py`. This duplicates ops/test F1 and matters for traceability because reviewers and implementers loading `SOURCES.md` will miss the live geometry/hull modules and the lofted-geometry test, and the workflow's write-scope (`workflow.json:176-183` per peer review) would push implementation into ghost packages. **Action for ledger:** correct `SOURCES.md` and `workflow.json` to point at `kayakgen/model/geometry.py`, `kayakgen/model/hull.py`, and `tests/test_geometry_lofted.py`, and widen the implementation write scope to include `kayakgen/model/`.

### T2 — Generated-body profile is RFC-only; no code or tests yet (High, expected for pre-implementation)

`generated_hull_plus_deck_closed_body_v1` appears only in the RFC text (`docs/rfcs/0022-generated-closed-body-construction.md`) and the workflow review logs. The closed-volume module still hard-rejects any body type other than `"explicit_synthetic_triangle_mesh"` (`kayakgen/eval/closed_volume.py:16-17,228-234`). This is the correct state for a pre-implementation traceability review, but it must remain the primary ledger item moving into implementation. **Action for ledger:** widen `ClosedVolumeBodyType` and `ClosedVolumePolicy.profile_name` enum to admit the generated profile *only when* the builder, RFC 0021 self-intersection wiring, and acceptance tests land together; do not add the literal as scaffolding ahead of the builder.

### T3 — Acceptance tests for generated body, caps, plumb endpoints, and `beam_wl_m != beam_oa_m` sheer joins are missing (Medium)

RFC 0022 acceptance criteria (`:139-152`) require tests for default and non-default `bow_rake`, `beam_wl_m != beam_oa_m`, waterline-as-metadata, outward normals, positive volume, body-level diagnostics, and display-STL separation. None of those tests exist. `tests/test_plumb_bow.py` covers RFC 0004 plumb behavior on the open lofted geometry but does not assert any closure or cap. **Action for ledger:** require those tests to land with the builder, not after. Reuse the existing self-intersection fixtures and signed-volume assertions where possible.

### T4 — RFC 0004 plumb-stem deferrals correctly forwarded to RFC 0022 (informational)

RFC 0004's status notes (`:6-15,17-25`) and acceptance section (`:138-148`) explicitly defer exact endpoint non-zero area, explicit end-cap polygons, and closed/watertight solid readiness to a future end-cap design. RFC 0022 picks these up by name in §"Bow and Stern Caps" (`:63-78`) and §"Acceptance Criteria" (`:139-152`). The chain is intact; no document orphans the deferral.

### T5 — RFC 0016 generated-body deferral list is now fully addressed by an in-scope RFC (informational)

The eight-item deferral list in RFC 0016 (`:112-124`) maps one-to-one onto RFC 0022 sections: cap policy → §"Bow and Stern Caps"; plumb endpoints → same; sheerline/deck join including `beam_wl_m != beam_oa_m` → §"Sheerline and Deck Join"; waterline semantics → §"Waterline Policy"; outward normals → §"Normals and Signed Volume"; positive signed-volume acceptance → same; body-level manifold authority → §"Sheerline and Deck Join" + §"Diagnostics"; serialized closure tolerances → §"Tolerances". No orphans.

### T6 — RFC 0021 self-intersection diagnostics are reusable for the generated body without additional RFC work (informational)

`_diagnose_self_intersections`, the AABB broad-phase, vertex-fan exclusions, and the conservative classification pipeline (`kayakgen/eval/closed_volume.py:530-723`) operate on the assembled body and are body-type agnostic. Once `ClosedVolumeBodyType` admits the generated profile, the RFC 0021 algorithm path can be reused as-is; the RFC 0021 model validator (`:195-206`) will already block closed-volume readiness without a `passed` self-intersection.

## Conclusion

The RFC bundle (0004, 0016, 0021, 0022) is internally consistent. RFC 0022 supersedes exactly the unresolved generated-body portion of RFC 0016, leaves the safe-slice contract untouched, and explicitly forecloses `cfd_ready` promotion in policy, diagnostics, dispatch, and mesh-package paths. No accidental solver-readiness expansion is present in code or in the new RFC text. The remaining gaps are implementation-side: stale `SOURCES.md`/`workflow.json` paths and write-scope (T1, peer F1), the generated-body builder itself (T2, peer F2 / domain F1–F3, F5), acceptance tests for the new contract (T3, peer F3 / domain F4), and small synthetic diagnostic coverage gaps inherited from RFC 0016 (peer F4). All of those belong in the findings ledger as blockers for the implementation phase rather than as reasons to halt the workflow.

Recommended verdict: `accept_with_findings` so the workflow can advance to the findings ledger and consolidate T1–T3 with the domain/ops peer findings before implementation begins.
