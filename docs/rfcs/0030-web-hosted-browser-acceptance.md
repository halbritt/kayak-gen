# RFC 0030: Web Hosted and Browser Acceptance

Status: deferred indefinitely per D023 (closed by RFC 0064)
Date: 2026-05-13
Context: closes deferred RFC 0008 hosted-demo, browser acceptance,
console-clean Lighthouse, plot/dashboard parity, and web CFD route boundaries.

## Problem

RFC 0008 established a Trame web frontend and local `kayakgen serve` path.
Headless construction, visual smoke tests, optional Playwright smoke, compact
analysis rows, and route scaffolding exist. The acceptance bar is still partial:

- There is no accepted hosted demo target.
- Browser acceptance is optional and can self-skip, so regressions can pass
  unnoticed in environments that are meant to gate browser behavior.
- Lighthouse Best Practices reached the threshold once, but console-clean
  acceptance still failed on a Trame `/paraview/` 405 network log.
- Plot/dashboard parity remains bounded and incomplete.
- Web CFD job route dependencies need explicit readiness and validation gates
  before the UI can expose them as working solver features.

## Goals

- Define a hosted-demo acceptance target and operational contract.
- Make browser acceptance explicit, reproducible, and separately skippable only
  for non-browser test profiles.
- Require console-clean and Lighthouse gates for the hosted/local browser path.
- Define the plot/dashboard parity boundary for RFC 0008 closure.
- Define how web CFD routes depend on mesh-package, solver-profile, job-state,
  and claim-gate readiness.

## Non-Goals

- Replacing Trame with a custom JavaScript frontend.
- Full mobile editing parity. Mobile view-only behavior remains acceptable for
  this closure.
- Real CFD solver execution or calibrated result claims.
- Accounts, authentication, collaborative editing, or persistent design
  libraries.

## Proposal

### 1. Hosted demo contract

A hosted demo is accepted when the repo documents a reproducible deployment for
the same Docker image or command surface used locally:

- `kayakgen serve --host 0.0.0.0 --port 8080` is the runtime entry point.
- The deployment exposes a URL that loads the web UI without local Python.
- The demo can be redeployed from a clean checkout and documented environment
  variables.
- Persistence is limited to URL state or an explicitly bounded hull-id store.
- The hosted demo is labeled as exploratory and must not imply validated CFD.

The accepted artifact may be a small VPS, Fly.io, Railway, Render, or equivalent
host. The contract is the reproducible runbook, not a specific vendor.

### 2. Browser acceptance gates

Browser tests are divided into two profiles:

- `headless-web`: available in normal CI and allowed to test app construction,
  route helpers, offscreen rendering, and non-browser logic.
- `browser-acceptance`: requires Playwright/Chromium or equivalent and must not
  self-skip in the acceptance environment.

The browser-acceptance profile must verify:

- Initial page renders a hull, controls, metrics, and analysis content.
- Changing representative controls updates metrics and does not blank the 3D
  view.
- Share URL round-trips the hull state.
- STL export route or button path returns a downloadable artifact when the
  feature is enabled.
- Browser console has no errors or unexpected failed network requests after
  initial load and one interaction.

### 3. Lighthouse and console-clean gates

RFC 0008's Lighthouse Best Practices threshold remains `>= 90`, but this RFC
adds a separate console-clean gate:

- Known Trame framework requests may be allowlisted only with exact URL pattern,
  status, rationale, and expiration/review note.
- A generic `/paraview/` 405 log is not acceptable as an unbounded permanent
  allowlist.
- Mixed-content warnings, uncaught exceptions, failed static assets, and failed
  API calls are acceptance failures.

The gate can run locally against `kayakgen serve` and against the hosted demo.

### 4. Plot and dashboard parity boundary

RFC 0008 closure requires parity for the primary analysis surfaces, not every
future dashboard idea:

- Web exposes the same core hull controls as desktop for implemented fields.
- Web shows hydrostatics and raw analytical resistance rows with units and
  exploratory/uncalibrated warnings.
- Web shows the 3D hull and at least the desktop-equivalent inspection plots
  required for current hull review, or documents a deliberate replacement with
  equivalent data.
- Larger comparison dashboards, sweep exploration, Pareto filtering, and
  multi-candidate report UIs remain future work unless specifically accepted by
  a later RFC.

Parity tests should compare shared data models and labels where possible,
rather than pixel-matching desktop matplotlib output.

### 5. Web CFD route dependencies

Web CFD routes remain disabled or explicitly unavailable until all dependencies
are met:

- Mesh package exists and declares a profile.
- Solver profile exists and declares readiness requirements.
- Mesh readiness satisfies solver-profile requirements.
- Job state records are serializable and inspectable through CLI and web.
- Claim gates distinguish raw, validation, calibration, and final-fitness
  states.

Routes may return 501 or structured unavailable records. They must not present
an unavailable solver as runnable, and the web UI must display dependency
failures rather than hiding them behind a generic error.

## Acceptance Criteria

- A hosted-demo runbook exists and names the accepted deployment command,
  environment variables, persistence caveats, and exploratory status wording.
- Browser-acceptance tests can be run deliberately and fail if Chromium or an
  equivalent browser is missing in the acceptance profile.
- The browser console-clean gate fails on uncaught errors, failed assets,
  unexpected failed network requests, or mixed-content warnings.
- Lighthouse Best Practices remains `>= 90` and is checked with the
  console-clean gate.
- The known Trame `/paraview/` 405 issue is fixed or narrowly documented with a
  temporary allowlist and owner.
- Web controls, metrics, share URL, and STL export behavior are tested in a real
  browser profile.
- Plot/dashboard parity boundaries are documented so RFC 0008 can close without
  implying full comparison-dashboard delivery.
- Web CFD routes expose structured unavailable/dependency states until solver
  readiness and claim gates allow more.

## Open Questions

- Should hosted-demo acceptance require a public URL in CI, or is a documented
  reproducible deploy plus manual smoke sufficient? Lean: require the runbook
  and a recorded smoke; avoid hard-coding a vendor URL into tests.
- Should mobile be tested in Lighthouse only or with a Playwright viewport
  smoke? Lean: add one mobile view-only smoke after desktop browser acceptance
  is stable.

## Implementation Path

1. Add hosted-demo runbook material and demo status wording.
2. Split browser tests into headless and required browser-acceptance profiles.
3. Add console-clean and Lighthouse gate scripts or documented commands.
4. Close or narrowly allowlist the Trame `/paraview/` 405 noise.
5. Add browser tests for control mutation, share URL, metrics, 3D nonblank, and
   STL export.
6. Wire web CFD routes to structured dependency/unavailable responses.
