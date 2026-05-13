# REVIEW_OPS

Verdict intent: accept_with_findings

## Scope

This is the `reviewer_ops` artifact for workflow
`0043-web-hosted-browser-acceptance-revision`. I reviewed RFC 0032 against the
0041 blocker context, hosted-demo documentation needs, Docker/local serve
behavior, browser-tooling failure behavior, deterministic tests, and CFD route
dependency states. I did not run Striatum mutation commands and did not edit
source or documentation outside this artifact path.

The prior 0041 review artifacts were absent from the current worktree, so I
read them from branch `striatum/0041-web-hosted-browser-acceptance` with
`git show`, per the task instructions.

## Conclusion

No blocking ops/test issue remains in RFC 0032 itself. It narrows RFC 0030 into
an implementation-ready local browser-acceptance and hosted-demo documentation
slice (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:28`), explicitly
does not require public hosted operation (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:45`),
and keeps real CFD solvers, hosted workers, Dockerized solver execution,
validated CFD output, calibrated resistance, and final-fitness claims out of
scope (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:53`).

The findings below should feed the ledger and implementation slice. They are
current implementation/documentation gaps or precision corrections needed to
satisfy RFC 0032 without overclaiming production hosting or solver readiness.

## Findings

### O1 - Major - Required browser acceptance is still optional/self-skipping today

RFC 0032 requires a separate browser-acceptance profile where missing
Playwright/Chromium or equivalent browser tooling fails, not skips
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:68`,
`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:132`). Current docs
still describe only optional browser smoke
(`docs/WEB_VERIFICATION.md:27`), and the current browser test uses
`pytest.importorskip` for Playwright plus `pytest.skip` for missing Chromium
(`tests/test_web_browser.py:50`, `tests/test_web_browser.py:78`).
`pyproject.toml` defines the `browser` extra but no marker/profile split
(`pyproject.toml:34`, `pyproject.toml:51`).

Correction needed: add and document a distinct required browser-acceptance
command/profile that hard-fails with the exact setup command when browser
tooling is absent. Keep the optional self-skipping smoke path available for
lean development, but do not cite it as acceptance evidence.

### O2 - Major - Real-browser coverage must expand beyond the existing smoke

RFC 0032 requires browser-visible initial render, controls, metrics, analysis
content, nonblank 3D before and after mutation, representative mutation/metrics
change, share URL round trip, STL bytes through a browser-facing path, and
console/network cleanliness
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:75`,
`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:136`). The current
Playwright test waits for text and verifies one slider-driven metrics change
only (`tests/test_web_browser.py:87`, `tests/test_web_browser.py:97`). URL
round-trip, STL bytes, and nonblank render evidence are headless-only today
(`tests/test_web.py:63`, `tests/test_web.py:142`, `tests/test_web.py:242`).

There is also a served-share path to verify carefully: `_share_url` writes a
`?hull=...` value (`kayakgen/ui/web/app.py:269`), while `kayakgen serve`
constructs `create_app(initial_hull=...)` and does not pass request query state
into app creation (`kayakgen/cli/main.py:338`).

Correction needed: extend browser acceptance to collect console/page/network
events, fail on unexpected errors or failed requests, assert nonblank
browser-visible VTK evidence, test mutate -> Share -> reload/query round trip,
and test STL export via button download or `/api/stl?part=hull` with binary STL
length/count checks. Any temporary network allowlist must include exact URL
pattern, status, rationale, and removal condition
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:91`).

### O3 - Major - Hosted-demo docs need exact runtime and persistence wording

RFC 0032 accepts hosted-demo documentation, not live hosted operation. It asks
the docs to record the serve command, supported environment variables,
persistence caveats, redeploy steps, smoke checks, and exploratory/raw-CFD
wording (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:95`,
`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:149`). Current
`WEB_VERIFICATION.md` has local manual and Docker checks
(`docs/WEB_VERIFICATION.md:51`, `docs/WEB_VERIFICATION.md:67`) and still says no
hosted public demo is deployed (`docs/WEB_VERIFICATION.md:116`), but it does
not yet provide the hosted-demo runbook content RFC 0032 requires.

The environment-variable wording needs precision. The CLI exposes `--host` and
`--port` options (`kayakgen/cli/main.py:322`, `kayakgen/cli/main.py:328`), and
the web code actually reads `KAYAKGEN_WEB_CFD_JOBS_ROOT`
(`kayakgen/ui/web/controllers.py:42`, `kayakgen/ui/web/controllers.py:641`).
The Dockerfile sets `TRAME_HOST` and `TRAME_PORT`, but its command hard-codes
`kayakgen serve --host 0.0.0.0 --port 8080` (`Dockerfile:21`,
`Dockerfile:25`), so those variables should not be documented as supported
runtime controls unless the implementation changes to consume them.

Correction needed: add a `Hosted Demo Runbook (documentation only)` section to
`docs/WEB_VERIFICATION.md` with clean checkout install, Docker build/run,
`kayakgen serve --host 0.0.0.0 --port 8080`, smoke URL/checklist,
stop/redeploy steps, and explicit no-public-URL/no-production-hosting wording.
Document `KAYAKGEN_WEB_CFD_JOBS_ROOT` for server-local CFD artifacts. State that
encoded share URLs survive redeploy, `/api/hulls` IDs are in-memory only
(`kayakgen/ui/web/controllers.py:301`), CFD artifacts persist only on the
server filesystem or mounted Docker volume, and there is no production database
or design library.

### O4 - Major - CFD fixture/unavailable states need clearer browser/test coverage

RFC 0032 keeps `/api/cfd/*` as a local job-record inspection surface and allows
profiles, readiness failures, queued/unavailable/failed/succeeded fixture
states, logs, and raw artifacts only with raw/unvalidated semantics
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:115`). The route
payload helpers already preserve `result_semantics: raw_unvalidated` and the raw
warning (`kayakgen/ui/web/controllers.py:645`), and browser status lines call
unavailable/failed terminal problem states while successful records remain raw
(`kayakgen/ui/web/controllers.py:554`).

The implementation now also has a deterministic `fixture-local-command` profile
(`kayakgen/eval/cfd/jobs.py:295`, `kayakgen/eval/cfd/jobs.py:937`), but
`docs/USER_GUIDE.md` still lists only the two unavailable profiles and
`mock-failing-local-command` (`docs/USER_GUIDE.md:269`). Web tests cover
unavailable and failed paths (`tests/test_web.py:338`, `tests/test_web.py:484`);
the successful fixture path is covered in core CFD tests but not through
`/api/cfd/*` (`tests/test_cfd_jobs.py:526`). The browser panel also presents a
plain `Solver profile` selector and `Run` button (`kayakgen/ui/web/app.py:486`,
`kayakgen/ui/web/app.py:520`), so implementation should make profile/test
adapter semantics visible before users press run.

Correction needed: add a deterministic web-route test for
`fixture-local-command` prepare/run/raw-result success, asserting raw claim fields
and warnings throughout. Update user-facing docs and browser copy to label the
fixture profile as a checked-in deterministic test adapter, not real CFD, and to
show profile metadata such as adapter name, required readiness/profile, and
raw/unvalidated semantics.

### O5 - Medium - Legacy generic job stubs should be explicitly scoped

The RFC 0008 generic `/api/jobs` stubs still return a minimal 501 error
(`kayakgen/ui/web/controllers.py:944`, `kayakgen/ui/web/controllers.py:1025`).
RFC 0032's CFD acceptance surface is the local `/api/cfd/*` route set, but the
older generic route can still look adjacent to solver work.

Correction needed: either document the legacy `/api/jobs` stub as outside RFC
0032 acceptance, or give it the same structured unavailable/raw wording used by
the CFD-specific route layer.

## Positive Evidence

Docker/local serve wiring is coherent for the current slice. The Docker image
installs `.[web]`, exposes port 8080, and runs `kayakgen serve --host 0.0.0.0
--port 8080` (`Dockerfile:19`, `Dockerfile:23`, `Dockerfile:25`). The CLI serve
command exposes host/port defaults and starts the Trame app with those values
(`kayakgen/cli/main.py:322`, `kayakgen/cli/main.py:340`).

The 0043 workflow fixes the 0041 process gap: it declares a first-pass review
revision policy (`docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json:12`)
and cycles first-pass traceability, browser, and ops `needs_revision` results
back to the review anchor once
(`docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json:153`).
The 0041 workflow only had a final-review cycle
(`docs/workflows/0041-web-hosted-browser-acceptance/workflow.json:122`).

## Verification

Commands run in this review:

- `.venv/bin/python -m pytest tests/test_web.py -q` -> `24 passed in 3.65s`
- `.venv/bin/python -m pytest tests/test_web_browser.py -q` -> `1 passed in 3.06s`
- `.venv/bin/python -m pytest tests/test_cfd_jobs.py -q` -> `21 passed in 4.58s`
- `.venv/bin/python -m kayakgen.cli.main serve --help` -> serve exposes
  `--host` and `--port`

I did not run `docker build` or `docker run`; Docker behavior was reviewed from
the Dockerfile and documented local/Docker checks.

## Sub-Agent Help Used

Three read-only sub-agents were used with disjoint scopes:

- Anscombe reviewed browser tooling and real-browser test coverage.
- Einstein reviewed hosted-demo docs, Docker/local serve behavior, and runtime
  environment/persistence wording.
- Dirac reviewed CFD route dependency states, fixture/unavailable wording, and
  deterministic CFD route test gaps.

Their findings were incorporated here. None reported editing files or running
Striatum mutation commands.
