# Findings Ledger - workflow 0043 web hosted browser acceptance revision

## Scope

This ledger deduplicates the traceability, browser, and ops reviews for
RFC 0032. The next implementation slice is local browser acceptance plus
hosted-demo documentation. It must not claim production hosting, real CFD
solver readiness, validated CFD output, calibrated resistance, or final
design fitness.

Primary review inputs:

- `striatum/0043-web-hosted-browser-acceptance-revision/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0043-web-hosted-browser-acceptance-revision/browser/REVIEW_BROWSER.md`
- `striatum/0043-web-hosted-browser-acceptance-revision/ops/REVIEW_OPS.md`
- `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md`

## Implementation-Required Findings

### F-1 - Browser acceptance is still optional/self-skipping

RFC 0032 requires a deliberate `browser-acceptance` profile where missing
Playwright/Chromium fails instead of skipping
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:68`,
`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:132`). Current
documentation still describes only optional browser smoke
(`docs/WEB_VERIFICATION.md:27`), and the current browser test self-skips with
`pytest.importorskip` and `pytest.skip`
(`tests/test_web_browser.py:50`, `tests/test_web_browser.py:78`). `pyproject.toml`
has the `browser` extra but no marker/profile split (`pyproject.toml:34`,
`pyproject.toml:51`).

Required slice: add a distinct browser-acceptance command/profile, document it
in `docs/WEB_VERIFICATION.md`, and make missing browser tooling a hard failure
with the setup command in the failure text. Keep the optional self-skipping
smoke path only for lean development; do not cite it as acceptance evidence.

### F-2 - Real-browser coverage must expand beyond the current smoke

RFC 0032 requires browser-visible initial render, controls, metrics, analysis
content, nonblank 3D before and after mutation, representative mutation with
metric change, share URL round trip, STL bytes, and console/network cleanliness
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:75`,
`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:136`). Current
Playwright coverage checks page text and one slider-driven metrics change only
(`tests/test_web_browser.py:88`, `tests/test_web_browser.py:97`). The URL
round trip, STL byte check, and nonblank render evidence are headless/unit-only
today (`tests/test_web.py:63`, `tests/test_web.py:142`, `tests/test_web.py:242`).

Required slice: extend `tests/test_web_browser.py` to assert value-bearing
analysis content from `analysis_lines_from_state`
(`kayakgen/ui/web/controllers.py:175`), browser-visible nonblank VTK evidence
before and after mutation, mutate -> metrics-change behavior, Share -> reload
for `?hull=...`, and STL bytes through either the button/download path or
`POST /api/stl` (`kayakgen/ui/web/controllers.py:1002`). The served share path
needs specific attention: `_share_url` writes `?hull=...`
(`kayakgen/ui/web/app.py:269`), while `kayakgen serve` currently constructs
`create_app(initial_hull=...)` without forwarding request query state
(`kayakgen/cli/main.py:338`).

### F-3 - Console/network cleanliness is not gated

RFC 0032 requires browser console and network collection to fail on uncaught
exceptions, page errors, failed assets, failed API calls, mixed content, and
unexpected failed requests (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:87`).
Any temporary allowlist must be exact and temporary
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:91`). Current
browser tests register no `console`, `pageerror`, or `requestfailed` handlers,
and `docs/WEB_VERIFICATION.md:97` still records the Trame `/paraview/` 405 as
an unresolved console-clean gap.

Required slice: collect console/page/network events during initial load and
the representative interaction. Fix the `/paraview/` 405 if practical; otherwise
document a narrow temporary allowlist in `docs/WEB_VERIFICATION.md` with URL
pattern, status, rationale, owner/removal condition, and no broad permanent
Trame/VTK exception.

### F-4 - Hosted-demo documentation is incomplete

RFC 0032 accepts hosted-demo documentation, not live public operation
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:95`). The docs must
record the serve command, environment variables, persistence caveats, redeploy
and smoke steps, and exploratory/raw-CFD wording
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:149`). Current
`docs/WEB_VERIFICATION.md` has local manual and Docker checks
(`docs/WEB_VERIFICATION.md:51`, `docs/WEB_VERIFICATION.md:67`) and says no
hosted public demo is deployed (`docs/WEB_VERIFICATION.md:116`), but it does
not yet provide a runbook.

Required slice: add a hosted-demo runbook section to `docs/WEB_VERIFICATION.md`
covering `kayakgen serve --host 0.0.0.0 --port 8080`, clean-checkout install,
Docker build/run, smoke checklist, stop/redeploy steps, and explicit
documentation-only/no-public-URL wording. Document `KAYAKGEN_WEB_CFD_JOBS_ROOT`
for server-local CFD artifacts (`kayakgen/ui/web/controllers.py:42`). Be precise
with env vars: `--host` and `--port` are CLI options (`kayakgen/cli/main.py:328`);
`TRAME_HOST` and `TRAME_PORT` are set in Docker (`Dockerfile:21`) but are not
supported runtime controls unless implementation changes.

### F-5 - Plot/dashboard parity boundary needs explicit documentation

RFC 0032 says the delivered compact analysis and comparison-report inspection
surfaces can close this slice if the boundary is explicit
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:111`). Current web
verification docs describe compact analysis/comparison views
(`docs/WEB_VERIFICATION.md:103`) but still leave plot/dashboard parity framed as
a generic deferral (`docs/WEB_VERIFICATION.md:113`). RFC 0008 and the RFC index
also still describe RFC 0008 as broadly partial
(`docs/rfcs/0008-web-frontend.md:253`, `docs/rfcs/README.md:60`).

Required slice: update the docs touched by implementation to say that compact
analysis with units and raw/uncalibrated warnings plus compact comparison
report inspection is the accepted RFC 0032 web-analysis boundary. Keep full
plot tabs, mobile editing parity, larger dashboards, sweep exploration,
Pareto filtering, and multi-candidate UI parity deferred.

### F-6 - CFD fixture/profile web coverage and wording need tightening

RFC 0032 keeps web CFD as a local job-record inspection surface and allows only
profiles, readiness failures, queued/unavailable/failed/succeeded fixture
states, logs, and raw artifacts with raw/unvalidated semantics
(`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:115`). The route
helpers already preserve `result_semantics: raw_unvalidated`
(`kayakgen/ui/web/controllers.py:645`) and browser status text keeps raw/local
warnings visible (`kayakgen/ui/web/controllers.py:554`). Ops review found that
the deterministic `fixture-local-command` profile exists, but `/api/cfd/*` tests
cover unavailable and failed paths only (`tests/test_web.py:338`,
`tests/test_web.py:484`), while fixture success is covered only in core CFD
tests. `docs/USER_GUIDE.md:269` also omits `fixture-local-command`, and the UI
labels the selector generically (`kayakgen/ui/web/app.py:486`,
`kayakgen/ui/web/app.py:520`).

Required slice: add deterministic web-route coverage for `fixture-local-command`
prepare/run/raw-result success, asserting raw warning fields throughout. Update
user-facing docs and browser copy so the fixture profile is clearly a checked-in
test adapter, not real CFD. Do not promote any output beyond raw/unvalidated.

### F-7 - Legacy generic `/api/jobs` stubs need explicit scoping if touched

The RFC 0032 CFD acceptance surface is the `/api/cfd/*` route set. The older
generic RFC 0008 `/api/jobs` stubs still return a minimal 501 payload
(`kayakgen/ui/web/controllers.py:944`, `kayakgen/ui/web/controllers.py:1025`).
They are adjacent enough to solver work that implementors should not let them
look like real CFD readiness.

Required slice: either leave the generic stubs untouched and document them as
outside RFC 0032 acceptance, or align their wording with the same structured
unavailable/raw boundary used by the CFD-specific route layer.

## Non-Blocking Preservation Notes

- Preserve the existing raw/unvalidated CFD contract: every route/UI path for
  `/api/cfd/*` must keep `result_semantics: raw_unvalidated` and the raw warning
  (`kayakgen/ui/web/controllers.py:645`). Do not add `validated`, `calibrated`,
  or `final_fitness` claim states in this slice.
- Preserve Docker/local serve wiring unless the implementation needs a narrow
  fix: the image installs `.[web]`, exposes 8080, and runs
  `kayakgen serve --host 0.0.0.0 --port 8080` (`Dockerfile:19`,
  `Dockerfile:23`, `Dockerfile:25`).
- Preserve the workflow-shape fix: workflow 0043 already declares bounded
  first-pass review revision routing and a bounded final-review cycle, satisfying
  RFC 0032's process requirement
  (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:121`).
- Preserve the PRD and user-guide caveats that current web and CFD support is
  local/plumbing-only, not a hosted worker or real solver system
  (`docs/PRD.md:41`, `docs/USER_GUIDE.md:330`).

## Explicit Deferrals

- No public hosted demo URL, production hosting claim, or vendor-specific
  deployment automation in this slice
  (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:47`).
- No replacement of Trame with a custom JavaScript frontend
  (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:49`).
- No full mobile editing parity, full comparison dashboards, sweep exploration,
  Pareto filtering, or multi-candidate report UI parity beyond the existing
  compact views (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:50`).
- No real CFD solver adapters, hosted workers, Dockerized solver execution,
  validated CFD output, calibrated resistance claims, or final design-fitness
  claims (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:53`).
- No accounts, authentication, quotas, billing, collaborative editing, or
  persistent design libraries (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:56`).
- No promotion of browser STL export or mesh packages to watertight,
  closed-volume, or `cfd_ready` artifacts; generated hull/deck STLs remain
  inspection/open-surface outputs (`docs/PRD.md:28`, `docs/USER_GUIDE.md:257`).

## Safe Implementation Slice

Implementors should carry out the following bounded slice next:

1. Add a required browser-acceptance profile and documented command while
   preserving the optional smoke path for non-acceptance environments.
2. Extend `tests/test_web_browser.py` for analysis content, in-browser nonblank
   3D evidence before/after mutation, Share reload, STL bytes, and console /
   page / network failure collection.
3. Fix only the local web issues exposed by those browser checks. If a
   console/network allowlist is unavoidable, make it exact and temporary.
4. Add `docs/WEB_VERIFICATION.md` hosted-demo runbook/status material with
   documentation-only, no-public-URL, no-production-hosting wording.
5. Clarify the accepted compact analysis/comparison boundary while keeping
   full dashboards and plot parity deferred.
6. Preserve and test `/api/cfd/*` raw/unvalidated unavailable/failed/fixture
   states, including deterministic fixture success, without claiming real solver
   execution or validated output.
7. Update the RFC index, changelog, and workflow-local implementation artifacts
   only as needed to record what landed and what remains deferred; leave the
   root `OPERATOR_REPORT.md` to the operator.
