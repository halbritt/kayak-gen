author: operator [self-declared: operator-ledger]

# Findings ledger - 0021 web plots and comparison UI

Run id: `run_f4bb27f7cfef403294497e8463a4b65b`  
Job: `findings_ledger`  
Gate result: proceed to implementation

## Stats

- Source artifacts: 3
- Source findings: 12
- Deduplicated findings: 5
- By severity: high 2 / medium 3 / low 0
- Safe-now findings: 5
- Deferred findings: 5

## Deduplicated Findings

### F-001 - RFC 0008 needs a small web analysis tab/data slice

- Sources: T-001, D-004, O-001, O-004
- Severity: high
- Classification: safe-now
- Files: `kayakgen/ui/web/controllers.py`, `kayakgen/ui/web/app.py`,
  `tests/test_web.py`
- Statement: The current web app has a metrics text panel but no analysis area
  for hydrostatics/resistance plot data. RFC 0008's full plot parity can remain
  deferred, but users need a reproducible way to inspect key curve/metric data
  in the browser.
- Required remediation: Add pure controller helpers and a small Trame analysis
  tab/view that shows labeled hydrostatics rows and a lightweight resistance
  curve/table. Keep units visible. Avoid heavy plotting dependencies and avoid
  recomputing expensive curves in the default slider path beyond the accepted
  lightweight slice.

### F-002 - RFC 0013 comparison reports need a web view model and UI surface

- Sources: T-002, D-002, D-003, O-001, O-002
- Severity: high
- Classification: safe-now
- Files: `kayakgen/ui/web/controllers.py`, `kayakgen/ui/web/app.py`,
  `tests/test_web.py`, `tests/test_compare.py`
- Statement: `ComparisonReport` exists for CLI output, but the web frontend
  cannot load or inspect it. The UI must preserve objective labels, Pareto
  membership, candidate status, warnings, and errors.
- Required remediation: Add a pure report view-model parser from
  `ComparisonReport` JSON and a small comparison tab/surface that displays
  report kind, objectives, warnings, Pareto membership, and candidate rows. Use
  generated tiny reports in tests; do not check in large fixtures.

### F-003 - Candidate reload must be parameter-only and explicit

- Sources: T-003, D-003, O-001
- Severity: medium
- Classification: safe-now
- Files: `kayakgen/ui/web/controllers.py`, `kayakgen/ui/web/app.py`,
  `tests/test_web.py`
- Statement: A comparison candidate can be safely reloaded from its summary
  `parameters`, but loading arbitrary `artifacts` would introduce filesystem
  coupling and unclear base-hull semantics.
- Required remediation: Implement candidate reload only by applying the selected
  candidate's `parameters` onto current web state, or explicitly defer reload if
  a safe UI binding is too large. The UI/docs must name that only sweep
  parameters are applied.

### F-004 - Browser/headless tests must cover the new discoverable surface

- Sources: O-003
- Severity: medium
- Classification: safe-now
- Files: `tests/test_web.py`, `tests/test_web_browser.py`
- Statement: New analysis/comparison UI can regress without tests because the
  current browser smoke only checks the basic page and slider/metrics update.
- Required remediation: Add focused pure/helper tests and app-factory tests for
  new state. Extend browser smoke only for stable visible tab/control text.

### F-005 - RFC/readme status must remain partial and precise

- Sources: T-004, D-001, D-002
- Severity: medium
- Classification: safe-now
- Files: `docs/rfcs/0008-web-frontend.md`,
  `docs/rfcs/0013-pareto-frontier-comparison-ui.md`, `docs/rfcs/README.md`,
  `docs/WEB_VERIFICATION.md`
- Statement: This workflow can land a web-analysis slice but will not complete
  hosted demo, mobile view-only mode, console-clean Lighthouse, optimizer,
  solver dispatch, or full comparison-dashboard work.
- Required remediation: Update docs/RFC status to describe the exact landed
  plot/comparison slice and preserve remaining deferrals.

## Implementation Guidance

Safe now:

- Add pure web controller/view-model helpers for:
  - hydrostatics rows with units;
  - lightweight resistance curve rows with speed in knots and resistance in N;
  - `ComparisonReport` JSON parsing and row formatting;
  - parameter-only candidate reload state.
- Add a compact Trame analysis/comparison UI. Tables/preformatted rows are
  acceptable for this slice if they are clear, unit-labeled, and browser-tested;
  do not introduce a new frontend charting dependency.
- Preserve all comparison warnings, failed/skipped candidate statuses,
  exploratory frontier labels, and resistance calibration warnings.
- Use generated tiny sweep/comparison reports in tests.
- Extend `tests/test_web.py` for helper and app-state behavior. Extend
  `tests/test_web_browser.py` only for stable visible text such as tab labels.
- Update RFC 0008/RFC 0013/RFC index/web verification status text.
- Run focused web/comparison/browser tests, full pytest, and `git diff --check`.

Do not implement:

- Full desktop-equivalent plot parity, mobile view-only mode, hosted public demo,
  optimizer controls, solver dispatch, accounts/persistence, or a React/JS
  frontend.
- New claims that raw analytical resistance is calibrated or suitable for final
  prediction.
- Loading arbitrary local artifact files from a comparison report into the web
  app.
- Large static fixture reports unless final review proves generated fixtures are
  insufficient.
