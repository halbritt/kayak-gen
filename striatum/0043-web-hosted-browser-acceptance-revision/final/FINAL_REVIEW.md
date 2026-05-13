# Final Review - Workflow 0043 Web Hosted Browser Acceptance Revision

## Scope of this review

Verify the landed RFC 0032 slice against
`striatum/0043-web-hosted-browser-acceptance-revision/ledger/FINDINGS.md`
implementation-required findings (F-1..F-7), preservation notes, and explicit
deferrals; confirm browser-acceptance gating, console/network/Lighthouse
handling, hosted-demo doc wording, parity boundary, and `/api/cfd/*` raw
semantics on `main` after commit `2798591 Land RFC 0032 browser acceptance
revision`.

Tests run from this review:

- `.venv/bin/python -m pytest tests/test_web.py -q` -> 27 passed.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py tests/test_cfd_jobs.py -q` -> 68 passed.
- `.venv/bin/python -m pytest tests/test_web_browser.py -q` -> 1 passed (Playwright/Chromium were installed in this venv).
- `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q` -> 1 passed.

## Ledger finding verification

### F-1 - Required browser-acceptance profile (satisfied)

- `pyproject.toml:34` declares the `browser` extra (`playwright>=1.45`) and
  `pyproject.toml:54-56` declares the `browser_acceptance` marker.
- `tests/conftest.py:12-18` registers `--browser-acceptance`.
- `tests/test_web_browser.py:40-66` gates Playwright/Chromium loading on
  `_browser_acceptance_required` (CLI flag or `KAYAKGEN_BROWSER_ACCEPTANCE`
  env), failing with `PLAYWRIGHT_SETUP` text in the acceptance profile and
  self-skipping with the same setup command otherwise.
- `tests/test_web_browser.py:309` marks the test with
  `@pytest.mark.browser_acceptance`, so `-m browser_acceptance
  --browser-acceptance` selects exactly the acceptance path.
- `docs/WEB_VERIFICATION.md:8-67` documents headless, optional smoke, and
  required acceptance commands, and `docs/WEB_VERIFICATION.md:42-44` calls
  out that the optional smoke "must not be cited as browser acceptance
  evidence."

### F-2 - Expanded real-browser coverage (satisfied)

`tests/test_web_browser.py:310-399` starts `kayakgen serve` over a free port
and verifies:

- Browser-visible controls and analysis text including `kayakgen`, `Length
  (m)`, `Metrics`, `Hydrostatics`, `Displacement`, `GM0`, `Resistance curve
  (raw comparative filter)`, `comparative_filter_only`, and `Comparison`
  (lines 321-331).
- Nonblank 3D before and after mutation via
  `_assert_nonblank_3d` (`tests/test_web_browser.py:204-214`), which
  picks the largest matching `canvas, img, [class*='vtk'], [class*='Vtk']`
  element, then unpacks the PNG screenshot via a hand-rolled decoder
  (`_png_rgb_range`, `_unfilter_png_scanline`, `_paeth`) and asserts a
  `max_rgb - min_rgb > 8` spread - a real pixel-level nonblank check, not
  just a bounding-box probe.
- Slider mutation via `ArrowRight` on the focused slider, with
  `page.wait_for_function` asserting the `pre` metrics text changes
  (lines 336-345).
- Share -> reload round trip: click Share, wait until an `input` value
  starts with `?hull=`, decode it locally via
  `hull_from_query_string` and assert `length_m != Hull().length_m`,
  then open a fresh page at `url + share_path` and confirm the metrics
  match the mutated value plus nonblank 3D
  (lines 348-370). The middleware in
  `kayakgen/ui/web/app.py:278-296` ensures GET `/` / `/index.html` rehydrate
  from `?hull=...`, closing the gap that F-2 flagged about
  `kayakgen serve --initial-query` not being wired.
- STL bytes via in-browser `fetch('/api/stl?part=hull', ...)`
  asserting `status == 200`, `content-type` includes `application/sla`,
  and `length == 84 + tri * 50` with `tri > 0`
  (lines 372-394, `_assert_stl_response` at lines 300-306).

### F-3 - Console / page / network failure collection and `/paraview/` (satisfied)

- `_collect_browser_failures` (`tests/test_web_browser.py:126-155`) hooks
  `console` (errors plus mixed-content warnings only - aligned with the
  RFC 0030 §3 mixed-content rule), `pageerror`, `requestfailed`, and
  `response` with `status >= 400` on the local origin, accumulating into a
  shared list that is asserted empty at the end of the test
  (`_assert_no_browser_failures` at lines 158-159, called at line 394).
- Failures are also collected on the reload page (line 363) so the share
  reload contributes to the same gate.
- The historical `/paraview/` 405 is handled by an exact local middleware:
  `kayakgen/ui/web/app.py:283-290` returns a JSON `{"sessionURL":
  "ws[s]://<host>/ws", "secret": "wslink-secret"}` for `POST /paraview/`,
  so the browser probe sees a 200 instead of a 405. No broad Trame, VTK,
  or `/paraview/` allowlist is added in the test or docs; the temporary
  `/favicon.ico` 204 (line 291-292) is a single narrow rule, not a wildcard.
- `docs/WEB_VERIFICATION.md:72-75` records the constraint that "Browser
  acceptance has no broad Trame, VTK, or `/paraview/` allowlist" and that
  future allowlists must document exact URL pattern, status, rationale, and
  removal condition - matching RFC 0032 §2 wording.
- `docs/WEB_VERIFICATION.md:110-128` keeps Lighthouse explicitly optional
  ("not part of the mandatory pytest suite"), preserves the historical 92
  score as threshold-only evidence with a note that the previous
  `/paraview/` 405 console log makes it "historical threshold evidence
  rather than console-clean acceptance evidence," and points at the new
  direct browser checks as the gate. Lighthouse handling aligns with RFC
  0032 §3 deferring the score gate while requiring direct console-clean
  evidence.

### F-4 - Hosted-demo documentation (satisfied)

`docs/WEB_VERIFICATION.md:148-210` adds the "Hosted Demo Runbook
(Documentation Only)" section. It includes:

- The exact run command `kayakgen serve --host 0.0.0.0 --port 8080`
  (lines 154-158).
- Clean-checkout install with `python -m pip install -e ".[web]"` and the
  `KAYAKGEN_WEB_CFD_JOBS_ROOT=/srv/...` env var
  (lines 160-169).
- Docker build/run with `-e KAYAKGEN_WEB_CFD_JOBS_ROOT=/data/cfd-jobs` and
  volume mount (lines 171-179).
- Persistence caveats for `?hull=...`, `/api/hulls`, `/api/cfd/*`, and the
  absence of a production DB / account / quota system (lines 186-194).
- A manual hosted-demo smoke checklist (lines 196-204).
- Redeploy guidance and an explicit exploratory / no-OpenFOAM / no-hosted-
  worker / no-validated-CFD paragraph (lines 206-210).
- Env-var precision (lines 181-184): `--host` and `--port` are CLI runtime
  controls; `TRAME_HOST` / `TRAME_PORT` are Docker image defaults but the
  entry point still passes explicit CLI options.
- `docs/WEB_VERIFICATION.md:148-150` and the section heading explicitly
  state "No hosted public demo URL is deployed from this repo today, and
  this section is not a production-hosting claim." This satisfies F-4 and
  the explicit deferral note about no public hosting / no real solver
  claims.

### F-5 - Plot / dashboard parity boundary documentation (satisfied)

- `docs/WEB_VERIFICATION.md:131-145` adds a "Web Analysis Boundary" section
  that names the accepted RFC 0032 surface (hydrostatics rows with units,
  raw comparative resistance curve rows with warnings, comparison report
  inspection from `ComparisonReport` JSON, Pareto/candidate parameter
  reload) and lists what stays deferred (sheer plan / cross-section tabs,
  mobile editing parity, larger comparison dashboards, sweep exploration,
  Pareto filtering, multi-candidate UI parity, hosted report persistence,
  final design-fitness claims).
- `docs/rfcs/0008-web-frontend.md:9-23` updates the status note to call the
  compact analysis with units and raw warnings plus comparison report
  inspection "the accepted RFC 0032 web-analysis boundary" and records
  workflow 0043's direct console/network checks and `/paraview/` handling.
- `docs/rfcs/README.md:60-67` reflects the same parity boundary in the
  RFC index.
- `docs/USER_GUIDE.md:341-356` carries the same wording about the supported
  web shell scope versus deferred items.

### F-6 - CFD fixture profile coverage and wording (satisfied)

- New test `test_cfd_routes_fixture_command_success_remains_raw_unvalidated`
  (`tests/test_web.py:585-663`) walks the `fixture-local-command` profile
  through `/api/cfd/profiles`, `POST /api/cfd/jobs`, `POST
  /api/cfd/jobs/{id}/run`, `GET .../logs`, and `GET .../raw-result`,
  asserting `result_semantics == "raw_unvalidated"`, `warning ==
  CFD_RAW_RESULTS_WARNING`, `claim_state == "raw_unvalidated"`,
  `accepted_uses == []`, empty `validation_fixture_ids` and
  `calibration_fixture_ids`, presence of `CFD_FIXTURE_RESULTS_WARNING`, and
  positive raw `drag_force_n`. The panel text rendering is also asserted
  ("still raw solver output", "not calibrated or validated").
- Browser/panel wording lives in
  `kayakgen/ui/web/controllers.py:589-624`: every `cfd_status_lines_from_
  payload` output prepends `CFD_RAW_RESULTS_WARNING`,
  `CFD_LOCAL_FILESYSTEM_NOTICE`, and the line "fixture-local-command is a
  deterministic checked-in test adapter, not real CFD." Status transitions
  for `unavailable` / `failed` / `succeeded` all keep the raw framing
  (lines 620-623).
- Selector copy was tightened: `kayakgen/ui/web/app.py:514-520` labels the
  picker "Local solver/test profile."
- `docs/USER_GUIDE.md:275-281` now lists `fixture-local-command` as a
  "checked-in deterministic test adapter" and explicitly states it is
  "not a real CFD solver and does not produce validated or calibrated
  output," matching the F-6 wording requirement.

### F-7 - Generic `/api/jobs` scoping (satisfied)

- `kayakgen/ui/web/controllers.py:984-990` rewrites `job_stub_payload` to
  start from `_cfd_common_payload()` (so `result_semantics:
  raw_unvalidated` and the raw warning are present) and adds an `error`
  message that explicitly says "heavy CFD jobs are reserved by RFC 0008
  and not implemented; RFC 0032 acceptance uses the local raw /api/cfd/*
  route surface." `post_job` / `get_job` still return 501
  (lines 1070-1074).
- `tests/test_web.py:332-335` asserts the new wording: `stub["error"]`
  starts with `"heavy CFD"`, `result_semantics == "raw_unvalidated"`,
  `warning == CFD_RAW_RESULTS_WARNING`. Route registration is still
  checked at `tests/test_web.py:359-360`.

## Preservation notes verification

- Raw-unvalidated CFD contract preserved across `/api/cfd/*`:
  `_cfd_common_payload` (`controllers.py:685-689`) is the single source of
  `result_semantics: raw_unvalidated` and `warning: CFD_RAW_RESULTS_WARNING`,
  and is included in profile, job creation, status, run, logs, raw-result,
  and error responses (lines 402-413, 447, 455, 472, 508-516, 573-586,
  692-696). No `validated`, `calibrated`, or `final_fitness` state is
  introduced.
- Dockerfile-driven serve wiring is untouched in this patch summary's file
  set; `docs/WEB_VERIFICATION.md` records `TRAME_HOST` / `TRAME_PORT` as
  image defaults while CLI `--host` / `--port` remain the supported runtime
  controls, consistent with the preservation note.
- The bounded review-revision routing for the workflow is preserved in
  RFC 0032 §5 (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:130-138`).
- PRD / user-guide caveats about local-only web/CFD plumbing remain in
  `docs/PRD.md:41-49` and `docs/USER_GUIDE.md:341-356, 372-382`.

## Explicit deferral verification

The landed scope does not promote any deferral:

- No public hosted demo URL or production hosting language; the runbook
  section is gated by the "Documentation Only" header
  (`docs/WEB_VERIFICATION.md:148-150`).
- No JS-frontend replacement; the Trame shell remains intact.
- No mobile editing parity, larger dashboards, sweep exploration, Pareto
  filtering, or multi-candidate UI parity were added; the boundary section
  explicitly defers them.
- No real OpenFOAM / SU2 / hosted-worker / Dockerized-solver execution; CFD
  routes/panel keep raw/unvalidated wording.
- No accounts / auth / quota / billing / persistent design library work.
- Browser STL export remains an inspection artifact (`docs/USER_GUIDE.md:
  85-91, 263-271` keep open-surface / not-`cfd_ready` framing).

## Residual findings

None block acceptance. The following are non-blocking observations the
operator may choose to address.

- `R-1` Patch summary references a proposed CHANGELOG entry
  (`striatum/0043-web-hosted-browser-acceptance-revision/implementation/
  PATCH_SUMMARY.md:74-80`) but no "Land workflow 0043" entry has been added
  under `## Unreleased` in `CHANGELOG.md`. `CHANGELOG.md:64-67` only
  records the *addition* of RFC 0032 and workflow 0043, not the landed
  browser-acceptance slice. The ledger explicitly leaves changelog updates
  to the implementor/operator scope and does not require it, so this is an
  operator-side bookkeeping item, not a code/test regression.
- `R-2` `_collect_browser_failures` flags only `mixed content` warnings and
  ignores other console warnings
  (`tests/test_web_browser.py:131-135`). This matches RFC 0032 §2 and
  RFC 0030 §3 wording (mixed-content warnings are the named failure mode),
  and any deviation would require an RFC update, so this is reported as
  intentional behavior worth noting rather than a regression.
- `R-3` Lighthouse Best Practices is left as an optional documented gate
  rather than a CI-required check
  (`docs/WEB_VERIFICATION.md:110-128`). RFC 0032 carries this as a deferral
  ("Lighthouse Best Practices remains an optional separately documented
  check," per the patch summary) and RFC 0030's Lighthouse gate remains
  proposed-not-landed for this slice. Future workflows can pick it up
  without revisiting the local-acceptance contract.

## Conclusion

The landed implementation satisfies F-1 through F-7. Browser acceptance
fails closed when Playwright/Chromium are missing under the
`--browser-acceptance` profile while preserving an optional self-skipping
smoke path for lean environments. Browser-visible analysis content,
controls, metrics, nonblank 3D before/after mutation, Share -> reload, STL
bytes through `POST /api/stl`, and console/page/network collection are all
asserted against a real `kayakgen serve` process. The historical
`POST /paraview/` 405 is fixed by an exact local `/ws` connection JSON
response (no broad allowlist). Hosted-demo documentation is added with
explicit no-public-URL / no-production-hosting / no-validated-CFD wording.
The compact analysis / comparison-report parity boundary is documented in
the RFC, RFC index, and user guide. `/api/cfd/*` route coverage now spans
unavailable, failed, and `fixture-local-command` success states while
preserving `result_semantics: raw_unvalidated`, `claim_state:
raw_unvalidated`, empty `accepted_uses`, and `CFD_FIXTURE_RESULTS_WARNING`
throughout. Generic `/api/jobs` stubs carry the same raw/unvalidated
framing and explicitly scope RFC 0032 acceptance to `/api/cfd/*`. The full
pytest invocation in the patch summary (`-q` -> 252 passed) reproduces on
this checkout for the focused web/CLI/CFD subsets (96 passed across
`tests/test_web.py`, `tests/test_web_browser.py`, `tests/test_cli.py`,
`tests/test_cfd_jobs.py`, plus the browser-acceptance run).

Verdict intent: accept
