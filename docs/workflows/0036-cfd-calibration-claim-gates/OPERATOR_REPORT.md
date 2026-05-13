# Operator report - workflow 0036

Updated: 2026-05-13

## Current state

- Three review lanes are complete: traceability, domain/source, and ops/test.
- Findings are consolidated in
  `striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`.
- Ledger gate result is `accept_with_findings`.
- The accepted safe slice has been implemented: claim-state metadata, promotion
  gates, visible CLI/web warnings, source/fixture state validation, and negative
  tests are present on the working branch.
- The boundary remains explicit: do not add real solver success, validated CFD,
  accepted calibration fixtures, calibrated resistance models, or final
  design-fitness scoring in this workflow slice.

## Next action

- Commit the working branch and hand it off for final review without publishing
  Striatum artifacts from this session.

## Checks

- Passed with no output: `git diff --check -- docs/workflows/0036-cfd-calibration-claim-gates/OPERATOR_REPORT.md striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`.
- New ledger file also produced no whitespace output under
  `git diff --check --no-index /dev/null striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`;
  that command exits nonzero because `--no-index` reports file differences.
- Passed: `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q
  tests/test_resistance.py tests/test_cfd_jobs.py tests/test_compare.py
  tests/test_cli.py::test_evaluate_accepts_non_default_bow_rake_and_beam_wl
  tests/test_cli.py::test_evaluate_with_resistance_prints_claim_warning
  tests/test_cli.py::test_cfd_prepare_status_and_unavailable_run
  tests/test_web.py::test_metrics_match_evaluate_hydrostatics
  tests/test_web.py::test_compact_metrics_lines_include_resistance_claim_warning
  tests/test_web.py::test_analysis_lines_include_units_and_resistance_warnings`
  (`49 passed`).
- Passed: `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q`
  (`180 passed`).
- Passed with no output: `git diff --check`.
