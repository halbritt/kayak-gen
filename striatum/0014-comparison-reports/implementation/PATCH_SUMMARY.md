# Patch summary - 0014

author: operator [self-declared: operator-implementer]
run: run_98b5ec4a7a31461bbdc78bbc00179aad
job: implement_findings
date: 2026-05-13

## Summary

Implemented the comparison-report CLI slice from the 0014 findings ledger.
`kayakgen compare` now reads sweep run records and writes deterministic
comparison reports. Default objectives exclude raw uncalibrated resistance, and
explicit resistance objectives are marked as exploratory with accepted-use
provenance warnings.

## Findings addressed

- F-001: added `kayakgen compare <run-dir> --out <file>`.
- F-002: added `CandidateSummary`, `ComparisonReport`, report loading/building,
  and report writing in `kayakgen.search.compare`.
- F-003: default objectives use safe available metrics only and exclude raw
  resistance.
- F-004: missing/unsupported objective metrics become report and candidate
  warnings.
- F-005: failed and skipped candidates stay visible but do not participate in
  Pareto computation.
- F-006: `summary.csv` now includes deterministic `param_<name>` columns.
- F-007: RFC 0013 and the RFC index now state that only the report/CLI slice
  has landed; web UI remains deferred.

## Files changed

- `kayakgen/search/compare.py`
- `kayakgen/search/__init__.py`
- `kayakgen/search/sweep.py`
- `kayakgen/cli/main.py`
- `tests/test_compare.py`
- `tests/test_sweep.py`
- `tests/test_cli.py`
- `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- `docs/rfcs/README.md`
- `docs/workflows/0014-comparison-reports/OPERATOR_REPORT.md`

## Verification

- `.venv/bin/python -m pytest tests/test_compare.py tests/test_sweep.py tests/test_pareto.py tests/test_cli.py -q` -> 25 passed
- `.venv/bin/python -m pytest -q` -> 111 passed
- `git diff --check` -> clean
- `.venv/bin/ruff check kayakgen tests` -> not run; `ruff` is not installed in the current virtualenv
