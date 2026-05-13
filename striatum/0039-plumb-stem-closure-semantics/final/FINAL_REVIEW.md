I have all the information I need. The implementation correctly addresses every blocker finding from the ledger and full test suite (211 tests) passes. Producing the artifact now.

Verdict intent: accept_with_findings

# Final Review: 0039 Plumb-Stem Closure Semantics

Role: independent Striatum final-review agent for workflow `0039-plumb-stem-closure-semantics`, lane `claude / Opus 4.7`, worktree `/tmp/kayak-gen-ledger-worktrees/0039`, session `sess_378dd8e7efe44f44bd7e10f25deb6bc3`, job `job_run_53f17f26285941c3a3992705772ce07d_final_review`, lease `lease_58cbfb89622c41b2a70dd038bd62d177`.

No `striatum` command was called. No project code was mutated. No commits, pushes, or root `OPERATOR_REPORT.md` updates were made. The artifact path `striatum/0039-plumb-stem-closure-semantics/final/FINAL_REVIEW.md` is written via the operator's stdout redirect, not by this agent.

## Scope

Verify that the implementation at branch `striatum/0039-plumb-stem-closure-semantics` (HEAD `8367b65`) satisfies the RFC 0028 acceptance criteria, closes all ledger blockers, and preserves the open-surface readiness contract. The role gate is: "Accept only if exact plumb end caps, asymmetric rake, coordinate conventions, closed-body dependency boundaries, diagnostics, and docs are coherent and covered by tests."

## Sub-agent help used

None spawned. The operator instruction is to use the maximal *useful* number of sub-agents. The relevant surfaces are small and disjoint sub-agent scopes would not change the conclusion:

- `kayakgen/model/hull.py` (94 lines), `kayakgen/model/geometry.py` (327 lines), `kayakgen/eval/generated_closed_body.py` (202 lines), and `kayakgen/eval/mesh_diagnostics.py` (270 lines) — the four implementation files.
- `tests/test_plumb_bow.py`, `tests/test_hull_roundtrip.py`, `tests/test_generated_closed_body.py`, `tests/test_mesh_diagnostics.py`, `tests/test_mesh_package.py`, `tests/test_cli.py` — the focused test surfaces.
- The three first-pass reviews, the findings ledger, the implementer patch summary, RFC 0004, RFC 0028, and the user guide.

Sub-agent help previously used by the three peer reviewers (4 for ops, 0 for traceability, 0 for domain), by the ledger (4), and by the implementer (5) is cited rather than re-derived. The full pytest suite was re-run by this final-review agent to verify the implementer's recorded result.

## Sources reviewed

- `AGENTS.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/{SOURCES.md, workflow.json, roles/final_reviewer.md, prompts/final_review.md}`
- `docs/rfcs/0004-plumb-bow.md`, `docs/rfcs/0028-plumb-stem-closure-semantics.md`, `docs/rfcs/README.md`
- `docs/USER_GUIDE.md`, `docs/PRD.md`, `CHANGELOG.md`
- `kayakgen/model/hull.py`, `kayakgen/model/geometry.py`
- `kayakgen/eval/{generated_closed_body.py, closed_volume.py, mesh_diagnostics.py, mesh_package.py}`
- Test modules listed above.
- First-pass review artifacts under `striatum/0039-plumb-stem-closure-semantics/{traceability,domain,ops}/`.
- Findings ledger at `striatum/0039-plumb-stem-closure-semantics/ledger/FINDINGS.md`.
- Patch summary at `striatum/0039-plumb-stem-closure-semantics/implementation/PATCH_SUMMARY.md`.
- Branch-local diff against `main` (32 files; +1261 / -46).

## Acceptance Criterion Verification

RFC 0028 acceptance criteria (`docs/rfcs/0028-plumb-stem-closure-semantics.md:124-138`) map onto code and tests as follows:

| AC# | Behavior | Implementation | Test | Result |
|---|---|---|---|---|
| AC1 | Independent bow/stern rake; legacy `bow_rake` JSON preserves geometry | `Hull.stern_rake` (`kayakgen/model/hull.py:52-57`) + `_seed_legacy_symmetric_stern_rake` pre-validator (`:64-71`) | `tests/test_hull_roundtrip.py:41-75`, `tests/test_plumb_bow.py:23-31` and `:89-97` | PASS |
| AC2 | Pin X-coordinate, orientation, cap winding, signed volume in docs and tests | `docs/USER_GUIDE.md:54-67`, `kayakgen/eval/mesh_package.py:29` ("longitudinal, stern positive, bow negative, spans -L/2 to +L/2") | `tests/test_plumb_bow.py:34-41`, `tests/test_generated_closed_body.py:55-67` | PASS |
| AC3 | `bow_rake = 0.0` → non-zero terminal bow section at `x = -L/2` (closed body) | `_rake_for_x` (`kayakgen/model/geometry.py:139-141`), `_is_exact_plumb_endpoint` (`:143-148`), `closed_body_endpoint` plumbing (`:178-194`), and `generated_hull_plus_deck_closed_body` (`kayakgen/eval/generated_closed_body.py:48-74`) | `tests/test_generated_closed_body.py:23-33` | PASS |
| AC4 | `stern_rake = 0.0` → non-zero terminal stern section at `x = +L/2` (closed body) | Same path; sides selected by `_rake_for_x` under bow-negative/stern-positive convention | `tests/test_generated_closed_body.py:23-33` (covers both ends) | PASS |
| AC5 | Mixed plumb-bow/raked-stern → asymmetric geometry, default unchanged | `_rake_for_x` returns side-specific rake; default `Hull()` has `bow_rake = stern_rake = 1.0`, identical to legacy symmetric | `tests/test_plumb_bow.py:100-106`, golden SHA preserved at `:23-31` | PASS |
| AC6 | Open hull/deck STL exports remain labeled "open inspection surfaces" unless closed-body command/profile is explicit | `mesh_diagnostics._readiness` ceiling at `stl_surface` (`kayakgen/eval/mesh_diagnostics.py:240-269`); mesh-package readiness gating (`kayakgen/eval/mesh_package.py:127-171`) | `tests/test_generated_closed_body.py:99-105`, `tests/test_cli.py:172-208` (mixed-rake stays below `cfd_ready`) | PASS |
| AC7 | Diagnostics (not rake settings) decide closed-volume/watertight readiness | Closed-body builder uses `explicit_synthetic_self_intersection_policy()` (`kayakgen/eval/generated_closed_body.py:87`); `closed_volume` only reached after passing self-intersection, boundary-edge, signed-volume, and degeneracy checks | `tests/test_generated_closed_body.py:36-52`, `:70-79`, `:82-96` | PASS |

All seven acceptance criteria are exercised by focused tests. Default golden geometry is preserved (`tests/test_plumb_bow.py:23-31` re-asserts the legacy STL payload SHA256 `bd3ba7d4…`).

## Ledger Finding Closure

The ledger recorded five functional blockers (F-001 through F-005), two required documentation/test items (F-006, F-007), and two non-blocking items (F-008, F-009). Status:

- **F-001 — Stale `SOURCES.md` paths.** Closed by `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md` now listing `kayakgen/model/geometry.py`, `kayakgen/eval/closed_volume.py`, `kayakgen/eval/generated_closed_body.py`, `kayakgen/eval/mesh_diagnostics.py`, and `kayakgen/eval/mesh_package.py`, with `workflow.json` updated to match.
- **F-002 — Missing `stern_rake` serialization.** Closed by `Hull.stern_rake` with `ge=0, le=1` validation, plus the pre-validator that seeds `stern_rake` from `bow_rake` only when `stern_rake` is absent from input. Round-trip and validation tests in `tests/test_hull_roundtrip.py:41-75` confirm legacy compatibility, independent round-trip, and `[0, 1]` rejection.
- **F-003 — Symmetric `abs(x)` loft.** Closed by `_rake_for_x(x)` returning `bow_rake` for `x ≤ 0` and `stern_rake` for `x > 0`, threaded through `_end_decay`, `_get_deck_height_scaling`, and `_get_slice_points`. The `test_legacy_bow_rake_geometry_matches_explicit_symmetric_stern_rake` test pins programmatic legacy equivalence at `bow_rake = 0.5`; mixed-rake asymmetry is pinned in `test_mixed_bow_and_stern_rake_produces_asymmetric_geometry`.
- **F-004 — Endpoint/cap semantics absent.** Closed by the new `kayakgen/eval/generated_closed_body.py`:
  - `_is_exact_plumb_endpoint` selects per-side endpoint promotion only when that side's rake is exactly `0.0` and `x` is within `1e-12` of `±L/2`.
  - Exact-plumb endpoints emit a full ring + planar cap fan (`_cap_center`-anchored).
  - Raked endpoints (`rake > 0`) emit a single-vertex apex closure at `(±L/2, 0, 0)`, deterministic and degeneracy-free.
  - `test_exact_plumb_endpoints_have_nonzero_terminal_sections` asserts ptp > 0.5 in Y and > 0.2 in Z at both `x = ±L/2`. The patch summary correctly notes that the existing `test_plumb_section_at_end_has_nonzero_area` test was renamed/clarified to `test_plumb_section_near_end_has_nonzero_area` so it does not imply exact endpoint coverage.
- **F-005 — Closed-body winding and signed volume.** Closed by `_section_ring` normalizing each station ring to positive Y-Z signed area, deliberate bow-vs-stern cap winding asymmetry in `_add_endpoint_closures` (`stern_base + point_index, stern_base + point_next` vs. the bow's reversed order), and a defensive global flip in `generated_hull_plus_deck_closed_body` when `_signed_volume < 0`. `test_plumb_cap_normals_are_mirrored_under_x_convention` pins outward bow-cap normals (`x < 0`) and outward stern-cap normals (`x > 0`); diagnostics tests assert zero boundary edges, zero nonmanifold edges, zero degenerate faces, positive signed volume, and `self_intersection_status == "passed"`.
- **F-006 — Coordinate convention and user-facing wording.** Closed by:
  - `docs/USER_GUIDE.md:54-67` adding the `stern_rake` line, the X-positive-stern coordinate convention, and the legacy symmetric meaning of `bow_rake`.
  - `docs/rfcs/0004-plumb-bow.md:27-31` status note redirecting the asymmetric-rake deferral to RFC 0028.
  - `docs/rfcs/0028-plumb-stem-closure-semantics.md` status updated from `proposed` to `partial safe-slice`; the open-question text on rake threshold is hardened to the exact `rake == 0.0` rule (closes TRACE-004).
  - `docs/rfcs/README.md` index row reflects the new status.
  - `docs/PRD.md` updates the bow/stern-geometry bullet to RFC 0028 and re-asserts the open-surface, non-`cfd_ready` ceiling.
  - `CHANGELOG.md` adds an Unreleased entry for the safe slice.
- **F-007 — Finite degenerate/nonmanifold meshes still reading as `stl_surface`.** Closed in `kayakgen/eval/mesh_diagnostics.py:264-265`: any `degenerate_faces`, `raw_nonmanifold_edges`, or `welded_nonmanifold_edges` now demotes readiness to `display`. New tests `test_finite_degenerate_mesh_is_below_stl_surface` and `test_finite_nonmanifold_mesh_is_below_stl_surface` in `tests/test_mesh_diagnostics.py:105-149` pin the new floor.
- **F-008 — CLI watertight-profile failure verbosity.** Correctly deferred (patch summary lists this explicitly). Manifest warnings still discoverable via JSON, gated by `tests/test_cli.py:172-208`. Non-blocking.
- **F-009 — Editorial cleanup.** Partly addressed (RFC 0004 status note, RFC 0028 open question hardened, golden SHA preserved). The remaining traceability notes (e.g., naming expected test modules from inside RFC 0028) are editorial only and were classified non-blocking by the ledger.

All five blocker findings are closed. The required documentation/test items (F-006, F-007) are closed. Non-blocking items are either deferred with rationale (F-008) or partially addressed in line with the ledger's "do not block on these" framing (F-009).

## Diff and Test Inspection

Branch-local diff is 32 files, +1261 / -46. The non-artifact code surface is concentrated in:

- `kayakgen/model/hull.py` (+25 / -3): `stern_rake` field, `_seed_legacy_symmetric_stern_rake` pre-validator, updated descriptions.
- `kayakgen/model/geometry.py` (+39 / -2): `_rake_for_x`, `_is_exact_plumb_endpoint`, `closed_body_endpoint` parameter threading, side-specific `_end_decay` and `_get_deck_height_scaling`.
- `kayakgen/eval/generated_closed_body.py` (+201 / 0, new file): builder, ring assembly, cap construction, signed-volume normalization.
- `kayakgen/eval/mesh_diagnostics.py` (+2 / 0): readiness demotion for finite-degenerate and finite-nonmanifold meshes.
- `kayakgen/eval/mesh_package.py` (+2 / 0): wording update.
- `kayakgen/ui/{desktop.py, gui_params.py, web/app.py, web/state.py}` (+5 / 0 total): `stern_rake` exposed in the GUI/web surfaces.

The patch is tightly scoped to the safe slice declared by the ledger; no rocker, flare, multi-chine, manufacturing-stem-thickness, reverse-rake, `cfd_ready`, or volume-mesh changes are introduced. The closed-body builder explicitly opts into `explicit_synthetic_self_intersection_policy()` so the RFC 0021 self-intersection gate is required before reporting `closed_volume`.

I re-ran the full test suite in this worktree using the same venv the implementer used:

```
PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest \
  -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039-final tests/
```

Result: **211 passed in 34.45s**, matching the implementer's recorded result.

## Coherence Review

The role gate asks for coherence across "exact plumb end caps, asymmetric rake, coordinate conventions, closed-body dependency boundaries, diagnostics, and docs."

- **Exact plumb end caps:** Geometrically consistent. At `rake == 0.0`, the endpoint station inherits the full-section ring (`_get_slice_points(..., closed_body_endpoint=True)` returns `hull_decay = 1.0` and `deck_scale = 1.0`); the cap is a planar fan around `_cap_center` at the endpoint x; bow and stern fans use mirrored vertex orderings so outward normals point in `-X` at the bow and `+X` at the stern.
- **Asymmetric rake:** Side selection is by sign of `x`. The bow-negative/stern-positive convention is matched by the loft (`waterplane`, `keel_line`, `deck_centreline`), the mesh-package coordinate-system metadata, and the user guide.
- **Coordinate conventions:** Pinned by `MeshPackageCoordinateSystem`, by `test_coordinate_convention_pins_bow_negative_stern_positive`, and by the user-guide text. The mesh-package manifest is the machine-readable single source of truth.
- **Closed-body dependency boundaries:** `kayakgen.model.Hull` validates rake fields. `kayakgen.model.geometry` owns rings via `_get_slice_points`. `kayakgen.eval.generated_closed_body` joins rings, caps, and signed-volume normalization. `kayakgen.eval.closed_volume` owns diagnostics. CLI, desktop, and web layers consume readiness metadata; none infer watertightness from `bow_rake == 0`. This matches RFC 0028 §4 exactly.
- **Diagnostics:** Closed-body diagnostics require the RFC 0021 self-intersection profile (`explicit_synthetic_self_intersection_policy`), and `closed_volume` is only reported after passing all gates. The mesh-diagnostics readiness ceiling for the open inspection mesh is `stl_surface`; the `watertight-solid` solver profile keeps generated open packages at `stl_surface` with explicit warnings (`tests/test_cli.py:172-194`).
- **Docs:** RFC 0028 status updated; RFC 0004 status note added; user guide, PRD, and changelog align with the implementation.

## Verification of Independent Concerns

1. **Legacy SHA preserved.** `test_default_rake_preserves_legacy_geometry` still asserts the golden STL payload SHA256 `bd3ba7d497e78349d43495bb0d02097ddfcc3c0e2c5781945c25f781218a4c39` with the new `stern_rake` default of `1.0`. Re-ran the test under the full suite — passes. AC5's "without changing the default hull" clause is mechanically pinned.

2. **Validator handles all input modes.** `_seed_legacy_symmetric_stern_rake` only seeds when input is a dict containing `bow_rake` but not `stern_rake`. Programmatic `Hull(bow_rake=0.5)` and JSON `{"bow_rake": 0.25}` both go through; `Hull(bow_rake=0.5, stern_rake=0.5)` and `Hull(stern_rake=0.0)` are unaffected. Tests cover legacy-only, both-supplied, and stern-only.

3. **Outward-normal mathematics.** The bow cap face order `[center, next, current]` and stern cap face order `[center, current, next]` produce mirrored normals around `±X` because every cap-face vertex has the same x coordinate; the cross product's only non-zero component is x. With each ring normalized to positive Y-Z signed area by `_section_ring`, this gives `normal.x < 0` at the bow and `normal.x > 0` at the stern. `test_plumb_cap_normals_are_mirrored_under_x_convention` pins this property.

4. **Defensive signed-volume flip.** If for any pathological station shape the assembled body has negative signed volume, the global flip in `generated_hull_plus_deck_closed_body:77-78` rewinds all faces. The tests confirm that the default and exact-plumb constructions land on positive signed volume without needing the flip; the flip remains a defensive guard.

5. **Self-intersection gate.** Closed bodies now use `explicit_synthetic_self_intersection_policy()`, which forces `required_rfc0021_conservative`. The `test_generated_plumb_body_diagnostics_prove_closed_positive_volume` and `test_default_raked_generated_body_uses_apex_closure_without_degenerate_faces` tests both assert `self_intersection_status == "passed"`, which means the assembled bodies are evidence-clean, not just structurally closed.

6. **Open surfaces still open.** `test_open_plumb_stl_surface_remains_inspection_mesh_not_closed_body` exercises the path that matters most for the AC6 contract: at `bow_rake = 0.0` with the open inspection mesh, readiness is `stl_surface` and the warning `"mesh has boundary edges and is not a closed volume"` is present. This is the safety guarantee the workflow exists to preserve.

## Observations (non-blocking)

1. **Endpoint-section vs. final-decay interpretation.** RFC 0028 §3 describes the exact-plumb endpoint section as "the limiting section shape after the plumb transition." The implementation interprets this as the full midship section (forcing `hull_decay = 1.0` and `deck_scale = 1.0` at the exact endpoint). At default `stations = 32`, the second-to-last station sits right at the `x_norm ≈ 0.935` boundary of the plumb-flat zone, so the closed body has a near-continuous transition. At significantly higher refinement, station(s) inside the last 5% of L would receive the natural decay while the exact endpoint snaps back to a full section, producing a small geometric step. The current test coverage uses `stations` in `[4, 6]`, where no interior transition-zone stations exist. The body is still topologically valid in all cases (no boundary edges, no degenerate faces, positive signed volume). If a higher-station closed-body command lands later, consider either documenting this snap-back behavior or explicitly using the limiting plumb-transition section instead of the full midship section.

2. **Apex closure for raked ends.** The raked-end apex at `(±L/2, 0, 0)` is a clean, deterministic choice and avoids degenerate-face risk from collapsing rings. It is geometrically consistent with the open inspection mesh's natural endpoint (both keel and deck approach z=0). RFC 0028 §3 allows the closed-body path to cap the collapsed endpoint without requiring exact non-zero endpoint area for `rake > 0`. No change needed.

3. **Branch divergence from `main`.** The diff against `main` shows two changes that look out of scope at first read but are merge artifacts of the branch being behind `main`:
   - `docs/rfcs/README.md` shows RFC 0026 reverting from `landed fixture-local-command` to `proposed`. Main has since landed `9c6e24a Land RFC 0026 fixture adapter implementation`.
   - `OPERATOR_REPORT.md` shows a 9-line deletion that is actually a 9-line addition on `main` (`2523fce Record UI prompt and 0039 implementation`) that this branch never picked up.
   Both will resolve on rebase. The branch itself does not regress these surfaces.

4. **TRACE-002 / RFC 0004 redirect.** The traceability review's TRACE-002 finding is closed via the new status-note block at `docs/rfcs/0004-plumb-bow.md:27-31` plus the Open Question rewording at `:163-165`.

5. **TRACE-005 / default-pin under new defaults.** The default-pin SHA in `tests/test_plumb_bow.py:23-31` is re-asserted under the new `stern_rake = 1.0` default. AC5's "default unchanged" promise is mechanically protected.

## Verdict Reasoning

All seven RFC 0028 acceptance criteria have focused, passing tests in the worktree. All five ledger blockers (F-001 through F-005) are closed at the code, doc, and test level. The two required documentation/test items (F-006, F-007) are closed. F-008 is deferred with explicit rationale; F-009 is partly handled. The open-surface readiness ceiling (the most load-bearing safety property of this workflow) is preserved: open hull/deck STLs and their packages still cap at `stl_surface` or `cfd_surface_candidate`, never `cfd_ready`. Closed bodies report `closed_volume` only after passing self-intersection, signed-volume, manifold, and degeneracy gates. The default geometry SHA is unchanged.

The non-blocking observations above (endpoint-section interpretation under high refinement; merge-artifact diff lines that will resolve on rebase) do not affect acceptance. They are noted so the next workflow that touches the closed-body builder has the context.

## Verdict

accept_with_findings

The findings are the non-blocking observations listed above. The workflow may complete; the operator should rebase the branch onto current `main` before merging to absorb the RFC 0026 status and `OPERATOR_REPORT.md` updates that landed on `main` after this branch diverged.
