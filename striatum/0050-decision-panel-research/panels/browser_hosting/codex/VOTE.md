---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-001
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Browser Hosting Vote

Vote: Narrow server-backed exploratory demo

## Decision Sentence

Adopt a narrow server-backed exploratory browser-demo posture: kayak-gen may
pursue a public demo now only through the existing `kayakgen serve` command or
repo Docker image, with an operator owner, recorded hosted smoke, explicit
persistence/cost/capacity limits, and no hosted-CFD, real-solver, calibrated
performance, watertight-readiness, full-parity, production-SLA, or final
design-fitness claims; static/Pyodide demos and production hosted systems remain
deferred.

## Evidence

- The local product boundary supports the web frontend but still labels hosted
  demo acceptance, hosted CFD workers, real solver adapters, full browser
  parity, calibrated resistance, and real high-angle stability as roadmap
  deferrals, not delivered behavior (`docs/PRD.md:39-59`).
- The current roadmap says the web frontend is local/browser-capable with
  runbook coverage, not a completed public hosted demo or hosted CFD system, and
  instructs contributors to split public hosted demo operation from
  console/Lighthouse, dashboard parity, desktop parity, and solver/calibration
  work (`docs/ROADMAP.md:57-67`, `docs/ROADMAP.md:105-122`).
- The browser-hosting research packet reaches the same boundary: hosted should
  mean a public URL backed by `kayakgen serve --host 0.0.0.0 --port 8080` or the
  Docker path, not static GitHub Pages, Pyodide, a custom JavaScript frontend,
  hosted workers, real CFD, persistent design libraries, or production SLA
  (`striatum/0050-decision-panel-research/research/browser_hosting/RESEARCH.md:44-48`).
- Option B is the smallest path that satisfies RFC 0008's original no-install
  and sharing motivation while preserving RFC 0032 deferrals; its required
  acceptance evidence is host/command/revision/env/persistence/redeploy/smoke
  ownership plus no-production/no-SLA and no validated/calibrated claims
  (`striatum/0050-decision-panel-research/research/browser_hosting/RESEARCH.md:58-62`,
  `striatum/0050-decision-panel-research/research/browser_hosting/RESEARCH.md:85-96`).
- RFC 0032 deliberately landed only local browser acceptance and hosted-demo
  documentation; public hosted operation, production hosting, full dashboard
  parity, real solver execution, validated CFD, calibrated resistance, and final
  design fitness remain deferred (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:9-16`,
  `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:104-128`).
- The current runbook already defines the operational shape: required local
  browser acceptance, Docker check, the hosted-demo command, clean-checkout and
  Docker runs, persistence caveats, and manual smoke checks while explicitly
  saying no public hosted demo URL is deployed today (`docs/WEB_VERIFICATION.md:49-75`,
  `docs/WEB_VERIFICATION.md:147-210`).

Independent external checks on 2026-05-14:

- Kitware's Trame guide describes Trame as a Python framework for web visual
  analytics that can run locally as desktop/client-server software or be
  deployed in the cloud, supporting a server-backed posture for the current app:
  https://kitware.github.io/trame/guide/
- Kitware's Trame architecture post says a Trame app uses a dedicated stateful
  server process per client and points to Docker images for multi-user shared
  hardware, so a public URL is an operations/capacity decision, not just static
  hosting: https://kitware.github.io/trame/blogs/trame-architecture-and-capabilities
- The official Trame VTK tutorial distinguishes local and remote rendering and
  exposes both `VtkLocalView` and `VtkRemoteView`, so render mode should remain
  an operational choice inside the server-backed app rather than an acceptance
  prerequisite: https://kitware.github.io/trame/guide/tutorial/vtk.html
- GitHub Pages is documented as static hosting for HTML, CSS, and JavaScript
  files, which does not run the current Python/Trame server:
  https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- Pyodide is CPython in WebAssembly for browser/Node.js and can run many Python
  packages, making a backend-free demo plausible only as a separate runtime and
  viewer decision: https://pyodide.org/en/stable/index.html
- Fly.io's launch docs show a representative Dockerfile/source-directory
  deployment path, supporting the operational plausibility of a small
  server-backed demo without making Fly.io the project decision:
  https://fly.io/docs/getting-started/launch/

## Rejected Alternatives

- Option A, keep public hosting deferred, loses as the selected posture because
  it preserves the status quo after the repo already has a documented
  server-backed run command, Docker path, browser acceptance profile, and
  explicit hosted smoke checklist. It remains the fallback if no operator owner
  and cost/capacity cap are named.
- Option C, static/backend-free demo, loses because it is not a deployment of
  the current Trame app. It would require a new RFC or workflow for Pyodide or
  custom JavaScript, package compatibility, 3D rendering, evaluator subset,
  export behavior, and no-CFD boundaries.
- Option D, production hosted app or hosted CFD system, loses because it
  crosses multiple current boundaries: accounts, persistent design libraries,
  quotas, hosted workers, solver execution, validated CFD, calibrated
  resistance, watertight readiness, and production reliability are all separate
  blocked or evidence-gated tracks.

## Implementation Gates

- Name an operator owner before work starts, including budget/cost cap, expected
  concurrency, shutdown/redeploy procedure, and dependency/security update
  responsibility.
- Deploy only the current Trame app via `kayakgen serve --host 0.0.0.0 --port
  8080` or the repo Docker image, recording repo revision, host type, exact
  command, environment variables, mounted volumes, and redeploy steps.
- Record a hosted smoke against the public URL: initial hull/deck render,
  controls, metrics, compact analysis rows, nonblank 3D before and after a
  representative mutation, Share URL reload, STL bytes, and console/page/network
  cleanliness.
- Keep any console/network allowlist exact: URL pattern, status, rationale,
  owner, and removal condition. No broad Trame, VTK, or `/paraview/` allowlist.
- Require Lighthouse Best Practices `>= 90` only if the workflow claims RFC
  0030 Lighthouse upkeep or RFC 0008 hosted/Lighthouse closure; otherwise record
  Lighthouse as optional evidence.
- Document persistence truthfully: `?hull=...` survives restart, `/api/hulls`
  IDs are in memory unless a bounded store is deliberately configured, and
  `/api/cfd/*` artifacts exist only on the server filesystem or mounted volume.
- Isolate `KAYAKGEN_WEB_CFD_JOBS_ROOT` for the public host and define cleanup
  policy before exposing local filesystem CFD inspection routes.
- Update `docs/ROADMAP.md`, `docs/WEB_VERIFICATION.md`, the RFC index/status
  notes, and `CHANGELOG.md` only after the public URL and smoke evidence exist.

## No-Claims Language

The public demo is exploratory hull editing, compact analysis, share URL, and
STL export only. It does not run OpenFOAM, SU2, hosted workers, Dockerized
solvers, or real CFD adapters; does not provide validated CFD, calibrated
resistance, high-angle `GZ`, watertight `cfd_ready` generated packages, final
prediction, final design fitness, production hosting, production SLA, accounts,
quotas, or persistent design libraries; and does not close full desktop parity
or broader browser dashboard parity.

Confidence: medium

The technical path is straightforward and well supported by the current Trame
architecture and project runbook. Confidence is not high because the vote
creates an operator-owned public endpoint with unresolved cost, capacity,
state-cleanup, dependency-update, and abuse-handling risks that the repo does
not currently model.
