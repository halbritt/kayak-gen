---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-001
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14

# Browser Hosting Posture Research

## Decision Question

Should kayak-gen pursue a public hosted browser demo now, what should "hosted" mean for the current Trame web frontend, should any demo be static/local-only or server-backed, and what acceptance bar should apply?

## Local Project Constraints

The current product boundary allows a browser frontend, but it is not a completed hosted-demo or full-parity product. The PRD says the web frontend is Trame-based and currently covers parameter editing, rendered hull inspection, compact analysis, comparison report loading, local filesystem CFD job inspection, and optional browser smoke; full desktop parity, hosted-demo acceptance, hosted CFD workers, and real solver adapters remain roadmap items (`docs/PRD.md:44-49`). It also states current CFD support is local job/run/profile plumbing only and does not run OpenFOAM, SU2, hosted workers, Dockerized solvers, or any real CFD adapter (`docs/PRD.md:37-43`).

The roadmap's no-claims rules are the strongest local constraint. The web frontend is "local/browser-capable with runbook coverage," not a completed public hosted demo, full dashboard parity, hosted CFD system, or desktop parity rewrite (`docs/ROADMAP.md:57-59`). Browser hosting and parity is explicitly `partial` / `blocked`; the next work is to split public hosted demo operation, console-clean/Lighthouse upkeep, richer dashboard parity, desktop parity rewrite, and mobile/view-only acceptance into independent workflows (`docs/ROADMAP.md:67`, `docs/ROADMAP.md:105-122`). That means a public URL must not be bundled with solver, calibration, watertight readiness, or full-parity claims.

RFC 0008 originally wanted one Dockerfile to deploy the app remotely and share hulls by URL (`docs/rfcs/0008-web-frontend.md:49-64`), but it also deferred Pyodide / fully static deployment (`docs/rfcs/0008-web-frontend.md:66-73`). Its current status note says local browser acceptance, compact web analysis, direct local console/page/network checks, Share reload, STL bytes, and nonblank 3D checks are present, while hosted public demo operation, full desktop-equivalent plot parity, auto-open, mobile editing parity, and larger comparison-dashboard work remain follow-up (`docs/rfcs/0008-web-frontend.md:9-23`).

RFC 0030 defines the broader hosted/browser acceptance target: a hosted demo should expose a URL without local Python, use the same Docker image or command surface as local, be redeployable from a clean checkout and documented environment variables, limit persistence to URL state or a bounded hull-id store, and label itself exploratory without validated CFD (`docs/rfcs/0030-web-hosted-browser-acceptance.md:44-57`). RFC 0032 deliberately landed a narrower slice: local browser acceptance and hosted-demo documentation only, with public hosted operation, production hosting, full dashboard parity, real solver execution, validated CFD, calibrated resistance, and final design-fitness claims still deferred (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:9-16`, `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:54-66`).

The current runbook already specifies the local/server-backed shape. Required browser acceptance starts `kayakgen serve`, opens local Chromium, verifies controls, metrics, compact analysis, nonblank 3D before/after mutation, Share reload, STL bytes, and console/page/network cleanliness (`docs/WEB_VERIFICATION.md:58-75`). The hosted-demo runbook is documentation-only and says no hosted public demo URL is deployed today (`docs/WEB_VERIFICATION.md:147-152`). The accepted runtime command is `kayakgen serve --host 0.0.0.0 --port 8080`, with Docker and clean-checkout instructions, `KAYAKGEN_WEB_CFD_JOBS_ROOT` as the server-local CFD artifact variable, in-memory `/api/hulls` IDs, and no production database, account system, quota system, design library, hosted worker queue, or public-service SLA (`docs/WEB_VERIFICATION.md:154-194`). The demo smoke must keep local/raw/unvalidated CFD wording visible (`docs/WEB_VERIFICATION.md:196-210`).

## External Evidence

External sources were accessed on 2026-05-14.

| Source | Claim supported |
| --- | --- |
| [Trame guide](https://kitware.github.io/trame/guide/) | Trame is a Python framework for web-based visual analytics, can run locally as a desktop or client/server app, and can be deployed in the cloud as a service. This supports treating current kayak-gen hosting as a Python server deployment, not static file hosting. |
| [Trame VTK tutorial](https://kitware.github.io/trame/guide/tutorial/vtk.html) | Trame supports local and remote rendering. Local rendering sends geometry to the browser; remote rendering keeps data server-side and sends images, requiring a more capable server. This makes render mode an operational choice within a server-backed app, not proof of a static app. |
| [Trame architecture post](https://kitware.github.io/trame/blogs/trame-architecture-and-capabilities) | Trame applications use a dedicated stateful server process per client, and Trame provides Docker images for multi-user shared hardware. This is a capacity and operations concern for a public URL. |
| [Trame Docker example](https://kitware.github.io/trame/examples/core/docker.html) | Official Trame docs describe cloud deployment via Docker. This aligns with kayak-gen's existing Dockerfile/runbook path. |
| [GitHub Pages docs](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | GitHub Pages is static hosting for HTML, CSS, and JavaScript files. A Pages-style public demo would not run the current Python/Trame server. |
| [Pyodide docs](https://pyodide.org/en/stable/index.html) | Pyodide runs CPython in the browser via WebAssembly and supports pure-Python wheels plus some ported extension packages. This makes a backend-free Python demo possible in principle, but it is a separate runtime/packaging and viewer decision. |
| [Fly.io launch docs](https://fly.io/docs/getting-started/launch/) | Fly Launch works with a Dockerfile or language/framework scanning and deploys from the project source. This is representative evidence that a small server-backed Docker deployment is operationally plausible without selecting a vendor in the RFC. |

## What "Hosted" Should Mean

For the current codebase, "hosted" should mean a public URL backed by the existing `kayakgen serve --host 0.0.0.0 --port 8080` command or the existing Docker image path. It should be the same Trame server-backed app verified locally, with a bounded manual or automated smoke against the deployed URL. It should not mean static GitHub Pages, a Pyodide rewrite, a custom JavaScript frontend, a hosted worker queue, a real CFD service, a persistent design library, or a production SLA.

There is a useful distinction inside "server-backed": remote VTK rendering versus local/browser VTK rendering. That choice affects bandwidth, browser requirements, and server load, but both still depend on a live Python service for the current app. The current acceptance should avoid requiring a render-mode change unless a browser-hosting workflow specifically elects it.

## Viable Options

### Option A - Conservative Default: Keep Public Hosting Deferred

Keep the current posture: local Trame server, Docker/runbook documentation, required local browser acceptance, and no public URL. This is the lowest-risk option and matches the roadmap's current no-claims wording. It avoids creating an endpoint that needs uptime, cost, abuse handling, state cleanup, and capacity management.

Acceptance: no new hosted claim. Preserve `docs/WEB_VERIFICATION.md` required browser acceptance and runbook. Do not call this hosted operation or RFC 0008 hosted-demo closure.

### Option B - Narrow Public Exploratory Demo, Server-Backed

Run the existing Trame app publicly as a demo using the documented command/Docker path. This is the smallest path that satisfies the original share/no-install motivation from RFC 0008 while honoring RFC 0032's deferrals. It should be framed as an exploratory public demo for hull editing, compact analysis, share URLs, and STL export only.

Acceptance: the workflow records the host/deployment command, public URL, operator owner, environment variables, persistence caveats, redeploy steps, manual or automated hosted smoke, no-production/no-SLA wording, and no validated CFD or calibrated performance claims. This option is viable now only if the operator accepts public endpoint ownership and cost/capacity limits.

### Option C - Static / Backend-Free Demo

Build a separate static browser demo using Pyodide or a custom JavaScript frontend. This would fit static hosts such as GitHub Pages, but it is not a deployment of the current Trame app. It would need a new RFC or scoped workflow for the runtime, package compatibility, 3D renderer, evaluator subset, file export path, and explicit no-CFD boundary.

Acceptance: not suitable for "now" unless the decision is explicitly to fund a frontend/runtime rewrite. It should not be used as the acceptance path for RFC 0008's current Trame implementation.

### Option D - Production Hosted App / Hosted CFD System

Add accounts, persistence, quotas, async workers, solver execution, hosted CFD jobs, or production reliability controls. This is outside the current browser-hosting decision. It collides with the PRD, roadmap, RFC 0032, RFC 0040, and RFC 0041 no-claims boundaries unless several independent solver, evidence, and operations decisions land first.

Acceptance: defer. Do not schedule this as browser demo work.

## Recommended Posture

The evidence supports a split decision:

1. The conservative default is Option A: do not promote the project as having a public hosted demo until an operator-owned deployment workflow lands.
2. If the panel wants public shareability now, choose Option B only: a narrow server-backed exploratory demo using the existing `kayakgen serve`/Docker path. The work is operational, not architectural, and must not close full parity, hosted CFD, real solver, calibration, or production-hosting scope.
3. Do not choose Option C as the "now" path. Static hosting is a different frontend/runtime commitment, not a cheaper way to host current Trame.
4. Defer Option D entirely.

## Acceptance Bar For Option B

A public hosted demo workflow should be accepted only if it proves all of the following:

- The deployed app is the current Trame app launched by `kayakgen serve --host 0.0.0.0 --port 8080` or the repo Dockerfile, with exact repo revision, host type, command, environment variables, and redeploy steps recorded.
- A public URL loads without local Python and is clearly labeled exploratory.
- The smoke uses either the existing browser-acceptance checks against the hosted URL or an equivalent recorded hosted smoke: initial hull/deck render, controls, metrics, compact analysis rows, nonblank 3D, representative mutation, Share URL reload, STL bytes, and console/page/network cleanliness.
- Any network or console allowlist is exact: URL pattern, status, rationale, owner, and removal condition. No broad Trame/VTK allowlist.
- Lighthouse Best Practices `>= 90` is required only if the workflow claims RFC 0030 Lighthouse upkeep or RFC 0008 hosted/Lighthouse closure. Otherwise, record it as optional evidence, consistent with `docs/WEB_VERIFICATION.md`.
- Persistence limits are explicit: `?hull=...` survives restart, `/api/hulls` IDs are in memory unless a bounded store is deliberately configured, and `/api/cfd/*` artifacts exist only on the server filesystem or mounted volume.
- The page and docs state that the demo does not run OpenFOAM, SU2, hosted workers, Dockerized solvers, real CFD adapters, validated CFD, calibrated resistance, high-angle GZ, final prediction, or final design-fitness decisions.
- The public deployment has an owner, shutdown/redeploy procedure, cost/capacity boundary, and fallback plan if Trame's stateful per-client process model becomes too expensive or unreliable under public traffic.

## Risks And Unknowns

- Public hosting creates an operations surface that the repo intentionally does not yet model: cost, uptime expectations, abuse, concurrency, stale state, and dependency/security updates.
- Trame's stateful per-client model is suitable for interactive visualization but makes public capacity planning more important than a static site.
- Remote rendering may increase server requirements; local rendering may increase browser/client compatibility risk. The current decision can avoid changing render mode.
- The app has local filesystem CFD job inspection routes. Even with raw/unvalidated wording, a public deployment needs careful artifact root isolation and cleanup.
- Static hosting remains attractive for low-cost demos, but it requires a separate runtime and viewer decision. Pyodide makes browser-side Python plausible, not automatically compatible with the current PyVista/Trame implementation.
- Public URL smoke is not equivalent to production reliability. A demo acceptance should avoid accidental SLA wording.

## Implementation Gates Before Any Work

- Name the selected posture in a decision row or RFC/workflow prompt: no public URL yet, narrow public server-backed demo, or static rewrite exploration.
- If public server-backed demo is selected, assign an operator owner and hosting budget/cap before implementation.
- Decide whether the hosted smoke is manual recorded evidence or a CI-invoked Playwright run against the public URL. Avoid hard-coding vendor-specific infrastructure into ordinary CI unless the operator explicitly wants that coupling.
- Keep browser-hosting work separate from RFC 0040/0041 solver-readiness and real-adapter work.
- Update `docs/ROADMAP.md`, `docs/WEB_VERIFICATION.md`, RFC index/status notes, and `CHANGELOG.md` only after the public URL or decision artifact exists.

## Sub-Agent Help

No spawned sub-agents were used. I used parallel read-only local inspections and external primary-source research.
