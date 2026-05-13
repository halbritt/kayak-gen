# Deferred Workflow Queue

Updated: 2026-05-13

This queue records completed backlog workflows after 0018 and structures the
remaining known work starting at workflow 0026. The IDs below are ordered by
dependency and implementation leverage, not by RFC number.

Each implementation workflow should use three review lanes before coding:

- Traceability lane: verify RFC acceptance criteria, prior workflow findings,
  and status wording.
- Domain lane: verify kayak/geometry/hydrostatics/CFD assumptions and guard
  against false claims.
- Ops/test lane: verify package boundaries, CLI/web behavior, reproducibility,
  and test strategy.

For implementation jobs, use Codex by default for code changes unless a workflow
has a narrower reason to prefer another implementor. The implementor prompt for
each workflow must include: "Use the maximal number of useful sub-agents with
disjoint write scopes. Prefer parallel agents for independent code, test, docs,
and review tasks, but keep one agent responsible for final integration."

## Completed History

Workflows 0019-0025 have landed on `main` and are no longer queued work:

- 0019 legacy RFC partial closure: landed safe package/core slices for RFCs 0004
  and 0006, with exact plumb end caps, watertight hull-plus-deck solid
  readiness, asymmetric rake, future shape parameters, desktop yellow-banner
  closure, and browser/Lighthouse acceptance left as explicit deferrals.
- 0020 browser acceptance and demo: landed headless verification and optional
  Playwright browser-smoke coverage; Lighthouse console-clean and hosted-demo
  acceptance remain open.
- 0021 web plots and comparison UI: landed compact web analysis/comparison
  views, report loading, tests, and status updates.
- 0022 generalized trim and GZ stability: landed longitudinal load components,
  bounded fixed-body upright trim equilibrium, CLI/sweep summaries, and the
  explicit high-angle GZ deferral pending closed-volume geometry.
- 0023 resistance calibration dataset vetting: recorded the University of
  Edinburgh Pacific-canoe dataset as validation-only source metadata; no kayak
  calibration fixture landed and resistance remains uncalibrated.
- 0024 watertight solid mesh profile: landed
  `watertight_solid_resistance_v1` as a blocked readiness profile and kept
  current generated packages below `cfd_ready`.
- 0025 CFD solver dispatch and jobs: landed local job/run/profile records,
  readiness gating, local artifact directories, unavailable solver state, mock
  failed-command state, and `kayakgen cfd prepare/status/run/profiles`; real
  solver adapters, normalized physical outputs, web job routes, container
  execution, and validated CFD claims remain deferred.

## 0026 - Docs Roadmap And User Guide

Target docs: `docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/rfcs/README.md`,
proposed RFCs 0016-0020,
`docs/workflows/0018-deferred-backlog/QUEUE.md`, `OPERATOR_REPORT.md`.

Purpose: reconcile stale documentation after workflows 0019-0025 and add a
practical user guide that tells users what the tool can do today without
claiming watertight solids, calibrated resistance, high-angle GZ, full web
parity, or real CFD execution.

Prerequisites: workflow 0025 landed; Striatum bundle refresh landed.

Review lanes:

- Documentation accuracy: verify current/delivered wording against landed
  behavior and known deferrals.
- User guide: verify quick start, CLI task examples, desktop/web entry points,
  mesh packaging, local CFD dispatch status, troubleshooting, and limitations.
- Roadmap: verify next RFC/workflow links and ensure proposed work is not
  described as accepted implementation.

Implementation prompt:

```text
Reconcile stale documentation after workflows 0019-0025. Use the maximal number
of useful sub-agents with disjoint write scopes. Prefer parallel agents for
independent docs, RFC/navigation, backlog, and review tasks, but keep one agent
responsible for final integration. Do not edit runtime code. Do not describe
raw/unvalidated resistance or CFD outputs as calibrated or physically accepted.
```

Exit criteria: user-facing docs distinguish current behavior from roadmap
deferrals, completed workflows 0019-0025 are history, proposed RFCs 0016-0020
exist, and workflow 0026 is the active docs-roadmap run.

## 0027 - Closed-Volume Geometry Contract

Target RFCs: 0004, 0006, 0010, 0015, and proposed RFC 0016.

Purpose: define and implement the first explicit closed-volume hull-plus-deck
geometry contract that future high-angle GZ and real solver dispatch can depend
on. This is the successor to the blocked watertight profile from workflow 0024,
not a relabeling of current open surfaces.

Prerequisites: RFC 0016 accepted or amended.

Review lanes:

- Traceability: map exact plumb end-cap, watertight solid, readiness-profile,
  and solver-dispatch deferrals to the accepted geometry contract.
- Domain/geometry: verify closure policy, deck/hull body semantics, normal
  orientation, manifold checks, volume integration boundaries, and waterline
  handling.
- Ops/test: verify deterministic package artifacts, synthetic invalid meshes,
  CLI behavior, and downstream solver profile hooks.

Implementation prompt:

```text
Implement closed-volume geometry only where the accepted RFC defines the
contract. Use the maximal number of useful sub-agents with disjoint write
scopes. Prefer parallel agents for independent geometry/profile, diagnostics,
CLI/package, tests, and docs tasks, but keep one agent responsible for final
integration. Do not relabel open surfaces as watertight.
```

Exit criteria: current open packages remain honestly classified, and any new
closed-volume profile has tests proving manifold/closure behavior.

## 0028 - Real CFD Solver Adapter

Target RFCs: 0015 and proposed RFC 0017.

Purpose: integrate the first real external solver only after readiness,
installation, execution, artifact, and validation boundaries are explicit.

Prerequisites: RFC 0017 accepted or amended; workflow 0027 closed-volume
geometry complete if the selected solver requires watertight solid input.

Review lanes:

- Traceability: map RFC 0015 deferrals and the accepted adapter RFC to landed
  behavior, missing work, or explicit future slices.
- Domain/CFD: verify solver setup, boundary conditions, raw/unvalidated result
  wording, speed/fluid inputs, and artifact provenance.
- Ops/test: verify dependency detection, local execution isolation,
  reproducible job directories, failure capture, and baseline tests that do not
  require unavailable solver binaries.

Implementation prompt:

```text
Implement the first accepted real CFD adapter slice. Use the maximal number of
useful sub-agents with disjoint write scopes. Prefer parallel agents for
independent adapter, CLI, artifact, docs, and test tasks, but keep one agent
responsible for final integration. Do not normalize raw outputs into calibrated
physical claims unless a separate validation/calibration RFC has landed.
```

Exit criteria: the first real solver path is executable where dependencies are
installed, unavailable dependencies fail truthfully, and outputs remain clearly
raw/unvalidated unless backed by calibration work.

## 0029 - Web CFD Job Routes

Target RFCs: 0008, 0015, and proposed RFC 0018.

Purpose: expose CFD job preparation, status, and artifact inspection in the web
frontend without implying solver success or validated physics.

Prerequisites: workflow 0025 local dispatch landed; web-routes RFC accepted or
amended; real adapter optional if unavailable/mock states remain first-class.

Review lanes:

- Traceability: map RFC 0008 job-stub expectations and RFC 0015 dispatch
  behavior to routes, UI states, tests, and explicit deferrals.
- Browser/domain: verify state wording, artifact visibility, and no false CFD
  acceptance.
- Ops/test: verify route error handling, local filesystem queue access,
  browser/headless coverage, and security boundaries for served artifacts.

Implementation prompt:

```text
Implement accepted web CFD job routes and UI states over the existing local
dispatch contract. Use the maximal number of useful sub-agents with disjoint
write scopes. Prefer parallel agents for independent API, UI, tests, docs, and
review tasks, but keep one agent responsible for final integration. Do not fake
solver success and do not hide unavailable solver states.
```

Exit criteria: web users can prepare or inspect CFD jobs according to the
accepted contract, with truthful unavailable/failure states and tests covering
the route/UI behavior.

## 0030 - Resistance Calibration Fixture

Target RFCs: 0012 and proposed RFC 0019.

Purpose: land a licensed, relevant kayak-scale calibration or validation fixture
before any calibrated resistance claim appears in the product docs.

Prerequisites: dataset source accepted by RFC; provenance and licensing checked.

Review lanes:

- Traceability: verify RFC 0012 acceptance requirements and calibration RFC
  requirements.
- Domain/source: verify hull class, measurement type, units, licensing, and
  applicability to kayak-scale slender hulls.
- Ops/test: verify fixture size, provenance metadata, reproducible fitting, and
  no calibrated-claim leakage.

Implementation prompt:

```text
If and only if the accepted RFC approves a dataset, implement calibration ingest
and provenance metadata. Use the maximal number of useful sub-agents with
disjoint write scopes. Prefer parallel agents for independent source,
ingestion, fitting/report, tests, and docs tasks, but keep one agent responsible
for final integration. If no dataset is accepted, do not fabricate fixtures.
```

Exit criteria: either a licensed fixture lands with provenance and tests, or the
calibration RFC remains blocked with precise reasons.

## 0031 - High-Angle GZ And Secondary Stability

Target RFCs: 0011, 0014, proposed RFC 0016, and proposed RFC 0020.

Purpose: compute secondary-stability curves only after closed-volume geometry
and heeled-volume semantics are accepted and implemented.

Prerequisites: workflow 0027 closed-volume geometry complete; RFC 0020 accepted
or amended.

Review lanes:

- Traceability: map RFC 0011/0014 deferrals and accepted GZ requirements to
  tests and docs.
- Domain: verify load-position conventions, heeled volume integration,
  righting-arm sign conventions, and secondary-stability interpretation.
- Ops/test: verify numerical tolerances, non-convergence handling, CLI/JSON
  compatibility, sweep record compatibility, and frontend display behavior.

Implementation prompt:

```text
Implement high-angle GZ only against the accepted closed-volume model. Use the
maximal number of useful sub-agents with disjoint write scopes. Prefer parallel
agents for independent geometry, solver, CLI/frontend, tests, and docs tasks,
but keep one agent responsible for final integration. Do not emit secondary
stability values for open-surface packages.
```

Exit criteria: high-angle GZ is available only for supported closed-volume
geometry and remains explicitly unavailable elsewhere.
