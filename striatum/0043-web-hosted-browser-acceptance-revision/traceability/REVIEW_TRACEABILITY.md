# Traceability review - web hosted browser acceptance revision (workflow 0043)

## Scope

Mapping RFC 0032 acceptance criteria back to RFC 0030 acceptance direction, RFC
0008 partial web status, RFC 0018 local web CFD route status, the 0041 blocker
carry-forward, the `review_revision_anchor` handoff, current implementation in
`kayakgen/ui/web/` and `kayakgen/cli/`, the current `tests/test_web.py` /
`tests/test_web_browser.py` suite, `Dockerfile`, and the documentation surfaces
in `docs/USER_GUIDE.md` and `docs/WEB_VERIFICATION.md`. This review confirms
the successor workflow has a traceable path from the 0041 browser blocker to
actionable implementation/review work, and does not overstate hosted or CFD
capabilities that have not landed.

Sources used (all read in this job):

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/WEB_VERIFICATION.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0018-web-cfd-job-routes.md`
- `docs/rfcs/0030-web-hosted-browser-acceptance.md`
- `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md`
- `docs/rfcs/README.md`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/SOURCES.md`
- `docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json`
- `docs/workflows/0041-web-hosted-browser-acceptance/SOURCES.md`
- `docs/workflows/0041-web-hosted-browser-acceptance/workflow.json`
- `docs/workflows/0029-web-cfd-job-routes/workflow.json`
- `docs/workflows/0037-first-real-cfd-fixture-adapter/workflow.json`
- `striatum/0043-web-hosted-browser-acceptance-revision/review_anchor/REVIEW_SCOPE.md`
- `striatum/0041-web-hosted-browser-acceptance/traceability/REVIEW_TRACEABILITY.md` (from `striatum/0041-web-hosted-browser-acceptance` branch via `git show`)
- `striatum/0041-web-hosted-browser-acceptance/browser/REVIEW_BROWSER.md` (same branch)
- `striatum/0041-web-hosted-browser-acceptance/ops/REVIEW_OPS.md` (same branch)
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/state.py`
- `kayakgen/cli/main.py`
- `tests/test_web.py`
- `tests/test_web_browser.py`
- `Dockerfile`
- `pyproject.toml`

## Sub-agent and parallel help used

None. This review was performed directly from the main context using Read,
Grep, and Bash (read-only). No sub-agents were spawned. No Striatum mutation
commands were run; the only intended write is this artifact.

## Successor workflow shape vs. 0041 blocker

RFC 0032 §"Successor Workflow Shape" requires a bounded revision route for
first-pass review `needs_revision` verdicts, especially for the browser review
that returned `needs_revision` in workflow 0041 without an explicit remediation
path. Workflow 0043 declares that route:

- `docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json:12-15` adds
  `review_revision_policy.root_review_needs_revision = declared_cycle`.
- `workflow.json:153-158` declares per-lane cycles for `review_traceability`,
  `review_browser`, and `review_ops` back to `review_revision_anchor` with
  `max_iterations: 1`. The ops cycle sets `allow_same_lane: true` to permit a
  same-lane re-anchor when the codex lane originated the artifact.
- `workflow.json:155-158` keeps the existing `final_review → implement_findings`
  cycle with `max_iterations: 1`, matching the "normal final review may still
  cycle back to implementation once" sentence in RFC 0032 §5.
- `review_revision_anchor` is a `draft` job (`workflow.json:55-66`) that runs
  before the three review lanes (`workflow.json:144-146`), so the bounded
  remediation anchor exists before any first-pass review can fire and re-fires
  when a review verdict is `needs_revision`.
- The anchor artifact at
  `striatum/0043-web-hosted-browser-acceptance-revision/review_anchor/REVIEW_SCOPE.md:69-117`
  records the conservative RFC 0032 scope, in/out-of-scope lists,
  `review_revision_anchor` carry-forward of every 0041 blocker, and per-lane
  first-pass review anchors. That is the actionable bridge between the 0041
  `needs_revision` blocker and the 0043 first-pass reviews.

This satisfies the 0041 blocker the most directly: in 0041 the browser
`needs_revision` had no declared remediation path
(`docs/workflows/0041-web-hosted-browser-acceptance/workflow.json:122`'s
single `cycles` entry only covers `final_review → implement_findings`); in 0043
the policy and per-lane cycles plus the anchor doc make the remediation path
explicit.

## RFC 0032 acceptance-criterion map

| RFC 0032 criterion (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md`) | RFC 0030 / RFC 0008 / RFC 0018 origin | Current implementation surface | Test surface | Status going into the ledger |
|---|---|---|---|---|
| §"Acceptance Criteria" item 1 — `docs/WEB_VERIFICATION.md` documents the default headless web command **and** the required browser-acceptance command (`0032:132-134`) | Narrowing of RFC 0030 §2 (`0030:59-71`); successor of RFC 0008 §"Optional Playwright smoke" partial (`0008:14-19`) | `docs/WEB_VERIFICATION.md:7-26` documents the default headless command; the "Optional Browser Smoke" section (`docs/WEB_VERIFICATION.md:28-46`) frames the browser test as optional only | `tests/test_web_browser.py` is the only browser test; it is documented as optional in its own module docstring (`tests/test_web_browser.py:1-9`) | **Gap (Finding T-1).** Headless command is present; required `browser-acceptance` command is not yet documented. |
| §"Acceptance Criteria" item 2 — the browser-acceptance command **fails** when required browser tooling is unavailable in an environment claiming browser acceptance (`0032:135-137`) | Narrowing of RFC 0030 §2 "must not self-skip in the acceptance environment" (`0030:64-66`) | None. `kayakgen/cli/main.py:323-340` `serve` is correct; pytest configuration in `pyproject.toml` has no marker split | `tests/test_web_browser.py:51-57` uses `pytest.importorskip("playwright.sync_api")` and `tests/test_web_browser.py:79-85` uses `pytest.skip(...)` when `playwright.Error` is raised by `pw.chromium.launch` | **Gap (Finding T-2).** Browser tooling absence still produces a green skip in the acceptance environment. |
| §"Acceptance Criteria" item 3 — browser acceptance starts `kayakgen serve`, opens the local app in a real browser, and verifies **initial** hull/deck render, controls, metrics, and analysis content (`0032:138-140`) | Narrowing of RFC 0030 §"Acceptance Criteria" "Web controls, metrics, share URL, and STL export behavior are tested in a real browser profile" (`0030:139-141`) | `kayakgen/ui/web/app.py` renders the hull/deck VtkRemoteView, controls, metrics, and Analysis/Comparison/CFD tabs | `tests/test_web_browser.py:88-95` waits for `kayakgen`, `Length (m)`, `Metrics`, `Displacement`, `Analysis`, `Comparison`, and `Resistance curve` text after navigation | **Partial — substantially met (Finding T-3).** Initial render check exists. Add browser-visible analysis-row assertion to match `analysis_lines_from_state` (`kayakgen/ui/web/controllers.py:281-340`) output rather than text labels alone. |
| §"Acceptance Criteria" item 4 — mutates at least one representative control and verifies browser-visible metrics change (`0032:141-142`) | Narrowing of RFC 0030 §"Acceptance Criteria" (`0030:139-141`) | Slider bindings in `kayakgen/ui/web/app.py:165-260`, mutation handlers in `kayakgen/ui/web/controllers.py` | `tests/test_web_browser.py:97-106` focuses a slider, presses `ArrowRight`, and waits for the metrics `pre` text to change | **Met.** |
| §"Acceptance Criteria" item 5 — the 3D view remains nonblank after initial load **and** after the representative mutation (`0032:143-144`) | Narrowing of RFC 0030 §"Acceptance Criteria" "Changing representative controls updates metrics and does not blank the 3D view" (`0030:69-71`) | `VtkRemoteView`/`VtkLocalView` wiring in `kayakgen/ui/web/app.py`; offscreen render helpers in `kayakgen/ui/web/app.py` exercised by headless tests | Only offscreen VTK nonblank assertion in `tests/test_web.py:241-261`; no browser-visible canvas-size or image-buffer check | **Gap (Finding T-4a).** Browser-side nonblank 3D evidence is missing both at initial load and after mutation. |
| §"Acceptance Criteria" item 6 — share URL state round-trips for the current hull parameters (`0032:144-145`) | Narrowing of RFC 0008 §4 URL state contract (`0008:155-170`) and RFC 0030 §"Acceptance Criteria" share URL (`0030:139-141`) | `kayakgen/ui/web/app.py:269-270` `_share_url`, `kayakgen/ui/web/app.py:373-379` `load_from_query`, `kayakgen/ui/web/app.py:563-566` `create_app(initial_query=...)`, `kayakgen/ui/web/state.py:51-68` `encode_hull_query`/`decode_hull_query` | Only headless coverage in `tests/test_web.py:62-68` and `tests/test_web.py:283-288` | **Gap (Finding T-4b).** Note (carried from 0041): `kayakgen/cli/main.py:338-340` passes `initial_hull=` only and never forwards a query string; the browser test must drive Share→reload through the real served URL, not the headless helper. |
| §"Acceptance Criteria" item 7 — STL export returns STL bytes through a browser-facing button path or route (`0032:145-146`) | Narrowing of RFC 0030 §"Acceptance Criteria" (`0030:139-141`) | `kayakgen/ui/web/app.py:271-276` triggers `download_stl`; `kayakgen/ui/web/controllers.py:272-280` `stl_bytes_for_part`; REST handler at `kayakgen/ui/web/controllers.py:1007` | Only headless STL byte counts in `tests/test_web.py:141-149` | **Gap (Finding T-4c).** STL is not yet exercised through a browser download or `/api/stl` request in `tests/test_web_browser.py`. |
| §"Acceptance Criteria" item 8 — console/network checks fail on unexpected browser errors, failed assets, failed API calls, mixed-content warnings, or unexpected failed requests (`0032:146-148`) | Narrowing of RFC 0030 §3 "Lighthouse and console-clean gates" (`0030:79-92`) | None. `kayakgen/ui/web/app.py:174-180` mounts REST routes on `on_server_bind`; the Trame `/paraview/` 405 surface in `docs/WEB_VERIFICATION.md:97-101` is still open | `tests/test_web_browser.py` registers no `page.on("console", ...)`, `page.on("pageerror", ...)`, or `page.on("requestfailed", ...)` handler | **Gap (Finding T-5).** No console-clean gate exists. Lighthouse Best Practices 92 score is recorded (`docs/WEB_VERIFICATION.md:97-101`) but is explicitly separate from console-clean acceptance per RFC 0032 §3. |
| §"Acceptance Criteria" item 9 — any temporary console/network allowlist is exact, documented, and tied to a removal condition (`0032:148-149`) | Narrowing of RFC 0030 §3 (`0030:79-92`) | `docs/WEB_VERIFICATION.md:97-101` notes the `/paraview/` 405 as an open issue, not a narrow allowlist with URL pattern, status, rationale, and expiration | None | **Gap (Finding T-5).** Same as item 8; the implementation slice must either fix the 405 or record a bounded allowlist. A broad permanent allowlist for `/paraview/` is explicitly prohibited (`0032:91-94`). |
| §"Acceptance Criteria" item 10 — hosted-demo documentation records serve command, env vars, persistence caveats, redeploy/smoke steps, exploratory/raw-CFD wording (`0032:150-151`) | Narrowing of RFC 0030 §1 (`0030:43-58`) | `docs/USER_GUIDE.md:322-340` documents `kayakgen serve` and `KAYAKGEN_WEB_CFD_JOBS_ROOT`; `Dockerfile:21-25` sets `TRAME_HOST=0.0.0.0`, `TRAME_PORT=8080`, and runs `kayakgen serve --host 0.0.0.0 --port 8080`; `docs/WEB_VERIFICATION.md:67-81` documents Docker build/run | `docs/WEB_VERIFICATION.md:116-120` says "No hosted public demo is deployed" — there is no runbook section that names env vars, persistence caveats (ephemeral hull-id store, local CFD jobs root), or exploratory/raw-CFD wording in one place | **Gap (Finding T-6).** RFC 0032 §3 accepts documentation, not live deployment, but requires the runbook content in one place. |
| §"Acceptance Criteria" item 11 — web CFD routes and UI continue to expose structured unavailable/dependency or raw/unvalidated states and do not present unavailable solvers as runnable (`0032:151-153`) | RFC 0018 §"Acceptance Criteria" and RFC 0030 §5 (`0018:78-89`, `0030:113-126`) | `kayakgen/ui/web/controllers.py:556`, `:592`, `:616`, `:631` emit `CFD_RAW_RESULTS_WARNING`; `:647-648` adds `result_semantics: raw_unvalidated` and the warning to every CFD payload; `kayakgen/ui/web/app.py:312-370` renders the CFD panel; `docs/USER_GUIDE.md:316-340` and `docs/USER_GUIDE.md:340-353` describe the raw/unvalidated route surface | `tests/test_web.py:306-590` covers route registration, `mesh_readiness_rejected`, `unknown_solver_profile`, `solver_profile_mismatch`, `solver_unavailable`, `mock-failing-local-command` failure, path-traversal rejection, and malformed raw-result handling (per 0041 traceability mapping) | **Met. (Finding T-7 — preservation only.)** Implementation slice must not regress this surface or expand the claim-gate vocabulary beyond `raw_unvalidated`. |
| §"Acceptance Criteria" item 12 — the implementation workflow validates with a bounded revision route for first-pass browser-review `needs_revision` and a bounded final-review cycle (`0032:153-155`) | New requirement carried from the 0041 blocker (`docs/workflows/0041-web-hosted-browser-acceptance/workflow.json:122`, `striatum/0041-web-hosted-browser-acceptance/browser/REVIEW_BROWSER.md`) | `workflow.json:12-15` `review_revision_policy.declared_cycle`; `workflow.json:153-158` per-lane revision cycles (`max_iterations: 1`); `workflow.json:155-158` `final_review → implement_findings` cycle; `review_revision_anchor` job ahead of all three reviews; `REVIEW_SCOPE.md:119-200` carry-forward of 0041 blockers | n/a (workflow shape) | **Met.** |

## Findings

### T-1 — `docs/WEB_VERIFICATION.md` does not yet document a required browser-acceptance command

RFC 0032 §"Acceptance Criteria" item 1 requires `docs/WEB_VERIFICATION.md` to
document both the default headless web command **and** the required
`browser-acceptance` command. The default headless command is documented at
`docs/WEB_VERIFICATION.md:7-26`. The "Optional Browser Smoke" section at
`docs/WEB_VERIFICATION.md:28-46` still frames the browser test as optional and
documents the workflow 0020 self-skipping invocation.

Severity: blocker for closure (but inside the conservative RFC 0032 slice).

Required correction: add a "Required browser acceptance" section to
`docs/WEB_VERIFICATION.md` (next to the existing "Optional Browser Smoke" or
replacing it for the acceptance profile). It must name the exact invocation —
e.g. `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest -m
browser_acceptance` or `pytest --browser-acceptance` — and state that missing
Playwright or Chromium is a failure, not a skip. The existing optional smoke
path may remain documented for normal development with that distinction
explicit.

### T-2 — `tests/test_web_browser.py` self-skips on missing Playwright/Chromium, so it cannot be cited as the browser-acceptance profile

RFC 0032 §1 / §"Acceptance Criteria" item 2 requires the browser-acceptance
profile to fail when Playwright/Chromium or equivalent tooling is missing.
Today the only browser test uses `pytest.importorskip("playwright.sync_api")`
at `tests/test_web_browser.py:51-57` and `pytest.skip(...)` at
`tests/test_web_browser.py:79-85` when `pw.chromium.launch(...)` raises
`playwright.Error`. Both paths produce a green skip rather than a failure.

Severity: blocker. This is the same 0041 carry-forward blocker (see
`striatum/0041-web-hosted-browser-acceptance/browser/REVIEW_BROWSER.md`,
`striatum/0041-web-hosted-browser-acceptance/traceability/REVIEW_TRACEABILITY.md` finding T-002,
and `striatum/0041-web-hosted-browser-acceptance/ops/REVIEW_OPS.md` finding O2).

Required correction: split the browser test into two profiles. Keep the
self-skipping smoke under a `headless-web`-compatible marker, and add a
`browser-acceptance` marker (or env-var/pytest-flag gate) that promotes both
"Playwright not installed" and "Chromium launch failed" into hard pytest
failures with the install command (`pip install -e '.[web,browser]'` and
`python -m playwright install chromium`) in the failure message.
`pyproject.toml:34-35` already names the `browser` extra with
`playwright>=1.45`, so the install pathway is already accepted; the missing
piece is the failure-mode wiring and the runner invocation documented in T-1.

### T-3 — Initial render check exists; add browser-visible analysis-row evidence

`tests/test_web_browser.py:88-95` already waits for `kayakgen`, `Length (m)`,
`Metrics`, `Displacement`, `Analysis`, `Comparison`, and `Resistance curve`
text. RFC 0032 §"Acceptance Criteria" item 3 also requires "analysis content".
The existing `analysis_lines_from_state` and `comparison_view_model_from_json`
in `kayakgen/ui/web/controllers.py:281-340` produce labelled hydrostatics and
raw-resistance rows that the browser-acceptance lane should assert against,
rather than relying on tab text alone.

Severity: minor.

Required correction: extend the browser-acceptance test (T-2) to wait for a
specific hydrostatics row label (e.g. a value-bearing row from
`analysis_lines_from_state` such as the displacement or `GM0` row) and a
raw-resistance row carrying the `raw / uncalibrated` wording, so the
acceptance evidence covers actual analysis content and not only tab headings.

### T-4 — Browser-side coverage missing for share URL, STL export, and nonblank 3D

RFC 0032 §"Acceptance Criteria" items 5, 6, and 7 require browser-side
evidence. Today only headless equivalents exist:

- 3D nonblank: only `tests/test_web.py:241-261` (offscreen VTK render);
  `tests/test_web_browser.py` makes no canvas-dimension or image-buffer
  assertion at initial load or after the slider mutation.
- Share URL round-trip: only `tests/test_web.py:62-68` and
  `tests/test_web.py:283-288` (headless `encode_hull_query`/`decode_hull_query`
  and `KayakgenApp.load_from_query`). `tests/test_web_browser.py` never clicks
  the Share button at `kayakgen/ui/web/app.py:392` and never re-navigates to
  the produced `?hull=...` URL.
- STL export: only `tests/test_web.py:141-149` (byte count). The browser path
  through `kayakgen/ui/web/app.py:271-276` `_export_stl` and the REST handler
  at `kayakgen/ui/web/controllers.py:1007` is not exercised.

Severity: blocker (three sub-findings, T-4a/T-4b/T-4c).

Required correction in the browser-acceptance test added in T-2:

- T-4a: after initial `page.goto`, assert the VtkRemoteView canvas/image
  element exists with nonzero `boundingBox()` width and height; after the
  slider mutation, re-assert the same so the "does not blank the 3D view"
  requirement (RFC 0032 §"Acceptance Criteria" item 5, RFC 0030 §"Acceptance
  Criteria" `0030:69-71`) has in-browser evidence.
- T-4b: click the Share button (`kayakgen/ui/web/app.py:391`), read the
  populated `share_url` field (bound to `kayakgen/ui/web/app.py:412`'s
  `v-model="share_url"`), then `page.goto(url + share_url)` and assert that
  hydrostatics and the served hull hash match the pre-share state.
  Implementation context (carried from `REVIEW_SCOPE.md:140-146`): the CLI
  `serve` at `kayakgen/cli/main.py:323-340` calls `create_app(initial_hull=...)`
  and **does not** forward a request query string into `create_app`, while the
  `KayakgenApp` itself supports `initial_query` and `load_from_query` at
  `kayakgen/ui/web/app.py:114-121`, `:373-379`, and `:563-566`. The browser
  acceptance must verify the actual served behavior, which means the
  share/reload path goes through `KayakgenApp.load_from_query` rather than the
  CLI constructor — that is the correct browser-visible contract.
- T-4c: intercept the `download_stl` trigger or call `POST /api/stl` over the
  same browser context, assert the response body starts with the binary STL
  header bytes, and assert a nonzero triangle count matching the parameters of
  `stl_bytes_for_part` for the current hull state.

### T-5 — No console-clean gate; `/paraview/` 405 is unresolved and not narrowly allowlisted

RFC 0032 §"Acceptance Criteria" items 8 and 9 require a console/network
collection that fails on uncaught exceptions, page errors, failed static
assets, failed API calls, mixed-content warnings, or unexpected failed
requests, and require any temporary allowlist to be exact and tied to a
removal condition. Today `tests/test_web_browser.py` registers none of
`page.on("console", ...)`, `page.on("pageerror", ...)`, or
`page.on("requestfailed", ...)`. `docs/WEB_VERIFICATION.md:97-101` still
records the Trame `/paraview/` 405 as an unresolved gap from workflow 0020 and
explicitly notes that "full console-clean browser acceptance remains partial".
The Lighthouse Best Practices score of 92 (workflow 0020) is recorded as
documentation, but RFC 0032 §3 / RFC 0030 §3 keep Lighthouse threshold and
console-clean acceptance as **separate** gates.

Severity: blocker. This is the most direct technical heir to the 0041 browser
blocker.

Required correction:

- In the browser-acceptance test (T-2), register `console`, `pageerror`, and
  `requestfailed` handlers on the page, collect their entries during initial
  load **and** the representative slider mutation (T-4), and fail when any
  non-allowlisted entry is collected.
- Resolve the `/paraview/` 405 either by adjusting where Trame's REST routes
  are mounted (`kayakgen/ui/web/app.py:174-180` registers via
  `on_server_bind`, which is plausibly where the 405 originates) or by
  recording an explicit narrow allowlist in `docs/WEB_VERIFICATION.md` with
  URL pattern, expected status, rationale, owner, and a workflow- or RFC-bound
  expiration. A broad permanent allowlist for Trame, VTK, or `/paraview/` is
  prohibited by RFC 0032 (`0032:91-94`) and is not accepted.
- Keep the existing Lighthouse `npx lighthouse ... --only-categories=best-practices`
  documentation (`docs/WEB_VERIFICATION.md:84-95`), and update the surrounding
  prose so the 92 score is treated as recorded evidence, not as closing
  console-clean acceptance.

### T-6 — Hosted-demo runbook content is not in `docs/WEB_VERIFICATION.md`

RFC 0032 §3 / §"Acceptance Criteria" item 10 accepts hosted-demo documentation
in this slice, not a live public deployment. Today the run command and the
relevant env vars are scattered:

- `kayakgen serve --host 0.0.0.0 --port 8080` is the runtime entry point and is
  invoked by `Dockerfile:25`.
- `TRAME_HOST=0.0.0.0` and `TRAME_PORT=8080` are set in `Dockerfile:21-22`.
- `KAYAKGEN_WEB_CFD_JOBS_ROOT` is documented in `docs/USER_GUIDE.md:337-340`
  for the local CFD jobs root.
- The ephemeral hull-id store is implicit in the absence of any persistent
  store hook in `kayakgen/ui/web/controllers.py` REST routes today.
- `docs/WEB_VERIFICATION.md:116-120` states "No hosted public demo is deployed
  from this repo today" and offers Docker as a "future deployment input", but
  no runbook section ties these pieces together with persistence caveats,
  redeploy steps from a clean checkout, manual smoke steps, or
  exploratory/raw-CFD wording.

Severity: blocker for closure (documentation only).

Required correction: add a "Hosted-demo runbook" section to
`docs/WEB_VERIFICATION.md` covering:

- the `kayakgen serve --host 0.0.0.0 --port 8080` command;
- the relevant environment variables (`TRAME_HOST`, `TRAME_PORT`,
  `KAYAKGEN_WEB_CFD_JOBS_ROOT`);
- persistence caveats (ephemeral in-memory hull-id store today; local CFD jobs
  root persisted under the configured directory; no auth, no quotas);
- clean-checkout redeploy steps for both the local server and the Docker image
  (`docker build -t kayakgen-web .` then `docker run --rm -p 8080:8080 -v ...`);
- a manual smoke-check checklist (hull/deck visible, sliders update metrics,
  Share/Export STL functional, CFD panel visible);
- exploratory-status wording stating the demo offers no validated CFD, no
  calibrated resistance, no real solver execution, and no final design
  fitness.

Do not pin a vendor URL into tests. RFC 0032 §"Non-Goals" excludes operating a
public hosted demo (`0032:46-49`) and any vendor-specific deploy automation
(`0032:47-49`).

### T-7 — Preserve raw/unvalidated CFD wording (no regression)

`kayakgen/ui/web/controllers.py:556`, `:592`, `:616`, `:631`, and `:647-648`
emit `CFD_RAW_RESULTS_WARNING` and `result_semantics: raw_unvalidated` on
every CFD payload. `docs/USER_GUIDE.md:316-353` documents this contract
end-to-end. `tests/test_web.py:306-590` (per 0041 traceability) covers
mesh-readiness rejection, unknown profile, solver mismatch, solver-unavailable,
mock-failing-local-command, path-traversal rejection, and malformed
raw-result handling. This satisfies RFC 0032 §"Acceptance Criteria" item 11
and RFC 0018's local-web-dispatch slice today.

Severity: non-blocking preservation.

Required correction: the implementation slice must not regress this surface
or introduce a `validated`/`calibrated`/`final_fitness` claim state. If the
legacy generic `/api/jobs` 501 stub (noted in 0041 ops review O5) is touched
at all, scope it explicitly outside RFC 0032 acceptance. RFC 0018 / RFC 0030
§5's calibration/claim-gate progression remains the responsibility of future
RFCs (the project's claim-gate work is upstream of these route layers).

## Anti-overstatement check

Several places in the RFC index and surrounding docs read as residual gaps
that RFC 0032 §"Acceptance Criteria" item 7 / RFC 0030 §4 actually closes if
worded correctly:

- `docs/rfcs/0008-web-frontend.md:14-19` and `:253-259` still read "Full
  desktop-equivalent plot parity, hosted demo deployment, auto-opening a
  browser by default, console-clean Lighthouse acceptance, mobile view-only
  mode, and larger comparison-dashboard work remain follow-up work" as a
  generic residual list.
- `docs/rfcs/README.md:61-63` and `:140-145` echo the same wording.
- `docs/WEB_VERIFICATION.md:104-131` reads similarly.

RFC 0032 §4 explicitly says the compact analysis/comparison surface is the
**accepted** boundary for this slice. Implementation should reflect that:
RFC 0008's residual list should be replaced with an explicit boundary
("compact analysis with units and uncalibrated warnings + compact comparison
report inspection is the accepted parity slice; full dashboard, sweep
exploration, Pareto filtering, sheer-plan/cross-section plot tabs, and mobile
editing parity remain deferred to later RFCs"). This is documentation work,
not a behavior change. It is not a blocker for the workflow's reviews to
proceed but is part of the implementation slice the ledger should accept (see
0041 carry-forward finding T-5 in
`striatum/0041-web-hosted-browser-acceptance/traceability/REVIEW_TRACEABILITY.md`).

This review does not find any text in `docs/PRD.md`, `docs/USER_GUIDE.md`, or
the RFCs that overclaims hosted operation, full browser parity, real solver
execution, calibrated resistance, validated CFD, or final design fitness. The
PRD's "Roadmap And Deferrals" (`docs/PRD.md:51-60`) and "Delivered Today"
sections (`docs/PRD.md:20-50`) keep the boundaries honest:

- "Full browser parity with the desktop application, including hosted-demo
  acceptance and any remaining real-browser/Lighthouse criteria" is on the
  Roadmap list (`docs/PRD.md:58-59`).
- "Real CFD solver adapters, normalized solver outputs, Docker/container
  execution, hosted workers, and browser job-management beyond the local
  filesystem route/panel slice" is on the Roadmap list (`docs/PRD.md:57-58`).
- The CFD section in "Delivered Today" (`docs/PRD.md:41-42`) states current
  CFD support is plumbing only and "does not run OpenFOAM, SU2, hosted
  workers, Dockerized solvers, or any real CFD adapter".

The successor workflow can land RFC 0032 without modifying these statements.

## Lane and parallel-write check

The 0043 workflow declares disjoint write scopes per lane
(`workflow.json:60-67,80-92,96-105,107-117,118-129,130-141`):
`review_revision_anchor` writes only inside `review_anchor/`; each of the
three first-pass reviews writes only inside its own review directory; the
ledger writes to `ledger/` and the workflow's operator report; the
implementer writes to product code, docs, and `implementation/`; the final
reviewer writes only inside `final/`. The reviewer lanes — including this
traceability lane — write `review_only_artifact` mode with `repo_write: false`,
matching the role boundary in the role brief.

The three first-pass reviews are declared parallel
(`workflow.json:74-105` `parallel_group: "reviews"`), with
`max_active_jobs: 3` and `require_disjoint_write_scopes: true`
(`workflow.json:53`). This is consistent with the 0041 workflow shape and
matches the bounded revision policy.

## Verdict

Verdict intent: accept_with_findings

RFC 0032's acceptance criteria map cleanly to RFC 0030 direction, RFC 0008
partial status, RFC 0018 local web CFD route status, the current web/CFD
implementation surface, and the existing test suite. The workflow shape
itself directly addresses the 0041 blocker: `review_revision_policy` plus
per-lane revision cycles plus the `review_revision_anchor` job and its
`REVIEW_SCOPE.md` artifact give the first-pass browser review (and the other
two first-pass reviews) an explicit bounded remediation path that 0041
lacked. The CFD route surface and raw/unvalidated wording are already met by
prior work and only need preservation. Findings T-1 through T-6 are the
remaining actionable implementation slice; T-7 records the preservation
constraint. None of the findings expand scope beyond RFC 0032 §"Non-Goals".

Proceed to the ledger lane.
