# Findings ledger - 0013

author: operator [self-declared: operator-ledger]
run: run_09d8fab3d88e4a6588b8838ff9f34e61
job: findings_ledger
date: 2026-05-13

## Gate result

Proceed with acceptance revision. The current model may be accepted only as a
raw comparative filter with explicit warnings and provenance. Retire the two
RFC 0005 expected-failure tests from the active suite because their underlying
claims are no longer part of the landed raw-filter tier.

## Stats

- Source findings: 9
- Deduplicated findings: 5
- By severity: high 4 / medium 1
- Actionable now: 5

## Findings

### F-001 - RFC 0005 acceptance criteria need tier split

- Sources: T-001, D-001, D-002
- Severity: high
- Classification: actionable-now
- File(s): `docs/rfcs/0005-cfd-resistance.md`
- Statement: RFC 0005 mixes the landed raw-filter behavior with future
  calibrated/optimized behavior.
- Required remediation: Mark the landed tier as raw comparative filtering and
  explicitly move low-Froude component-ratio and 200 ms full-curve requirements
  to future calibrated/optimized work.

### F-002 - Expected failures encode retired claims

- Sources: T-002, O-001
- Severity: high
- Classification: actionable-now
- File(s): `tests/test_resistance.py`
- Statement: The two xfails are not pending implementation within the accepted
  raw-filter contract.
- Required remediation: Remove or replace them with passing tests that enforce
  the raw-filter warnings and accepted realistic budget.

### F-003 - RFC index should state the new status clearly

- Sources: T-003
- Severity: medium
- Classification: actionable-now
- File(s): `docs/rfcs/README.md`
- Statement: The index still says RFC 0005 is merely partial, without explaining
  the accepted raw-filter tier.
- Required remediation: Update the index note.

### F-004 - Preserve anti-overclaiming guardrails

- Sources: O-002, D-003
- Severity: high
- Classification: actionable-now
- File(s): `tests/test_resistance.py`, `kayakgen/eval/resistance.py`
- Statement: Removing xfails must not make raw resistance look calibrated.
- Required remediation: Keep tests for uncalibrated metadata, comparative-only
  accepted use, missing validity envelope, source registry with no calibration
  fixtures, and Wigley verification.

### F-005 - Runtime budget should match evaluator tier

- Sources: O-003, D-002
- Severity: high
- Classification: actionable-now
- File(s): `docs/rfcs/0005-cfd-resistance.md`, `tests/test_resistance.py`
- Statement: The raw evaluator's budget is a snapshot/offline filter budget,
  not the original 200 ms interactive full-curve target.
- Required remediation: Keep the existing 5 s regression test for the raw
  default test settings and document any 200 ms full-curve target as future
  optimized/surrogate work.

## Implementation guidance

Safe now:

- Update RFC 0005 status note, goals/acceptance criteria, and implementation
  path to separate landed raw filter from future calibrated/optimized work.
- Update the RFC index note.
- Remove the two xfailed tests or replace them with passing raw-filter contract
  tests.
- Keep all current raw metadata/provenance tests.

Do not implement:

- Numeric calibration.
- `calibrated_kayak_v1`.
- Default Pareto resistance objective.
- New external source fixtures.
