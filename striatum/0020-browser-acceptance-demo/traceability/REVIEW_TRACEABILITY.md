author: operator [self-declared: operator-traceability-review]

# Traceability review - browser acceptance and demo

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0008 browser acceptance is still not represented by an automated browser check

`docs/rfcs/0008-web-frontend.md` requires a browser page that shows the hull,
updates after slider movement, and passes browser-facing acceptance criteria.
Current tests in `tests/test_web.py` cover state, controller helpers, REST route
registration, Trame app construction, and offscreen VTK pixels, but there is no
`tests/test_web_browser.py` or equivalent Playwright/Selenium/browser harness.

Required action: add a reproducible browser acceptance entry point that is
skipped only when the browser automation stack is unavailable, and document the
exact skip reason and install/run command.

### T-002 - The RFC 0008 `kayakgen serve` acceptance wording conflicts with current CLI behavior

RFC 0008 says `kayakgen serve` opens a browser tab. `kayakgen/cli/main.py`
starts the Trame server on the requested host/port and does not open a browser.
`docs/WEB_VERIFICATION.md` documents that behavior as intentional for Docker and
CI friendliness.

Required action: keep the default server behavior scriptable, but update RFC and
verification docs so the accepted behavior is explicit. If an opt-in browser
open flag is added, tests should cover that it is opt-in and not the Docker/CI
default.

### T-003 - Lighthouse acceptance is not installed, run, or recorded

RFC 0008 requires Lighthouse Best Practices >= 90. The environment has `node`,
`npm`, and `npx`, but no `lighthouse` executable, no Chrome/Chromium binary, and
no recorded Lighthouse output.

Required action: do not claim Lighthouse acceptance. Add a reproducible optional
Lighthouse command and record that it remains skipped unless a Chromium-family
browser and Lighthouse are present.

### T-004 - Hosted demo acceptance remains a deployment recipe, not a deployed demo

RFC 0008's hosted goal says a user with a URL and no Python installed can design
a hull. The repo currently provides a Dockerfile and manual local/Docker
verification notes, but no hosted public URL or deployment artifact record.

Required action: document the Docker image as the current demo artifact and keep
hosted demo deployment listed as deferred until a real URL exists.

### T-005 - Desktop/web parity is still partial beyond the browser tooling gap

The web app exposes Trame sliders and metrics, but RFC 0008 still mentions class
selection, plot tabs, identical desktop slider parity, and web comparison views.
The desktop GUI has a class selector and station/plot views; web comparison UI
is also explicitly deferred by RFC 0013.

Required action: update status wording after this workflow so real-browser
coverage, if added, is not mistaken for full RFC 0008 completion.

## Required gate

Proceed to ledger. The implementation should focus on browser-acceptance
scaffolding, truthful docs/status, and optional tooling detection. It should not
claim full RFC 0008 parity, Lighthouse success, hosted demo availability, or web
comparison UI unless those artifacts actually land.
