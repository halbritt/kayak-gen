# Patch Summary

## Summary

Implemented the ledger-approved RFC 0033 slice conservatively:

- Added `kayakgen/ui/theme.py` as the shared source for UI colors,
  typography, chip specs, matplotlib rcParams, Vuetify theme config, and VTK
  background RGB.
- Added immutable structured `Advisory` records alongside unchanged
  `DesignAdvisory.warnings`.
- Added pure web read-model helpers for status summary, resistance target rows,
  mesh diagnostics, and mesh package/profile views without changing REST JSON
  route shapes.
- Refactored the Trame shell toward a three-region workspace with stable region
  ids, grouped parameter rail, review tabs, persistent claim/readiness/CFD copy,
  status segments, share toast behavior, and responsive class hooks.
- Applied bounded desktop touch-ups: `Cm` control, `Export STLs` label with
  unchanged filenames, theme-sourced plot/PyVista colors, and four status
  vocabulary segments.
- Updated user-facing docs to describe the current workspace and desktop slice
  without claiming new backend capabilities.

No operator reports were edited by this implementation. No Striatum mutation
commands were run, `.striatum` was not edited, and no commit or push was made.

## Files Changed

- `docs/USER_GUIDE.md`
- `kayakgen/model/advisory.py`
- `kayakgen/ui/theme.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/gui_params.py`
- `kayakgen/ui/pv_window.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `tests/test_advisory.py`
- `tests/test_gui_params.py`
- `tests/test_ui_theme.py`
- `tests/test_web_browser.py`
- `tests/test_web_layout.py`
- `tests/test_web_read_models.py`
- `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md`

## Findings Resolved

- P0 workspace shell: added `region-params`, `region-geometry`, and
  `region-review` contracts, scan-order-aligned layout constants, review tabs,
  metrics strip, status bar segments, and first-viewport browser coverage.
- P0 parameter rail: grouped controls into Principal dimensions, Shape
  coefficients, and Ends and view; kept `target_speed_kt` out of `Hull`; kept
  unsupported fields out of the rail.
- P0 responsive collapse: added stable responsive class hooks for rail
  collapse, geometry accordion behavior, metrics scrolling, toolbar export
  collapse, and status wrapping.
- P0 review state/copy: added persistent Hydro, Mesh, Comparison, CFD, and
  Advisories copy for the safe-now states, including high-angle GZ deferral and
  CFD raw/local banners.
- P0 claim/readiness guardrails: preserved `uncalibrated_comparative`, raw
  comparative filter copy, high-angle unavailable copy, no-hosted-worker copy,
  raw solver artifact copy, and the allowed `not watertight cfd_ready` negation.
- P0 theme discipline: added theme tokens and tests for orphan color literals,
  VTK background parity, contrast pairs, and advisory-yellow/raw-orange
  separation.
- P0 structured advisories: added additive `Advisory` records from existing
  design-validity findings while keeping `warnings` compatible.
- P1 read models: added `evaluation_summary`,
  `mesh_diagnostics_lines_from_state`, `mesh_package_view_model`, and
  `resistance_table_view_model`.
- P1 mesh/profile handling: welded counts are primary with raw counts retained;
  `open-wetted-surface` and `watertight-solid` map explicitly to canonical
  profile IDs.
- P1 resistance target row: target speeds more than `0.05 kt` from fixed sweep
  speeds are inserted as sorted target rows.
- P1 desktop touch-ups: added `Cm`, renamed export button, routed plot/PyVista
  colors through theme, and added status vocabulary.
- P1 CFD/comparison tightening: kept CFD unavailable/raw state copy visible and
  preserved existing local route/controller behavior.

## Explicit Deferrals

- PyVista docking remains deferred; the desktop 3D view still opens in the
  existing separate PyVista window.
- Full desktop Review-tab/chip/focus parity remains deferred; desktop status is
  vocabulary only.
- No hosted/cloud CFD workers, worker queue, real solver adapter, calibrated
  drag, final prediction, high-angle GZ numeric output, watertight-solid
  readiness claim, Pareto plot widget, or web-side mesh-package authoring API
  was added.
- Root `CHANGELOG.md` was not edited because it is outside this job's write
  scope.

## Validation

- `git diff --check` -> passed.
- `.venv/bin/python -m pytest -q` -> `291 passed in 57.49s`.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_ui_theme.py -q`
  -> `43 passed in 4.34s`.
- `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  -> `1 passed in 5.84s`.

Browser acceptance dependencies were available in this environment; no required
browser checks were skipped.

## Proposed Changelog Entry

```markdown
- Added the RFC 0033 workspace UI slice: shared UI theme tokens, structured
  advisory records, web workspace regions/status copy, mesh/readiness read
  models, desktop `Cm`/Export STLs touch-ups, and regression tests. Current
  resistance, mesh, and CFD outputs remain raw/open-surface/local plumbing and
  are not final prediction, watertight-solid, hosted-worker, or calibrated
  claims.
```

## Sub-Agent And Parallel Assistance

- Theme/tests helper: implemented `kayakgen/ui/theme.py` and
  `tests/test_ui_theme.py`.
- Advisory helper: implemented additive `Advisory` records and
  `tests/test_advisory.py`.
- Read-model helper: implemented `evaluation_summary`, mesh/package helpers,
  target-speed resistance rows, and `tests/test_web_read_models.py`.
- Web shell helper: implemented workspace constants/layout refactor and
  `tests/test_web_layout.py`.
- Desktop/docs helper: implemented desktop `Cm`, export label, theme color
  routing, status vocabulary, docs, and GUI parameter tests.
- Forbidden-copy explorer: supplied the exact required/forbidden copy checklist
  used during integration.
- Integrator pass: resolved cross-scope theme lint issues, preserved browser
  share round-trip behavior without a pinned Shareable URL field, restored
  stable VTK viewport sizing, ran required validation, and wrote this summary.
