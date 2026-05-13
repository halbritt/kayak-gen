author: operator [self-declared: operator-implementer]

# Patch summary - 0020 browser acceptance and demo

## Files changed

- `pyproject.toml`
- `tests/test_web_browser.py`
- `docs/WEB_VERIFICATION.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/README.md`
- `docs/workflows/0020-browser-acceptance-demo/OPERATOR_REPORT.md`

## Findings addressed

- F-001: Added optional Playwright browser smoke coverage for `kayakgen serve`.
  The test starts the server, opens the Trame UI in Chromium, waits for visible
  app/metric text, focuses a slider, presses ArrowRight, and asserts the metrics
  panel changes. It self-skips with setup guidance if Playwright or Chromium is
  unavailable.
- F-002: Added Lighthouse documentation and recorded the workflow 0020
  Lighthouse run. Best Practices scored 92. Console-clean acceptance remains
  partial because Lighthouse recorded a Trame `/paraview/` 405 network log.
- F-003: Updated RFC 0008 and verification docs so `kayakgen serve` is
  described as a scriptable server start, not default browser auto-open.
- F-004: Documented Docker as the current reproducible demo artifact and kept
  hosted public demo deployment deferred.
- F-005: Updated RFC/readme status to `partial browser-smoke` without claiming
  plot tabs, hosted demo, auto-open, console-clean Lighthouse, or RFC 0013 web
  comparison views.

## Verification

- `.venv/bin/python -m pip install -e ".[web,browser]" --quiet` -> passed.
- `.venv/bin/python -m playwright install chromium` -> passed.
- `.venv/bin/python -m pytest tests/test_web_browser.py -q` -> 1 passed.
- `CHROME_PATH=/home/halbritt/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome npx --yes lighthouse@latest http://127.0.0.1:18082/ --only-categories=best-practices --chrome-flags="--headless=new --no-sandbox" --output=json --output-path=/tmp/kayakgen-lighthouse.json --quiet` -> passed; Best Practices 92; `errors-in-console` audit reported `/paraview/` 405.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py tests/test_web_browser.py -q` -> 24 passed.
- `.venv/bin/python -m pytest -q` -> 134 passed.
- `docker build -t kayakgen-web-verify-0020 .` -> passed.
- Container HTTP smoke on `http://127.0.0.1:18083/` -> 200, 1376 bytes.
- `git diff --check` -> clean.
- `.venv/bin/python -m ruff check .` -> not run successfully; current virtualenv
  does not have `ruff` installed.
