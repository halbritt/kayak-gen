author: operator [self-declared: operator-ledger-temp]

# Findings ledger - 0017 web verification

Run id: `run_afd669b376de46f4912dc11749dcd5fb`  
Job: `findings_ledger`  
Gate result: proceed to implementation

## Stats

- Source artifacts: 3
- Source findings: 13
- Deduplicated findings: 6
- By severity: high 3 / medium 3 / low 0
- Safe-now findings: 6
- Deferred findings: 3

## Deduplicated Findings

### F-001 - RFC 0008 status does not name the verified slice

- Sources: T-001, T-002, B-003
- Severity: high
- Classification: safe-now
- Files: `docs/rfcs/0008-web-frontend.md`, `docs/rfcs/README.md`
- Statement: The current Trame web frontend has meaningful headless coverage,
  but browser/Lighthouse/demo criteria remain unverified. The status should say
  exactly that.
- Required remediation: Update RFC 0008 and the RFC index to `partial
  verified-headless` or equivalent, and list the remaining deferred browser,
  Lighthouse, plot-tabs, hosted-demo, and web-comparison work.

### F-002 - Headless visual smoke should assert nonblank VTK rendering

- Sources: T-003, B-001, O-003
- Severity: high
- Classification: safe-now
- Files: `tests/test_web.py`
- Statement: Current tests instantiate the app but do not prove the offscreen
  render window contains a visible hull/deck scene.
- Required remediation: Add a test that creates the Trame app, checks actor
  count, renders offscreen with VTK, and asserts nonblank/nonuniform pixels.

### F-003 - Browser/Lighthouse skips need reproducible documentation

- Sources: T-002, B-002, O-002
- Severity: high
- Classification: safe-now
- Files: future web verification/deployment doc,
  `docs/workflows/0017-web-verification/OPERATOR_REPORT.md`
- Statement: Playwright, pytest-playwright, Lighthouse, Chrome, and Chromium are
  not available in this environment.
- Required remediation: Add docs that record what was run, what was skipped,
  why, and what future commands should run when tooling is installed.

### F-004 - Docker/local deployment docs are missing

- Sources: T-004, O-001, B-004
- Severity: medium
- Classification: safe-now
- Files: future web verification/deployment doc
- Statement: The Dockerfile exists, but the repo has no deployment/verification
  instructions for `kayakgen serve`, Docker build/run, or manual browser smoke.
- Required remediation: Add a concise `docs/WEB_VERIFICATION.md` with local,
  Docker, and manual browser verification commands.

### F-005 - `kayakgen serve` behavior should be documented, not changed

- Sources: O-004, B-004
- Severity: medium
- Classification: safe-now
- Files: future docs, possibly RFC 0008 status note
- Statement: RFC 0008 says local serve opens a browser tab, but current CLI
  starts a server and does not auto-open a browser. Auto-open is undesirable in
  Docker and CI without an explicit opt-in.
- Required remediation: Document current behavior. Do not change CLI defaults in
  this verification workflow.

### F-006 - Web comparison UI remains deferred

- Sources: T-005, B-003
- Severity: medium
- Classification: safe-now
- Files: `docs/rfcs/README.md`, `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- Statement: RFC 0013's web comparison view is not implemented. This workflow
  verifies the existing web app and should not claim comparison UI.
- Required remediation: Keep web comparison UI listed as deferred.

## Implementation Guidance

Safe now:

- Add a VTK offscreen pixel smoke test to `tests/test_web.py`.
- Add `docs/WEB_VERIFICATION.md` with local, Docker, headless, optional browser,
  and future Lighthouse commands.
- Update RFC 0008 and the RFC index to describe the headless-verified slice.
- Update RFC 0013/readme language only to preserve web comparison deferral.
- Run focused web/CLI tests, full suite, `git diff --check`, and Docker build if
  practical.

Do not implement:

- Playwright or Lighthouse dependency installation.
- A hosted public demo.
- Plot tabs or web comparison UI.
- A Trame replacement or major UI redesign.
- Auto-opening browsers from `kayakgen serve` by default.
