# Changelog

This changelog is reconstructed from `git log`, the RFC index, workflow
operator reports, and user-facing docs. It records product-visible changes and
workflow landings; detailed review findings remain in `docs/workflows/*/`.

## Unreleased

### Added

- Added workflow 0032's RFC 0021 explicit synthetic closed-volume
  self-intersection diagnostics: serialized `not_checked`, `passed`,
  `failed`, and `inconclusive` status, assembled-body triangle-pair evidence,
  bounded examples, and a new profile that still keeps `cfd_ready` false.
- Documented workflow 0027's closed-volume safe slice: serializable explicit
  synthetic diagnostics and evidence-based watertight dispatch rejection may
  land, while generated hull-plus-deck closure and `cfd_ready` handoff remain
  deferred pending RFC 0016 policy decisions.
- Scaffolded queued roadmap workflows 0027-0031:
  - 0027 closed-volume geometry contract.
  - 0028 real CFD solver adapter.
  - 0029 web CFD job routes.
  - 0030 resistance calibration fixture.
  - 0031 high-angle `GZ` and secondary stability.
- Added the project convention that future RFC/workflow/user-facing changes
  update this changelog.
- Added proposed RFCs 0021-0030 for the remaining roadmap blockers:
  self-intersection diagnostics, generated closed-body construction,
  watertight handoff, high-angle `GZ` handoff, CFD/calibration claim gates,
  fixture-first CFD adapter work, resistance calibration acceptance,
  plumb-stem closure semantics, design-constraint surfacing, and hosted browser
  acceptance.
- Scaffolded workflows 0032-0041 for those RFCs using the three-lane
  Striatum review pattern and implementer prompts requesting maximal useful
  sub-agent fanout with disjoint write scopes.

### Changed

- Refreshed project Striatum Claude/Codex skill bundles to the running 1.36.0
  install so `striatum doctor` is clean again.
- Recorded the dependency plan for the next implementation batch:
  start self-intersection diagnostics, claim gates, and local-dispatch web CFD
  routes first; block generated bodies, watertight handoff, and real GZ output
  until their upstream evidence lands.

## 2026-05-13

### Added

- Added the root `README.md` and `docs/USER_GUIDE.md`, documenting current CLI,
  desktop, web, mesh package, and local CFD dispatch behavior without claiming
  calibrated resistance, real solver execution, watertight solids, or high-angle
  stability.
- Added proposed RFCs 0016-0020 to split the remaining roadmap into
  closed-volume geometry, first real CFD adapter, web CFD job routes,
  resistance calibration fixtures, and high-angle secondary stability.
- Added deterministic local CFD dispatch records and CLI surfaces:
  `kayakgen cfd prepare`, `kayakgen cfd status`, `kayakgen cfd run`, and
  `kayakgen cfd profiles`.
- Added a named `watertight_solid_resistance_v1` mesh-readiness profile as a
  blocked future profile, while keeping current generated packages below
  `cfd_ready`.
- Added generalized load components and bounded fixed-body upright trim
  equilibrium for explicit load cases.
- Added compact web analysis and comparison views plus comparison report
  loading.
- Added headless and optional Playwright web verification coverage.
- Added mesh-package diagnostics, manifest/profile metadata, and CLI/test
  coverage for packaging generated hull surfaces.
- Added sweep/candidate report foundations for Pareto-style comparison and
  filtering.
- Added source/provenance metadata for the University of Edinburgh
  Pacific-canoe dataset as validation-only input; no kayak calibration fixture
  was accepted.

### Changed

- Reconciled the PRD, RFC index, backlog queue, and operator report so current
  behavior is separated from roadmap deferrals.
- Reframed resistance output as an uncalibrated raw comparative filter rather
  than an accepted final prediction model.
- Marked RFC 0004 and RFC 0006 as partial safe slices after package/core work,
  with exact plumb-stem closure, asymmetric rake, watertight solid readiness,
  and remaining UI polish deferred.
- Marked RFC 0008 as partial: Trame shell, headless checks, and compact web
  analysis landed; full REST/browser/hosted-demo parity remains deferred.
- Updated Striatum skill/plugin bundles in the target repo.

### Deferred

- Real OpenFOAM/SU2/container/hosted CFD execution.
- Normalized or validated CFD physical outputs.
- Calibrated kayak resistance fixtures and calibrated product claims.
- Closed-volume hull-plus-deck geometry and watertight solid generation.
- High-angle `GZ` and secondary-stability curves.
- Web CFD job routes and full hosted browser acceptance.

## 2026-05-12

### Added

- Added the Striatum-driven RFC completion review/remediation workflow and
  pipeline-pivot RFC set.
- Added RFC 0009-0015 covering sweep records, CFD-ready mesh contracts,
  hydrostatic load cases, resistance calibration, Pareto comparison UI,
  generalized trim/GZ, and CFD solver dispatch.
- Added the accepted RFC 0007 package extraction path:
  `kayakgen/`, CLI entry points, compatibility shims, evaluators, and golden
  regression tests.
- Added `KayakClass` presets and `beam_wl` wiring for design constraints.
- Added the analytical resistance evaluator using Michell-wave and ITTC-style
  components as an exploratory comparative model.
- Added plumb-bow support through the `bow_rake` parameter and blended
  end-decay behavior.
- Added the Trame web frontend shell.
- Added context-hygiene docs and agent orientation for Striatum sessions.

### Changed

- Expanded the PRD from a single desktop hull generator toward a generative
  CFD/evaluation pipeline with desktop and web frontends.
- Audited and completed earlier GUI/layout work from RFC 0002 and RFC 0003,
  including class radio controls and plotting/layout cleanup.

## Initial History

### Added

- Added the original parametric kayak generator, desktop GUI, PyVista preview,
  STL exports, and Striatum scaffolding.
- Added early RFC/workflow scaffolds for GUI usability, layout/station view,
  3D rendering, plumb bow, resistance estimation, design constraints,
  architecture revisit, and web frontend direction.
