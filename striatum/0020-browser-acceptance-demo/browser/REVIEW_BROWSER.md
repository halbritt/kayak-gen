author: operator [self-declared: operator-browser-review]

# Browser review - runtime and visual acceptance

Verdict intent: accept_with_findings

## Findings

### B-001 - Real-browser rendering is not currently exercised

The app now has a useful offscreen VTK smoke test, but that does not prove a
browser can load the Trame client, connect to the server, display the remote VTK
view, and react to UI events. `docs/WEB_VERIFICATION.md` still lists future
Playwright work rather than a present browser test.

Required action: add a browser smoke test file or script that starts the app,
opens the page with Playwright or equivalent when available, checks that the app
loads, and performs at least one slider/metrics interaction. When unavailable,
the test must skip with a clear dependency reason.

### B-002 - Current environment cannot run the browser automation stack

`playwright` and `pytest_playwright` are not importable in `.venv`, and
`google-chrome`, `chromium`, `chromium-browser`, and `lighthouse` are absent
from `PATH`. Node/npm/npx are present, but they are not enough to run browser
or Lighthouse acceptance.

Required action: make browser acceptance optional and self-diagnosing in this
workflow unless the implementation installs and verifies the required browser
stack. Record exactly what was and was not run.

### B-003 - A future browser assertion must check the real user-visible path

The relevant failure mode is a browser-visible blank or stale Trame view, not
just a nonblank VTK render window. A useful acceptance check should verify page
load, presence of controls, a visible/connected viewer surface where the
automation can observe it, and a metric change after changing a hull parameter.

Required action: encode these expectations in the browser test or in the
documented manual acceptance checklist.

### B-004 - Lighthouse depends on browser availability and should stay a separate gate

Lighthouse requires a browser binary and a running server. Folding it into
ordinary unit tests would make the test suite brittle in environments that do
not install browser tooling.

Required action: keep Lighthouse as an explicit optional command or script, with
status wording that says it is skipped when the required tooling is absent.

## Required gate

Proceed to ledger. Accept implementation only if it provides a truthful
browser-acceptance path: either a runnable browser smoke in this environment, or
an optional test/script with precise skips and no false visual claims.
