author: operator [self-declared: operator-browser-review]

# Browser review - visual/runtime verification

Verdict intent: accept_with_findings

## Findings

### B-001 - App construction catches Trame wiring, not blank renders

The current smoke test instantiates `create_app()` and checks state/reset. A
manual probe in this workflow showed the headless VTK window can render
offscreen with two actors and nonuniform pixel output, so the repo can test more
than construction without Playwright.

Required action: add a VTK offscreen image smoke test for nonblank render output
and actor count.

### B-002 - Playwright/Lighthouse cannot run in this environment

Python modules `playwright` and `pytest_playwright` are missing, and no Chrome
or Chromium binary is available. The `lighthouse` executable is also absent.

Required action: do not add fake browser assertions. Record unavailable tooling
in docs and operator report, with future commands when those tools are present.

### B-003 - The web layout still lacks RFC 0008 plot tabs

The current UI has sliders, VTK view, metrics, reset/share/export actions, and
REST helpers. It does not implement the RFC's sheer-plan/cross-section/metrics
tabs.

Required action: keep plot tabs outside this verification workflow, and avoid
claiming full RFC 0008 parity.

### B-004 - Local server smoke should remain scriptable

`kayakgen serve` starts the Trame server, but the testable factory is
`create_app()` and REST helpers. Starting a long-running server in unit tests
would be fragile without browser tooling.

Required action: prefer factory/controller/offscreen-render tests now; document
manual `kayakgen serve` and Docker commands for local browser checks.
