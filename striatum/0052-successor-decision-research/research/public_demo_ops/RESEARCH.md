---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_ffd88a87aa514a80bbb3b13a7df11a7d
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_public_demo_ops
lease: lease_3300ad98a0cc45c78db02006dbfcd38c
date: 2026-05-14

# Public Demo Operations Research

## Decision Question

Can kayak-gen proceed with a narrow public browser demo now, which hosted path
is lowest-risk for the current Trame app, and what operator, budget,
persistence, smoke, cleanup, no-SLA, and no-hosted-CFD evidence must gate it?

## Short Answer

The conservative answer is **not yet as accepted public operation** because the
current repo evidence records no operator owner, no budget/cap, no deployment
revision, no hosted smoke, and no cleanup receipt. D008 and `docs/ROADMAP.md`
already permit a narrow server-backed exploratory demo, but only after those
records exist.

If the missing operator evidence is supplied, the lowest-risk hosted path is a
**single fixed-size managed container web service using the existing Docker
image/`kayakgen serve --host 0.0.0.0 --port 8080` path**, with autoscaling off,
no database, no persistent volume by default, and an explicit monthly cap or
fixed instance price. DigitalOcean App Platform fixed shared containers are the
clearest current example of that provider class because their pricing page
emphasizes flat pricing/monthly caps and fixed one-instance shared CPU options.
Render paid/free web services and Railway can also host containers, but the
panel should treat them as alternatives only if their caps and resource limits
are recorded. Fly.io fits the Docker/port shape well but is less safe as the
default budget path because its own cost-management docs say there is no free
tier, free allowances do not cap bills, and billing alerts are not supported.

## Local Constraints And No-Claims Boundaries

- `docs/PRD.md` says the browser frontend is delivered as a local/browser
  surface with compact analysis, comparison loading, local filesystem CFD job
  inspection, and optional browser smoke. Hosted-demo acceptance, hosted CFD
  workers, full desktop parity, and real solver adapters remain roadmap items.
- `docs/ROADMAP.md` allows browser hosting only as a narrow server-backed
  exploratory demo using `kayakgen serve` or the repo Docker path, and only
  with an operator owner, budget/cap, hosted smoke, bounded persistence, and
  no production or hosted-CFD claims.
- D008 in `docs/DECISION_LOG.md` accepted that same posture and explicitly
  says no public URL was delivered by workflow 0050.
- RFC 0008 originally wanted remote Docker deployment, URL shareability, and a
  future CFD seam, but its current status note leaves hosted public operation,
  full plot/dashboard parity, mobile editing parity, and larger comparison
  dashboard work as follow-up.
- RFC 0032 landed local browser acceptance and hosted-demo documentation only.
  It explicitly excludes live public hosted operation, production hosting,
  hosted workers, real solver execution, validated CFD, calibrated resistance,
  and final design-fitness claims.
- `docs/WEB_VERIFICATION.md` already defines the current runtime command,
  Docker run path, persistence caveats, and manual smoke. It also says no
  hosted public demo URL exists today.
- Workflow 0051 did not implement D008. Its final review confirms no browser
  hosting work landed and no hosted CFD/public-service SLA claim was added.

## Current External Evidence

Access date for all external sources: 2026-05-14.

| Source | Claim supported |
| --- | --- |
| Trame guide, https://kitware.github.io/trame/guide/ | Trame is a Python web-application framework for interactive visual analytics, can run locally or as a client/server app, and can be deployed in the cloud as a service. This supports a server-backed demo, not a static-site deployment. |
| Trame VTK tutorial, https://kitware.github.io/trame/guide/tutorial/vtk.html | Trame/VTK supports both local and remote rendering. Local rendering shifts GPU work to the browser but transfers geometry; remote rendering keeps data server-side but needs a more capable server. Hosted smoke must therefore verify the selected render mode rather than assuming it is cheap. |
| Trame Docker deployment docs, https://kitware.github.io/trame/guide/deployment/docker.html | Trame's Docker guidance discusses EGL/offscreen setup for VTK/ParaView. This aligns with kayak-gen's existing Dockerfile installing Mesa/OpenGL libraries and argues for smoke-testing the built container. |
| Trame NGINX deployment docs, https://kitware.github.io/trame/guide/deployment/nginx.html | Trame behind a proxy needs WebSocket-aware settings to avoid disconnections. Any host/reverse proxy must prove WebSocket behavior through the public smoke. |
| GitHub Pages docs, https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages | GitHub Pages hosts static HTML/CSS/JavaScript from a repository. It cannot run the current Python/Trame server path. |
| Pyodide package docs, https://pyodide.org/en/stable/usage/packages-in-pyodide.html | Pyodide can load built-in packages and pure-Python wheels from PyPI, but a static/Pyodide kayak-gen demo would be a new runtime/viewer compatibility decision, not deployment of the current Trame app. |
| DigitalOcean App Platform container docs, https://docs.digitalocean.com/products/app-platform/how-to/deploy-from-container-images/ | App Platform deploys Linux AMD64 container images from registries, web services default to public HTTP port 8080, and services must bind `0.0.0.0`. This matches the current Dockerfile/serve command shape. |
| DigitalOcean App Platform pricing, https://www.digitalocean.com/pricing/app-platform | DigitalOcean describes App Platform pricing as flat/monthly-capped and offers fixed shared CPU container tiers, including one-instance fixed shared options. This supports a simple cost cap if the operator selects one instance and disables autoscaling. |
| DigitalOcean App Platform limits, https://docs.digitalocean.com/products/app-platform/details/limits/ | App Platform containers have no persistent local storage, a 4 GiB local filesystem limit, and no volumes. This is acceptable for a demo if persistence is intentionally limited to share URLs and temporary server-local artifacts. |
| Render Docker docs, https://render.com/docs/docker | Render can build from Dockerfiles, supports custom Docker commands, automatic HTTPS, WebSockets, health checks, and persistent disks. It is a viable managed-container alternative. |
| Render free instance docs, https://render.com/docs/free | Render free web services are non-production, spin down after 15 minutes idle, can lose local filesystem changes on spin-down/redeploy, and have monthly usage limits. This can be useful for a no-cost preview but is operationally brittle for Trame/VTK smoke. |
| Render pricing, https://render.com/pricing | Render web services include WebSockets and custom Docker containers; current instance pricing includes Free, Starter, Standard, and larger tiers, with bandwidth overage terms. This supports Render as a viable alternative if the operator records instance size and bandwidth cap policy. |
| Fly Launch docs, https://www.fly.io/docs/launch/ | Fly supports Docker-style launch/deploy, app configuration, scaling, and autostop/autostart. The platform fits the current Docker app shape. |
| Fly app configuration docs, https://www.fly.io/docs/reference/configuration/ | Fly's `http_service` defaults/recommends internal port 8080 and supports `auto_stop_machines`, `auto_start_machines`, `min_machines_running`, and concurrency settings. This matches kayak-gen's port and gives operational controls. |
| Fly cost-management docs, https://fly.io/docs/about/cost-management/ | Fly recommends budgeting for always-on cost; outbound bandwidth, volumes, managed services, and dedicated IPv4 can add charges; free allowances do not cap bills; Fly states it does not support billing alerts yet. This makes Fly less attractive as the default budget-capped public demo host. |
| Railway cost-control docs, https://docs.railway.com/pricing/cost-control | Railway supports usage hard limits that take workloads offline after the configured limit, plus email alerts and resource limits. It is viable if the panel prefers a usage-based platform with an explicit hard stop. |
| Hugging Face Spaces docs, https://huggingface.co/docs/hub/main/spaces and Docker Spaces docs, https://huggingface.co/docs/hub/main/spaces-sdks-docker | Spaces are intended for hosted demo apps and support arbitrary Dockerfiles, configurable Docker `app_port`, variables, and ephemeral disk unless storage is attached. This is a demo-oriented alternative, but it needs port/user/filesystem compatibility work and a separate smoke before it can be called lower risk than the current Docker/PaaS path. |

## Options

### Option A - Conservative Default: Defer Public Operation

Keep the current state: local browser acceptance plus hosted-demo runbook
documentation, but no public URL and no "hosted demo accepted" claim.

This is the only option that is fully supported by current repo evidence today.
It honors D008's dissent risk and avoids cost, abuse, uptime, cleanup, storage,
and dependency-update obligations until a named operator accepts them.

Acceptance evidence: none beyond this decision artifact. Docs should continue
to say no hosted public demo URL exists.

### Option B - Lowest-Risk Hosted Path: Single Fixed Managed Container

Deploy the existing Dockerfile or equivalent repo image as exactly one managed
container web service, running:

```bash
kayakgen serve --host 0.0.0.0 --port 8080
```

Use a fixed-size instance, no horizontal autoscaling, no database, no managed
queue, no persistent disk by default, and a provider/account budget cap. A
DigitalOcean App Platform fixed shared container is the clearest current
example because it matches port 8080, supports container-image deployment, and
advertises flat/monthly-capped pricing. Render paid web service is a plausible
fallback if its Docker/WebSocket path smokes cleaner. The decision should name
the provider only after the operator records the actual account, region, tier,
monthly cap, and public smoke.

This is the smallest path that satisfies "no local Python install" while
preserving the current Trame architecture. It is still not a production app,
not RFC 0008 full parity, and not hosted CFD.

Acceptance evidence is listed under "Required Gates" below.

### Option C - Usage-Based Container Platform With Hard Limit

Use Railway, Fly.io, or another usage-based container host only if the operator
records a hard usage limit or a credible fixed worst-case budget. Railway has a
documented hard usage limit that takes workloads offline. Fly fits the Docker
shape and has good autostop/concurrency controls, but its docs explicitly warn
that free allowances do not cap bills and billing alerts are not supported.

This option is viable when the operator values platform ergonomics more than
fixed pricing, but it is not the lowest-risk default for a public link.

### Option D - Static/Pyodide Or Demo-Specialty Rewrite

Do not use this as the "proceed now" path. GitHub Pages and similar static
hosts cannot run the current Python/Trame server. Pyodide or a custom static
viewer could eventually make a cheaper public demo, and Hugging Face Docker
Spaces may be attractive for a public demo page, but both are separate runtime
or packaging decisions requiring new compatibility evidence.

This option should be a future RFC/workflow, not a shortcut around D008.

## Required Gates Before Any Public URL Is Accepted

### Operator And Budget Evidence

- Named operator owner and backup, with contact handle.
- Provider/account/org/project name, region, and who can deploy, stop, and
  delete the service.
- Exact monthly budget/cap. Acceptable evidence:
  - fixed one-instance pricing with autoscaling disabled and bandwidth/overage
    policy recorded;
  - provider hard usage limit that takes service offline;
  - no-payment/free account suspension policy, if using a free tier;
  - or a documented always-on worst-case budget plus explicit manual monitoring
    cadence if the provider has no hard cap.
- Confirmation that no managed database, object store, worker queue, GPU,
  persistent volume, extra IPv4, or autoscaler is provisioned unless listed in
  the budget and cleanup checklist.

### Deployment Evidence

- Git SHA and branch deployed.
- Docker image digest or clean-checkout command transcript.
- Exact command and environment:

```bash
kayakgen serve --host 0.0.0.0 --port 8080
KAYAKGEN_WEB_CFD_JOBS_ROOT=<ephemeral-or-bounded-path>
```

- Host public URL and TLS/proxy path.
- Instance size, memory, CPU, storage cap, and concurrency/request limits.
- Confirmation that the service binds `0.0.0.0` and that WebSocket/Trame
  connections survive the hosted smoke.

### Persistence And Cleanup Evidence

- `?hull=...` Share URLs are the only accepted durable persistence.
- `/api/hulls` IDs are in-memory and may disappear on restart.
- `/api/cfd/*` artifacts are either disabled by policy or kept under
  `KAYAKGEN_WEB_CFD_JOBS_ROOT` with a storage cap and cleanup TTL. For the
  first demo, prefer ephemeral filesystem/no mounted volume.
- If a volume is mounted, record size, retention, cleanup command, and cost.
- Cleanup procedure must delete or stop the web service, images/build cache if
  billed, domains/DNS records if applicable, volumes, managed databases,
  object stores, queues, public IPs, and provider project/org resources.
- Final cleanup receipt should include a URL check showing the demo is offline
  and a provider dashboard/bill check showing no leftover billable resources.

### Hosted Smoke Evidence

The smoke may be a manual transcript or a Playwright run pointed at the public
URL, but it must be recorded with timestamp, deployed revision, browser, and
operator.

Required checks:

- Public URL loads without local Python.
- Hull/deck view is visible and nonblank.
- Core controls and compact analysis rows render.
- Representative slider mutation changes browser-visible metrics and does not
  blank the 3D view.
- Share URL reload reconstructs the current hull.
- Hull or deck STL export returns STL bytes.
- Browser console/page/network checks have no unexpected failures. Any
  allowlist must be exact: URL pattern, status, rationale, owner, and removal
  condition.
- Public page or adjacent docs show exploratory/no-SLA/no-production wording.
- CFD panel/API still says local/raw/unvalidated and no hosted worker.
- No real solver evidence is present: no OpenFOAM/SU2 binary installed in the
  hosted image, no Docker socket mounted, no external worker queue configured,
  no `/api/cfd/*` result presented as validated/calibrated, and no real
  `succeeded` solver path accepted.

Lighthouse Best Practices >= 90 should be required only if the workflow claims
RFC 0030 Lighthouse upkeep or RFC 0008 hosted/Lighthouse closure. For a narrow
operations decision, record Lighthouse as optional supporting evidence.

### Required Public Wording

The public demo page, README snippet, or linked status note should say:

- exploratory browser demo;
- best-effort availability, may be shut down or redeployed without notice;
- no public-service SLA;
- no accounts, quotas, collaboration, or design library;
- no hosted CFD workers, OpenFOAM, SU2, Dockerized solver execution, or real
  solver adapter success;
- analytical resistance remains `uncalibrated_comparative`;
- local/route CFD records remain raw and unvalidated;
- no calibrated resistance, final prediction, final design fitness,
  seaworthiness, safety, or production watertight-solver-readiness claim.

## Risks And Unknowns

- The current code exposes local filesystem CFD job routes. Even with honest
  labels, public operation creates storage and abuse risk unless the artifact
  root is ephemeral, capped, and cleaned.
- Trame/VTK memory and WebSocket behavior under a small free/low-tier host are
  unknown. The hosted smoke should test the exact selected instance size before
  any URL is accepted.
- Remote rendering can shift cost to the server; local rendering can shift
  compatibility risk to clients. The public demo decision should not change
  render mode without explicit smoke evidence.
- Render free and similar free tiers are useful for previews but may spin down,
  lose local filesystem state, or restart. That supports no-SLA wording, not
  public reliability.
- Usage-based hosts without hard caps can create surprise bills under bot or
  accidental traffic. A public link should avoid autoscaling and should have a
  documented shutdown owner.
- Static/Pyodide remains attractive for cost but is not the current app. It
  would need a separate viewer/runtime acceptance path.

## Recommendation

Choose Option A unless the panel packet or operator report can name an owner
and budget/cap now. If those records can be supplied, choose Option B: a
single fixed-size managed container deployment using the current Docker/serve
path, no persistent volume by default, no autoscale, no database, and a hosted
smoke before any public URL is treated as accepted.

Do not select Fly.io as the default "lowest-risk" path unless the operator
explicitly accepts its usage-based billing posture and records a manual cost
monitoring plan. Do not select static/Pyodide or a production hosted app for
this decision.

