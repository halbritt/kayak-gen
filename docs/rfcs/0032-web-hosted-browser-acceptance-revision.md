# RFC 0032: Web Hosted Browser Acceptance Revision

Status: proposed
Date: 2026-05-13
Context: revises RFC 0030 into a conservative implementation slice after the
blocked workflow 0041 run. Builds on RFC 0008 web frontend status, RFC 0018
local web CFD routes, `docs/USER_GUIDE.md`, and `docs/WEB_VERIFICATION.md`.

## Problem

RFC 0030 set the right broad acceptance direction for hosted/demo and
real-browser closure, but workflow 0041 showed that the first implementation
slice was too large and too easy to block before the ledger could form. The
browser review returned `needs_revision`, while the workflow only declared a
revision cycle after final review. A first-pass browser revision therefore did
not have an explicit remediation path.

The product state is also still partial. The web frontend has a Trame shell,
parameter controls, hull rendering, compact analysis views, optional browser
smoke coverage, Docker input, and local web CFD job routes. It does not yet
have a live hosted demo, required browser acceptance, console-clean gates,
fully closed Lighthouse acceptance, or full dashboard parity. The local web CFD
routes expose raw local job records only; they are not hosted workers or
validated solver output.

## Goals

- Preserve RFC 0030's acceptance direction while narrowing the next slice to
  implementation-ready local browser acceptance and hosted-demo documentation.
- Separate default headless web checks from a deliberate browser-acceptance
  profile that fails when browser tooling is missing.
- Verify delivered browser behavior: initial render, core controls, metrics,
  analysis content, nonblank 3D view, representative control mutation, share
  URL round trip, STL export, and console/network cleanliness.
- Document the hosted-demo run command, environment variables, persistence
  caveats, smoke procedure, and exploratory/raw-CFD status without requiring a
  public deployment in this slice.
- Keep local CFD route wording honest: unavailable, failed, and raw
  unvalidated states must remain visible and must not imply real solver
  execution or calibrated results.
- Require the successor workflow to route first-pass review `needs_revision`
  verdicts through an explicit bounded revision/remediation path before the
  ledger and implementation jobs run.

## Non-Goals

- Deploying or operating a public hosted demo URL.
- Vendor-specific deployment automation.
- Replacing Trame with a custom JavaScript frontend.
- Full mobile editing parity.
- Full comparison dashboards, sweep exploration, Pareto filtering, or
  multi-candidate report UI parity beyond the already delivered compact views.
- Real CFD solver adapters, hosted workers, Dockerized solver execution,
  validated CFD output, calibrated resistance claims, or final design-fitness
  claims.
- Accounts, authentication, quotas, billing, collaborative editing, or
  persistent design libraries.

## Proposal

### 1. Acceptance Profiles

Keep the default `headless-web` path available for normal development and lean
CI environments. It may continue to cover Trame app construction, URL/state
helpers, route helpers, evaluator parity, offscreen render smoke, and
non-browser logic.

Add or document a separate `browser-acceptance` profile. In that profile,
missing Playwright/Chromium or equivalent real-browser tooling is a failure,
not a skip. Optional self-skipping browser smoke may remain outside this
profile, but it cannot be cited as browser acceptance.

### 2. Browser Checks

Browser acceptance runs against `kayakgen serve` on a local port. It should wait
on stable browser-visible state rather than fixed sleeps. The required checks
are:

- initial page load shows the hull/deck view, core parameter controls, metrics,
  and analysis content;
- the 3D render is nonblank after initial load;
- changing at least one representative hull parameter updates
  browser-visible metrics without blanking the 3D view;
- share URL behavior reconstructs the same hull parameters on reload;
- STL export returns downloadable STL bytes through the browser-facing path or
  route;
- browser console and network collection fails on uncaught exceptions, mixed
  content, failed static assets, failed API calls, and unexpected failed
  requests.

Any temporary allowlist must be exact: URL pattern, status, rationale, and
removal condition. A broad permanent allowlist for Trame, VTK, or `/paraview/`
errors is not acceptable.

### 3. Hosted-Demo Documentation

This slice accepts hosted-demo documentation, not live hosted operation. The
docs should state the run command:

```bash
kayakgen serve --host 0.0.0.0 --port 8080
```

They should also name supported environment variables, persistence caveats,
redeploy steps from a clean checkout or Docker image, the manual smoke checks,
and the wording that the demo is exploratory and does not provide validated
CFD or calibrated performance claims.

### 4. Plot and CFD Boundaries

The web UI may close this slice with the already delivered compact analysis and
comparison-report inspection surfaces, provided the boundary is explicit in
documentation. Full dashboard parity remains future work.

The CFD browser surface remains a local job-record inspection surface. It may
show profiles, readiness failures, queued/unavailable/failed/succeeded fixture
states, logs, and raw artifacts, but every route and UI path must preserve
raw/unvalidated status until later RFCs accept real solver and claim-gate
evidence.

### 5. Successor Workflow Shape

Any successor implementation workflow for this RFC should keep the three-lane
review pattern for traceability, browser behavior, and ops/tests. It must also
declare a bounded revision cycle for first-pass review jobs, especially the
browser review, so `needs_revision` creates an explicit remediation/re-review
attempt instead of pausing at an unplanned human checkpoint. The normal final
review may still cycle back to implementation once.

## Acceptance Criteria

- `docs/WEB_VERIFICATION.md` documents the default headless web command and the
  required browser-acceptance command.
- The browser-acceptance command fails when required browser tooling is
  unavailable in an environment claiming browser acceptance.
- Browser acceptance starts `kayakgen serve`, opens the local app in a real
  browser, and verifies initial hull/deck render, controls, metrics, and
  analysis content.
- Browser acceptance mutates at least one representative control and verifies
  that browser-visible metrics change.
- The 3D view remains nonblank after initial load and after the representative
  mutation.
- Share URL state round-trips for the current hull parameters.
- STL export returns STL bytes through a browser-facing button path or route.
- Console/network checks fail on unexpected browser errors, failed assets,
  failed API calls, mixed-content warnings, or unexpected failed requests.
- Any temporary console/network allowlist is exact, documented, and tied to a
  removal condition.
- Hosted-demo documentation records the serve command, environment variables,
  persistence caveats, redeploy/smoke steps, and exploratory/raw-CFD wording.
- Web CFD routes and UI continue to expose structured unavailable/dependency or
  raw/unvalidated states and do not present unavailable solvers as runnable.
- The implementation workflow validates with a bounded revision route for
  first-pass browser-review `needs_revision` and a bounded final-review cycle.

## Risks

Browser acceptance can become flaky if it depends on timing instead of explicit
UI or route state. The implementation should prefer DOM state, response events,
or deterministic helper hooks over fixed sleeps.

Console/network allowlists can hide real failures. The RFC allows only exact
temporary entries with rationale and removal conditions.

The scope can expand back into all of RFC 0030. Hosted operation, full dashboard
parity, mobile editing parity, and real CFD execution remain deferred so this
slice can land independently.

## Implementation Path

1. Add or document the required browser-acceptance profile and keep the
   headless web profile separate.
2. Extend browser tests for initial render, nonblank 3D evidence, control
   mutation, metrics change, share URL round trip, STL export, and
   console/network collection.
3. Fix local web issues surfaced by those checks without changing domain
   semantics or making new CFD claims.
4. Add hosted-demo runbook/status material to the web verification docs.
5. Keep CFD route/panel wording raw and unvalidated.
6. Update the RFC index, changelog, and workflow artifacts to record what
   landed and what remains deferred.

## Domain Modeling

This is a boundary-clarification RFC for the web application layer. It does not
introduce a new domain aggregate; it defines acceptance gates around the
existing Trame UI, local route adapters, and documentation surfaces.
