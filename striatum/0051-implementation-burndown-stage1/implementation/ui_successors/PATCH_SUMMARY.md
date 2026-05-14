author: implementer-codex-gpt-5.5-007
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_d80e8ca7c68b4ccbae6142ed7d2c63aa
job: job_run_c6989300a86c4c6cb66e44555bb19067_implement_ui_successors
lease: lease_aba9189a89764779add29acd16009090
date: 2026-05-14

# Patch Summary - UI Successor Cleanup RFCs 0036-0039

## Scope

Implemented the workflow 0051 UI-maintenance lane for RFCs 0036-0039. The
change is limited to the Trame web app, web read-model/controller tests,
browser acceptance, and this workflow-local artifact. It does not change REST
payload shapes, export availability, backend capability, solver behavior,
mesh-package authoring, readiness promotion, resistance claims, or CFD claims.

## Changes

- RFC 0036: retained `_state_matches_preset_seed` because the browser path is
  real. A removal attempt caused the browser test to select `surfski_elite`,
  reach the seeded length value, then observe custom global bounds
  (`aria-valuemin=2.0`) instead of the preset bounds. The retained path is now
  pinned in `tests/test_web_browser.py`: selecting `surfski_elite` through the
  real Trame page must leave the elite radio checked and the preset slider
  bounds active; reselecting the same preset keeps those bounds; only an actual
  length slider edit flips the selector to `custom`. The focused
  `tests/test_web_layout.py` regression still covers direct same-seed listener
  behavior.
- RFC 0037: removed duplicate `description` fields from `EXPORT_MENU_ROWS`.
  `subtitle` is now the only export-row guidance-copy field, and tests assert
  the exact row key set, labels, availability, disabled states, row classes,
  action keys, and rendered-schema ownership.
- RFC 0038: changed the disabled mesh-package export label from
  `Mesh package...` to `Mesh package (CLI only)`. The row remains disabled and
  unavailable in the browser, with the existing subtitle pointing users to
  `kayakgen mesh-package`.
- RFC 0039: added `WebStateSchema` in `kayakgen/ui/web/state.py` to own
  snapshot keys and CFD/mesh compatibility aliases. The app snapshot helper,
  mesh package state lookup, and controller CFD status/readiness readers now
  consume that shared schema source.

## Files Changed

- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/state.py`
- `tests/test_web_browser.py`
- `tests/test_web_layout.py`
- `tests/test_web_read_models.py`
- `striatum/0051-implementation-burndown-stage1/implementation/ui_successors/PATCH_SUMMARY.md`

## Validation

- `python -m pytest tests/test_web_layout.py tests/test_web_read_models.py -q`
  - Result: 30 passed.
- `python -m pytest tests/test_web.py -q`
  - Result: 27 passed.
- `python -m pytest tests/test_web_browser.py -q`
  - Result: 1 passed.
- `python -m compileall kayakgen/ui/web`
  - Result: clean.
- `git diff --check`
  - Result: clean.

## Notes

The visible mesh-package label changed in the web UI and is pinned by focused
tests. User-guide/changelog files were outside this lane's write scope; the
current user guide did not contain the old `Mesh package...` label string.

The shared worktree contains concurrent edits outside this packet's write
scope, including docs, CFD, calibration, volume-mesh, search, and operator
report paths. Those were not modified or reverted by this UI-successor lane.
