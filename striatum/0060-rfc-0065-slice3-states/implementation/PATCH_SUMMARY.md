author: implementer-codex-gpt-5.5-001

# Patch Summary

Implemented RFC 0065 Slice 3 as a presentation-only UI state pass.

## Changes

- Added uniform token-sourced hover, active, focus-visible/focus-within, selected,
  and disabled styling for workspace buttons, tabs, Vuetify fields, sliders,
  toggles, native selects, inputs, textareas, and Generate-form buttons.
- Added explicit state surfaces and stable hooks for:
  - Generate jobs table empty/running/failed/cancelled/resumable states, including
    `GenerativeJobError.kind` in the jobs table when available.
  - Pareto frontier loading/empty/rendered states.
  - Comparison no-report/report-present states while preserving the live/imported
    report blocks.
  - CFD no-job/status states with both persistent CFD banners left intact.
  - Share URL state and invalid-hull-state banner.
- Preserved the honestly disabled surfaces and copy for watertight-solid
  readiness, disabled export rows, Cm reserved-preset behavior, and Generate
  submit blocking reasons.
- Updated `tests/test_web_layout.py` and `tests/test_web_inline_help.py` to pin
  all new state hooks and the Slice 3 focus/disabled CSS contract.
- Updated `CHANGELOG.md` with the Slice 3 landing note.

## Verification

- `.venv/bin/python -m pytest tests/test_ui_theme.py tests/test_web_layout.py tests/test_web_inline_help.py -q`
  - 59 passed.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_generate_spec_form.py tests/test_generate_frontier_view.py tests/test_generative_jobs.py -q`
  - 68 passed.
