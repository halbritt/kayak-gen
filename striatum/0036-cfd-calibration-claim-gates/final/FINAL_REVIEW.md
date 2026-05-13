author: operator [self-declared: operator-0036-final]

# Final review - workflow 0036 CFD calibration claim gates

run: run_38b1b70956eb48eabbf39449375579ed
job: final_review
date: 2026-05-13
verdict: accept

## Changed file

- `striatum/0036-cfd-calibration-claim-gates/final/FINAL_REVIEW.md`

## Scope reviewed

- `docs/workflows/0036-cfd-calibration-claim-gates/prompts/final_review.md`
- `striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`
- `striatum/0036-cfd-calibration-claim-gates/implementation/PATCH_SUMMARY.md`
- workflow review artifacts from traceability, domain/source, and ops
- relevant RFCs: 0005, 0012, 0015, 0017, 0019, 0025, and 0027
- changed implementation, test, changelog, and operator-report files on the
  branch

## Review result

The implementation matches the accepted ledger scope. The shared RFC 0025 claim
contract is now first-class in resistance metadata, CFD job/profile/run/raw
records, and the reserved CFD result type. Current analytical resistance remains
`uncalibrated_comparative` with comparative-only use and final-prediction /
no-validity-envelope warnings. Current CFD dispatch remains `raw_unvalidated`
with no accepted uses, no fixture IDs, no fit evidence, and no validity
envelope.

The comparison-report gate no longer trusts legacy `calibration_status` or
`accepted_use` strings by themselves. Calibrated prediction provenance requires
the shared claim state, fixture IDs, model version, fit evidence, validity
envelope, and absence of current uncalibrated warning codes. Final
design-fitness provenance remains rejected for calibrated resistance.

The source registry now distinguishes validation fixtures and calibration
fixture candidates from accepted calibration fixtures, and attempted
`calibration_fixture` records require review metadata. No default source was
promoted to an accepted calibration fixture.

The visible warning requirements landed: `kayakgen evaluate` prints a compact
uncalibrated/comparative warning when resistance is included, compact web
metrics carry claim metadata and render a raw comparative warning, and the
existing analysis view still exposes resistance warnings.

No real solver success, validated CFD drag, accepted calibration fixture,
calibrated resistance model, accepted fit, or final design-fitness claim was
added.

## Checks

- Passed: `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q tests/test_resistance.py tests/test_cfd_jobs.py tests/test_compare.py tests/test_cli.py::test_evaluate_accepts_non_default_bow_rake_and_beam_wl tests/test_cli.py::test_evaluate_with_resistance_prints_claim_warning tests/test_cli.py::test_cfd_prepare_status_and_unavailable_run tests/test_web.py::test_metrics_match_evaluate_hydrostatics tests/test_web.py::test_compact_metrics_lines_include_resistance_claim_warning tests/test_web.py::test_analysis_lines_include_units_and_resistance_warnings`
  (`49 passed`)
- Passed with no output: `git diff --check`
- Wording scan confirmed stronger claim states appear only in RFCs, tests,
  claim gates, or explicit deferred/not-accepted language.

