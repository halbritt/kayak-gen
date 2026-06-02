# Workflow 0061 Traceability Review

author: reviewer-traceability-claude-opus-4.8-001
date: 2026-06-02

## Verdict

**accept_with_findings** — every change under workflow 0061 traces to RFC 0065 §5
or a row in `SLICE_4_DECISIONS.md` (D1–D8). No scope creep that warrants
`needs_revision`. Three advisory findings (all low/informational, remediable in
this run) are recorded below.

## Scope of changes reviewed

Working-tree diff (uncommitted) — 11 files, +288/-17:

- `CHANGELOG.md`, `docs/DECISION_LOG.md`, `docs/USER_GUIDE.md`,
  `docs/WEB_VERIFICATION.md` (docs, D8)
- `kayakgen/ui/web/app.py` (focus-ring CSS + CSS-injection rewrite)
- `tests/test_web_browser.py` (hard gate + a11y)
- `tests/test_web_layout.py` (source-shape assertions follow the app.py change)
- `tests/visual_baselines/{1440x900,1024x768,960x720}.png` (regenerated)
- `tests/visual_baselines/README.md`

`kayakgen/ui/theme.py` and `tests/test_ui_theme.py` are **not** modified — so the
`CONTRAST_MANIFEST` / `theme.py` additive constraint (D4) is trivially satisfied
(zero change).

## Decision-by-decision traceability

| # | Decision | Status | Evidence |
| --- | --- | --- | --- |
| D1 | Baselines regenerated on canonical env, explained diff, BEFORE hard flip | **Traces** | Three PNGs regenerated via `--update-visual-baselines` (PATCH_SUMMARY Verification: `3 passed`). Canonical env recorded identically in `tests/visual_baselines/README.md` and `docs/WEB_VERIFICATION.md` (Linux 6.8.0-111, Playwright Chromium `147.0.7727.15` / chromium-1217, capture `2026-06-02`). Explained diff in PATCH_SUMMARY "Baseline Diff Review" + per-file byte-size deltas. VTK region masked (`VISUAL_MASK_FILL`, `test_web_browser.py:43`). See F2. |
| D2 | Visual compare = HARD gate; SKIP/HARD posture | **Traces** | `test_web_browser.py:816` now calls `_load_playwright`/`_launch_chromium` (non-optional) + `_browser_acceptance_required`; missing PW/Chromium → `pytest.fail` under acceptance, `pytest.skip` otherwise (`test_web_browser.py:71-103`). Missing baseline and over-tolerance mismatch both `pytest.fail` when acceptance-required (`:847-868`). VTK mask retained. |
| D3 | Documented per-viewport tolerance; demonstrably FAILs | **Traces (w/ F1)** | `VISUAL_PIXEL_CHANNEL_TOLERANCE = 8`, `VISUAL_MISMATCH_PIXEL_RATIO = 0.02` (`test_web_browser.py:43-44`), documented in `WEB_VERIFICATION.md` "Visual Baselines" + D047. Each viewport compared independently (parametrized). FAIL-not-no-op shown by PATCH_SUMMARY injected diff (`passed=False`, ratio `0.079`). See F1 (no committed self-test). |
| D4 | a11y checks present + deterministic; theme additive; fixes minimal/token-sourced | **Traces** | `_assert_workspace_focus_order_and_ring`, `_assert_workspace_hit_targets` (24 px), `_assert_contrast_manifest` wired into `test_kayakgen_serve_browser_acceptance` (`:902-904`). Contrast also stays a no-browser mandatory gate — pre-existing `tests/test_ui_theme.py:149 test_contrast_manifest_clears_thresholds`, parametrized over `COLORS_LIGHT`/`COLORS_DARK` (both palettes), unchanged. Only UI fix is the focus-ring selector extension to `.kg-toolbar-action` / `.kg-export-menu-under-1200` / `.kg-class-preset-select` using the Slice 1 `--state-focus-ring` token (`app.py:442-450`). `theme.py`/`CONTRAST_MANIFEST` unchanged → additive. |
| D5 | Lighthouse ≥ 90 recorded, not a pytest gate | **Traces** | Best Practices `1.0` (100) recorded in `WEB_VERIFICATION.md` ("RFC 0065 Slice 4 result") + PATCH_SUMMARY. No pytest test asserts Lighthouse (grep clean); gate table marks it "Optional … do not make it a pytest gate". |
| D6 | Retain every behavioural acceptance check | **Traces** | nonblank-3D before/after (`:905,961,1010`), Share-URL reload round-trip (`:987-1010`, asserts `shared_hull.length_m != Hull().length_m` then mutated metrics persist on reload), STL via `POST /api/stl?part=hull` and `part=deck` (`:1013-1056`), console/page/network cleanliness (`_collect_browser_failures` + `_assert_no_browser_failures`, `:1057`). No network-allowlist entry added. |
| D7 | Claim line + RFC 0032 boundary intact | **Traces** | `CHIP_*` and captions byte-identical (not in diff); `app.py` diff adds no `CHIP_*`/route/`claim_state`/`Readiness`/`accepted_uses` literal (grep clean). `ROOT_THEME_CSS`/`PARAMETER_RAIL_CSS` content unchanged (only injection mechanism). USER_GUIDE addition is explicitly "presentation-only … does not add routes, evaluators, solver capability, or new claim/readiness states". RFC 0033 §8 no-go terms absent from new prose. Rendered chip-colour confirmation delegated to reviewer_claims (PASS). See F3. |
| D8 | Docs updated + D047 ratified | **Traces** | `WEB_VERIFICATION.md`: baseline-update procedure (canonical OS+Chromium, regen command, reviewed-diff expectation) + mandatory-vs-optional gate table. `USER_GUIDE.md`: polish + gate, presentation-only. `DECISION_LOG.md`: D047 `proposed` → `accepted`, recording tolerance (delta `8`, ratio `0.02`) and in-repo PNG storage. `CHANGELOG.md`: Slice 4 entry. |

## Scope-creep assessment

No blocking scope creep. Checked against the role's flag list:

- **No** new analysis surface / REST route / `claim_state` / `Readiness` /
  `accepted_uses` literal (grep of `app.py` diff clean).
- **No** `CHIP_*` or persistent-caption change; **no** recoloured chip
  (`theme.py` untouched; CSS content unchanged).
- **No** non-additive `CONTRAST_MANIFEST` / `theme.py` change (both untouched).
- **No** new capability/availability language in the docs (USER_GUIDE/​
  WEB_VERIFICATION additions are presentation- and verification-only and
  explicitly disclaim new capability).
- The known NB-2 `tests/test_services_boundaries.py` services→ui import-boundary
  failure stays out of scope (PATCH_SUMMARY Verification flags it as the single
  known failure; no Slice 4 file touches it).
- The CSS-injection rewrite (F2) is a functional change to rendered output, but
  it is traceable to D1/D2 and is not a new layout/visual design — see F2.

## Findings

### F1 — D3: hard-gate teeth rest on manual evidence, not a committed self-test (low, advisory)

`_compare_visual_png` (`tests/test_web_browser.py:315`) is exercised in-repo only
by the live actual-vs-baseline compare, which is expected to **pass**. D3's
"must demonstrably FAIL on an over-tolerance diff (not a no-op)" is satisfied
only by PATCH_SUMMARY's manual injected-diff evidence (`passed=False`,
`mismatch_ratio=0.079`, `max_channel_delta=255`). That evidence is not pinned by
a committed regression test, so a future refactor of `_compare_visual_png` or the
tolerance constants could silently neuter the gate without any test going red.

**Remediation (this run):** add a no-browser unit test that feeds two synthetic
PNGs differing beyond `VISUAL_PIXEL_CHANNEL_TOLERANCE` / `VISUAL_MISMATCH_PIXEL_RATIO`
and asserts `VisualCompareResult.passed is False`, plus an under-tolerance case
asserting `passed is True`. Owner: ops_tests / remediation lane. Non-blocking —
the gate is functionally correct today.

### F2 — D1/scope: the `workspace_style_html` CSS-injection rewrite is traceable but larger than a "minimal a11y fix" (informational)

`app.py:819-820` + `:1872` replace the two `html_widgets.Style(ROOT_THEME_CSS)` /
`Style(PARAMETER_RAIL_CSS)` calls (which `SinglePageWithDrawerLayout` dropped, so
the token CSS was **inert in Chromium**) with a `state.workspace_style_html`
`<style>` block rendered into `layout.content`. This is what makes the Slice 2/3
tokenized shell actually render in the browser — and therefore is a **precondition**
for D1's baselines to capture the true post-Slice-2/3 appearance and for the D2
hard gate to be meaningful. It is the explanation for the large (~30 %) PNG growth
(`1440x900`: 118617→154476 bytes).

This traces to D1/D2 and introduces **no** new visual design (the CSS strings are
byte-unchanged; only the injection mechanism changed), so it is not a layout
re-flow in the prohibited sense. Flagged for reviewer awareness because the
"explained diff" (D1) is materially "previously-absent CSS rendering for the first
time," not a small reflow — PATCH_SUMMARY's Baseline Diff Review owns this, so D1
holds. `tests/test_web_layout.py:152-153` was updated in lockstep to assert the
new source shape. Non-blocking.

### F3 — D7: rendered chip-colour confirmation delegated to reviewer_claims (informational)

From the traceability angle, no chip recolour is introduced at source:
`CHIP_SPECS`/`CHIP_LABELS`/`CHIP_CLASSES` and captions are byte-identical (not in
the diff) and the theme CSS content is unchanged. Pixel-level confirmation that
the regenerated screenshots bake no raw/unvalidated result into a confident
treatment is the claims reviewer's concern; the sibling `reviews/claims/REVIEW.md`
records **PASS** on exactly this. Noted for completeness; no action.

## Note (non-finding)

The canonical Chromium build recorded for the baselines moved from Slice 0's
`148.0.7778.96` (v1223) to `147.0.7727.15` (v1217). This is consistent across all
three surfaces (`visual_baselines/README.md`, `WEB_VERIFICATION.md`,
PATCH_SUMMARY) and reflects the actual host build used for the regeneration — not
an inconsistency.
