# Web Verification

This document records reproducible checks for the RFC 0008 Trame web frontend.
It distinguishes default headless verification from optional browser and
Lighthouse checks that require extra tooling.

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

## Optional Browser Smoke

Install the optional browser tooling and the Chromium browser binary:

```bash
pip install -e ".[web,browser]"
python -m playwright install chromium
```

Run the browser smoke:

```bash
.venv/bin/python -m pytest tests/test_web_browser.py -q
```

The test starts `kayakgen serve`, opens the app in headless Chromium, waits for
the Trame UI and metrics panel, and changes a slider input to verify the
browser-facing page responds. If Playwright or Chromium is unavailable, the test
skips with the exact setup command rather than pretending browser acceptance
ran.

Workflow 0020 result: after installing `kayakgen[web,browser]` and Chromium via
Playwright, `.venv/bin/python -m pytest tests/test_web_browser.py -q` passed.

## Local Manual Browser Check

Start the app:

```bash
kayakgen serve --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` in a browser. Verify that the hull and deck are
visible, sliders update the shape and metrics, Reset restores defaults, Share
fills the share URL field, and Export Hull STL / Export Deck STL trigger STL
downloads.

The current CLI starts the server and does not auto-open a browser tab. That
scriptable default is intentional for Docker and CI friendliness.

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

## Lighthouse

Lighthouse remains an optional gate because it requires both Lighthouse and a
Chromium-family browser. It is not part of the mandatory pytest suite.

When those tools are available, start `kayakgen serve` and run:

```bash
npx lighthouse http://127.0.0.1:8080/ --only-categories=best-practices
```

Record the Lighthouse Best Practices score before claiming the RFC 0008
Lighthouse criterion. The target remains Best Practices >= 90.

Workflow 0020 result: Lighthouse ran with `npx --yes lighthouse@latest` and
Playwright's Chromium against a local server. Best Practices scored 92. The
console-errors audit still reported a Trame `/paraview/` 405 network log, so
the score threshold is recorded but full console-clean browser acceptance
remains partial.

## Hosted Demo Status

No hosted public demo is deployed from this repo today. The Docker image is the
current reproducible demo artifact and deployment input for a future Fly.io,
Railway, Render, or VPS demo.

## Deferred Web Work

The following RFC 0008 and RFC 0013 items remain deferred:

- always-on browser automation in the default test suite;
- console-clean Lighthouse acceptance;
- hosted public demo deployment;
- plot tabs for sheer plan and cross-section views;
- web comparison report views.
