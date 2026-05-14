---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-003
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_75e7425d831d47f6b30ed86b1c230745
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_desktop_parity_codex
lease: lease_b974a341a2dc4bb7930b41287a68d1cd

# Vote - Desktop Parity Strategy

Vote: Web Primary, Desktop Supporting

## Decision Sentence

Make the Trame web workspace the primary UI composition and browser-acceptance
target for new user-facing workflows; keep `kayakgen view` supported for local
slider, preview, STL export, and no-claim/status maintenance, and require a
later evidence-backed decision before funding any native desktop rewrite or
desktop-shell packaging effort.

## Evidence

The research packet frames the decision as native/embedded desktop parity
versus a Trame-primary workspace with the desktop GUI as a supporting surface
(`striatum/0050-decision-panel-research/research/desktop_parity/RESEARCH.md:14-18`).
Its Option A is the cleanest fit: new workflow UI targets CLI/read models first
and then web, while desktop consumes shared helpers where cheap and keeps launch,
export, preview, and no-claim regressions in scope
(`striatum/0050-decision-panel-research/research/desktop_parity/RESEARCH.md:92-120`).

The local product docs already describe asymmetric surfaces, not equal parity.
The PRD says desktop, CLI, and browser all exist, but not every roadmap
capability is equally complete; it identifies the CLI as the scriptable core,
desktop as PyQt6/matplotlib/PyVista, and web as Trame with compact analysis,
comparison loading, and local CFD inspection while full desktop parity and
hosted/browser acceptance remain roadmap items (`docs/PRD.md:16`,
`docs/PRD.md:44-49`, `docs/PRD.md:55-60`). The user guide makes the practical
split explicit: desktop exposes implemented sliders, STL export, status labels,
and a separate PyVista preview, but no mesh-package preparation or CFD job start;
the web shell owns interactive inspection, compact analysis, comparison report
loading, and local CFD job panel work, with public hosting, full dashboard
parity, hosted workers, auth/cancellation guarantees, and real adapters still
incomplete (`docs/USER_GUIDE.md:337-367`).

The roadmap no-claims rule is decisive: the web frontend is local/browser-capable
with runbook coverage, not a completed public hosted demo, full dashboard parity,
hosted CFD system, or desktop parity rewrite (`docs/ROADMAP.md:57-59`). Its
browser/parity batch says hosted public operation, console/Lighthouse upkeep,
richer dashboards, desktop parity rewrite or embedding, and mobile/view-only
acceptance must be split into independent workflows, with desktop parity work
only if still desired (`docs/ROADMAP.md:105-122`).

RFC 0008 still matters, but as a boundary, not a native parity mandate. It made
the web frontend a presentation layer over the same core and explicitly said the
desktop GUI stays (`docs/rfcs/0008-web-frontend.md:49-68`). Current RFC 0008
status says the Trame shell, sliders, VTK view, share, STL bytes, browser checks,
and compact analysis are present while hosted public operation, full desktop
plot parity, mobile editing parity, and larger dashboards remain open
(`docs/rfcs/0008-web-frontend.md:9-23`, `docs/rfcs/0008-web-frontend.md:257-265`).
RFC 0033 explains the real UI failure as disconnected claim/readiness surfacing,
not lack of a second full UI implementation, and its goal was a shared
three-region workspace that both desktop and web can map onto while preserving
REST and CLI behavior (`docs/rfcs/0033-workspace-ui-rework.md:21-72`).

Independent external check supports the strategy. Trame's current guide presents
it as an open-source Python framework for interactive visual analytics that can
run locally, on desktop, across the web, or in cloud deployment modes
([trame guide](https://kitware.github.io/trame/guide/), accessed 2026-05-14).
The Trame VTK tutorial documents both local and remote rendering modes with
clear client/server tradeoffs, so web-primary still needs explicit browser and
performance gates rather than assuming one rendering path always wins
([trame VTK tutorial](https://kitware.github.io/trame/guide/tutorial/vtk.html),
accessed 2026-05-14). The Trame desktop deployment guide, pywebview guide, Qt
WebEngine docs, and PyInstaller docs all support later desktop-shell feasibility,
but also show that packaging is its own platform/security/update problem rather
than a reason to keep two native UI implementations
([trame desktop](https://kitware.github.io/trame/guide/deployment/desktop.html),
[pywebview](https://pywebview.idepy.com/en/guide/),
[Qt WebEngine Widgets](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/index.html),
[PyInstaller](https://pyinstaller.org/en/stable/usage.html), accessed
2026-05-14). PyVista's Trame tutorial also supports reusing the existing
PyVista/VTK investment through browser-oriented views
([PyVista Trame tutorial](https://tutorial.pyvista.org/tutorial/09_trame/index.html),
accessed 2026-05-14).

## Rejected Alternatives

Option B, web primary plus thin desktop shell later, is not wrong; it is a
possible future packaging track. It loses as the immediate decision because the
project does not yet have a recorded user or operations need for a desktop icon,
and the wrapper choice, platform build matrix, dependency size, security/update
story, and failure-mode tests are separate gates
(`striatum/0050-decision-panel-research/research/desktop_parity/RESEARCH.md:128-155`).

Option C, full native desktop rewrite, loses because it maximizes duplicated UI
ownership. Every web workflow, no-claim copy update, route/read-model change,
and dashboard expansion would need a PyQt analog or an explicit exception, while
the roadmap already has blocked/evidence-gated work in hosting, solver
readiness, resistance evidence, high-angle stability, and search
(`striatum/0050-decision-panel-research/research/desktop_parity/RESEARCH.md:157-176`).

Option D, web-only desktop deprecation, loses because it conflicts with the
current PRD and user guide and with RFC 0008's explicit non-goal that the desktop
GUI stays (`docs/rfcs/0008-web-frontend.md:66-68`;
`striatum/0050-decision-panel-research/research/desktop_parity/RESEARCH.md:178-191`).

## Gates And No-Claims Language

- "Primary" means primary UI composition and browser-acceptance target, not
  public hosted operation, SaaS readiness, production hosting, or completed
  dashboard parity.
- Core evaluator/JSON/read-model parity is mandatory; UI parity is limited to
  claim state, implemented controls where surfaced, and documented workflows.
  Pixel parity and duplicate native widgets are not required unless a later RFC
  says so.
- Desktop support remains explicit: keep `kayakgen view` launch, implemented
  hull sliders, STL export, 3D preview, and no-claim/status copy checks alive
  while the PRD and user guide document the desktop surface.
- Web-primary work must continue to pass real browser gates for initial render,
  representative mutation, nonblank 3D, Share reload, STL bytes, and
  console/network cleanliness before claiming closed browser behavior
  (`docs/WEB_VERIFICATION.md:49-75`).
- Hosted operation remains a separate decision: the current runbook is
  documentation-only and no public hosted URL, production database, hosted worker
  queue, or public-service SLA exists today (`docs/WEB_VERIFICATION.md:147-210`).
- Do not use desktop parity wording to promote mesh-package authoring, hosted
  CFD, real solver execution, calibrated resistance, high-angle `GZ`, watertight
  `cfd_ready`, final prediction, design fitness, or solver readiness beyond
  existing evidence gates (`docs/ROADMAP.md:38-59`).

Confidence: high
