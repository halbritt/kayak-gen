# Operator report - workflow 0036

Updated: 2026-05-13

## Current state

- Three review lanes are complete: traceability, domain/source, and ops/test.
- Findings are consolidated in
  `striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`.
- Ledger gate result is `accept_with_findings`.
- The accepted safe slice is limited to claim-state metadata, promotion gates,
  visible CLI/web warnings, source/fixture state validation, and negative tests.
- The boundary remains explicit: do not add real solver success, validated CFD,
  accepted calibration fixtures, calibrated resistance models, or final
  design-fitness scoring in this workflow slice.

## Next action

- Implement the accepted ledger findings in order: shared claim contract first,
  then report/source gates, then CLI/web warning surfaces and
  forbidden-promotion tests.
- Preserve existing raw/unvalidated behavior while making the claim state
  machine-readable and visible wherever resistance or CFD numbers are shown.

## Checks

- Passed with no output: `git diff --check -- docs/workflows/0036-cfd-calibration-claim-gates/OPERATOR_REPORT.md striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`.
- New ledger file also produced no whitespace output under
  `git diff --check --no-index /dev/null striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`;
  that command exits nonzero because `--no-index` reports file differences.
