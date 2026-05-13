# Patch summary - 0013

author: operator [self-declared: operator-implementer]
run: run_09d8fab3d88e4a6588b8838ff9f34e61
job: implement_findings
date: 2026-05-13

## Summary

Implemented the resistance acceptance revision from the 0013 findings ledger.
RFC 0005 now describes the landed behavior as a raw comparative filter and
explicitly defers calibrated prediction, validity envelopes, Pareto-default
scoring, and 200 ms full-curve interactive latency.

## Files changed

- `docs/rfcs/0005-cfd-resistance.md`
  - Changed status to `landed-raw-filter`.
  - Replaced the stale single acceptance list with a landed raw-filter tier and
    deferred calibrated/optimized criteria.
  - Replaced the old performance-budget claim with a raw-filter regression
    budget and future optimized-evaluator target.
- `docs/rfcs/README.md`
  - Updated RFC 0005 index status and roadmap note.
- `docs/rfcs/0012-resistance-model-calibration.md`
  - Updated stale context and acceptance text after RFC 0005 was revised.
- `tests/test_resistance.py`
  - Removed the two expected-failure tests for retired low-Froude ratio and
    200 ms full-curve claims.
  - Kept metadata, warnings, source-registry, Wigley, and realistic regression
    budget coverage.
- `docs/workflows/0013-resistance-acceptance-revision/OPERATOR_REPORT.md`
  - Recorded workflow progress, findings, and verification state.

## Verification

- `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed
- `.venv/bin/python -m pytest -q` -> 100 passed
- `git diff --check` -> clean
