author: reviewer-traceability-claude-opus-4.8-002

# Workflow 0060 — Traceability Review (RFC 0065 Slice 3)

**Verdict: `accept_with_findings`**

Every change in workflow 0060 traces to RFC 0065 §3 or a row of
`SLICE_3_DECISIONS.md` (D1–D8). The slice is presentation-only: control
interaction states and per-panel empty/loading/error states. No scope creep
into Slice 1 (tokens), Slice 2 (layout), or Slice 4 (docs/a11y/D047) was found.
One actionable D6 coverage gap (F1, low severity) and two minor observations
are recorded for the remediation lane.

Reviewed surfaces: `kayakgen/ui/web/app.py` (+222), `generate_frontier_view.py`
(+21/-8), `tests/test_web_layout.py` (+115), `tests/test_web_inline_help.py`
(+31), `CHANGELOG.md` (+10). Verified `.venv/bin/python -m pytest
tests/test_ui_theme.py tests/test_web_layout.py tests/test_web_inline_help.py
-q` → **59 passed**.

## Traceability ledger (D1–D8)

- **D1 — uniform control states from tokens — PASS.** `WORKSPACE_SHELL_CSS`
  (app.py ~408–470) adds default/hover/focus/active/disabled rules over
  `.v-btn`, `.v-tab`, `.v-field`, `.v-slider`, `.v-selection-control`,
  `select`, `input`, `textarea`, `button`. The Slice-2-deferred focus-ring
  (workflow 0059 ledger S1) is **reintroduced uniformly**: every control type
  receives `:focus-visible`/`:focus-within` →
  `outline: var(--state-focus-ring-width) var(--border-style-solid)
  var(--state-focus-ring)` — not a partial subset (D1's explicit requirement).
  All values are tokens; no literals.
- **D2 — honestly-disabled controls keep copy — PASS.** No `-`/`+` edits to
  `WATERTIGHT_DISABLED_COPY`, `EXPORT_MENU_ROWS`, the Cm reserved-preset path,
  or the `submit-blocking-reason-*` copy (grep over `git diff kayakgen/`
  confirms only hunk-context/`PERSISTENT_COPY`-insertion lines). The disabled
  rule restyles (`--state-disabled-surface/-text`, `cursor: not-allowed`) and
  adds an `[aria-disabled="true"]` selector — it never enables a control or
  removes `aria-disabled`.
- **D3 — explicit states with stable hooks — PASS.** New/confirmed
  `data-testid` hooks: jobs `generative-jobs-{empty,running,failed,cancelled,
  resumable}-state` (`_generative_job_state_flags`), with
  `GenerativeJobError.kind` surfaced via `generative_jobs_failed_kind` and a new
  "Error kind" VDataTable column; frontier `frontier-view-{loading,empty,
  rendered}` (generate_frontier_view.py); `comparison-no-report-state` /
  `comparison-report-present-state` alongside the preserved
  `comparison-live-frontier-block` / `-imported-report-block`;
  `cfd-no-job-state` / `cfd-status-state` with **both** CFD banners intact;
  `invalid-hull-state`; `share-url-state` (now `aria-live="polite"`). The mesh
  chip pair is pre-existing and pinned.
- **D4 — copy byte-stable — PASS.** No `CHIP_SPECS`/`CHIP_LABELS`/`CHIP_CLASSES`
  edits; no persistent caption edits. No chip recoloured. State panels draw from
  `--state-info*`, `--state-error*`, `--state-advisory*`, `--state-focus-row`,
  `--text-primary` — **never the success palette** (`--state-success*` is not
  used by any new rule), so no failed/empty/loading surface reads as a
  validated/confident claim. New state strings are pinned exactly in
  `test_persistent_claim_readiness_and_cfd_copy_is_static_and_exact` (jobs ×5,
  frontier ×2, invalid-hull) and via byte-exact presence assertions.
- **D5 — hook discipline + token-only — PASS.** Every new/changed hook
  (invalid-hull, comparison-no-report/report-present, cfd-no-job/status,
  generative-jobs-* ×5, frontier-view-loading/empty/rendered, share-url-state)
  appears in **both** `tests/test_web_layout.py`
  (`test_slice3_empty_loading_error_state_hooks_are_rendered`) **and**
  `tests/test_web_inline_help.py`
  (`test_slice3_state_hooks_are_present_in_inline_help_contract`). Every token
  used by the new CSS is already defined in **both** `theme.py` palettes (state
  colours L45–69 / L114–134; `space-1..3`, `radius-sm`, `border-*`,
  `state-focus-ring-width`, `surface-muted/-border`, `text-*`, `type-caption`).
  `theme.py` is **not** modified → no token re-typed/removed, no additive token
  needed. The widened `tests/test_ui_theme.py` orphan lint is green (59-pass
  bundle). Slice 2 region hooks `region-params/-geometry/-review`, the four
  status segments, 1440×900 first-viewport, and ≤960 px collapse all persist.
- **D6 — forbidden-copy scan extended — PARTIAL (see F1).** New app.py strings
  are scrubbed and the no-go list stays absent; new frontier strings are
  presence-asserted but **not** scrubbed (the changed render file is excluded
  from the no-go scan).
- **D7 — RFC 0032 boundary intact — PASS.** No new REST route, `claim_state`,
  `Readiness`, or `accepted_uses` literal (grep clean). The failed-state column
  reads an **existing** field (`GenerativeJobError.kind`) via the existing
  `_generative_manager.get(...)`; it adds no evaluator/analysis surface.
- **D8 — docs footprint CHANGELOG only — PASS.** Working tree touches only
  `CHANGELOG.md`; `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`,
  `docs/DECISION_LOG.md` (D047), and the harness/`workflow.json` are untouched.

## Scope-creep scan — clean

No layout/hierarchy re-flow beyond control + state styling (state panels are
inserted into existing containers; the "Error kind" column traces to D3's
"`GenerativeJobError.kind` in the jobs table"). No re-typed/removed token. No
harness / WEB_VERIFICATION / USER_GUIDE change; no D047 ratification. No touched
`CHIP_*` entry or persistent caption; no recoloured chip. No new
route/`claim_state`/`Readiness`/`accepted_uses` literal.

## Findings

### F1 — D6 no-go scrub does not cover the changed frontier render file (low, actionable)

`tests/test_web_layout.py:397`
(`test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`)
builds two source bundles:

```python
render_source = "\n".join([app_source, controllers_source, spec_form_source])
new_state_source = "\n".join([render_source, frontier_source])
...
scrubbed = render_source            # ← frontier_source NOT included
for forbidden in (...): assert forbidden not in scrubbed
for state_copy in (...): assert state_copy in new_state_source   # presence only
```

`generate_frontier_view.py` (`frontier_source`) is the file this slice actually
added rendered strings to ("Loading Pareto frontier.", "Pareto frontier
rendered."), yet it feeds only the **positive presence** loop — the no-go scrub
(`GZ_max`, `OpenFOAM`, `final prediction`, `hosted`, `cloud`, …) runs over
`render_source`, which **excludes** it. D6 requires the scan be *extended so
every NEW rendered string the slice introduces is covered*; here the newly
edited render surface escapes the actual no-go scrub. The inversion is sharpened
by the scan being widened to `spec_form_source` (a file this slice did **not**
change) while omitting the file it did change. Impact is low — the two new
frontier strings are benign and pass — but D6 is a hard gate and this leaves a
genuine coverage hole. Note: the ops_tests peer review (item #2) reads this as
"successfully extended"; that conflates the presence assertions with the no-go
scrub. **Remediation:** scrub over `new_state_source` (or include
`frontier_source` in `render_source`) so the no-go list runs across the frontier
render surface.

## Observations (non-blocking)

- **O1 — hover/active narrower than focus/disabled (D1).** `:hover` and
  `:active` rules apply to `.v-btn`/`.v-tab`/native `select`/`input`/`textarea`/
  `button` but not to `.v-field`/`.v-slider`/`.v-selection-control`; focus and
  disabled *do* cover all control types. D1's hard requirement — the deferred
  focus-ring reintroduced **uniformly** — is met; restricting hover/active away
  from Vuetify slider/toggle/field internals (which carry their own hover) is a
  defensible presentation choice, noted only against the literal "uniform …
  hover … active" wording.
- **O2 — per-row `_generative_manager.get()` (efficiency).** The jobs listing
  now calls `get(job_id)` per row to read `error.kind` — an N+1 read of data the
  manager already holds. Traceable to D3 and within the D7 boundary (no new
  route/analysis); flagged purely as an efficiency follow-up for remediation.

## Out of scope (confirmed not regressed here)

Playwright/contrast/Lighthouse a11y gates, `WEB_VERIFICATION.md` + `USER_GUIDE.md`
updates, D047 ratification (all Slice 4); the pre-existing NB-2
`tests/test_services_boundaries.py` import-boundary failure (workflow 0059 S2).
