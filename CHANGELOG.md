# Changelog

This changelog is reconstructed from `git log`, the RFC index, workflow
operator reports, and user-facing docs. It records product-visible changes and
workflow landings; detailed review findings remain in `docs/workflows/*/`.

## Unreleased

### Fixed

- Hardened `parse_openfoam_force_dat` against the real OpenFOAM-v2512
  `forces` function-object tabular schema: rows are 10 numeric fields
  (`time` + total/pressure/viscous triples) by default, or 13 with porous
  contributions. The previous implementation assumed a combined
  19-field force+moment layout that the real v2512 binary does not emit
  (moments live in a separate `moment.dat`). Legacy parenthesised-tuple
  layouts remain rejected with `code='unsupported_layout'`. Fixtures
  under `tests/fixtures/openfoam_v2512/` and `tests/fixtures/openfoam/`
  were regenerated from a real interFoam smoke run; the
  `CfdOpenFoamForceDatSample` now reports a `porous_recorded: bool`.
- Remediated workflow 0051 must-fix review findings: OpenFOAM local adapter
  reruns now clear stale per-run raw outputs before command execution, and the
  canonical `GZCurve`/`StabilityResult` contract now round-trips
  fixed-trim generated-body v1 heel metadata. The OpenFOAM path remains
  failed/raw-unvalidated with no real `succeeded` solver path enabled, and
  generated-body high-angle stability output remains an unvalidated
  hydrostatic comparison behind the existing evidence gates.
- Fixed the workflow 0053 web-share regression: browser Share URL reconstruction
  now seeds hull state from the query string deterministically without
  perturbing slider rails. No new browser capability, hosted operation, or
  no-claim wording changed.

### Added

- Landed RFC 0045 ordinary-package solver-readiness promotion. New
  `kayakgen mesh-evidence <hull> --out <dir>` subcommand runs the
  OpenFOAM-v2512 meshing stage against a generated closed-body STL and
  emits a serialized `SnappyHexMeshEvidence` plus the polyMesh artifacts;
  refuses without `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and a sourceable
  bashrc. New `kayakgen mesh-package --bind-evidence <path>` reads the
  evidence and embeds the resulting `VolumeMeshDiagnostic` into the
  manifest. A new `bind_evidence_to_mesh_package(evidence, *,
  closed_body_hash, polymesh_dir)` helper performs three hash checks
  with structured rejection codes (`closed_body_hash_mismatch`,
  `snappy_evidence_body_mismatch`, `polymesh_artifact_drift`, plus
  `evidence_not_recorded` and `evidence_translation_failed`). Default
  `kayakgen mesh-package` JSON is byte-equal to before when
  `--bind-evidence` is absent. +7 tests.
- Landed RFC 0046 non-env-gated OpenFOAM `succeeded` path. Three
  mechanisms admit the real-solver path in precedence order:
  per-job profile flag (`kayakgen cfd prepare
  --allow-real-solver-execution`), persistent setting
  (`~/.config/kayakgen/cfd.json` with
  `allow_real_solver_execution_profiles`), and the existing
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` env knob (backwards-compatible).
  Default behavior (no opt-in) stays `solver_success_blocked`.
  `CfdRunRecord` gains a `real_solver_execution_opt_in: Literal[
  "profile_flag","persistent_setting","env_knob"] | None` field and a
  `SolverExecutionAudit` block (bashrc path, provenance summary, locked
  case-template version, mesh seconds, solve seconds). `claim_state`
  stays `raw_unvalidated`; `accepted_uses` stays `[]`. +11 tests across
  `tests/test_cfd_config.py` and `tests/test_cfd_opt_in_resolver.py`.
- Landed RFC 0047 v2 EHVI active-search successor. New
  `kayakgen/search/active/gp.py` ships a vendored Cholesky-factorized
  Gaussian process with Matern 5/2 and RBF kernels and a vendored
  Nelder-Mead marginal-likelihood optimizer (numpy only; no scipy /
  scikit-learn / BoTorch / GPyTorch / scikit-optimize dependency).
  `kayakgen/search/active/ehvi.py` implements EHVI for 1, 2, and 3
  objectives via axis-aligned cell decomposition; raises
  `EhviDimensionError` for 4+. `SearchAlgorithmSpec.kind` accepts a new
  `"ehvi"` literal; `EhviAlgorithmConfig` carries
  `initial_population_size`, `iteration_budget`, `seed`, `gp_kernel`,
  `gp_noise_floor`, `reference_point`, `candidate_pool_size`. The
  runner dispatches on `isinstance(spec.algorithm, EhviAlgorithmConfig)`
  to the new `_run_ehvi_search` path; the RFC 0043 high-angle-GZ
  display-only refusal and the RFC 0044 claim-admissibility gate apply
  unchanged. Seeded determinism is enforced via a single
  `numpy.random.default_rng(seed)` thread through LHS sampling, GP fit,
  candidate-pool draw, and tie-breaking. The synthetic-landscape
  regression test verifies EHVI achieves >=5x hypervolume improvement
  vs random selection at equal budget. Surrogate predictions never
  appear in candidate `summary` or `run.json` objective fields. Default
  NSGA-II behavior is byte-equal. +19 tests across
  `tests/test_active_search_{gp,ehvi,v2_runner}.py`.
- Landed RFC 0043 stage 4 desktop minimal indicator: a new
  `high_angle_gz: cli_only_unvalidated_hydrostatic_comparison` segment
  in the desktop status block points users at the staged opt-in
  surfaces (`kayakgen stability --high-angle-gz`, sweep
  `evaluators.high_angle_gz`, comparison `high_angle_gz_display`, Trame
  web workspace). Per D021 the desktop does not render a curve; the
  segment is a labelled pointer. Forbidden-copy regression in
  `tests/test_desktop_layout.py` confirms no safety / seaworthiness /
  validated / calibrated / final-prediction / design-fitness wording
  leaks onto the desktop status surface.
- Phase 5 of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`:
  centralised the metric registry. `ObjectiveMetadata` gains
  `display_format`, `availability_conditions`, and
  `default_objective_eligible`. New helpers
  `register_objective_metadata(metadata)` (refuses duplicate
  registration) and `is_objective_metric_admissible(metric, *,
  explicit_exploratory)` return structured rejection codes
  (`objective_metric_unknown`, `high_angle_gz_display_only`,
  `objective_claim_state_not_admissible`). New `ObjectiveRole`
  literal `"display_only"` is applied to `max_gz_m`,
  `heel_at_max_gz_deg`, `range_positive_stability_deg`; the RFC 0043
  token still owns the refusal. `ensure_objectives_claim_admissible_
  for_search` raises `UnknownSearchObjectiveError` for unknown
  metrics unless `objectives_explicit_exploratory: true`. Sweep
  `summary.csv` now writes every registry-known metric the candidate
  reports (legacy ordering preserved); display-only metrics never
  leak in. Web `read_models._format_metric` consults the registry's
  `display_format`. +16 tests in `tests/test_objective_registry.py`.
  Full suite 733 + 2 skipped; ruff clean.
- Executed Phases 0-4 + 6 of
  `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Phase 0+1
  installed ruff (now clean), added `docs/ARCHITECTURE_MAP.md`, and
  filled the previously-scaffold `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/DDD.md`, and `docs/SPEC.md`; added vocabulary-coverage and
  import-boundary regression tests. Phase 2 moved
  `build_high_angle_gz_block` from `kayakgen.cli` to
  `kayakgen.eval.high_angle_gz` (CLI becomes a compat shim), added a
  public `HullGeometry.section_for_closed_body` accessor replacing
  the private `_get_slice_points(..., closed_body_endpoint=True)`
  reach-in, and added a neutral `kayakgen/eval/evidence/` facade
  (re-exports `OpenFoamProvenanceProbe`, `CheckMeshSummary`, claim
  contracts). Phase 3 split four large orchestration files into
  focused sibling modules with byte-stable public surfaces:
  `kayakgen/eval/cfd/jobs.py` 2611 → 180-line shim + 13 modules
  (records, profiles, job_store, manifest_validation, provenance,
  parsers/openfoam_forces, adapters/{unavailable, mock, fixture,
  openfoam_v2512}); `kayakgen/eval/stability.py` 1322 → 9 modules
  under `kayakgen/eval/stability/`;
  `kayakgen/eval/closed_volume.py` 1452 → 6 modules under
  `kayakgen/eval/closed_volume/`; `kayakgen/ui/web/controllers.py`
  1602 → ~297 lines with the orchestration logic moved into a new
  `kayakgen/services/` package (design, evaluation, artifacts,
  cfd_jobs, comparison) — boundary-test-enforced not to import from
  ui/cli. Phase 4 and Phase 6 land as proposed RFCs 0049
  (ArtifactStore + identity normalization) and 0048 (Geometry V2
  distribution model). All 685 prior tests pass plus 32 new
  (vocabulary + import-boundary + services-boundary); full suite
  717 passed + 2 skipped. Ruff clean across `kayakgen` and `tests`.
  OpenFOAM env-gated smoke remains 2/2 in ~10s.
- Promoted the Edinburgh DataShare Pacific-canoe source-review packet
  from `validation_candidate` to `validation_fixture` (RFC 0042 / D025).
  The `ResistanceSourceReviewPacket` validator relaxes in two narrow,
  named ways: `validation_fixture` may carry `non_promotion_reasons`
  describing calibration-fixture blockers (token
  `VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS`), and
  `validation_fixture` may have `uncertainty.status == "incomplete"`
  when `uncertainty_notes` is bound and `warnings` carries
  `uncertainty_documented_caveat` (token
  `VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT`).
  `calibration_fixture` still cannot carry non-promotion reasons.
  Edinburgh now binds full `ResistanceSourceRecord` fixture metadata
  (`fixture_id`, `fixture_version="1"`, `accepted_uses=["validation_only"]`,
  `validity_envelope`, `validity_ranges`, `fixture_review_status="accepted"`)
  and keeps `outside_sea_kayak_calibration_envelope` as the lone
  calibration blocker per D013. +2 new tests; the regenerated pinned
  packet JSON lives at
  `tests/fixtures/calibration/edinburgh_review_packet.json`.
- Landed RFC 0044 v1: additive opt-in `kayakgen search` CLI with a vendored
  NSGA-II multi-objective evolutionary algorithm (pure Python, no external
  optimization-library dependency). New subpackage
  `kayakgen/search/active/` ships `SearchSpec`/`SearchAlgorithmSpec`/
  `SearchConstraint`/`SearchBudget`/`SearchLimits`/`SearchVariable`/
  `ObjectiveSpec`/`SearchMetadata` Pydantic records (`spec.py`), the
  vendored NSGA-II implementation with SBX crossover (eta=15) and
  polynomial mutation (eta=20, per-gene probability `1/n_vars`) and binary
  tournament selection (`nsga2.py`), constraint enforcement
  (`constraints.py`), and an orchestrator that reuses the RFC 0009
  candidate-record writer and `pending` lifecycle (`runner.py`). A new
  `ensure_objectives_claim_admissible_for_search` gate in
  `kayakgen/search/pareto.py` (token
  `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`) refuses
  `raw_unvalidated` and `uncalibrated_comparative` objectives unless
  `objectives_explicit_exploratory: true` is set; the existing
  `ensure_objectives_not_high_angle_gz` gate always wins. Constraint
  violations produce `status="constraint_failed"` candidate records that
  stay frontier-ineligible. Seeded determinism is enforced by threading a
  single `random.Random(seed)` through every operator; two independent
  invocations of the same spec produce byte-identical
  `candidates/<key>/record.json`. +32 tests across
  `tests/test_active_search_{spec,nsga2,runner,cli,pareto_gate}.py`.
  Default `kayakgen sweep` and `kayakgen compare` behavior is unchanged
  (single one-line literal extension of `CandidateStatus`).
- Closed D012: landed the real `openfoam-v2512-interfoam-local` `succeeded`
  path under opt-in env knobs. New subpackage
  `kayakgen/eval/cfd/openfoam_v2512_interfoam/` ships a vendored case
  template (15 parameterised dicts derived from the proven OpenFOAM
  DTCHull-style smoke), an `OpenFoamCaseSpec`/`render_case` renderer that
  emits byte-deterministic case files, a `runner` that sources
  `/usr/lib/openfoam/openfoam2512/etc/bashrc` and runs
  `blockMesh + surfaceFeatureExtract + snappyHexMesh + checkMesh` (mesh
  stage) plus `setFields + interFoam` (solve stage), and an
  `evidence` module that binds the rendered dict hashes, real
  `constant/polyMesh/*` artifact checksums, parsed `CheckMeshSummary`,
  patch metadata, and the real `OpenFoamProvenanceProbe` (from
  `interFoam -help` banner) into a fully-populated `SnappyHexMeshEvidence`
  record. `OpenFoamLocalAdapter` now flips to `status="succeeded"` only
  when BOTH `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and `is_openfoam_available()`
  hold; otherwise the historical `solver_success_blocked` path is
  byte-equal. The returned `CfdOpenFoamRawResult` preserves the locked
  `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
  `claim_state="raw_unvalidated"`, and empty `accepted_uses`. +8
  binary-free tests under `tests/test_openfoam_v2512_case_render.py` and
  +2 env-gated tests under `tests/test_openfoam_v2512_smoke.py` (auto-skip
  unless `KAYAKGEN_OPENFOAM_SMOKE=1` and the bashrc is sourceable).
  Observed wall-clock: 6.8s mesh + 1.9s solve = ~10.7s end-to-end on a
  default `Hull()` closed body.
- Acquired the Edinburgh DataShare bundle (DOI 10.7488/ds/3785, CC BY 4.0,
  workbook SHA-256
  `dffbd5d4547c9e1c1f5597d6188dc2a1efffd316ab301451fb818e11a22acade`) and
  vendored it under `tests/fixtures/calibration/edinburgh/` with a
  `DATASHARE_PROVENANCE.md` manifest. Rewrote
  `kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py`
  against the real workbook schema: `Averaged Data` sheet, header row 12,
  data from row 14, columns Day/Model/Test/Yaw/Speed/Stbd Drag/Port Drag/
  FWD Side/AFT Side/Heave/Pitch/Velocity/Time/Comment. The extractor filters
  setup/zero/negative test numbers and emits the pinned
  `EXPECTED_OUTPUT_COLUMNS` schema (58 accepted rows from the vendored
  bundle). The source-review packet for the Edinburgh source now binds the
  workbook checksum, removes `pending_data_acquisition` from
  non-promotion reasons, and reports `is_validation_fixture_ready() = True`;
  calibration promotion remains blocked by
  `outside_sea_kayak_calibration_envelope` per decision D013. `openpyxl` is
  now an optional dependency under the `calibration` extras (and pinned in
  `dev`). +5 calibration tests (replaced the stub-raises test).
- Landed RFC 0040 stage 2 `snappyHexMesh` evidence-harness contract in
  `kayakgen/eval/snappy_hex_mesh.py`: locked
  `SNAPPYHEXMESH_CASE_TEMPLATE_VERSION = "openfoam-v2512-snappyhexmesh-watertight-v1"`,
  `SnappyHexMeshEvidence` Pydantic record with required dictionary-hash set
  (`controlDict`, `snappyHexMeshDict`, `meshQualityDict`,
  `surfaceFeatureExtractDict`, `blockMeshDict`), deterministic scaffold builder
  hashed off the generated body identity, patch metadata, `CheckMeshSummary`,
  artifact checksums, and `OpenFoamProvenanceProbe`. A new
  `snappy_hex_mesh_volume_mesh_diagnostic` translator returns `None` for
  partial evidence and hands off into the existing watertight readiness gate;
  no new `cfd_ready` promotion path is opened. +15 tests in
  `tests/test_snappy_hex_mesh_harness.py`. No real `snappyHexMesh` execution.
- Extended RFC 0043 stage 3 to the web workspace: the Trame comparison panel
  now hides the high-angle GZ section when no candidate has artifacts and
  surfaces a "High-angle GZ (display-only)" section with the fixed caption
  "Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated,
  validated, or final-prediction claim" when at least one candidate carries a
  block. Each row includes body/load/trim provenance, summary metrics,
  warnings, assumptions, and any `unavailable_reason`. A new
  `kayakgen/ui/web/read_models.py` hosts the `WebHighAngleGzRows` view-model
  so the existing forbidden-claim scan on `app.py`/`controllers.py` stays
  green. +7 web tests across `tests/test_web.py` and
  `tests/test_web_read_models.py`. Desktop GUI is intentionally unchanged
  (stage 4 "desktop minimal"; decision recorded as D021).
- Landed RFC 0043 stage 2 (opt-in sweep evaluator) and stage 3 (display-only
  comparison) for high-angle GZ:
  - Sweep: `evaluators.high_angle_gz: bool` (+ optional
    `evaluators.high_angle_gz_heel_grid_deg`) writes per-candidate
    `candidates/<key>/high_angle_gz.json` via the existing stage-1 block
    builder. Records `high_angle_gz_artifact: {path, bytes, sha256}` on the
    candidate. Failed and pending candidates skip emission; resume preserves
    artifacts byte-for-byte. No high-angle key enters `summary.csv` or
    default Pareto objectives.
  - Comparison: `kayakgen compare` reads per-candidate `high_angle_gz.json`
    when present and attaches a `high_angle_gz_display` block to each row
    (body/load/trim provenance, `max_gz_m`, `heel_at_max_gz_deg`,
    `range_positive_stability_deg`, warnings, assumptions,
    `unavailable_reason`). Report adds a `high_angle_gz_columns: bool` flag
    (true only when at least one row has the block). Pareto frontier
    eligibility, default objectives, and resolved metadata are unchanged; a
    new `HighAngleGzObjectiveRefusedError` (token
    `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`) refuses any high-angle metric as a
    Pareto objective. +19 tests across `tests/test_sweep.py`,
    `tests/test_compare.py`, `tests/test_pareto.py`.
- Landed RFC 0040 generated-body parameter-matrix hardening: a new 55-case
  parametrized test surface (`tests/test_generated_closed_body_hardening.py`,
  11 hull cases × 5 invariant assertions) pins generated closed-body
  diagnostics across default, exact-plumb, mixed-rake, waterline-pinch,
  shallow/deep draft, low/high Cp, and low/high Cm cases. Hardening proves
  body-ref hash round-trip, RFC 0021 self-intersection `passed` (non-stub
  algorithm), positive signed volume, and that ordinary generated packages
  stay below `cfd_ready` with the expected `generated_body_missing` and
  `volume_mesh_missing` blockers on both open and watertight readiness
  reports. No new mesher or solver-readiness promotion landed.
- Landed RFC 0041 partial: locked the OpenFOAM-v2512 interFoam case-template
  constant (`openfoam-v2512-interfoam-dtchull-v1`), added a Pydantic
  `OpenFoamProvenanceProbe` plus injectable runner seam that requires
  application/build/API token evidence (explicitly refuses
  `$WM_PROJECT_VERSION`-only evidence), and hardened `parse_openfoam_force_dat`
  to require the v2512 19-field schema (`porous` header token); v2306 legacy
  layout and corrupt/short files are rejected with structured codes. The
  `succeeded` path stays blocked: the adapter still returns
  `error_kind=solver_success_blocked`, and the `CfdOpenFoamRawResult` Literal
  refuses non-locked case templates and non-`raw_unvalidated` payload classes.
  +12 tests under `tests/test_cfd_jobs_openfoam.py` with fixtures under
  `tests/fixtures/openfoam_v2512/`. No real OpenFOAM binary or solver success
  path was enabled.
- Landed RFC 0042 partial: restructured `kayakgen/eval/calibration.py` into a
  package with an `extractors/` subpackage, added 12 new packet fields
  (locators, access date, checksum/pending-reason, license, attribution,
  extraction-script ref, units, Froude basis, uncertainty notes, accepted-fit
  ref), and added validators that (a) refuse `rejected` as a runtime
  `SourceUse`, (b) require both `source_checksum_sha256` (lowercase hex) and
  `extraction_script_ref` before a packet can promote to
  `validation_fixture`, and (c) require `accepted_fit_ref` before any
  promotion to `calibration_fixture`. The Edinburgh DataShare Pacific-canoe
  extractor stub raises `NotImplementedError("requires Edinburgh DataShare
  download; pending data acquisition")`. +11 tests under
  `tests/test_calibration.py`; the Edinburgh packet remains a validation
  candidate with `pending_data_acquisition` and
  `outside_sea_kayak_calibration_envelope` non-promotion reasons.
- Landed RFC 0043 stage 1: opt-in `kayakgen stability --high-angle-gz`
  (optional `--heel-grid-deg`) emits a `high_angle_gz` JSON block with the
  fixed-trim generated-body v1 curve, per-heel records, summary metrics only
  when every required grid point converges, mandatory surface warnings, and a
  structured `unavailable_reason` for synthetic bodies. Default
  `kayakgen stability` output is byte-equal to the prior behavior. No web,
  desktop, sweep summary, or comparison-frontier surfaces changed.
- Landed RFC 0009 sweep-side STL artifact emission: `evaluators.stl: true`
  in a sweep spec writes `candidates/<key>/hull.stl` and
  `candidates/<key>/deck.stl` via the same `kayakgen generate` STL writer.
  Each successful candidate record gains `stl_artifacts.{hull,deck}` with
  `{path, bytes, sha256}`. Failed and pending candidates skip artifact
  emission; resume preserves existing STL files byte-for-byte without
  regeneration. Sweep STLs are open inspection surfaces only and do not
  promote any candidate to watertight `cfd_ready`.
- Landed RFCs 0036-0039 as the post-workflow-0048 UI cleanup safe slice.
  RFC 0036 retains `_state_matches_preset_seed` with a Trame-state listener
  proof that drives the same-seed event sequence end-to-end without invoking
  the private helper. RFC 0037's `EXPORT_MENU_ROWS` schema is subtitle-only
  with no duplicate guidance fields. RFC 0038 polished the disabled mesh-package
  label to "Mesh package (CLI only)". RFC 0039 unified web snapshot keys and
  CFD/mesh-package aliases onto a shared `WebStateSchema`. No backend
  capability, REST payload shape, calibration, watertight readiness,
  real-solver, or hosted operation changed.

- Landed workflow 0053 stage 2: web query bootstrap and slider-safe state
  handling, sweep pending lifecycle reporting, high-angle stability summary
  semantics, and the accompanying roadmap/user-guide/RFC index and workflow
  report updates. This was a workflow and documentation landing; no new solver,
  calibration, or hosted execution capability changed.
- Scaffolded workflow 0053 as the next implementation burn-down stage for the
  remaining roadmap backlog: browser parity, geometry evidence harness,
  OpenFOAM adapter gate, resistance source evidence, high-angle GZ surfacing,
  sweep pending lifecycle, and a docs-sync tail followed by reviews and
  remediation. No runtime behavior, solver execution, or product capability
  changed.
- Integrated workflow 0052's majority decisions as documentation-only design
  records: the first production volume-mesher candidate is an OpenFOAM-v2512
  `snappyHexMesh` evidence harness, OpenFOAM `succeeded` remains blocked behind
  full mesh/provenance/case/parser gates, Edinburgh is the first validation-only
  resistance source-review packet, high-angle `GZ` surfacing is staged and
  opt-in, public demo operation remains deferred until owner/budget/smoke/
  cleanup evidence exists, and RFC 0009 `pending` lifecycle is the next
  sweep/search delta. No runtime behavior, tests, solver execution, public URL,
  calibration, watertight readiness, default high-angle output, desktop rewrite,
  optimization behavior, or product capability changed.
- Scaffolded workflow 0051 as the first implementation burn-down after the
  workflow 0050 decisions: seven parallel Codex implementation lanes for
  docs/status follow-through, UI successor cleanup, sweep objective metadata,
  solver-readiness reporting/schema hardening, OpenFOAM adapter skeleton,
  resistance source-review packets, and high-angle stability v1 gates,
  followed by three independent reviews, a findings ledger, remediation, and
  final review.
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

- Refreshed `docs/PRD.md` "Delivered Today", "Roadmap And Deferrals", and
  success-criteria sections to match the 2026-05-16 landed state:
  high-angle GZ surfacing is now a delivered opt-in display-only path under
  `unvalidated_hydrostatic_comparison` semantics; the OpenFOAM-v2512
  succeeded path is recorded as an opt-in env-gated capability with
  `raw_unvalidated` payloads; the calibration and measured-GZ deferrals are
  re-scoped against the 2026-05-16 null findings; generative search points
  at RFC 0044.
- Refreshed `AGENTS.md` current-direction paragraph and dropped the stale
  "DECISION_LOG is mostly template" negative-space note (D001-D023 are now
  real recorded decisions).
- Added `ARCHITECTURE_REVIEW_2026-05-16.md` at the repo root — an
  operator-authored systems architecture review of kayakgen as of
  2026-05-16 covering verification snapshot, executive summary, what
  the project is trying to be, and architectural risks. Independent of
  the cowboy-session implementation commits; included for shared
  reference.
- Added `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md` recording
  the two null findings from the 2026-05-16 research investigations
  (in-envelope measured kayak resistance and measured kayak GZ-vs-heel)
  along with the open-access references that were vendored as schema
  examples only.
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
