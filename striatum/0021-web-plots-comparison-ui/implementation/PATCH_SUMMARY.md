author: operator [self-declared: operator-implementer]

# Patch summary - 0021 web plots and comparison UI

Run id: `run_f4bb27f7cfef403294497e8463a4b65b`  
Job: `implement_findings`

## Findings addressed

- F-001: added a compact web analysis view-model and Trame tab with
  unit-labeled hydrostatics rows and lightweight raw resistance curve rows.
- F-002: added `ComparisonReport` JSON parsing/formatting and a compact web
  comparison tab preserving objectives, warnings, Pareto membership, candidate
  status, and candidate rows.
- F-003: implemented candidate reload as parameter-only state application from
  `summary.parameters`; artifact loading remains intentionally out of scope.
- F-004: added focused helper/app tests and extended browser smoke coverage for
  the discoverable `Analysis`, `Comparison`, and `Resistance curve` surface.
- F-005: updated RFC/status docs to mark the landed slice precisely while
  preserving deferred hosted-demo, full plot/dashboard parity, and
  console-clean Lighthouse work.

## Files changed

- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/app.py`
- `tests/test_web.py`
- `tests/test_web_browser.py`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- `docs/rfcs/README.md`
- `docs/WEB_VERIFICATION.md`
- `docs/workflows/0021-web-plots-comparison-ui/OPERATOR_REPORT.md`

## Verification

- `.venv/bin/python -m pytest tests/test_web.py tests/test_web_browser.py tests/test_compare.py tests/test_cli.py -q`
  passed: 38 tests.
- `.venv/bin/python -m pytest -q` passed: 139 tests.
- `git diff --check` passed.
- `striatum --repo . doctor` passed with zero problems.
- `.venv/bin/python -m ruff check .` was not run because `ruff` is not
  installed in the project virtualenv.

## Deferred

- Full desktop-equivalent plot parity, hosted public demo deployment,
  console-clean Lighthouse acceptance, mobile view-only mode, larger comparison
  dashboards, solver dispatch, optimizer flows, accounts/persistence, and
  arbitrary artifact-file loading remain out of scope for this workflow.
