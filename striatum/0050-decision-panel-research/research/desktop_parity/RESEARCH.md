---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-002
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_a928189261684813affd0c1df129913f
job: job_run_dc0a506896094745b380fd3ad2535d59_research_desktop_parity

# Research - Desktop Parity Strategy

## Decision Question

Should desktop parity remain a native rewrite or desktop-embedding target, or
should the Trame web workspace become the primary UI while the desktop GUI
remains a legacy/supporting surface?

## Local Project Constraints And No-Claim Boundaries

- The PRD says the product has desktop, CLI, and browser surfaces, but not every
  roadmap capability is equally complete on every surface. The CLI is explicitly
  the scriptable core entry point, the desktop GUI is PyQt6/matplotlib/PyVista,
  and the browser frontend is Trame with compact analysis, comparison loading,
  and local CFD job inspection. Full desktop parity, hosted-demo acceptance,
  hosted CFD workers, and real solver adapters remain roadmap items
  (`docs/PRD.md:16`, `docs/PRD.md:44-49`).
- Current no-claim rules say the web frontend is local/browser-capable with
  runbook coverage, not a completed public hosted demo, full dashboard parity,
  hosted CFD system, or desktop parity rewrite (`docs/ROADMAP.md:57-59`).
  Browser hosting/parity work is `partial`/`blocked`, and future work should
  split hosted operation, console/Lighthouse upkeep, dashboard parity, desktop
  parity rewrite or embedding, and mobile view-only acceptance into independent
  workflows (`docs/ROADMAP.md:105-122`).
- The user guide exposes an asymmetry that matters to this decision. Desktop
  currently offers implemented-field sliders, STL export, status labels, and a
  separate PyVista 3D preview; it does not prepare mesh packages, start CFD
  jobs, or promote resistance output. The web shell supports interactive hull
  inspection, compact analysis, comparison report loading, and a local CFD job
  panel, while public hosting, full dashboard parity, hosted CFD workers,
  auth/cancellation guarantees, and real solver adapters remain incomplete
  (`docs/USER_GUIDE.md:327-367`).
- Web review/export surfaces are still bounded. The Review area renders
  existing read models only; Stability JSON and Mesh package remain unavailable
  in the browser, and web CFD routes remain local raw/unvalidated job-record
  plumbing (`docs/USER_GUIDE.md:384-405`).
- RFC 0008 originally made the web frontend a presentation layer over the same
  core, not a replacement for desktop. Its non-goals say the desktop GUI stays
  and both consume the same core (`docs/rfcs/0008-web-frontend.md:44-68`).
  Its current status also records that the Trame shell, browser checks, Share,
  STL bytes, and compact analysis are present, while hosted operation, full
  desktop-equivalent plot parity, mobile editing, and larger dashboards remain
  open (`docs/rfcs/0008-web-frontend.md:9-23`,
  `docs/rfcs/0008-web-frontend.md:257-265`).
- RFC 0033 identified the actual UI problem as divergent, inconsistently
  labeled surfaces around already-landed backend slices. Its goal was a
  three-region workspace that both desktop and web "map onto", with claim and
  readiness language anchored in the UI, while preserving existing REST and CLI
  behavior (`docs/rfcs/0033-workspace-ui-rework.md:20-72`). The acceptance
  shape includes an embedded desktop PyVista view via `QDockWidget`, but the
  roadmap and RFC index still classify remaining desktop parity work as
  successor scope, not delivered behavior (`docs/rfcs/0033-workspace-ui-rework.md:91-164`,
  `docs/rfcs/README.md:115-127`).
- The domain requires a UI that exposes tradeoffs and claim state, not just
  visual matching. The design constraints frame kayak design as a Pareto
  problem across speed, stability, tracking, maneuverability, and primary vs
  secondary stability, with cheap geometry/hydrostatic metrics used as filters
  before CFD (`docs/design/kayak_hull_design_constraints.md:7-15`,
  `docs/design/kayak_hull_design_constraints.md:244-264`).
- This research does not claim any runtime change, desktop deprecation, public
  hosting, production packaging, calibrated resistance, real CFD, high-angle
  stability, web-side mesh-package authoring, or completed desktop/web parity.

## Current External Evidence

Access date for all external sources: 2026-05-14.

| Source | Claim Supported | Decision Implication |
| --- | --- | --- |
| [trame User Guide](https://kitware.github.io/trame/guide/) | trame is maintained as a Python framework for interactive visual analytics and scientific visualization, centered on Python-backed web apps and reusable UI pieces. | This supports keeping the current Trame workspace as a serious primary presentation layer rather than treating it as a throwaway prototype. |
| [trame VTK tutorial](https://kitware.github.io/trame/guide/tutorial/vtk.html) | trame supports both server-side rendering and client-side/local rendering for VTK scenes, with different bandwidth and browser/client tradeoffs. | Web-primary does not force one rendering mode, but the decision should preserve explicit performance and browser-acceptance gates. |
| [trame Cloud deployment guide](https://kitware.github.io/trame/guide/deployment/cloud.html) | trame applications can be deployed in server-backed cloud/container environments; deployment still requires server process, routing, and operational configuration. | A primary web workspace is compatible with local and hosted operation, but public hosted demo remains an operations decision, not automatic parity. |
| [trame Desktop deployment guide](https://kitware.github.io/trame/guide/deployment/desktop.html) | trame documents desktop packaging routes that bundle a Python server with a local webview/window, including PyInstaller plus webview-style wrappers. | Desktop parity can be reframed as a future shell/packaging target over the web workspace rather than a separate native PyQt rewrite. |
| [PyVista trame tutorial](https://tutorial.pyvista.org/tutorial/09_trame/index.html) | PyVista documents trame as a way to expose PyVista/VTK views in browser contexts and distinguishes client, server, and Jupyter rendering modes. | The current PyVista/VTK investment can be reused in web contexts; a web-primary path need not abandon the VTK rendering stack. |
| [Qt WebEngine Widgets documentation](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/index.html) | Qt provides desktop widgets for embedding web content inside Qt applications. | If the project wants a Qt-branded desktop shell later, embedding a local web workspace is technically plausible, but it should be gated as packaging/shell work. |
| [pywebview guide](https://pywebview.idepy.com/en/guide/) | pywebview presents a lightweight cross-platform native window around web content with Python interop. | A thin desktop wrapper is a viable later option for users who want a desktop icon without maintaining two full UI implementations. |
| [PyInstaller usage documentation](https://pyinstaller.org/en/stable/usage.html) | PyInstaller bundles Python apps and their dependencies, but builds are platform-specific rather than cross-compiled. | Any desktop-shell or single-binary distribution should carry per-platform build gates; it is not a cheap substitute for deciding UI ownership. |

## Viable Options

### Option A - Conservative Default: Web Workspace Primary, Desktop Supporting

Make the Trame web workspace the primary surface for new UI composition and
review workflows. Keep the desktop GUI supported for local slider/preview/export
use, compatibility, and small no-claim/status fixes, but do not chase full native
desktop parity unless a later decision records a user or operations need.

What this would mean:

- New user-facing workflow work targets CLI/read models first, then web.
- Desktop consumes shared model/evaluator/status helpers where cheap, but does
  not become the owner of comparison dashboards, CFD job UX, hosted semantics,
  or future browser-only acceptance.
- Parity means "same core data, same claim boundaries, same implemented hull
  controls where surfaced", not pixel-matching every plot or duplicating every
  web workflow natively.
- Desktop work remains allowed for regressions, install breakage, launch
  failures, export failures, incorrect no-claim copy, and cheap control parity
  like an exposed model field.

Why it is viable:

- It matches the roadmap's instruction to split desktop parity rewrite or
  embedding into independent work "only if still desired"
  (`docs/ROADMAP.md:112-118`).
- It exploits already-landed browser acceptance and web-analysis boundaries
  while preserving the desktop GUI that RFC 0008 said should stay
  (`docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:83-128`).
- It prevents two full UI stacks from competing to own every new feature.

Main cost:

- Existing desktop users get maintenance, not guaranteed feature parity.
  The decision should say this plainly so future workflows do not accidentally
  re-open a native rewrite.

### Option B - Web Primary Plus Thin Desktop Shell Later

Use the web workspace as the canonical UI, then package it behind a local
desktop shell if a desktop installer/icon is required. Candidate shells include
trame's documented desktop deployment pattern, pywebview, Tauri, or a Qt
WebEngine wrapper.

What this would mean:

- Desktop parity remains an embedding target, not a native PyQt rewrite target.
- The project first finishes the web workspace gates that matter locally
  (browser acceptance, rendering nonblank checks, copy/no-claim checks, export
  routes, route error handling).
- A later workflow chooses the wrapper, per-platform build matrix, update story,
  and security posture.

Why it is viable:

- External docs support webview/bundled-server desktop routes for Python/trame
  apps.
- It offers a migration path for users who prefer desktop launch semantics
  without duplicating every UI behavior in PyQt.

Main cost:

- It adds packaging and platform gates. PyInstaller-style packaging is
  platform-specific, and webview shells inherit browser engine/security update
  concerns.

### Option C - Full Native Desktop Rewrite To Match Web Workspace

Implement the three-region workspace natively in PyQt/matplotlib/PyVista:
embedded 3D view, parameter rail, review tabs, status bar, comparison, mesh,
and CFD panels.

Why it is viable:

- RFC 0033 already sketched how desktop could map to the workspace, including
  embedding the PyVista window via `QDockWidget`
  (`docs/rfcs/0033-workspace-ui-rework.md:91-164`).
- It preserves a fully local native UI for users who do not want a browser.

Main cost:

- Highest duplication risk. Every future web workflow, no-claim copy update,
  route/read-model change, and dashboard expansion needs a desktop analog or an
  explicit exception.
- It competes with already-blocked/partial roadmap work: browser hosting,
  solver readiness, resistance evidence, high-angle stability, and search.

### Option D - Web-Only, Deprecate Desktop

Freeze or remove the desktop GUI and ask all users to use `kayakgen serve`.

Why it is viable:

- It maximizes focus and eliminates UI duplication.

Main cost:

- It conflicts with RFC 0008's explicit "desktop GUI stays" non-goal, the PRD's
  current desktop surface, and the user guide's documented `kayakgen view`
  workflow. This should not be the conservative choice without fresh user and
  maintainer evidence.

## Risks, Unknowns, And Implementation Gates

- Define "primary" carefully. It should mean primary UI composition and browser
  acceptance target, not hosted production availability or public SaaS.
- Define parity as a contract. Recommended split: core evaluator/JSON parity is
  mandatory through CLI/shared read models; UI parity is limited to claim state,
  implemented controls, and documented user-visible workflows; pixel and widget
  parity is not required unless a later RFC says so.
- Keep desktop support explicit. At minimum, maintain `kayakgen view` launch,
  implemented-field sliders, STL export, 3D preview, and no-claim/status copy
  tests or manual checks. Do not silently let desktop rot if it remains in the
  PRD and user guide.
- Keep web gates honest. Web-primary should still require browser acceptance
  for initial render, mutation, nonblank 3D, Share reload, STL bytes, and
  console/network cleanliness before claiming closed browser behavior
  (`docs/WEB_VERIFICATION.md:49-75`).
- Treat hosted operation separately. The runbook documents local/server
  commands and Docker use, but no public hosted URL or production hosting exists
  today (`docs/WEB_VERIFICATION.md:147-210`).
- Treat packaging separately. A desktop shell needs a wrapper choice, platform
  build matrix, dependency size review, security/update story, and failure-mode
  tests. Do not bundle that into normal UI cleanup.
- Track Trame-specific behavior through browser tests, not direct helper calls.
  RFC 0036 exists because one same-seed preset listener path still needs a real
  browser proof or removal (`docs/rfcs/0036-trame-seed-listener-proof.md:1-31`).
- Do not use desktop parity to smuggle new backend capability. Mesh-package
  authoring, hosted CFD, real solver execution, calibrated drag, high-angle GZ,
  and watertight promotion remain separate RFC tracks.

## Short Recommendation

Evidence supports Option A as the conservative default: make the web workspace
the primary UI target for new work, keep the desktop GUI as a supported
legacy/local surface, and preserve Option B as a later packaging/embedding path
only if users need desktop launch semantics. Do not fund a full native desktop
rewrite now unless the panel records a specific desktop-only requirement that
the web workspace plus CLI cannot satisfy.

This recommendation is conditional on recording the no-claim boundaries above:
web-primary is not public hosting, not completed dashboard parity, not a
desktop deprecation, and not a solver/calibration/stability capability change.
