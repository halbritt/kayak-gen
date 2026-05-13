author: operator [self-declared: operator-0036-implementer]

# Patch summary - workflow 0036 CFD calibration claim gates

run: run_38b1b70956eb48eabbf39449375579ed
job: implement_findings
date: 2026-05-13

## Findings addressed

- F-001: Added shared RFC 0025 claim metadata in `kayakgen.eval.claims` and
  exposed first-class claim fields on resistance, CFD job/profile/run/raw
  result records, and the reserved `CfdResult`.
- F-002: Hardened comparison-report provenance so calibrated resistance
  prediction requires `claim_state = "calibrated_model"`, accepted fixture IDs,
  model version, fit evidence, validity envelope, and no current uncalibrated
  warning codes.
- F-003: Extended source-state vocabulary with `validation_fixture` and
  `calibration_fixture_candidate`, and required fixture-review metadata before
  any source record can become a `calibration_fixture`.
- F-004: Carried resistance claim state, accepted uses, and warnings through
  compact web metrics and rendered a visible raw comparative warning beside the
  at-speed resistance values.
- F-005: Added a `kayakgen evaluate` stdout warning when resistance is included;
  `--skip-resistance` remains quiet.
- F-006: Added focused forbidden-promotion tests for raw CFD promotion,
  validation-only fixtures, uncalibrated resistance, forged legacy report
  metadata, incomplete calibrated prediction metadata, and final design fitness.

## Boundary preserved

- No real CFD solver success path was added.
- No current source was promoted to an accepted calibration fixture.
- No calibrated resistance model or accepted calibration fixture was added.
- No final design-fitness score was accepted.
- Current analytical resistance remains an uncalibrated comparative filter.
- Current CFD dispatch remains raw and unvalidated.

## Files changed

- `kayakgen/eval/claims.py`
- `kayakgen/eval/contract.py`
- `kayakgen/eval/resistance.py`
- `kayakgen/eval/cfd/jobs.py`
- `kayakgen/eval/calibration.py`
- `kayakgen/eval/__init__.py`
- `kayakgen/search/compare.py`
- `kayakgen/search/sweep.py`
- `kayakgen/cli/main.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/app.py`
- `tests/test_resistance.py`
- `tests/test_cfd_jobs.py`
- `tests/test_compare.py`
- `tests/test_cli.py`
- `tests/test_web.py`
- `CHANGELOG.md`
- `docs/workflows/0036-cfd-calibration-claim-gates/OPERATOR_REPORT.md`
- `striatum/0036-cfd-calibration-claim-gates/implementation/PATCH_SUMMARY.md`

## Verification

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
