author: remediator-codex-gpt-5.5-001

# Remediation Patch Summary

## Scope

Fixed the single must-fix from
`striatum/0061-rfc-0065-slice4-visual-regression/ledger/FINDINGS_LEDGER.md`:

- MF-1: commit a no-browser self-test for the visual diff comparator.

## What Changed

- Added synthetic PNG regression tests for
  `tests/test_web_browser.py::_compare_visual_png`.
- The failing case changes three pixels in a `10x10` image, exceeding the
  documented `0.02` mismatch-ratio tolerance. It asserts
  `VisualCompareResult.passed is False` and verifies actual/diff evidence is
  written.
- The passing case changes one pixel in a `10x10` image, staying below the
  documented `0.02` mismatch-ratio tolerance while still exercising a real
  channel delta. It asserts `passed is True` and verifies no diff artifact is
  written.
- Updated `CHANGELOG.md` and the workflow `OPERATOR_REPORT.md` for the
  remediation.

## Boundaries Preserved

- No visual comparator constants changed.
- No viewport list, VTK mask, browser-acceptance scope, baseline PNG, or
  regeneration procedure changed.
- No claim/readiness/status chip contract, claim line, RFC 0032 boundary text,
  D047 ratification, `WEB_VERIFICATION.md`, or `USER_GUIDE.md` claim wording
  changed in remediation.
- The known NB-2 services import-boundary failure remains deferred to the
  separate hygiene follow-up.

## Verification

- `.venv/bin/python -m pytest tests/test_web_browser.py::test_compare_visual_png_fails_over_tolerance_and_writes_diff tests/test_web_browser.py::test_compare_visual_png_passes_under_mismatch_ratio_without_diff -q`
  - `2 passed in 0.07s`
- `.venv/bin/python -m pytest tests/test_ui_theme.py::test_contrast_manifest_clears_thresholds tests/test_desktop_layout.py -q`
  - `6 passed in 4.04s`
- `.venv/bin/python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline -q`
  - `3 passed in 19.97s`
- `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  - `4 passed, 2 deselected in 34.88s`
- `.venv/bin/python -m pytest -q`
  - `1 failed, 1307 passed, 4 skipped in 471.93s`
  - Failure is the known out-of-scope NB-2 services boundary:
    `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
    reports `kayakgen/services/evaluation.py` importing
    `kayakgen.ui.hydrostatics_metadata`.
- `.venv/bin/python -m ruff check tests/test_web_browser.py`
  - `All checks passed!`
- `git diff --check`
  - clean
