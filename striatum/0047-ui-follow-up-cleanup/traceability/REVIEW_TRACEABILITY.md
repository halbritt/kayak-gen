author: operator [self-declared: operator-0047-review-traceability]
kind: finding
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_67b861e6f1ed459c865ea208b3dc39ce
job: job_run_489eb28aa3e0453b916113addacd02e3_review_traceability
lease: lease_30ae95a0f9bd4849a00a99d2c7a4d120
date: 2026-05-14

# Review - Traceability for Workflow 0047 (RFC 0035 UI Follow-Up Cleanup)

## Verdict Intent

`accept_with_findings`

The drafted RFC 0035 and the workflow 0047 scope each map their proposed
cleanup items to a specific finding in workflow 0045's final review or
workflow 0046's final review (M-series), and the only loosely-coupled item
(validity-badge parity) is anchored to W0045 F1 plus the existing desktop
classifier behavior in `kayakgen/ui/desktop.py:362-376`. RFC 0035 status
(`proposed`) is consistent with the RFC index entry at
`docs/rfcs/README.md:51`, and the narrative in the README (lines 113-119)
correctly characterises RFC 0035 as the narrow successor for workflow 0045
and 0046 final-review findings. No item is a redesigned backend, real
solver, calibrated-drag, high-angle `GZ`, or watertight-readiness change in
disguise. The findings below are non-blocking traceability notes the
findings ledger should consider when scoping the implementation lane.

## Item-By-Item Traceability

| RFC 0035 item | Cited / matching evidence | Trace verdict |
| --- | --- | --- |
| 1. Preset and validity semantics (web badge classifies against all envelopes, preserves RFC 0033 badge vocabulary). | W0045 final review F1 (`striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md:27-37`); desktop reference behavior `kayakgen/ui/desktop.py:362-376`; badge vocabulary anchored in RFC 0033 `## Acceptance Criteria` and RFC 0034 AC2. | Cited; small scope-stretch flagged as F-T1. |
| 2. Preset edit model (canonical-five seed/narrow; hull-shaping edits flip to `custom`; `target_speed_kt` does not). | W0045 final review F3 (`final/FINAL_REVIEW.md:51-65`); existing tests `tests/test_web_layout.py::test_class_preset_reseeds_bounds_and_manual_hull_edit_flips_custom` and the `test_target_speed_edit_does_not_flip_class_preset` test referenced in W0045 final review. | Cited; pure docs/tests scope. |
| 3. Dead branch cleanup (`_state_matches_preset_seed`). | W0045 final review F2 (`final/FINAL_REVIEW.md:39-49`); `kayakgen/ui/web/app.py:688-704` per F2 line refs. | Cited; pure code cleanup. |
| 4. Export menu single source from `EXPORT_MENU_ROWS`. | W0045 final review F4 (`final/FINAL_REVIEW.md:67-77`); `kayakgen/ui/web/app.py:103-137` (`EXPORT_MENU_ROWS`) vs `app.py:1039-1083` (`_render_export_menu`). | Cited; rendering refactor only. |
| 5. State snapshot schema (declared keys, preserve REST shapes). | W0045 final review F5 (`final/FINAL_REVIEW.md:79-87`); `kayakgen/ui/web/app.py:495-514` (`_state_snapshot`). | Cited; preserves payload shapes per RFC 0035 §Proposal #5. |
| 6. Slider-label CSS + wrapper accessibility. | W0046 final review M2 wrapper `Div` + `role="group"` (`striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md:150-165`); W0046 final review M3 duplicate `:root` block (`final/FINAL_REVIEW.md:167-180`); `kayakgen/ui/web/app.py:201-210,246-254,980-993`. | Cited; CSS hygiene + a11y verification only. |
| 7. Desktop slider-label fallback maintenance. | W0046 final review M1 (`final/FINAL_REVIEW.md:124-147`); `kayakgen/ui/desktop.py:47-49,233-248`; W0046 ledger F1 implementation direction. | Cited; isolation/documentation only. |

Every cleanup item in RFC 0035 §Proposal traces to either an
`accept_with_findings` finding from workflow 0045's final review (F1-F5)
or a non-blocking finding from workflow 0046's final review (M1-M3). RFC
0035 §Acceptance Criteria mirror these items 1:1.

## Status And Index Consistency

- `docs/rfcs/0035-ui-follow-up-cleanup.md:3` declares `Status: proposed`.
- `docs/rfcs/README.md:51` records RFC 0035 as `proposed` with the matching
  topic blurb.
- `docs/rfcs/README.md:113-119` describes RFC 0035 as the narrow cleanup
  successor for workflow 0045 and 0046 final-review findings, calling out
  the same boundary list (no desktop parity, no hosted CFD, no real
  solvers, no calibrated drag, no final prediction, no high-angle `GZ`, no
  web-side mesh-package authoring beyond safe entries, no watertight
  `cfd_ready`). This boundary set matches RFC 0035 §Non-Goals verbatim in
  topic.
- `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md` lists RFC 0033,
  RFC 0034, the W0045 final review, the W0046 final review, the W0046
  ledger, the touched UI source files, and `tests/`. No source pointer is
  missing for any RFC 0035 item.
- `striatum/0047-ui-follow-up-cleanup/rfc_scope/RFC_SCOPE.md` enumerates
  the same eight findings (W0045 F1-F5, W0046 M1-M3) and lists matching
  deferrals; the synthesis is consistent with RFC 0035.

No status/index drift detected.

## Disguised-Scope Audit

The traceability prompt asks whether any item is a broad redesign,
backend feature, real solver, calibrated-resistance, high-angle stability,
or watertight-readiness change disguised as cleanup.

- **Backend / REST route shape.** RFC 0035 §Proposal #5 explicitly
  preserves existing keys and route payload shapes; §Non-Goals forbids new
  REST route shape, hosted service, hosted CFD, worker queue, and cloud
  storage. No backend capability surface is added.
- **Real solver.** §Non-Goals forbids OpenFOAM/SU2 integration and any
  real solver adapter.
- **Calibrated resistance / final prediction.** §Non-Goals forbids
  calibrated drag, accepted final prediction, design fitness, and any new
  resistance validity envelope.
- **High-angle stability.** §Non-Goals forbids real high-angle `GZ`,
  `GZ_max`, `heel_angle_max_deg`, and capsize-range claims.
- **Watertight readiness.** §Non-Goals forbids watertight-solid promotion
  and bare `cfd_ready` promotion. Item #4 (export menu) keeps Stability
  JSON and Mesh package as honest unavailable rows, matching W0045
  ledger P0.
- **Desktop redesign.** §Non-Goals forbids desktop parity rewrite,
  Qt-native slider rewrite, `QMainWindow` migration, and broader desktop
  layout redesign. Item #7 limits desktop changes to fallback isolation,
  removal-condition documentation, and the existing bbox tests.
- **Validity envelope expansion.** Item #1 reuses the existing
  `KayakClass` envelopes and the existing badge string set; it does not
  introduce a new class definition or numeric threshold. The risk note is
  recorded as F-T1 below.

No item is a disguised broad-redesign, backend, calibration, stability, or
watertight-readiness change.

## Findings

Ordered by severity. None are blocking.

### F-T1 - Validity-badge "all envelopes" change is the largest non-cosmetic delta (low)

`kayakgen/ui/web/controllers.py:128-141` (per W0045 final review F1)
currently derives the badge from `state["class_preset"]`. RFC 0035
§Proposal #1 moves it toward
`kayakgen/ui/desktop.py:362-376`'s `_classify` behavior, which scans every
class envelope. This is the largest behavioral change in the cleanup
slice, even though the user-visible badge vocabulary
(`In <class> envelope`, `Custom - sub-touring`, `Custom - beyond elite`,
`Custom (L/B_wl=X.X)`) does not change. Recommend the findings ledger:

- require an explicit unit test pinning the new web `validity_badge_from_state`
  outcome against the desktop classifier on at least one custom hull
  whose dimensions fall inside a non-selected class envelope, plus one
  custom hull that falls outside every envelope;
- forbid changes to `class_preset_options`, `class_preset_read_model`,
  preset reseed/narrow code paths, and the badge string set itself.

Why: F1 is recorded as a "successor consideration" rather than an accepted
defect. RFC 0035 promotes it to a goal but should keep the change scoped
to `validity_badge_from_state` and its tests.

### F-T2 - Implementation should split write scope by surface (low)

The seven RFC 0035 proposal items touch four largely disjoint code
surfaces:

- web semantics: items 1, 2, 3 (`kayakgen/ui/web/controllers.py`,
  `kayakgen/ui/web/app.py:688-704`);
- web rendering / state hygiene: items 4, 5
  (`kayakgen/ui/web/app.py:103-137,495-514,1039-1083`);
- web slider-label CSS + a11y: item 6
  (`kayakgen/ui/web/app.py:201-210,246-254,980-993`,
  `kayakgen/ui/theme.py`);
- desktop fallback: item 7 (`kayakgen/ui/desktop.py:47-49,233-248`).

The findings ledger and implementation lane should keep these write
scopes disjoint so parallel sub-agents do not collide and so any single
item can be deferred to a follow-up workflow without unwinding the others.
This matches RFC 0035 §Implementation Path #3.

### F-T3 - Item #5 wording could be tightened to forbid `_state_snapshot` removal (very low)

RFC 0035 §Proposal #5 says "Replace ad-hoc web state snapshot key copying
with a small declared snapshot schema, without changing public REST
payload shapes." `_state_snapshot` is a private helper; the controller
boundary it feeds (`controllers._cfd_status_from_state`) and the routes
above it must keep current behavior. Recommend the findings ledger
explicitly disallow:

- changes to `kayakgen/ui/web/state.py` shape or aliases that callers
  outside the snapshot helper depend on;
- removal of any legacy alias key (`cfd_status`, `cfd_payload`,
  `cfd_job_payload`, `cfd_last_payload`) noted in W0045 F5 unless a test
  proves no caller depends on it.

This is a phrasing tightening, not an RFC defect.

### F-T4 - Item #6 should explicitly preserve the W0046 contrast manifest pair (very low)

`kayakgen/ui/theme.py:340` records the
`slider.label.rail` contrast pair (W0046 final review evidence,
`tests/test_ui_theme.py:139-145`). RFC 0035 §Proposal #6 talks about
removing duplicate `:root` token emission but does not mention the
contrast manifest entry. The findings ledger should make explicit that the
contrast pair stays registered and the contrast-clearance test continues
to gate the change.

## Recommended Implementation Slicing

If the findings ledger accepts this RFC, the implementation lane should
treat the four scope buckets in F-T2 as candidate disjoint slices. Items 1
and 5 carry the most behavioral risk (badge logic and snapshot/controller
boundary); items 3, 4, 6, and 7 are mostly code-shape changes. None of
the items requires a new RFC, and no item should bring forward any
deferred capability listed in RFC 0035 §Non-Goals.

## Evidence Reviewed

- `AGENTS.md`
- `docs/workflows/0047-ui-follow-up-cleanup/prompts/review_traceability.md`
- `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`
- `docs/workflows/0047-ui-follow-up-cleanup/roles/reviewer_traceability.md`
- `docs/rfcs/0035-ui-follow-up-cleanup.md`
- `docs/rfcs/0033-workspace-ui-rework.md`
- `docs/rfcs/0034-workspace-ui-follow-up.md`
- `docs/rfcs/README.md`
- `striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md`
- `striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md`
- `striatum/0046-slider-label-visibility/ledger/FINDINGS.md`
- `striatum/0047-ui-follow-up-cleanup/rfc_scope/RFC_SCOPE.md`

No product runtime files were modified by this review.
