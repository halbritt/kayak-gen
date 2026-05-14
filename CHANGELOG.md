# Changelog

This changelog is reconstructed from `git log`, the RFC index, workflow
operator reports, and user-facing docs. It records product-visible changes and
workflow landings; detailed review findings remain in `docs/workflows/*/`.

## Unreleased

### Added

- Integrated workflow 0050's majority decisions as documentation-only design
  records: solver readiness is readiness-report-first, the first real solver
  target is OpenFOAM.com v2512 `interFoam` behind watertight evidence,
  resistance source/calibration promotion remains gated, high-angle stability
  has a fixed-trim generated-body v1 design, browser hosting is only a narrow
  server-backed exploratory demo posture, web is the primary UI composition
  target, and sweep/search defaults remain conservative. No runtime behavior,
  tests, solver execution, public URL, calibration, watertight readiness,
  high-angle stability output, desktop rewrite, optimization behavior, or
  product capability changed.
- Scaffolded workflow 0050 as a design-only decision workflow. Each open
  roadmap decision now has a required research packet, independent
  Claude/Codex/Gemini panel votes, strict majority integration, and final
  review before dependent implementation work can begin. No runtime behavior,
  tests, solver execution, calibration, watertight readiness, hosted operation,
  desktop rewrite, optimization behavior, or product capability changed.
- Added `docs/ROADMAP.md` through workflow 0049 as a documentation-only
  reconciliation of outstanding RFCs, stale deferred-queue items, workflow 0048
  successor RFCs, dependency tracks, and future Striatum implementation
  batches. No runtime behavior, tests, API payloads, export availability,
  solver execution, calibration, watertight readiness, final prediction,
  design-fitness, hosted-demo, full-parity, or real high-angle stability
  capability changed.
- Scaffolded workflow 0048 as a docs-only successor RFC backlog workflow with
  parallel Codex RFC drafting lanes for UI follow-up findings, closed-volume/
  solver readiness, real CFD adapter work, resistance calibration fixtures,
  and high-angle `GZ`, followed by traceability, no-claims, ergonomics/design,
  ops/test, integration, and final-review gates.
- Added proposed RFCs 0036-0043 through workflow 0048 as docs-only successor
  backlog scopes: four UI cleanup follow-ups from workflow 0047 plus
  closed-volume solver-readiness, real CFD adapter, resistance calibration
  fixture, and high-angle `GZ` successor gates. No runtime behavior, tests, API
  payloads, export availability, solver execution, calibration, watertight
  readiness, final prediction, or real stability output changed.
- Landed workflow 0047's RFC 0035 UI cleanup slice: web validity badges now
  classify the current hull against canonical web class envelopes before custom
  fallback, preset edit behavior is documented and test-pinned, export-menu
  rows and web state snapshots use declared source-of-truth schemas,
  slider-label CSS/accessibility checks preserve existing tokens and canonical
  labels, and the desktop Matplotlib slider fallback records its removal
  condition. This is maintenance cleanup only; no backend capability, REST
  payload shape, hosted CFD, real solver, calibration, final prediction,
  high-angle `GZ`, web-side mesh-package authoring, watertight `cfd_ready`
  promotion, or desktop parity rewrite landed.
- Landed workflow 0045's RFC 0034 workspace UI follow-up safe slice: web class
  presets reseed canonical hull sliders and narrow ranges, manual hull edits
  return the preset selector to `custom`, the validity badge derives from
  class/envelope state, Resistance and Mesh review cards render existing read
  models, and the Export menu exposes enabled STL rows plus honest local-data or
  unavailable JSON/package states. The slice preserves RFC 0033's no-new-backend
  capability boundary; calibrated drag, final prediction, design fitness,
  high-angle `GZ`, hosted/cloud CFD, real solver adapters, web-side
  mesh-package authoring, watertight `cfd_ready`, and desktop parity rewrite
  remain deferred.
- Published workflow 0034 and 0035 findings ledgers, clearing both backlog
  workflows for conservative Codex implementation lanes: RFC 0023 remains
  evidence-bound on generated-body-derived volume-mesh diagnostics before any
  `cfd_ready` promotion, and RFC 0024 remains limited to generated-body GZ
  handoff contracts, structured unavailable results, fixture-only labeling,
  claim guards, and tests before any real high-angle stability claims.
- Landed RFC 0023 watertight volume-mesh handoff slice: typed manifest,
  diagnostic, artifact, hash, and path-bound evidence records now preserve
  conservative open-surface behavior while allowing `cfd_ready` only for
  matching generated-body fixture volume-mesh evidence. CLI and JSON dispatch
  surfaces expose structured rejection reasons for missing, stale, synthetic,
  mismatched, and unsafe handoff evidence.
- Corrected RFC 0023/RFC 0024 status and user-facing docs after the workflow
  0034/0035 landings so the index now distinguishes fixture-backed
  `cfd_ready` handoff evidence from production solver readiness and real
  high-angle GZ stability claims.
- Scaffolded workflow 0046 for the reported slider-label visibility issue with
  traceability, ergonomics/design, and ops/test review lanes before Codex
  implementation.
- Scaffolded workflow 0047 as a UI follow-up cleanup successor with a Codex
  RFC/scope lane, traceability/no-claims/ergonomics-design/ops first-pass
  reviews, a Codex implementation lane requiring maximal useful sub-agent
  fanout, and a Claude final-review gate.
- Added proposed RFC 0035 through workflow 0047's RFC/scope lane, limiting
  the next UI cleanup pass to workflow 0045 and 0046 final-review findings:
  validity-badge/class semantics, preset edit wording, export/state hygiene,
  slider-label CSS/accessibility maintenance, desktop slider fallback cleanup,
  and focused tests/docs. No runtime product code or new backend, CFD,
  stability, calibration, mesh-readiness, or hosted capability was changed.
- Fixed workflow 0046's desktop and web slider-label visibility issue: desktop
  hull-parameter labels and value text now render legibly without overlapping
  adjacent rows, and web parameter-rail slider labels no longer sit under
  persistent thumb labels while preserving the canonical label text.
- Added the RFC 0024 high-angle GZ handoff envelope: generated closed-body
  diagnostic validation, structured unavailable results, fixture-only synthetic
  math, provenance-safe GZ fields, and tests that keep unavailable or fixture
  curves out of CLI, web, and generated sweep secondary-stability claims.
- Added RFC 0034 and workflow 0045 for the workspace UI follow-up slice:
  dynamic web class presets, dynamic validity badge, resistance and mesh
  read-model wiring, export-menu completion, and broader forbidden-copy
  tests. This successor keeps RFC 0033's no-new-backend-capability boundary
  and leaves calibrated drag, final prediction, high-angle GZ, hosted CFD, and
  watertight `cfd_ready` deferred.
- Added RFC 0033 and workflow 0044 as the workspace UI rework: a single
  three-region desktop/web shell (parameters, geometry, review), a shared
  semantic theme module, claim/readiness/CFD status chips wired to existing
  literals, structured advisory records additive to `DesignAdvisory.warnings`,
  a four-segment status bar, and forbidden-claim regression coverage for the
  Claude Design handoff's no-go strings. No backend capabilities are
  introduced; every existing REST route keeps its JSON shape. Workflow 0044
  now includes a dedicated ergonomics/design review lane before findings are
  ledgered.
- Added workflow 0044's RFC 0033 workspace UI implementation slice: shared UI
  theme tokens, structured advisory records, web workspace regions/status
  copy, mesh/readiness read models, desktop `Cm`/Export STLs touch-ups, user
  guide updates, and regression tests. Current resistance, mesh, and CFD
  outputs remain raw/open-surface/local plumbing, not final prediction,
  watertight-solid, hosted-worker, or calibrated claims.
- Added workflow 0039's RFC 0028 plumb-stem closure safe slice: independent
  `stern_rake`, explicit bow/stern coordinate convention, and exact-plumb
  endpoint/cap semantics for generated closed-body diagnostics while keeping
  open hull/deck STLs labeled as inspection surfaces.
- Added workflow 0033's RFC 0022 generated hull-plus-deck closed-volume
  evaluation body with serialized cap/join policy, waterline metadata,
  positive-volume diagnostics, and RFC 0021 self-intersection gating while
  keeping generated bodies below `cfd_ready`.
- Added workflow 0032's RFC 0021 explicit synthetic closed-volume
  self-intersection diagnostics: serialized `not_checked`, `passed`,
  `failed`, and `inconclusive` status, assembled-body triangle-pair evidence,
  bounded examples, and a new profile that still keeps `cfd_ready` false.
- Added RFC 0025 claim-state metadata to resistance and raw local-CFD records,
  with forbidden-promotion tests for raw CFD, validation-only fixtures,
  uncalibrated resistance, calibrated prediction evidence, and final
  design-fitness claims.
- Added workflow 0029's local web CFD job slice: `/api/cfd/*` routes and a
  compact Trame panel now expose server-local CFD profiles, job preparation,
  status, synchronous local adapter runs, bounded logs, and raw-result lookup
  over RFC 0015 job records while keeping all output raw and unvalidated.
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
- Added RFC 0031 and workflow 0042 as the design-constraint surfacing revision,
  narrowing RFC 0029 into an implementation-ready validity-metadata slice with
  an explicit first-pass review remediation cycle.
- Documented workflow 0037's RFC 0026 fixture-adapter choices: a checked-in
  `python -m` module command, `raw-result.json` normalized output,
  `open_wetted_surface_resistance_v1` as the only fixture profile target, and
  continued raw/unvalidated wording while RFC 0017 OpenFOAM/SU2 selection
  remains deferred.
- Added workflow 0037's deterministic `fixture-local-command` CFD profile,
  fixture case files, local command execution, schema-validated raw-result
  parsing, persisted failure records, and CLI warning visibility, all kept
  raw/unvalidated with no solver validation or calibration claim.
- Scaffolded workflows 0032-0042 for those RFCs using the three-lane
  Striatum review pattern and implementer prompts requesting maximal useful
  sub-agent fanout with disjoint write scopes.
- Added RFC 0032 and workflow 0043 as the conservative successor to blocked
  workflow 0041: local browser-acceptance plus hosted-demo documentation scope,
  three first-pass review lanes, and a declared review-revision anchor for
  browser `needs_revision` routing.
- Added workflow 0042's RFC 0031 design-validity metadata across evaluate JSON,
  web payloads, desktop/web warning helpers, sweeps, and comparison reports
  while preserving advisory-only behavior, existing validation boundaries, and
  deferred geometry/CFD claims.
- Landed workflow 0043's local browser-acceptance profile, hosted-demo runbook
  documentation, exact `/paraview/` browser-probe handling, Share/STL/3D
  browser checks, and raw/unvalidated `/api/cfd/*` fixture-success coverage
  while keeping public hosting, real solver execution, validated CFD,
  calibrated resistance, and final design-fitness claims deferred.

### Changed

- Corrected the RFC index/status headers for previously landed safe slices:
  RFC 0016, RFC 0022, RFC 0025, RFC 0027, and RFC 0031 now match their landed
  workflow state instead of stale proposed/accepted-target labels.
- Aligned individual RFC `Status:` headers with the sequential RFC index for
  previously landed/partial slices, including RFC 0021's landed
  self-intersection diagnostic status, and clarified workflow 0034/0035 review
  verdict semantics so pre-implementation gaps route to findings ledgers rather
  than dead-end review revisions.
- Marked RFC 0031 as the accepted implementation target for workflow 0042 and
  clarified in the RFC index that RFC 0029 remains background for that
  narrowed revision slice.
- Removed ambiguous `OPERATOR_REPORT.md` basename forbids from workflow 0042
  job scopes while leaving the root operator report outside those allowed
  paths.
- Clarified that legacy `bow_rake` historically controlled both bow and stern
  and remains the symmetric compatibility behavior for older hull JSON that
  omits `stern_rake`.
- Hardened comparison-report accepted-use provenance so raw comparative
  resistance and forged legacy final-prediction strings cannot become accepted
  calibrated prediction without fixture IDs, model version, fit evidence, and a
  validity envelope.
- Hardened RFC 0027 resistance calibration acceptance gates so only
  `accepted_fit` records with metrics, accepted fixture IDs, model version, and
  validity envelopes can satisfy calibrated-prediction provenance, while weak
  calibration/validation fixture metadata remains rejected.
- `kayakgen evaluate` and compact web metrics now show visible warnings when
  resistance values are the current uncalibrated comparative filter.
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
