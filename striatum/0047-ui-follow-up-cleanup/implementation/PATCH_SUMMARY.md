author: operator [self-declared: operator-0047-implement-findings]
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_9de519b70cdd40faa7dd8f862aa82d15
job: job_run_489eb28aa3e0453b916113addacd02e3_implement_findings
lease: lease_f41d7e303be9421d998f44cda9fd7942
date: 2026-05-14

# Patch Summary - Workflow 0047 UI Follow-Up Cleanup

## Scope

Implemented only the ledger-approved RFC 0035 UI cleanup slice. No backend
capability, REST route shape, hosted service, solver adapter, calibration,
final prediction, high-angle stability, watertight-readiness promotion,
web-side mesh-package authoring, or desktop parity rewrite was added.

## Changed Files

- `kayakgen/ui/web/controllers.py`: validity badges now scan all canonical web
  class envelopes through the existing five-field helper before custom fallback.
- `kayakgen/ui/web/app.py`: export menu rows render from `EXPORT_MENU_ROWS`;
  state snapshots use `STATE_SNAPSHOT_KEYS`; root theme CSS and rail CSS are
  split; preset seed listener behavior is retained with explicit seed-snapshot
  proof.
- `kayakgen/ui/desktop.py`: added the Matplotlib slider shim removal-condition
  comment only.
- `tests/test_web_layout.py`: added export schema, snapshot schema, preset
  seed/listener, preset edit, CSS injection, and no-claims-preserving layout
  assertions.
- `tests/test_web_read_models.py`: added all-class badge coverage, strict
  five-field web envelope coverage, and CFD alias compatibility coverage.
- `tests/test_web_browser.py`: added browser proof for exact named parameter
  row groups, one slider control per row, and updated the badge expectation.
- `docs/USER_GUIDE.md`: clarified the five-field preset rule, target-speed
  rule, and current-hull class-envelope badge behavior.
- `CHANGELOG.md`: recorded the landed workflow 0047 maintenance cleanup and
  deferrals.
- `docs/workflows/0047-ui-follow-up-cleanup/OPERATOR_REPORT.md`: added an
  implementation checkpoint.
- `striatum/0047-ui-follow-up-cleanup/implementation/PATCH_SUMMARY.md`: this
  artifact.

## Findings Status

| Finding | Status | Notes |
| --- | --- | --- |
| F1 | implemented | `validity_badge_from_state` uses `_matching_kayak_class` / `_hull_in_kayak_class` across all `CLASSES` before custom fallback. Tests cover custom state inside every canonical envelope, outside-envelope fallback, and a desktop-length/beam match that fails web `draft_m`/`Cp` envelope rules. |
| F2 | retained with proof | Presets still seed/narrow only `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, and `Cp`; hull-shaping edits flip to `custom`; `target_speed_kt` does not. The seed short-circuit is retained because browser validation showed Trame can fire same-seed hull events after preset application; a focused test now pins that event sequence. |
| F3 | implemented | `_render_export_menu` iterates `EXPORT_MENU_ROWS`; rows own labels, status, availability/disabled state, row classes, action keys, subtitles, and descriptions. Enabled rows remain Hull STL, Deck STL, and Hydro JSON. Stability JSON and Mesh package remain unavailable. |
| F4 | implemented | `STATE_SNAPSHOT_KEYS` declares current and legacy snapshot aliases. Tests cover optional `None` alias behavior, mesh-package aliases, and CFD status/payload/status-line compatibility without changing route payload shapes. |
| F5 | implemented with proof | `PARAMETER_RAIL_CSS` is scoped to slider labels and uses only `var(--type-label)` and `var(--text-secondary)`; `ROOT_THEME_CSS` is injected once globally; contrast manifest coverage remains intact. Browser proof asserts one named `role="group"` wrapper and one slider control per parameter row with byte-for-byte visible labels. |
| F6 | implemented | `_SLIDER_SUPPORTS_LABEL_LOCATION` now has a removal-condition comment. No desktop behavior changed, and bbox/gui tests still pass. |

## Visible Copy And Docs

- Export labels and visible subtitles are unchanged.
- The user guide now states that presets seed and narrow only the five
  canonical fields, that hull-shaping edits switch to `custom`, that target
  speed remains view state, and that the validity badge scans current hull
  values against canonical web envelopes before custom fallback.
- `CHANGELOG.md` records workflow 0047 as maintenance cleanup only and repeats
  the no-new-capability boundary.

## Validation

- `git diff --check`: passed with no output.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_read_models.py tests/test_ui_theme.py -q -p no:cacheprovider`: 39 passed in 9.81s.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider`: 1 passed in 10.41s.
- `PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider`: 4 passed in 3.19s.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`: 333 passed in 89.05s.

## No-Claims Gates

Confirmed the required forbidden-copy gates pass as part of the focused and
full test runs:

- `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
- `tests/test_web_layout.py::test_persistent_claim_readiness_and_cfd_copy_is_static_and_exact`

## Sub-Agent Usage

- Faraday, explorer, F1/F2 web semantics: confirmed all-class badge change,
  seed-branch treatment, preset edit tests, and user-guide wording.
- Dalton, explorer, F3/F4 web rendering/state hygiene: confirmed export-row
  schema and state snapshot alias coverage.
- Halley, explorer, F5 slider CSS/accessibility: confirmed root CSS split,
  token-only rail CSS, contrast coverage, and browser/static proof targets.
- Anscombe, worker, F6 desktop fallback: added the isolated desktop shim
  removal-condition comment in `kayakgen/ui/desktop.py`.
- Herschel, explorer, docs/changelog/tests: drafted narrow docs, changelog,
  operator-report, and patch-summary structure and noted pre-existing dirty
  workflow artifacts.

## Deferred

- Optional export label polish for `Mesh package...` remains deferred; visible
  export copy was intentionally preserved.
- New visual signals for non-canonical hull sliders, toolbar/drawer
  consolidation, desktop parity redesign, web hover tooltips, persistent inline
  values, hosted demo behavior, real solvers, calibration, high-angle stability,
  watertight-readiness promotion, and web-side mesh-package authoring remain
  deferred to future workflows.
