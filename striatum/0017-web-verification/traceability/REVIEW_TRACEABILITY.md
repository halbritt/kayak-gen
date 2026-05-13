author: operator [self-declared: operator-traceability-review]

# Traceability review - web verification

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0008 remains partial, but the verified slice is not named

RFC 0008's status note says the Trame shell, sliders, VTK view, metrics helpers,
share-query encoding, REST route scaffolding, and Docker path exist. The current
repo now also has headless web tests, but the RFC and index do not distinguish
headless verification from full browser verification.

Required action: update RFC 0008 and the RFC index with a precise status such
as `partial verified-headless`, without marking browser/Lighthouse/demo criteria
landed.

### T-002 - Browser and Lighthouse acceptance criteria are unverified

RFC 0008 requires a Playwright smoke test and Lighthouse Best Practices >= 90.
The current environment lacks Playwright, pytest-playwright, Lighthouse, Chrome,
and Chromium.

Required action: document these checks as skipped/unavailable in this workflow
and define exact future commands/prerequisites rather than silently treating
headless tests as browser acceptance.

### T-003 - Visual verification is weaker than the current Trame code allows

`tests/test_web.py` constructs the app and checks state, but it does not assert
that the VTK render window has actors or nonblank rendered pixels.

Required action: add a headless VTK visual smoke test that creates the app,
renders offscreen, and asserts a nonblank image/scene.

### T-004 - Demo/deployment documentation is missing

The repo has a Dockerfile and `.dockerignore`, but no top-level deployment or
web verification document explaining local run, Docker build/run, known
environment constraints, or hosted-demo status.

Required action: add a concise repo document for local web verification,
Docker deployment, skipped browser/Lighthouse checks, and future hosted demo.

### T-005 - Web comparison UI remains deferred

RFC 0013 says web comparison views come after CLI report format stabilizes.
Workflow 0014 landed CLI report generation, but no web comparison view exists.

Required action: keep RFC 0013/web comparison language deferred unless a
separate workflow implements it.
