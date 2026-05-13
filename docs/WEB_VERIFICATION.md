# Web Verification

This document records reproducible checks for the RFC 0008 Trame web frontend.
It distinguishes headless verification that runs in this repo today from
browser and Lighthouse checks that require extra tooling.

## Local Headless Checks

Run the web-focused tests:

```bash
.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py -q
```

These tests cover URL/state round trips, metrics parity with the evaluator, STL
bytes, REST route registration, Trame app construction, reset/query loading, and
an offscreen VTK visual smoke test that asserts a nonblank hull/deck render.

Run the full suite before merging web changes:

```bash
.venv/bin/python -m pytest -q
git diff --check
```

## Local Manual Browser Check

Start the app:

```bash
kayakgen serve --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` in a browser. Verify that the hull and deck are
visible, sliders update the shape and metrics, Reset restores defaults, Share
fills the share URL field, and Export Hull STL / Export Deck STL trigger STL
downloads.

The current CLI starts the server and does not auto-open a browser tab. That is
intentional for Docker and CI friendliness.

## Docker Check

Build the image:

```bash
docker build -t kayakgen-web .
```

Run it locally:

```bash
docker run --rm -p 8080:8080 kayakgen-web
```

Open `http://127.0.0.1:8080/` and run the same manual browser check above.

## Browser Automation And Lighthouse

This workflow did not run Playwright or Lighthouse because the current
environment does not provide `playwright`, `pytest_playwright`, Lighthouse,
Chrome, or Chromium.

When those tools are available, add or run checks equivalent to:

```bash
.venv/bin/python -m pytest tests/test_web_browser.py -q
npx lighthouse http://127.0.0.1:8080/ --only-categories=best-practices
```

Future browser acceptance should launch the app, assert that the 3D view is
nonblank in a real browser, drag at least one slider, verify metrics change, and
record Lighthouse Best Practices >= 90.

## Hosted Demo Status

No hosted public demo is deployed from this repo today. The Docker image is the
reproducible deployment artifact for a future Fly.io, Railway, Render, or VPS
demo.

## Deferred Web Work

The following RFC 0008 and RFC 0013 items remain deferred:

- browser automation with Playwright or equivalent;
- Lighthouse verification;
- hosted public demo deployment;
- plot tabs for sheer plan and cross-section views;
- web comparison report views.
