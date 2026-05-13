# Review Scope - Workflow 0043

This is the first `review_revision_anchor` handoff for workflow
`0043-web-hosted-browser-acceptance-revision`. The artifact is intentionally
bounded: it carries forward workflow 0041 review blockers and anchors the three
first-pass review lanes for RFC 0032. It does not implement product code and
does not act as the Striatum operator.

No Striatum state mutation commands were run. The only intended write in this
job is this file.

## Sources Read

Required sources read in this job:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/WEB_VERIFICATION.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0018-web-cfd-job-routes.md`
- `docs/rfcs/0030-web-hosted-browser-acceptance.md`
- `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md`
- `docs/workflows/0041-web-hosted-browser-acceptance/SOURCES.md`
- `docs/workflows/0041-web-hosted-browser-acceptance/workflow.json`
- `docs/workflows/0029-web-cfd-job-routes/workflow.json`
- `docs/workflows/0037-first-real-cfd-fixture-adapter/workflow.json`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/SOURCES.md`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/prompts/review_revision_anchor.md`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/roles/review_anchor.md`

Optional implementation/test context read:

- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/state.py`
- `kayakgen/cli/main.py`
- `tests/test_web.py`
- `tests/test_web_browser.py`
- `Dockerfile`
- `pyproject.toml`

The 0041 review artifacts are absent from the current worktree, but the local
Git branch `striatum/0041-web-hosted-browser-acceptance` contains:

- `striatum/0041-web-hosted-browser-acceptance/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0041-web-hosted-browser-acceptance/browser/REVIEW_BROWSER.md`
- `striatum/0041-web-hosted-browser-acceptance/ops/REVIEW_OPS.md`

Those branch artifacts were read with `git show` and are the basis for the
0041 carry-forward below.

## Sub-Agent And Parallel Help Used

Three read-only sub-agents were used with disjoint investigation scopes:

- Averroes inspected 0041 artifact availability and blocker carry-forward.
  It reported the artifacts missing in the current worktree; the main agent
  then confirmed and read the three 0041 artifacts from the 0041 Git branch.
- Pasteur inspected browser acceptance, implementation, and test context for
  RFC 0032 scope checks.
- Lorentz inspected workflow/RFC traceability, the three first-pass review lane
  boundaries, and anti-scope wording.

In addition, required docs and code references were read through parallel shell
commands. No sub-agent edited files or ran Striatum mutation commands.

## Conservative RFC 0032 Scope

RFC 0032 is the implementation target for this workflow, not the full original
RFC 0030 scope. It preserves RFC 0030's direction but narrows the next slice to
local required browser acceptance, hosted-demo documentation, exact
console/network handling, Lighthouse status handling, share/STL browser paths,
explicit plot/dashboard boundaries, and honest raw/unvalidated CFD route
wording.

In scope:

- Document the default headless web command and a separate required
  `browser-acceptance` command in `docs/WEB_VERIFICATION.md`.
- Make the browser-acceptance profile fail when Playwright/Chromium or the
  chosen real-browser tooling is missing in an environment claiming browser
  acceptance.
- Run browser acceptance against local `kayakgen serve`, not a public hosted
  URL.
- Verify initial browser-visible hull/deck render, controls, metrics, analysis
  content, a representative control mutation, nonblank 3D evidence before and
  after mutation, share URL round trip, STL export bytes through a
  browser-facing path or route, and console/network cleanliness.
- Document hosted-demo operation without requiring a public deployment:
  `kayakgen serve --host 0.0.0.0 --port 8080`, supported environment variables,
  persistence caveats, clean redeploy/smoke steps, and exploratory/raw-CFD
  wording.
- Preserve Lighthouse Best Practices `>= 90` as the target while making clear
  that the prior score of 92 did not close console-clean acceptance.
- Keep the compact web analysis and comparison-report inspection views as the
  accepted boundary for this slice, while explicitly deferring full dashboard,
  sweep exploration, Pareto filtering, and plot parity beyond the delivered
  compact surfaces.
- Preserve `/api/cfd/*` as local filesystem job-record inspection with
  structured unavailable/dependency states and `raw_unvalidated` semantics.

Out of scope:

- Public hosted demo operation or vendor-specific deploy automation.
- Replacing Trame with a custom JavaScript frontend.
- Full mobile editing parity.
- Full comparison dashboards, sweep exploration, Pareto filtering, or
  multi-candidate report UI parity.
- Real OpenFOAM/SU2/solver adapters, hosted workers, Dockerized solver
  execution, validated CFD output, calibrated resistance claims, or final
  design-fitness claims.
- Accounts, authentication, quotas, billing, collaborative editing, persistent
  design libraries, or production multi-user hosting.
- Making unavailable, failed, fixture, or raw CFD states look runnable,
  calibrated, validated, or physically accepted.

## 0041 Carry-Forward Findings

### Blocker: browser acceptance is still optional/self-skipping

0041 traceability, browser, and ops reviews all identified that the current
browser suite is smoke-only and self-skipping. `tests/test_web_browser.py`
uses `pytest.importorskip("playwright.sync_api")` and skips when Chromium is
missing. `docs/WEB_VERIFICATION.md` describes this as optional browser smoke.

RFC 0032 requires a distinct browser-acceptance profile where missing browser
tooling fails, not skips. The review lanes should treat optional smoke coverage
as useful evidence for default development but insufficient for acceptance.

### Blocker: browser coverage does not yet cover the RFC 0032 behavior set

0041 carried forward missing real-browser checks for share URL round trip, STL
export, in-browser nonblank 3D evidence, and console/network cleanliness. The
headless tests already cover URL encoding/decoding, STL bytes, route helpers,
and offscreen VTK nonblank rendering, but RFC 0032 requires browser-facing
evidence against `kayakgen serve`.

One implementation-context detail for reviewers: current `kayakgen serve`
constructs `create_app(initial_hull=...)` from an optional hull file path. It
does not itself pass a request query string into `create_app`, while
`create_app(initial_query=...)` and `load_from_query(...)` exist at the app
level. The browser lane should verify the actual served share/reload path, not
only the headless helper path.

### Blocker: console/network clean gate and Trame `/paraview/` 405 are not closed

0041 found no browser collection for console errors, page errors,
request failures, failed static assets, failed API calls, mixed content, or
unexpected failed requests. `docs/WEB_VERIFICATION.md` still records the
workflow 0020 Lighthouse Best Practices score of 92 while noting a Trame
`/paraview/` 405 network log, so Lighthouse threshold evidence and
console-clean acceptance remain separate.

RFC 0032 permits only exact temporary allowlists: URL pattern, status,
rationale, and removal condition. Broad permanent allowlists for Trame, VTK, or
`/paraview/` errors are out of scope.

### Blocker: hosted-demo documentation/runbook is missing

0041 found Docker/local serve wiring present but no hosted-demo runbook. RFC
0032 accepts hosted-demo documentation, not a live public deployment. Reviewers
should require the docs to record:

- `kayakgen serve --host 0.0.0.0 --port 8080`
- Docker clean build/run redeploy steps
- `TRAME_HOST` and `TRAME_PORT` as Docker defaults, where relevant
- `KAYAKGEN_WEB_CFD_JOBS_ROOT` for local CFD job artifacts
- ephemeral in-memory hull-id persistence unless a future store is added
- local filesystem CFD jobs root persistence caveats
- manual smoke steps for hosted/demo operation
- exploratory status wording with no validated CFD or calibrated performance
  claims

### Major: plot/dashboard boundary needs explicit acceptance wording

0041 traceability found compact analysis and comparison-report inspection
substantially present, while full plot/dashboard parity remains deferred. RFC
0032 narrows this: compact analysis/comparison surfaces can close this slice if
the documentation explicitly names them as the accepted boundary and lists
larger dashboards, sweep exploration, Pareto filtering, and full plot parity as
future work.

Reviewers should avoid expanding this workflow into full RFC 0008 dashboard
parity.

### Major: raw/unvalidated CFD route wording must not regress

0041 ops found `/api/cfd/*` mostly sound: structured unavailable/dependency
states are visible, payloads carry `result_semantics: raw_unvalidated`, and the
UI/docs warn that local CFD output is raw and unvalidated. RFC 0018 also
records that hosted workers, real solvers, validated output, and calibrated CFD
claims remain deferred.

The implementation should preserve that boundary. If the legacy generic
`/api/jobs` RFC 0008 stub is touched, either explicitly scope it outside RFC
0032 acceptance or keep its unavailable wording from implying a runnable solver
job path.

## First-Pass Review Lane Anchors

### Traceability Review

Review against RFC 0032 first, then map back to RFC 0030, RFC 0008 partial web
status, and RFC 0018 local CFD route status. Required checks:

- RFC 0032 acceptance criteria are mapped to docs, tests, UI behavior, route
  behavior, and explicit deferrals.
- 0041 blocker/major findings above are either carried into review findings or
  explained as already addressed.
- `docs/WEB_VERIFICATION.md` and `docs/USER_GUIDE.md` do not overclaim hosted
  operation, full browser parity, full dashboard parity, real solver execution,
  calibrated resistance, validated CFD, or final design fitness.
- The three first-pass review jobs in workflow 0043 feed the ledger only after
  their revision cycle path is available; workflow 0043 declares that cycle for
  traceability, browser, and ops reviews.

### Browser Review

Review required local real-browser acceptance. Required checks:

- The acceptance command is distinct from the default headless path.
- Missing Playwright/Chromium or equivalent browser tooling fails in the
  browser-acceptance profile.
- The test starts `kayakgen serve` on a local port and waits on stable
  browser-visible state rather than fixed sleeps where practical.
- Initial page load shows hull/deck view, controls, metrics, and analysis
  content.
- The 3D view has nonblank browser-visible evidence after initial load and
  after a representative mutation.
- A representative hull parameter mutation changes browser-visible metrics.
- Share URL behavior reconstructs the current hull parameters on reload.
- STL export returns valid STL bytes through a button-driven or browser-facing
  route path.
- Console/network collection fails on uncaught exceptions, page errors, failed
  static assets, failed API calls, mixed content, unexpected failed requests,
  and unexpected console errors.
- Any temporary allowlist is exact and documented; the historical
  `/paraview/` 405 cannot be silently ignored.
- Lighthouse Best Practices `>= 90` is handled as recorded evidence and
  documentation, but the old score is not treated as closing console-clean
  acceptance.

### Ops And Tests Review

Review documentation, reproducibility, and test profile behavior. Required
checks:

- Hosted-demo scope is documentation/runbook only, not a public deployment.
- The runbook documents local and Docker paths for
  `kayakgen serve --host 0.0.0.0 --port 8080`.
- Environment variables and persistence caveats are documented, including
  `TRAME_HOST`, `TRAME_PORT`, `KAYAKGEN_WEB_CFD_JOBS_ROOT`, ephemeral hull-id
  storage, and local CFD jobs root behavior.
- Browser tooling prerequisites and failure behavior are documented without
  making required acceptance look optional.
- Headless web checks remain available for normal development and lean CI.
- Browser acceptance remains deterministic enough for review: local port,
  explicit waits, bounded server lifecycle, and clear setup/failure messages.
- `/api/cfd/*` route docs and UI copy preserve local filesystem job-record
  semantics, unavailable/failed terminal problem states, and raw/unvalidated
  warnings.
- Legacy `/api/jobs` generic stubs are either explicitly outside the RFC 0032
  route acceptance or worded as unavailable without implying real solver
  execution.

## Ledger Seed

The ledger should consolidate findings into a safe implementation slice with
roughly these remediation targets:

1. Add or document a required browser-acceptance profile separate from the
   headless/default web checks.
2. Extend real-browser checks for initial render, nonblank 3D, mutation/metrics,
   share URL round trip, STL export, and console/network collection.
3. Fix any local web issues discovered by those checks, without changing domain
   semantics or introducing new CFD claims.
4. Add hosted-demo runbook/status material to web verification docs.
5. Preserve raw/unvalidated CFD route and panel wording.
6. Update RFC/index/changelog/workflow status only as needed to record what
   landed and what remains deferred.

The ledger should not assign a public hosted deployment, dashboard parity
buildout, real solver adapter, or calibrated CFD claim to this workflow.
