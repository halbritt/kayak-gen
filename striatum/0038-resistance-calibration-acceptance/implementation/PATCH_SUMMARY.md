# Patch Summary - Workflow 0038 Resistance Calibration Acceptance

## Scope

Implemented the ledger-approved safe slice for RFC 0027 resistance calibration
acceptance. The patch hardens schema, source metadata, claim gates, tests, and
traceability while keeping the current ITTC/Michell resistance output
uncalibrated and comparative-only.

## Findings Addressed

- F-001: Added typed RFC 0027 resistance fit statuses and a
  `ResistanceFitRecord`; hardened `claim_allows_calibrated_prediction` so only
  canonical `accepted_fit` with metrics, accepted calibration fixture IDs,
  model version, validity envelope, and no uncalibrated warnings can pass.
- F-002: Reconciled RFC 0027's three acceptance-stage labels with the existing
  five-state `SourceUse` vocabulary and documented that no parallel
  `candidate_source` enum should be introduced.
- F-003: Strengthened `ResistanceSourceRecord` validation for calibration
  fixtures and validation fixtures, including measured-data, rights,
  extraction, and reproducible fixture metadata requirements.
- F-005: Added negative and positive tests for candidate/rejected fit states,
  accepted-fit contract evidence, weak fixture metadata, validation-only
  metadata, and raw default uncalibrated evidence.
- F-006: Anchored RFC 0027 to RFC 0025 claim gates and added supporting source
  files to the workflow source list.

## Changed Files

- `CHANGELOG.md`
- `docs/rfcs/0027-resistance-calibration-acceptance.md`
- `docs/workflows/0038-resistance-calibration-acceptance/SOURCES.md`
- `kayakgen/eval/calibration.py`
- `kayakgen/eval/claims.py`
- `kayakgen/eval/contract.py`
- `tests/test_compare.py`
- `tests/test_resistance.py`
- `striatum/0038-resistance-calibration-acceptance/implementation/PATCH_SUMMARY.md`

## Tests Run

- `.venv/bin/python -m pytest -q tests/test_resistance.py tests/test_compare.py tests/test_cli.py`
  - Result: 62 passed in 8.82s.
- `.venv/bin/python -m pytest -q`
  - Result: 184 passed, 2 skipped in 20.56s.
  - Skips: `kayakgen[web]` and Playwright browser dependencies are not
    installed in this worktree.
- `git diff --check`
  - Result: passed.

## Deferred Findings

- F-004 remains deferred: no calibrated CLI/web/report wording, envelope
  membership branch, selected calibrated model path, or raw fallback output was
  added in this safe slice.
- Deferred portions of F-005 remain open until fitting/output paths exist:
  fixture row loading, monotonic speed-row checks, persisted residual artifacts,
  validation-fixture holdout metrics, out-of-envelope warnings, and raw fallback
  wording.
- No source record was promoted to `validation_fixture` or
  `calibration_fixture`, and no current resistance output was marked calibrated.

## Sub-Agent Usage

- Read-only documentation cross-check agent: reviewed RFC/source requirements
  for F-002 and F-006 and returned the RFC mapping/claim-gate checklist.
- Fit-state worker: owned `kayakgen/eval/claims.py` and
  `kayakgen/eval/contract.py`, adding the fit-status contract and initial claim
  gate hardening.
- Fixture-validation worker: owned `kayakgen/eval/calibration.py`, adding
  calibration/validation fixture metadata validation.
- Test worker: owned `tests/test_resistance.py` and `tests/test_compare.py`,
  adding RFC 0027 negative and positive coverage.
- Documentation worker: owned RFC 0027 and workflow `SOURCES.md`, adding the
  normative `SourceUse` mapping and RFC 0025 claim-gate anchors.
- Final integration was performed locally in this implementer lane, including
  the metrics requirement in the calibrated-prediction gate, changelog update,
  verification, and this patch summary.
