# Patch Summary - workflow 0043 web hosted browser acceptance revision

## Files Changed

- `pyproject.toml`
- `tests/conftest.py`
- `tests/test_web_browser.py`
- `tests/test_web.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `docs/WEB_VERIFICATION.md`
- `docs/USER_GUIDE.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md`
- `docs/rfcs/README.md`
- `striatum/0043-web-hosted-browser-acceptance-revision/implementation/PATCH_SUMMARY.md`

## Behavior Changed

The browser test suite now has a declared `browser_acceptance` marker and
`--browser-acceptance` pytest option. The same test remains usable as optional
browser smoke, but the acceptance profile fails when Playwright or Chromium is
missing.

`tests/test_web_browser.py` now starts `kayakgen serve` and verifies
browser-visible controls, compact analysis content, nonblank 3D evidence before
and after mutation, metric mutation, Share URL reload in a fresh browser page,
STL bytes through `/api/stl`, and console/page/network failure collection.

The Trame server now rehydrates `?hull=...` on browser GET requests for `/` and
`/index.html`, returns an exact local `/ws` connection JSON response for the
historical `POST /paraview/` browser probe, and returns 204 for `/favicon.ico`.
This fixes local browser acceptance without adding a broad Trame or VTK
allowlist.

The compact CFD panel now labels the profile selector as local solver/test
state and always identifies `fixture-local-command` as a deterministic checked-in
test adapter, not real CFD. Generic `/api/jobs` stubs now carry the same
raw/unvalidated warning and explicitly scope RFC 0032 acceptance to `/api/cfd/*`.

Web route tests now cover deterministic `fixture-local-command` prepare, run,
logs, and raw-result success through `/api/cfd/*`, while asserting
`raw_unvalidated` claim fields, empty accepted uses, fixture warnings, and
browser raw-result wording.

`docs/WEB_VERIFICATION.md` now documents default headless checks, optional
browser smoke, required browser acceptance, hosted-demo documentation-only
runbook material, persistence caveats, smoke steps, and explicit no-public-URL /
no-production-hosting / no-validated-CFD wording. RFC docs now record RFC 0032
as landed for this local browser/docs slice and keep hosted operation, full
dashboard parity, real solver execution, validated CFD, calibrated resistance,
and final design-fitness claims deferred.

## Tests Run

- `python3 -m py_compile tests/test_web_browser.py tests/test_web.py tests/conftest.py kayakgen/ui/web/app.py kayakgen/ui/web/controllers.py` -> passed.
- `/tmp/kayakgen-0043-venv/bin/python -m pytest tests/test_web.py -q` -> 25 passed.
- `/tmp/kayakgen-0043-venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q` -> 1 passed.
- `/tmp/kayakgen-0043-venv/bin/python -m pytest tests/test_web.py tests/test_web_browser.py tests/test_cli.py tests/test_cfd_jobs.py -q` -> 65 passed.
- `/tmp/kayakgen-0043-venv/bin/python -m ruff check tests/conftest.py tests/test_web_browser.py tests/test_web.py kayakgen/ui/web/app.py kayakgen/ui/web/controllers.py` -> passed.
- `/tmp/kayakgen-0043-venv/bin/python -m pytest -q` -> 252 passed.
- `git diff --check` -> passed.

## Deferred Findings

- No public hosted demo URL or production hosting is claimed.
- No real OpenFOAM, SU2, hosted worker, Dockerized solver execution, validated
  CFD output, calibrated resistance, or final design-fitness claim is added.
- Full dashboard parity, full plot tabs, mobile editing parity, sweep
  exploration, Pareto filtering, and multi-candidate UI parity remain deferred.
- The browser acceptance profile verifies local console/page/network cleanliness;
  Lighthouse Best Practices remains an optional separately documented check.

## Proposed CHANGELOG.md Entry

- Land workflow 0043's local browser-acceptance profile, hosted-demo runbook
  documentation, exact `/paraview/` browser-probe handling, Share/STL/3D browser
  checks, and raw/unvalidated `/api/cfd/*` fixture-success coverage while
  keeping public hosting, real solver execution, validated CFD, calibrated
  resistance, and final design-fitness claims deferred.
