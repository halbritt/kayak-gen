author: operator [self-declared: operator-final-review]

# Final review - 0017 web verification

Verdict: accept

## Coverage

| Finding | Evidence | Result |
| --- | --- | --- |
| F-001 status naming | RFC 0008 and RFC index now say `partial verified-headless` | Pass |
| F-002 visual smoke | `tests/test_web.py` checks actors, interactor, and nonblank VTK pixels | Pass |
| F-003 skipped browser tooling | `docs/WEB_VERIFICATION.md` records missing Playwright/Lighthouse/browser prerequisites and future commands | Pass |
| F-004 deployment docs | `docs/WEB_VERIFICATION.md` documents local and Docker verification commands | Pass |
| F-005 serve behavior | Docs state that `kayakgen serve` starts a server and does not auto-open a browser | Pass |
| F-006 web comparison deferral | RFC 0013 and README keep web comparison UI deferred | Pass |

## Verification

- `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py -q`
  -> 19 passed.
- `.venv/bin/python -m pytest -q` -> 122 passed.
- `docker build -t kayakgen-web-verify .` -> passed.
- Container HTTP smoke on port 18080 returned a 1376-byte app response after
  following redirects.
- `git diff --check` -> clean.
- `ruff` was not run because it is not installed in the current virtualenv.
- Playwright and Lighthouse were not run because the required tooling and
  browsers are unavailable in this environment.

## Final gate

Accepted. The workflow lands a truthful headless-verification slice for the web
frontend, fixes Docker/server runtime issues found by that verification, and
keeps browser automation, Lighthouse, hosted demo, plot tabs, and web comparison
views explicitly deferred.
