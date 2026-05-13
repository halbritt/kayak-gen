author: operator [self-declared: operator-final-review]

# Final review - 0020 browser acceptance and demo

Verdict: accept_with_findings

## Coverage

| Finding | Evidence | Result |
| --- | --- | --- |
| F-001 browser test entry point | `tests/test_web_browser.py` starts `kayakgen serve`, opens Chromium with Playwright, checks app/metrics text, changes a slider, and asserts metrics change. `pyproject.toml` adds optional `browser` extra. | Pass |
| F-002 Lighthouse gate | `docs/WEB_VERIFICATION.md` records setup and command. Workflow run produced Best Practices 92. The Trame `/paraview/` 405 console audit finding is documented as residual. | Accept with finding |
| F-003 serve wording | RFC 0008 and web verification docs now describe `kayakgen serve` as a scriptable server start, not default auto-open. | Pass |
| F-004 hosted demo | `docs/WEB_VERIFICATION.md` says Docker is the current demo artifact and no hosted public demo exists. | Pass |
| F-005 precise RFC status | RFC 0008 and RFC index now say `partial browser-smoke` and defer hosted demo, plot tabs, console-clean Lighthouse, auto-open, and web comparison views. | Pass |

## Verification

- `.venv/bin/python -m pytest tests/test_web_browser.py -q` -> 1 passed.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py tests/test_web_browser.py -q`
  -> 24 passed.
- `.venv/bin/python -m pytest -q` -> 134 passed.
- `git diff --check` -> clean.
- `docker build -t kayakgen-web-verify-0020 .` -> passed.
- Container HTTP smoke on `http://127.0.0.1:18083/` -> 200, 1376 bytes.
- Lighthouse via `npx --yes lighthouse@latest` and Playwright Chromium ->
  Best Practices 92; `errors-in-console` reported `/paraview/` 405.
- `.venv/bin/python -m ruff check .` did not run because `ruff` is not
  installed in the current virtualenv.

## Final gate

Accepted with the explicit finding that console-clean Lighthouse acceptance is
still partial. The workflow now has a real browser smoke path, truthful browser
and Lighthouse documentation, Docker demo evidence, and no false hosted-demo or
web-comparison claims.
