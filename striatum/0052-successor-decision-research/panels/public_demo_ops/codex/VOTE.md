---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-002
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_c77e0b6f89144e3eb8f07f3ec67324fb
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_public_demo_ops_codex
lease: lease_d391041201724f8a97fa19aa3a6d8510
date: 2026-05-14

# Public Demo Operations Vote

Vote: Defer public operation; fixed managed container after gates

## Decision Sentence

Keep public browser operation deferred until a named operator records owner and
backup, budget/cap, deployed revision, public hosted smoke, bounded persistence,
cleanup receipt, and no-SLA/no-hosted-CFD/no-calibration/no-final-claim wording.
Once those gates exist, the authorized demo path is one fixed-size managed
container running the existing `kayakgen serve --host 0.0.0.0 --port 8080` or
repo Docker image, with autoscaling, databases, queues, hosted workers, and
persistent volumes off unless explicitly budgeted and cleaned up.

## Evidence

- The current PRD says the browser frontend is delivered as parameter editing,
  hull inspection, compact analysis, comparison loading, local filesystem CFD
  inspection, and optional browser smoke; hosted-demo acceptance, hosted CFD
  workers, real solver adapters, and full browser parity remain roadmap items
  (`docs/PRD.md:46-60`).
- The roadmap and D008 already allow only a narrow server-backed exploratory
  demo using `kayakgen serve` or the repo Docker path, and only with operator,
  budget/cap, hosted smoke, bounded persistence, and no production or hosted
  CFD claims (`docs/ROADMAP.md:57-88`; `docs/DECISION_LOG.md:41`).
- The web verification runbook says no hosted public demo URL exists today,
  records the accepted `0.0.0.0:8080` command, documents the Docker run path,
  and limits durable persistence to Share URLs while `/api/hulls` is in-memory
  and `/api/cfd/*` artifacts are server-local filesystem records
  (`docs/WEB_VERIFICATION.md:147-204`).
- Workflow 0051 did not implement D008; its final review explicitly says
  browser hosting was absent from stage 1 and hosted CFD/public production
  hosting stayed blocked
  (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:51-53`).
- The public-demo operations research packet finds no current repo evidence for
  an operator owner, budget/cap, deployment revision, hosted smoke, or cleanup
  receipt, and therefore recommends Option A unless the packet or operator
  report can supply owner and budget/cap now
  (`striatum/0052-successor-decision-research/research/public_demo_ops/RESEARCH.md:24-43`,
  `striatum/0052-successor-decision-research/research/public_demo_ops/RESEARCH.md:266-277`).
- The same research packet identifies the lowest-risk future hosted shape as a
  single fixed-size managed container using the existing Docker/serve command,
  no autoscale, no database, no persistent volume by default, and a recorded
  account/region/tier/monthly cap/public smoke before a provider is named as
  accepted
  (`striatum/0052-successor-decision-research/research/public_demo_ops/RESEARCH.md:109-131`).

Independent external checks on 2026-05-14:

- Kitware's Trame guide describes Trame as a Python framework for web visual
  analytics that can run locally, as a client/server app, or as a cloud service,
  so the current app needs a server-backed deployment rather than static file
  hosting: https://kitware.github.io/trame/guide/
- Trame's VTK tutorial documents local and remote rendering tradeoffs; hosted
  smoke must prove the selected render mode on the selected instance, because
  local rendering transfers geometry while remote rendering requires a more
  capable server: https://kitware.github.io/trame/guide/tutorial/vtk.html
- Trame's NGINX deployment guide calls out WebSocket settings to avoid
  disconnections behind a proxy, so WebSocket behavior belongs in the public
  smoke checklist: https://kitware.github.io/trame/guide/deployment/nginx.html
- GitHub Pages is documented as static hosting for HTML, CSS, and JavaScript
  files from a repository, which cannot operate the current Python/Trame server
  path: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- DigitalOcean App Platform container docs match the repo's command shape:
  Linux AMD64 container images, default web-service HTTP port `8080`, and a
  required bind to `0.0.0.0`:
  https://docs.digitalocean.com/products/app-platform/how-to/deploy-from-container-images/
- DigitalOcean App Platform pricing currently presents flat/monthly-capped
  pricing with fixed shared one-instance container tiers, while its limits page
  says App Platform containers have no persistent local storage, a 4 GiB local
  filesystem limit, and no volumes. That makes it a plausible example of the
  fixed-container class only if the operator accepts ephemeral storage and
  records bandwidth/overage policy:
  https://www.digitalocean.com/pricing/app-platform and
  https://docs.digitalocean.com/products/app-platform/details/limits/
- Fly.io fits Docker deployment mechanically, but its cost-management docs say
  free allowances do not cap bills, billing alerts are not supported yet, and
  there is no free account/free tier; it should not be the default budget-safe
  path without explicit operator acceptance:
  https://fly.io/docs/about/cost-management/
- Railway's cost-control docs support hard usage limits that take workloads
  offline, so it is viable only if the operator records those limits and accepts
  that shutdown behavior:
  https://docs.railway.com/pricing/cost-control
- Pyodide can load built-in packages and pure-Python wheels, but a Pyodide demo
  would be a separate runtime/viewer compatibility decision, not deployment of
  the current Trame app:
  https://pyodide.org/en/stable/usage/packages-in-pyodide.html

## Rejected Alternatives

- Proceeding with an accepted public URL now loses because the packet supplies
  no operator, budget/cap, deployed revision, hosted smoke, persistence policy,
  cleanup receipt, or public no-claims wording. That would turn D008's
  implementation gates into after-the-fact paperwork.
- A usage-based host as the default loses to the fixed managed-container class
  because the public link creates bot/traffic and surprise-bill risk. Railway is
  acceptable with a hard limit recorded; Fly.io is acceptable only with explicit
  manual cost monitoring and owner acceptance of its no-hard-cap posture.
- Static GitHub Pages, Pyodide, or a custom JavaScript viewer loses because it
  is not the current Trame app. It may become attractive for cost, but it needs
  a separate RFC for runtime support, 3D viewer behavior, package compatibility,
  export behavior, and CFD/no-claims boundaries.
- Production hosting or hosted CFD loses because it crosses current project
  boundaries: accounts, quotas, design libraries, hosted workers, OpenFOAM/SU2
  execution, Dockerized solvers, validated CFD, calibrated resistance,
  production SLA, and final design-fitness claims remain blocked or deferred.

## Implementation Gates

- Name the operator owner and backup, contact handle, provider account/org,
  region, and who can deploy, stop, and delete the service.
- Record the exact monthly cap or fixed worst-case cost, including instance
  tier, bandwidth/overage policy, autoscaling status, and confirmation that no
  database, queue, object store, GPU, extra IPv4, persistent volume, or managed
  worker is provisioned unless separately budgeted.
- Record git SHA/branch, Docker image digest or clean-checkout transcript,
  exact command, environment, public URL, TLS/proxy path, instance size,
  storage cap, request/concurrency limits, `0.0.0.0` bind, and WebSocket/Trame
  survival.
- Prefer ephemeral storage for the first demo. Treat `?hull=...` Share URLs as
  the only durable persistence; document `/api/hulls` as in-memory and
  `/api/cfd/*` artifacts as disabled or bounded under
  `KAYAKGEN_WEB_CFD_JOBS_ROOT` with storage cap and cleanup TTL.
- Run and record public hosted smoke with timestamp, operator, deployed
  revision, browser, and checks for page load without local Python, nonblank
  hull/deck view, core controls, compact analysis rows, slider mutation,
  Share reload, STL bytes, console/page/network cleanliness, exact allowlists
  if any, local/raw/unvalidated CFD wording, and absence of real solver
  evidence.
- Record cleanup before the URL is treated as accepted: stop/delete the service,
  images/build cache if billed, DNS/domain records if applicable, volumes,
  databases, object stores, queues, public IPs, and provider project resources;
  include an offline URL check and provider dashboard/bill check.
- Keep Lighthouse Best Practices `>= 90` optional unless the workflow claims
  RFC 0030 Lighthouse upkeep or RFC 0008 hosted/Lighthouse closure.

## No-Claims Language

Public wording must say exploratory browser demo, best-effort availability,
may be redeployed or shut down without notice, no public-service SLA, no
accounts/quotas/collaboration/design library, no hosted CFD workers, no
OpenFOAM/SU2/Dockerized solver execution, no real solver adapter success,
analytical resistance remains `uncalibrated_comparative`, CFD route records
remain local/raw/unvalidated, and there is no calibrated resistance, final
prediction, final design fitness, seaworthiness, safety, or production
watertight-solver-readiness claim.

Confidence: high

The local evidence is decisive that no accepted public operation exists yet and
that no operator/budget/smoke/cleanup evidence was supplied in this packet. The
provider-class recommendation is also well supported today, but the concrete
provider and pricing details must be rechecked immediately before deployment.
