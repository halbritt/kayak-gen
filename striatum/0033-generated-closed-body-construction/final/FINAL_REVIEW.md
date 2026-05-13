I have enough context to write the final review. The implementation cleanly closes all High/Medium findings from the ledger, all 205 tests pass, and the dispatch/`cfd_ready` boundary is preserved.

Verdict intent: accept

# FINAL_REVIEW — workflow 0033 generated closed-body construction

Role: `final_reviewer`
Lane/model: claude / Opus 4.7
Worktree: `/tmp/kayak-gen-ledger-worktrees/0033`
Striatum session: `sess_249526f376e74f26a99b92048064b81b`
Striatum job: `job_run_f33e467413ba4ca2a4e5e794338d9580_final_review`

## Sub-agent help used

No sub-agents were spawned. The review surface is small and well-bounded — one ledger, three peer reviews, one patch summary, one production module (`kayakgen/eval/closed_volume.py`), two test files (one new), one CFD jobs test, and the workflow metadata. The disjoint scopes the operator suggested are already covered by the three first-pass artifacts (`REVIEW_TRACEABILITY.md`, `REVIEW_DOMAIN.md`, `REVIEW_OPS_TEST.md`); the appropriate role here is to read those outputs against the realized diff and verify mechanically, not to re-fan the same searches. Verification was performed directly in this worktree: branch-local diff inspection, full pytest run, and a live REPL smoke check of the builder under default rake, plumb rake, and `beam_wl_m != beam_oa_m`. No project code, RFC text, root operator report, or Striatum state was mutated.

## Inputs read

- `AGENTS.md`
- `docs/workflows/0033-generated-closed-body-construction/SOURCES.md`
- `docs/workflows/0033-generated-closed-body-construction/roles/final_reviewer.md`
- `docs/workflows/0033-generated-closed-body-construction/prompts/final_review.md`
- `docs/workflows/0033-generated-closed-body-construction/workflow.json`
- `docs/rfcs/0022-generated-closed-body-construction.md`
- `striatum/0033-generated-closed-body-construction/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0033-generated-closed-body-construction/domain/REVIEW_DOMAIN.md`
- `striatum/0033-generated-closed-body-construction/ops/REVIEW_OPS_TEST.md`
- `striatum/0033-generated-closed-body-construction/ledger/FINDINGS.md`
- `striatum/0033-generated-closed-body-construction/implementation/PATCH_SUMMARY.md`
- Branch-local diff (`git diff main...HEAD`, 13 files, +1249/-32) and the impacted modules: `kayakgen/eval/closed_volume.py`, `tests/test_closed_volume.py`, `tests/test_generated_closed_body.py`, `tests/test_cfd_jobs.py`, `CHANGELOG.md`.

## Verdict and rationale

The implementation slice landed in commit `6903857` matches the conservative slice in the findings ledger. Every High finding (L1-L5) is closed in code, the Medium findings (L6-L7) are closed in tests, and the gate constraints in `roles/final_reviewer.md` all hold: construction is deterministic, body-level diagnostics are authoritative, display STL stays separate, and no generated body is promoted to `cfd_ready`.

### Ledger findings — closure check

- **L1 (metadata)** closed. `SOURCES.md` and `workflow.json` now point at `kayakgen/model/geometry.py`, `kayakgen/model/hull.py`, `tests/test_geometry_lofted.py`, and the implementation `allowed_paths` write scope has been replaced with `kayakgen/model/`. `python -m json.tool` accepts the workflow file.
- **L2 (RFC 0022 profile and builder)** closed. `kayakgen/eval/closed_volume.py:16-19,42-47,113-121` introduces `generated_hull_plus_deck_closed_body` as a body type, `generated_hull_plus_deck_closed_body_v1` as the profile name, and `generated_hull_plus_deck_policy()` as the policy factory. The `_align_profile_policy` validator (`:93-102`) forces the cap, join, and self-intersection policy onto any body that uses the RFC 0022 profile name, eliminating policy spoofing. The builder `generated_hull_plus_deck_body` (`:299-344`) takes a `Hull`, runs it through `Hull.model_validate`, derives a deterministic mesh from `hull.to_geometry()`, and stamps the body with `source_hull_hash`, `units="m"`, a coordinate system, and `waterline_metadata`. A compatibility alias `generated_hull_plus_deck_closed_body` (`:347-363`) keeps both naming options available.
- **L3 (endpoint rings and bow/stern caps)** closed. `_generated_hull_plus_deck_mesh` (`:474-537`) constructs explicit fan-cap triangles at bow and stern centered on the inboard ring centroid, and shifts the end stations' *shape* (not *position*) one station inboard (`shape_positions[0] = x_positions[1]`, `shape_positions[-1] = x_positions[-2]`) so plumb endpoints retain a non-zero ring while the endpoint x-coordinate stays at ±L/2. The orientation is then forced positive by `if _signed_volume(...) < 0.0: face_array = face_array[:, [0, 2, 1]]`. Live smoke test confirms zero raw/welded boundary and nonmanifold edges for `bow_rake=1.0`, `bow_rake=0.0`, and the deliberately wide-mismatch case, with positive signed volume (0.27 m³, 0.45 m³, 0.48 m³ respectively).
- **L4 (sheerline/topside/deck join)** closed. `_generated_cross_section_ring` (`:539-580`) walks each station's hull section, optionally adds the outboard hull endpoint, traverses the deck section in reverse port-direction, and welds within `max(vertex_weld_tolerance_m, join_match_tolerance_m)`. When `beam_oa_m > beam_wl_m`, this naturally produces a topside strip; the test `test_generated_closed_body_joins_waterline_beam_to_outer_sheer` exercises a 0.62 m / 0.46 m mismatch and asserts the body reaches the overall beam and retains both the waterline-beam ring and a topside extent beyond it.
- **L5 (diagnostics without CFD promotion)** closed. `diagnose_closed_volume_body` (`:366-450`) is now body-type-agnostic and routes through the same body-level boundary, nonmanifold, nonfinite, degenerate-face, invalid-index, signed-volume, outward-normal, and RFC 0021 self-intersection pipeline. The body-type guard the previous code carried (`raise ValueError("closed-volume diagnostics only accept explicit synthetic meshes")`) has been replaced by a policy/body-type *match* check, which is strictly tighter than the previous text-rejection. `_policy_requires_self_intersection` (`:1375-1382`) now includes the RFC 0022 profile, so generated bodies cannot reach `closed_volume` without a `passed` self-intersection result. `cfd_ready` remains `Literal[False]`, `dispatch_evidence_satisfies_profile` still returns `False` in every branch (including the `cfd_ready` short-circuit at `:469-471`), and `tests/test_cfd_jobs.py::test_prepare_rejects_generated_closed_body_as_cfd_ready_evidence` plumbs the generated diagnostic through a forged manifest and asserts `prepare_local_job` raises `CfdDispatchError`.
- **L6 (generated-body acceptance tests)** closed. `tests/test_generated_closed_body.py` (328 lines, new) covers policy round-trip with source-hull hash, determinism with `LoftedHullGeometry.generate_stl` monkey-patched to raise, default and plumb rake closure, plumb-vs-default volume monotonicity, waterline-beam to outer-sheer topside join, waterline-metadata recording without geometric cutting, outward-normal diagnostics round-trip, and display-STL/mesh-package separation including direct dispatch rejection for both the generated profile and `watertight_solid_resistance_v1`.
- **L7 (synthetic diagnostic hardening)** closed. `tests/test_closed_volume.py` adds `test_nonfinite_vertices_are_reported_without_crashing`, `test_degenerate_faces_are_reported_without_masking_closed_edges`, and `test_custom_tolerances_round_trip_through_diagnostics_json`. The tolerance round-trip test re-validates the JSON-serialized diagnostics and pins `self_intersection_tolerance_m` to the requested value.

### Gate criteria in `roles/final_reviewer.md`

- **Generated construction is deterministic.** The builder is a pure function of `Hull`; two invocations produce byte-identical `model_dump_json` output (`test_generated_closed_body_is_deterministic_and_does_not_use_display_stl`). `source_hull_hash` is derived from `Hull.hash()`, not from process state.
- **Diagnosed at body level.** Closure, manifold, nonfinite, degenerate, signed-volume, normal-orientation, and self-intersection checks all run on the assembled welded body in `diagnose_closed_volume_body` and `_assemble_parts_with_refs`. The `ClosedSurfacePartDiagnostics` view is now informational, not authoritative.
- **Separated from display STL.** The builder never touches `LoftedHullGeometry.generate_stl`; the determinism test asserts this via monkeypatch. `kayakgen/eval/mesh_package.py` is untouched, the mesh manifest test still confines watertight profiles to `stl_surface`, and `manifest.surfaces == {"hull": "hull.stl", "deck": "deck.stl"}` is asserted alongside the closed-body diagnostic.
- **Free of CFD-readiness claims.** `cfd_ready` is `Literal[False]`. `dispatch_evidence_satisfies_profile` still returns `False` for every `required_mesh_readiness == "cfd_ready"` request. CHANGELOG wording stays inside the closed-volume layer ("generated hull-plus-deck closed-volume evaluation body … keeping generated bodies below `cfd_ready`"). RFC 0022 §"Readiness Policy" wording is preserved.

### Independent verification

- `git diff main...HEAD --stat` — 13 files changed, +1249 / -32. Sources: workflow metadata, `closed_volume.py`, `tests/test_closed_volume.py`, `tests/test_cfd_jobs.py`, new `tests/test_generated_closed_body.py`, `CHANGELOG.md`, ledger/review artifacts, and the workflow operator report. No edit to display STL paths, mesh package writer, generator shims, CLI, or any RFC text.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_cfd_jobs.py tests/test_mesh_package.py -q` → 44 passed.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q` → 205 passed.
- `python -m json.tool docs/workflows/0033-generated-closed-body-construction/workflow.json >/dev/null` → exit 0.
- REPL smoke check with `Hull(name='inspect')`, `Hull(bow_rake=0.0)`, and `Hull(beam_wl_m=0.46, beam_oa_m=0.62, draft_m=0.13, deck_height_m=0.25, bow_rake=0.0)` returned closed-volume readiness with zero boundary edges, `self_intersection_status="passed"`, positive signed volume, the RFC 0022 profile name, and `cfd_ready=False`. `dispatch_evidence_satisfies_profile` returned `False` for both the generated profile and `watertight_solid_resistance_v1`.

### Observations carried forward (non-blocking)

These do not affect closure of L1-L7 or the gate. They are recorded so the next workflow has them in scope, not because the slice should be revised.

1. **`deck_join_policy` literal vs realized welding behavior.** Only one non-trivial literal exists today, `exact_shared_vertices_topside_sheerline_strip`, but `_append_ring_point` always tolerance-welds via `np.linalg.norm(point - points[-1]) <= tolerance`. The two regimes RFC 0022 §"Sheerline and Deck Join" calls out ("vertices shared exactly *or* welded within tolerance") are therefore serialized into a single literal whose name is biased toward the exact case. Functionally this is honest — when `beam_wl_m == beam_oa_m` and the hull endpoint coincides with the deck endpoint to numerical noise, welding collapses to exact sharing — but a future cleanup could expose a second literal (e.g. `welded_within_tolerance_topside_sheerline_strip`) and have the builder pick between them based on the realized weld distance. None of the L1-L7 acceptance assertions depend on this distinction; the join-policy assertion in `test_generated_closed_body_joins_waterline_beam_to_outer_sheer` is `"weld" in body.policy.deck_join_policy or "shared" in body.policy.deck_join_policy`, which is satisfied by `shared`.
2. **Endpoint sampling is more conservative than RFC 0022 strictly requires.** RFC 0022 §"Bow and Stern Caps" says the cap "may collapse toward the existing fine end if the station ring degenerates within tolerance" for `bow_rake = 1.0`. The implementation instead samples the inboard station's shape at the endpoint x-coordinate to keep the ring non-degenerate for all rake values. This produces a slightly fuller end stub than the lofted display surface implies, and is therefore a (small) departure from display geometry; it is intentional and defensible because it guarantees closure for every valid `Hull` and was explicitly contemplated by `roles/final_reviewer.md` ("Cap degeneracy may be reported by tolerance, but if it leaves boundary edges the body must remain below closed-volume readiness."). The "default rake fully tapered" alternative is a future refinement, not a regression.
3. **`generated_hull_plus_deck_body` vs `generated_hull_plus_deck_closed_body` alias.** Both names are exposed and behave identically. The acceptance test prefers the shorter name and falls back to the longer one. Consolidating on one and treating the other as a documented compatibility shim is cheap follow-up work; not in scope here.

None of these are reasons to gate.

## Conclusion

The conservative slice in `striatum/0033-generated-closed-body-construction/ledger/FINDINGS.md` is fully realized. RFC 0022 generated closed-body construction is deterministic, diagnosed at body level, separated from display STL, and barred from `cfd_ready` through three independent layers (`Literal[False]` field, `dispatch_evidence_satisfies_profile`, and forged-manifest CFD job rejection). The workflow metadata is repaired. Full pytest suite is green. I accept this implementation as the workflow 0033 final review.
