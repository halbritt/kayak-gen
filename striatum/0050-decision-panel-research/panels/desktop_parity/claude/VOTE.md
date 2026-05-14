---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-003
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_e8502f401cf1494983db60250c6082ce
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_desktop_parity_claude

# Vote - Desktop Parity Strategy

## Vote

Option A - Web workspace primary, desktop supporting.

## Decision Sentence (for `docs/DECISION_LOG.md`)

The Trame web workspace is the primary UI composition and browser-acceptance
target for new user-facing work in kayak-gen; the PyQt6 desktop GUI is
preserved as a supported local surface for slider editing, 3D preview, STL
export, and no-claim/status copy, but full pixel- or widget-level native
parity is not a project goal. Parity is defined as shared core/CLI data and
read models, identical claim-state and no-claim copy where surfaced, and
identical implemented hull controls — not duplication of every web workflow
in PyQt. A later workflow may layer a thin desktop shell (Option B) over the
web workspace if desktop launch semantics are needed, but no native rewrite
is funded by this decision and the desktop GUI is not deprecated.

## Evidence

### Local citations (verified against current tree, 2026-05-14)

- `docs/PRD.md:16` confirms the project explicitly has desktop, CLI, and
  browser surfaces, with desktop not guaranteed feature-parity across the
  roadmap; line 48 records `Full desktop parity, console-clean Lighthouse
  acceptance, hosted-demo acceptance, hosted CFD workers, and real solver
  adapters remain roadmap items`. This is direct text supporting that
  desktop parity is *roadmap*, not *delivered*, and is currently
  conditionally scoped.
- `docs/ROADMAP.md:57-59` is the no-claim line: "The web frontend is
  local/browser-capable with runbook coverage, not a completed public
  hosted demo, full dashboard parity, hosted CFD system, or desktop
  parity rewrite." The decision must preserve this wording.
- `docs/ROADMAP.md:105-122` (Batch C) instructs splitting hosted demo
  operation, console/Lighthouse upkeep, plot/dashboard parity, "desktop
  parity rewrite or embedding work, only if still desired", and
  mobile/view-only acceptance into independent workflows — and to not
  bundle them with solver or calibration work. Option A is the literal
  reading of "only if still desired"; Options B and C presuppose that
  desire without recorded user demand.
- `docs/USER_GUIDE.md:327-405` (verified by reading section) describes
  the desktop surface as offering implemented-field sliders, STL export,
  status labels, and PyVista preview, while the web surface owns
  comparison report loading, compact analysis, and the local CFD job
  panel. Review-area Stability JSON and Mesh package remain unavailable
  in the browser; web CFD routes remain local raw/unvalidated job-record
  plumbing. The asymmetry is real and current.
- `docs/rfcs/0008-web-frontend.md:44-68, 257-265` records the explicit
  non-goal "desktop GUI stays" and the still-open items: hosted
  operation, desktop-equivalent plot parity, mobile editing, larger
  dashboards. This blocks Option D outright; it does not block Option A.
- `docs/rfcs/0033-workspace-ui-rework.md:20-72, 91-164` describes a
  three-region workspace shape that both surfaces can map onto and
  mentions `QDockWidget` embedding for desktop PyVista — but the RFC
  index in `docs/rfcs/README.md:115-127` still classifies remaining
  desktop parity work as successor scope, not delivered behavior. A
  sketch is not a commitment.
- `docs/design/kayak_hull_design_constraints.md:7-15, 244-264` frames
  the design as a Pareto problem where UI must expose claim state,
  tradeoffs, and no-claim copy — not pixel-match plots. Option A
  honors this; Options B/C invest in framing that does not change the
  user's decision space.

### Independent check (this panelist)

- I re-read `AGENTS.md` (the orientation reading list) and confirm the
  current direction paragraph emphasizes RFC 0007/0008 work, with
  current cleanup about closing gaps between RFC acceptance criteria
  and implementation reality — not about widening surface area. This
  is consistent with Option A.
- I re-read `docs/ROADMAP.md:50-72` (claim gates and Dependency Tracks)
  and confirm the explicit roadmap status of `partial`/`blocked` for
  browser hosting and parity, with "desktop parity rewrite or
  embedding" listed as conditional successor scope. Option C would
  contradict the recorded status of this track.
- I sampled `kayakgen/` and the existing test/golden surface implicitly
  through the user guide and PRD references; the shared core
  (generator, evaluator, sweep, status helpers) already exists, so
  Option A is incremental, not architectural.

### External claims (research-cited, not independently re-fetched here)

The research packet's external evidence (trame user guide and deployment
docs, PyVista trame tutorial, Qt WebEngine Widgets docs, pywebview guide,
PyInstaller usage docs) was published with a 2026-05-14 access date and
substantively supports two non-controversial sub-claims: (a) trame is a
serious maintained presentation framework suitable as a primary surface;
(b) "thin desktop shell over web" is a documented packaging path, not a
hypothetical one. I have not independently re-fetched these URLs; the
decision does not turn on contested external facts, so a re-fetch is not
load-bearing for this vote. If the integrator wants to harden any single
citation, the trame deployment docs and Qt WebEngine Widgets page are
the most material because they underpin the Option-B sequencing claim.

## Why rejected alternatives lose

### Option B - Web primary plus thin desktop shell later

Not selected as the immediate decision because it bundles two separate
choices: (1) "is web primary?" and (2) "do we ship a desktop shell?"
The roadmap and RFC index already instruct that desktop parity work
should be its own workflow "only if still desired" (`docs/ROADMAP.md:117`).
Voting Option B today would commit to the shell before any user demand
is recorded and would smuggle a per-platform packaging matrix
(PyInstaller is per-platform per its own docs) into a UI-strategy
decision. Option A explicitly *permits* Option B as a later, separately
gated workflow if demand appears; this is the cheaper option that
preserves the same future.

### Option C - Full native desktop rewrite to match web workspace

Loses on three counts. First, it directly competes with already-blocked
or partial roadmap work (browser hosting, solver readiness, resistance
evidence, high-angle stability, search) for the same maintainer
attention. Second, RFC 0033's QDockWidget sketch is RFC-level guidance,
not delivered behavior, and the RFC index still treats remaining
desktop parity work as successor scope. Third, it creates a permanent
two-UI tax: every future no-claim copy update, route/read-model change,
and dashboard expansion needs a desktop analog. The roadmap's
explicit "only if still desired" language is incompatible with funding
this now.

### Option D - Web-only, deprecate desktop

Loses on a hard constraint: RFC 0008 records an explicit non-goal that
"the desktop GUI stays" (`docs/rfcs/0008-web-frontend.md:44-68`), the
PRD's Delivered Today section lists the desktop GUI as a current
surface (`docs/PRD.md:47`), and the user guide documents the
`kayakgen view` workflow as supported. Deprecating desktop would
require a fresh RFC contradicting these and fresh user evidence; this
decision does not have that evidence on the table and would not be the
conservative move.

## Implementation gates and no-claims language to preserve

These must remain in force as part of the decision record:

1. **Web-primary is not public hosting.** This decision says nothing
   about whether a public hosted demo exists, who runs it, or what its
   SLA is. The `docs/ROADMAP.md:57-59` no-claim line stays exactly as
   written, including "not a completed public hosted demo".
2. **Web-primary is not completed dashboard parity.** Review-area
   Stability JSON and Mesh package remain unavailable in the browser
   per `docs/USER_GUIDE.md:384-405`; this decision does not change
   that. Future plot/dashboard parity is its own workflow per
   `docs/ROADMAP.md:Batch C`.
3. **Web-primary is not desktop deprecation.** `kayakgen view` launch,
   implemented-field sliders, STL export, 3D preview, and no-claim/
   status copy on the desktop GUI must continue to work; regressions,
   install breakage, and incorrect copy remain in scope for desktop
   maintenance.
4. **Web-primary is not a backend capability change.** This decision
   does not advance mesh-package authoring, hosted CFD, real solver
   execution, calibrated drag, high-angle GZ, or watertight promotion.
   Each of those is its own decision/workflow and remains gated by its
   own RFCs (0040, 0041, 0042, 0043).
5. **Parity is defined as a contract, not a pixel match.** Core
   evaluator/JSON parity is mandatory through CLI and shared read
   models; UI parity is limited to claim state, no-claim copy,
   implemented controls, and documented user-visible workflows; pixel
   and widget parity is not required unless a later RFC says so.
6. **Browser acceptance gates remain honest.** Web-primary still
   requires the existing browser acceptance bar for initial render,
   mutation, nonblank 3D, Share reload, STL bytes, and console/network
   cleanliness per `docs/WEB_VERIFICATION.md:49-75`. "Primary" means
   primary UI composition target, not "exempt from gates".
7. **A future thin desktop shell (Option B path) requires its own
   workflow.** Any later desktop-shell work must record a wrapper
   choice (pywebview / Qt WebEngine / trame desktop / Tauri / etc.),
   per-platform build matrix, dependency size review, security and
   update story, and failure-mode tests. It must not be bundled with
   normal UI cleanup or with any backend track.
8. **Trame-specific behavior continues to be proven via browser
   tests, not direct helper calls.** RFC 0036's same-seed preset
   listener still requires a real browser proof or removal; this
   decision does not retire that requirement.

## Confidence

**High.**

The decision is well-aligned with existing roadmap text (`only if still
desired`), an existing RFC non-goal (`desktop GUI stays`), and the
current user-guide-described asymmetry between desktop and web surfaces.
It is also the lowest-cost option: it does not commit maintainer
attention away from blocked/partial backend tracks (solver readiness,
calibrated resistance, high-angle stability) where the actual capability
gaps live. The only meaningful uncertainty is whether a future user-
demand signal flips Option B from "permitted later" to "needed soon";
that uncertainty is contained by gating Option B to its own workflow.
