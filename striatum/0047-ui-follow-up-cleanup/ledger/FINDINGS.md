author: operator [self-declared: operator-0047-findings-ledger]
schema_version: striatum.findings_ledger.v1
kind: findings_ledger
logical_name: ledger
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_b6719f29507449dcb456300d1c315d19
job: job_run_489eb28aa3e0453b916113addacd02e3_findings_ledger
lease: lease_8f8a97a70f9f465a8f09279d1efa79a9
date: 2026-05-14

# Findings Ledger - Workflow 0047 UI Follow-Up Cleanup

## Gate Verdict

`accept_with_findings`

Implementation may proceed as a narrow RFC 0035 cleanup slice. The four
first-pass reviews found no blocker and no disguised backend, solver,
calibration, stability, watertight-readiness, or desktop-parity work. This
ledger is the implementation boundary: fix the small UI semantics,
source-of-truth, accessibility/CSS, desktop-fallback, tests, and docs issues
below without widening the capability surface.

The first-pass review set deduplicates to six safe-now findings. Optional copy
polish and broad UI redesign remain deferred.

## Source Review Treatment

| Source review | Verdict | Ledger treatment |
| --- | --- | --- |
| `traceability/REVIEW_TRACEABILITY.md` | `accept_with_findings` | Accept the mapping from workflow 0045 F1-F5 and workflow 0046 M1-M3 to RFC 0035. Carry the badge, snapshot, contrast, and disjoint-scope cautions forward. |
| `no_claims/REVIEW_NO_CLAIMS.md` | `accept` | Accept as the hard no-overclaim boundary. Keep forbidden capability claims out of implementation and docs. |
| `ergonomics/REVIEW_ERGONOMICS_DESIGN.md` | `accept_with_findings` | Accept the user-visible refinements around exact badge strings, export subtitle drift, slider accessibility, CSS scoping, preset wording, dead-branch cleanup, and desktop fallback bounds. |
| `ops/REVIEW_OPS.md` | `accept_with_findings` | Accept the required test gates, especially badge ambiguity, export single-source tests, snapshot compatibility, CSS token injection proof, accessibility proof, and docs/changelog discipline. |

## Safe-Now Findings

### F1 - Web validity badge must scan all canonical web class envelopes

Severity: Medium

Source reviews: traceability F-T1; ergonomics E1; ops O1; workflow 0045
final review F1.

Scope: `kayakgen/ui/web/controllers.py` and focused read-model tests.

Ledger decision:

- Update `validity_badge_from_state` to scan all `CLASSES` before falling
  back to the current L/B_wl custom branches.
- Use the web canonical class-envelope helper (`_hull_in_kayak_class` /
  `_matching_kayak_class`) so the scan covers the five RFC 0034 preset fields:
  `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, and `Cp`.
- Treat desktop `_classify` as the precedent for scanning all classes, not as
  a function to import or copy. Desktop's short classifier checks fewer fields
  and returns longer custom strings.
- Preserve the accepted web badge vocabulary exactly:
  `In <class> envelope`, `Custom — sub-touring`,
  `Custom — beyond elite`, and `Custom (L/B_wl=X.X)`.
- Do not change `class_preset_options`, `class_preset_read_model`,
  class-preset IDs, preset reseeding, slider narrowing, or the class
  definitions.

Required tests:

- `class_preset="custom"` with hull values inside a canonical class envelope
  returns `In <class> envelope`.
- A hull outside every five-field canonical envelope still returns one of the
  accepted custom strings.
- A hull that would match desktop's length/beam-only classifier but fails
  web's `draft_m` or `Cp` envelope is pinned to the chosen web-canonical
  behavior, so the intentional boundary is visible.
- Existing exact-string tests for sub-touring, beyond-elite, and
  `Custom (L/B_wl=X.X)` stay green.

### F2 - Preset edit semantics and the seed short-circuit must be explicit

Severity: Low

Source reviews: traceability F-T2; ergonomics E6/E7; ops O2; workflow 0045
final review F2/F3.

Scope: `kayakgen/ui/web/app.py`, focused layout/read-model tests, and
`docs/USER_GUIDE.md`.

Ledger decision:

- Keep the RFC 0034 edit model: class presets seed and narrow only
  `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, and `Cp`.
- Manual edits to hull-shaping rail fields continue to switch
  `class_preset` to `custom`.
- `target_speed_kt` remains view state and must not switch the preset to
  `custom`.
- Remove `_state_matches_preset_seed` if no reachable event sequence depends
  on it. If implementation retains it, add a focused test documenting the
  exact reachable same-value/seed event sequence.
- Add one user-guide sentence for the preset rule. Do not add new visual
  markers, rail grouping, selector consolidation, or broader preset UI.

Required tests/docs:

- Preserve or add tests for five-field reseed/narrow behavior.
- Preserve or add tests that non-canonical hull edits switch to `custom`.
- Preserve or add tests that `target_speed_kt` does not switch to `custom`.
- If the seed branch remains, add a focused event-sequence test. If removed,
  existing preset/browser coverage must remain green.
- Update `docs/USER_GUIDE.md` only for the user-visible preset rule.

### F3 - Export menu must have one row schema without silent visible-copy drift

Severity: Low

Source reviews: traceability F-T2; ergonomics E2/E3; ops O3; workflow 0045
final review F4.

Scope: `kayakgen/ui/web/app.py`, `tests/test_web_layout.py`, and browser
checks if visible menu behavior changes.

Ledger decision:

- Render `_render_export_menu` by iterating `EXPORT_MENU_ROWS`.
- Make the row schema own labels, availability, disabled states, row classes,
  actions/action keys, and visible guidance copy.
- Prefer zero visible-copy change: carry the currently shipped compact
  subtitles into the row schema, or split visible `subtitle` from longer
  read-model `description` if both are needed.
- Keep enabled rows limited to existing safe local actions: Hull STL, Deck
  STL, and Hydro JSON.
- Keep Stability JSON and Mesh package unavailable unless a later workflow
  accepts additional web-side behavior.
- Do not silently change `Mesh package...`; label polish such as
  `Mesh package` or `Mesh package (CLI only)` is optional and requires an
  explicit changelog note if it lands.

Required tests/docs:

- Static tests fail if rendered labels, disabled states, row classes, or
  guidance copy drift from `EXPORT_MENU_ROWS`.
- Browser acceptance continues to see the same honest enabled/unavailable
  rows.
- If visible copy changes, update `CHANGELOG.md` factually as UI cleanup.

### F4 - Web state snapshot needs a declared schema and compatibility proof

Severity: Low

Source reviews: traceability F-T3; ops O4; workflow 0045 final review F5.

Scope: `kayakgen/ui/web/app.py`, optionally `kayakgen/ui/web/state.py`, and
focused tests.

Ledger decision:

- Replace the ad-hoc `_state_snapshot` key list with a small named schema or
  key tuple.
- Preserve public route payload shapes and controller/read-model behavior.
- Preserve current optional and legacy alias keys unless tests prove they are
  unused: `mesh_package_ref`, `cfd_mesh_package_ref`, `cfd_status`, `status`,
  `cfd_payload`, `cfd_job_payload`, `cfd_last_payload`, and
  `cfd_status_lines`.
- Do not add REST routes, new route fields, hosted behavior, worker queues, or
  cloud storage.

Required tests:

- Snapshot compatibility test covers current keys and optional missing-key
  behavior.
- `_cfd_status_from_state` alias behavior remains compatible for status,
  payload, and status-line inputs.
- Mesh package refs continue to feed the existing read models without changing
  route payload shapes.

### F5 - Slider-label CSS and accessibility cleanup must be proof-oriented

Severity: Low

Source reviews: traceability F-T4; ergonomics E4/E5; ops O5/O6; workflow
0046 final review M2/M3.

Scope: `kayakgen/ui/web/app.py`, `kayakgen/ui/theme.py`, static layout/theme
tests, and browser accessibility/geometry tests.

Ledger decision:

- Split root token injection from the rail-specific CSS before removing the
  duplicate root block. If `PARAMETER_RAIL_CSS` becomes only the scoped
  `.kg-param-slider .v-slider__label` rule, the web layout must still inject
  `theme.css_root_block()` once globally.
- Keep `PARAMETER_RAIL_CSS` using existing tokens only:
  `var(--type-label)` and `var(--text-secondary)`.
- Preserve the `slider.label.rail` contrast manifest pair and its contrast
  test.
- Keep canonical visible slider labels byte-for-byte.
- Keep the current wrapper model for the implementation slice unless browser
  proof shows it creates duplicate or unclear named row semantics. The
  expected rule is exactly one named `role="group"` wrapper per parameter row,
  with the control's accessible name synchronized with the same canonical
  visible label.
- Do not redesign the rail, add persistent inline values, change focus rings,
  add new tokens, or alter slider bindings/ranges/defaults.

Required tests:

- Layout tests assert rail CSS token usage; theme tests assert token
  definitions and `slider.label.rail` contrast.
- Static tests assert wrapper role/ARIA attributes for the chosen model.
- Browser tests assert visible label geometry and the chosen accessible-name
  cardinality, not just that the label appears somewhere in the subtree.

### F6 - Desktop slider fallback stays bounded and removable

Severity: Low

Source reviews: ergonomics E8; workflow 0046 final review M1.

Scope: `kayakgen/ui/desktop.py` and desktop layout tests if touched.

Ledger decision:

- Keep `_SLIDER_SUPPORTS_LABEL_LOCATION` as a Matplotlib compatibility shim
  until the project version floor supports `widgets.Slider(label_location=...)`.
- Add a short removal-condition comment next to the shim if implementation
  touches the file.
- Keep the rendered bounding-box tests as the guard for label/value
  legibility.
- Do not widen this into a desktop parity rewrite, Qt-native slider rewrite,
  `QMainWindow` migration, new layout, or changed slider semantics.

Required tests:

- If desktop code changes, run the desktop bbox/gui parameter tests.
- Do not loosen bbox thresholds to make the fallback pass.

## Implementation Slicing

Use disjoint write scopes so any single bucket can be deferred without
unwinding the others:

- Web semantics: F1 and F2 (`controllers.py`, preset listener code, focused
  tests, user-guide sentence).
- Web rendering/state hygiene: F3 and F4 (`app.py`, optional `state.py`,
  layout/read-model tests).
- Web slider CSS/accessibility: F5 (`app.py`, `theme.py`, static/theme/browser
  tests).
- Desktop fallback: F6 (`desktop.py`, desktop bbox tests).
- Docs/changelog: only user-visible cleanup, accepted behavior, and workflow
  status. Invisible refactors do not need standalone user-guide prose.

## No-Overclaim Boundary

Do not implement or imply any of the following:

- Desktop parity rewrite, Qt-native slider rewrite, `QMainWindow` migration,
  or broader desktop layout redesign.
- New backend capability, REST route shape, hosted service, hosted CFD, worker
  queue, cloud storage, auth/cancellation, or hosted-demo behavior.
- OpenFOAM, SU2, Docker/container execution, or any real solver adapter.
- Calibrated drag, accepted final prediction, final design fitness, or a new
  resistance validity envelope.
- Real high-angle `GZ`, `GZ_max`, `heel_angle_max_deg`, capsize range, or
  secondary-stability numeric claims.
- Web-side mesh-package authoring beyond existing safe entries and local/CLI
  guidance.
- Watertight-solid promotion, current generated-package solver readiness, or
  bare `cfd_ready` promotion.
- New class definitions, hull geometry parameters, mesh profiles, solver
  readiness states, or domain concepts.

The existing forbidden-copy and persistent-copy tests remain required gates.
Docs and changelog must describe only cleanup and current safe behavior.

## Required Validation For Implementation Lane

Minimum focused gates:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_read_models.py tests/test_ui_theme.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

If desktop code changes:

```bash
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
```

Before final review if both web and desktop surfaces change:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

No-claims gates to preserve:

- `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
- `tests/test_web_layout.py::test_persistent_claim_readiness_and_cfd_copy_is_static_and_exact`

## Explicit Deferrals

- Optional export label polish for `Mesh package...` may be deferred.
- New visual signals for non-canonical hull sliders are deferred.
- Toolbar/drawer preset-selector consolidation is deferred.
- Desktop focus-ring, Qt-native slider, matplotlib accessibility-layer, and
  desktop layout redesign work are deferred.
- Web hover tooltips, persistent inline numeric values, richer comparison/plot
  surfaces, hosted browser/demo acceptance, and public service behavior are
  deferred.
- Any real solver, calibration, high-angle stability, watertight-readiness,
  mesh-authoring, or backend capability work requires a separate RFC/workflow.

## Patch Summary Requirements

The implementation patch summary should list:

- Which of F1-F6 were implemented, retained with proof, or explicitly
  deferred.
- Any visible copy changes, especially export subtitles or labels.
- Tests run and results.
- Confirmation that forbidden-copy/no-claims gates still pass.
- Docs and changelog updates, limited to user-visible cleanup and workflow
  status.
