# Web Verification

This document records reproducible checks for the RFC 0008 Trame web frontend.
It distinguishes default headless verification, optional browser smoke, and the
required RFC 0032 browser-acceptance profile.

## Local Headless Checks

Run the web-focused tests:

```bash
.venv/bin/python -m pytest tests/test_web.py tests/test_cli.py -q
```

These tests cover URL/state round trips, metrics parity with the evaluator, STL
bytes, REST route registration, Trame app construction, reset/query loading,
analysis/comparison view-model helpers, and an offscreen VTK visual smoke test
that asserts a nonblank hull/deck render.

Run the full suite before merging web changes:

```bash
.venv/bin/python -m pytest -q
git diff --check
```

## Optional Browser Smoke

Install the optional browser tooling and the Chromium browser binary:

```bash
pip install -e ".[web,browser]"
python -m playwright install chromium
```

Run the browser smoke:

```bash
.venv/bin/python -m pytest tests/test_web_browser.py -q
```

This invocation is useful on developer machines that may not have browser
tooling installed. If Playwright or Chromium is unavailable, it skips with the
exact setup command and must not be cited as browser acceptance evidence.

Workflow 0020 result: after installing `kayakgen[web,browser]` and Chromium via
Playwright, `.venv/bin/python -m pytest tests/test_web_browser.py -q` passed.

## Required Browser Acceptance

Install the browser tooling first:

```bash
pip install -e ".[web,browser]"
python -m playwright install chromium
```

Run the acceptance profile:

```bash
.venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q
```

In this profile, missing Playwright or Chromium is a hard failure. The test
starts `kayakgen serve`, opens the local app in headless Chromium, verifies
browser-visible controls, metrics, compact analysis rows, nonblank 3D evidence
before and after a representative control mutation, Share URL reload, STL bytes
from the browser-facing API path, console/page/network cleanliness, hard
visual-regression screenshots, and browser-level accessibility checks.

### Visual Baselines

The RFC 0065 Slice 4 visual-regression gate stores committed PNG baselines
directly in this repo under `tests/visual_baselines/` for these browser
viewports:

- `1440x900.png`
- `1024x768.png`
- `960x720.png`

The canonical render environment for the current baselines is:

- OS: `Linux proximal 6.8.0-111-generic #111-Ubuntu SMP PREEMPT_DYNAMIC Sat Apr 11 23:16:02 UTC 2026 x86_64`
- Chromium: Playwright Chromium `147.0.7727.15`
  (`/home/halbritt/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome`)
- Capture date: `2026-06-02`

The nondeterministic 3D `VtkRemoteView` region is masked before capture. Its
liveness stays covered by the separate nonblank-3D checks before and after a
control mutation.

Regenerate baselines only on the canonical render environment:

```bash
.venv/bin/python -m pytest \
  tests/test_web_browser.py::test_web_workspace_visual_baseline \
  --update-visual-baselines -q
```

Review regenerated PNGs as an explained diff. A baseline update must describe
what visibly changed and why; unexplained binary churn is not acceptable.

The hard compare uses a per-channel tolerance of `8` and a per-viewport
mismatch-pixel ratio tolerance of `0.02` after masking the 3D viewport. The
channel tolerance absorbs antialiasing and font-hinting jitter; the ratio bound
keeps layout, chip-colour, claim-copy, and state-treatment changes visible.
When the ratio exceeds `0.02`, the acceptance profile fails and writes
`*.actual.png` plus amplified `*.diff.png` files in the pytest temporary
directory.

### Mandatory vs Optional Gates

| Check | Optional smoke | Acceptance profile |
| --- | --- | --- |
| Screenshot visual regression | SKIP if Playwright/Chromium absent; mismatches are advisory outside `--browser-acceptance` | HARD FAILURE if Playwright/Chromium is absent, a baseline is missing, or masked diff exceeds tolerance |
| Focus order / visible focus ring / hit targets | SKIP if Playwright/Chromium absent | HARD FAILURE; focus ring must use `--state-focus-ring`, controls must meet the 24 px minimum target |
| Contrast vs `CONTRAST_MANIFEST` | Mandatory pytest gate; no browser needed | Rechecked inside the browser-acceptance profile against the same manifest |
| Lighthouse Best Practices >= 90 | Optional, tool-dependent | Optional, tool-dependent; record the score, do not make it a pytest gate |

Browser acceptance has no broad Trame, VTK, or `/paraview/` allowlist. The
local server handles the exact historical `POST /paraview/` browser probe with a
local `/ws` connection JSON response so it does not appear as the earlier 405
console-clean failure. Any future temporary allowlist must document the exact
URL pattern, expected status, rationale, and removal condition.

## Local Manual Browser Check

Start the app:

```bash
kayakgen serve --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` in a browser. Verify that the hull and deck are
visible, sliders update the shape and metrics, Reset restores defaults, Share
fills the share URL field, and Export Hull STL / Export Deck STL trigger STL
downloads or that `POST /api/stl?part=hull` returns binary STL bytes.

The current CLI starts the server and does not auto-open a browser tab. That
scriptable default is intentional for Docker and CI friendliness.

## `data-testid` Hook Contract

The Trame layout sprinkles `data-testid` attributes
(`validity-badge`, `generative-submit`, `comparison-source-toggle`,
`mesh-no-package-chip`, `mesh-live-readiness-chip`,
`generative-variable-table`, `generative-objective-refusal`,
`generative-jobs-table`, etc.) so `tests/test_web_layout.py` can pin the
layout without scraping copy. These hooks are an **internal test
contract**: their names, presence, and placement may change without
notice as the workspace evolves. They are not a public API. Do not
build external browser automation or third-party integrations against
these selectors; use the documented REST surfaces under `/api/*`
instead, or open an issue if a stable handle for a particular control
would unblock a real workflow.

Tests in `tests/test_web_layout.py` and `tests/test_web_inline_help.py`
pin the presence and placement of these hooks; if any hook is renamed,
removed, or moved, those tests fail and the change is caught at
verification time.

## Docker Check

Build the image:

```bash
docker build -t kayakgen-web .
```

Run it locally:

```bash
docker run --rm -p 8080:8080 kayakgen-web
```

Open `http://127.0.0.1:8080/` and run the same manual browser check above.

## Lighthouse

Lighthouse remains an optional gate because it requires both Lighthouse and a
Chromium-family browser. It is not part of the mandatory pytest suite.

When those tools are available, start `kayakgen serve` and run:

```bash
npx lighthouse http://127.0.0.1:8080/ --only-categories=best-practices
```

Record the Lighthouse Best Practices score before claiming the RFC 0008
Lighthouse criterion. The target remains Best Practices >= 90.

RFC 0065 Slice 4 result: Lighthouse ran on `2026-06-02` with
`npx --yes lighthouse@latest`, `CHROME_PATH` pointed at Playwright Chromium
`147.0.7727.15`, and a local `kayakgen serve` instance. Best Practices scored
`1.0` (100).

Workflow 0020 result: Lighthouse ran with `npx --yes lighthouse@latest` and
Playwright's Chromium against a local server. Best Practices scored 92. The
console-errors audit still reported a Trame `/paraview/` 405 network log, so
that score remains historical threshold evidence rather than console-clean
acceptance evidence. Workflow 0043's browser-acceptance profile now checks
console/page/network failures directly against the local server.

## Web Analysis Boundary

The accepted RFC 0032 web-analysis boundary is the compact
analysis/comparison surface already present in the Trame app:

- hydrostatics rows with units;
- raw comparative resistance curve rows with warnings;
- comparison report inspection from existing `ComparisonReport` JSON;
- Pareto membership, candidate status, warnings, and parameter-only candidate
  reload into the editor.

This boundary is intentionally smaller than full desktop/dashboard parity. Full
plot tabs for sheer plan and cross-section views, mobile editing parity, larger
comparison dashboards, sweep exploration, Pareto filtering, multi-candidate UI
parity, hosted report persistence, and final design-fitness claims remain
deferred to later RFCs.

## Hosted Demo Runbook (Documentation Only)

No hosted public demo URL is deployed from this repo today, and this section is
not a production-hosting claim. It is the reproducible runbook for a future
documentation-only demo smoke on a local server, small VPS, or equivalent
operator-managed host.

Accepted runtime command:

```bash
kayakgen serve --host 0.0.0.0 --port 8080
```

Clean checkout run:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[web]"
KAYAKGEN_WEB_CFD_JOBS_ROOT=/srv/kayakgen/cfd-jobs \
  kayakgen serve --host 0.0.0.0 --port 8080
```

Docker run:

```bash
docker build -t kayakgen-web .
docker run --rm -p 8080:8080 \
  -e KAYAKGEN_WEB_CFD_JOBS_ROOT=/data/cfd-jobs \
  -v kayakgen-cfd-jobs:/data/cfd-jobs \
  kayakgen-web
```

`--host` and `--port` are the supported CLI runtime controls. The Dockerfile
sets `TRAME_HOST=0.0.0.0` and `TRAME_PORT=8080` as image defaults, but the
entry point still passes explicit CLI options. `KAYAKGEN_WEB_CFD_JOBS_ROOT` is
the supported environment variable for server-local CFD job artifacts.

Persistence caveats:

- `?hull=...` Share URLs are self-contained and survive process restarts.
- `/api/hulls` IDs are stored in memory and are lost when the server restarts.
- `/api/cfd/*` artifacts live only on the server filesystem under
  `KAYAKGEN_WEB_CFD_JOBS_ROOT` or the default `.kayakgen-web-cfd-jobs`; they
  persist only when that directory or Docker volume is preserved.
- There is no production database, account system, quota system, design
  library, hosted worker queue, or public-service SLA in this slice.

Manual hosted-demo smoke:

- open the served URL and verify the hull/deck view is visible;
- change a representative slider and confirm metrics and compact analysis rows
  update;
- use Share, reload the produced `?hull=...` URL, and confirm the design
  reappears;
- verify STL export through the UI or `POST /api/stl?part=hull`;
- open the CFD panel and confirm local/raw/unvalidated wording is visible.

To redeploy, stop the process or container, update the checkout or rebuild the
image, preserve or intentionally replace the CFD jobs directory/volume, and
restart with the same command. The demo remains exploratory: it does not run
OpenFOAM, SU2, hosted workers, or Dockerized solvers; it does not provide
validated CFD output, calibrated resistance, or final design-fitness decisions.

## Deferred Web Work

The following RFC 0008 and RFC 0013 items remain deferred:

- always-on browser automation in the default headless test suite;
- hosted public demo deployment and production hosting;
- plot tabs for sheer plan and cross-section views;
- full web comparison dashboards beyond the compact report-inspection slice;
- real CFD solver execution, hosted workers, validated CFD output, calibrated
  resistance, and final design-fitness claims.
