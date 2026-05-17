# DDD

## Why this file exists

This file documents the domain-driven framing the project's codebase already
has. SPEC describes the implementation contract; this file sits one level up
and explains *why* SPEC looks the way it does. UBIQUITOUS_LANGUAGE.md is the
glossary; this file is the model.

A new reader should be able to read this file and re-derive why the
vocabulary in `UBIQUITOUS_LANGUAGE.md` is load-bearing, why decisions in
`DECISION_LOG.md` are gates rather than notes, and why the SPEC's invariants
are the invariants.

## Bounded context

Kayakgen models the lifecycle of a single-paddler hull design from parametric
inputs to scriptable, claim-aware evaluation outputs. The boundary is:

- **In**: a `Hull` Pydantic record (dimensions, form coefficients, end-shape
  controls, optional class preset and name).
- **Out**: geometric artifacts (open hull/deck STL, closed-body STL when
  bound), evaluation results (hydrostatics, raw resistance, stability,
  high-angle GZ when opted in, mesh diagnostics), local CFD dispatch
  artifacts (job records, raw OpenFOAM forces when opted in), comparison
  reports, and search-run histories.
- **Durable**: hull JSON, mesh packages, CFD job directories, sweep/search
  run directories, comparison reports, the Edinburgh validation fixture,
  the OpenFOAM case templates.
- **Not modeled** (out of scope per `docs/PRD.md`): production solid hull
  assembly, structural/scantling, outfitting, non-kayak hull forms.

Every legal mutation passes through the CLI write surface or a Python entry
point that mirrors it; refusals return a structured error with a stable
code.

## Ubiquitous language

`docs/UBIQUITOUS_LANGUAGE.md` is the canonical reference. Code agrees with
the vocabulary; drift is a bug, enforced by `tests/test_vocabulary_coverage.py`.

## Aggregate roots

Identity, lifecycle, and invariants attach to a small set of roots. Each row
gives storage location and the invariants enforced by Pydantic model
validators.

| Aggregate | Storage | Identity | Invariants |
| --- | --- | --- | --- |
| **Hull** | `<name>.json` Pydantic record | `Hull.record_hash()` for serialized-form identity; `Hull.design_hash()` for physical-inputs-only identity (RFC 0049). `Hull.hash()` is an alias for `record_hash()` and is byte-stable. | dimensions positive; `Cp`/`Cm`/`bow_rake`/`stern_rake` in canonical bands; class-preset constraints; rake fields are dimensionless fullness controls in `[0, 1]`. When `geometry_kind="distribution_v2"` (RFC 0048), a `DistributionV2Spec` must be present and `bow_rake`/`stern_rake` must be at defaults. |
| **MeshPackage** | directory written by `kayakgen mesh-package`; `manifest.json` is the canonical reader | manifest's `mesh_profile.name` + body identity | manifest's `body_ref_hash` matches the source hull; readiness chosen by the bound `VolumeMeshDiagnostic` and the profile; `cfd_ready` only when watertight evidence binds. |
| **ClosedVolumeBody** | in-process `ClosedVolumeBody` record; persisted via the package manifest | `body_id` + `source_hull_hash` | positive signed volume; passes RFC 0016 topology and RFC 0021 self-intersection diagnostics; per-part vertex/face arrays consistent. |
| **SnappyHexMeshEvidence** | `<dir>/evidence.json` written by `kayakgen mesh-evidence` | `body_ref_hash` + locked case-template version + dictionary hash set | `dispatch_state` only `evidence_recorded` when every dict hash, patch entry, `CheckMeshSummary.passed`, polyMesh checksum, and v2512 provenance bind. |
| **CfdJob** | directory written by `kayakgen cfd prepare` containing `profile.json`, `job.json`, `run.json` | UUID-named directory | mesh package profile and readiness match the solver profile's requirements before the job exists. |
| **CfdRunRecord** | `run.json` inside a `CfdJob` | (job_id, attempt) | claim_state preserved across status transitions; `succeeded` requires the RFC 0046 opt-in resolver to admit the run; `solver_execution_audit` populated on success, None on blocked. |
| **CfdOpenFoamRawResult** | `raw-result.json` inside a `CfdJob` | (job_id, case_template_version) | `claim_state="raw_unvalidated"`, `accepted_uses=[]`, `case_template_version` locked to literal `"openfoam-v2512-interfoam-dtchull-v1"`. |
| **ResistanceSourceReviewPacket** | `kayakgen/eval/calibration/__init__.py:default_resistance_source_review_packets()` + pinned JSON | `source_id` + `fixture_id` + `fixture_version` | promotion rules in `_review_verdict_controls_promotion_metadata`; D025 admits one documented-uncertainty caveat path and one calibration-blocker `non_promotion_reasons` path on `validation_fixture`. |
| **SweepRun** | `runs/<name>/` directory | run directory + spec hash | `pending` candidates frontier-ineligible; resume preserves seeded order; per-candidate record schemas frozen. |
| **SearchRun** | same as `SweepRun` with a `search_metadata` block | run directory + spec hash + seed | algorithm-determined byte-identical records across reseeded runs (NSGA-II + EHVI); claim-admissibility gate enforced before any evaluation. |
| **ComparisonReport** | `<run>/compare.json` written by `kayakgen compare` | (run_id, objective set hash) | pending rows visible but frontier-ineligible; high-angle GZ and turning metrics are display-only (RFC 0043 / RFC 0053); refused as Pareto objective via the registry's `display_only` role + the RFC 0043 token. RFC 0052 `pairwise_notes` are advisory only; frontier eligibility unchanged. |
| **TankTestCampaign** / **IncliningTestCampaign** | directories under operator-chosen `--out` (RFC 0054) | `source_id` + row-source-id consistency | every `TankTestRun` row's `source_id` matches the campaign's; `RightsChecklist` records license/attribution/redistribution intent. Promotion to `validation_fixture` / `calibration_fixture` runs through the existing `ResistanceSourceReviewPacket` validator. |
| **AcceptedFitRecord** | `accepted_fit.json` under a calibration fixture directory (RFC 0054) | (fit_id, immutable model_version) | `fit_metric ∈ {RMSE, MAPE, R2}`; below-threshold fits refused at accept-fit time AND at `ResistanceSourceReviewPacket` validation time with structured tokens. Calibration_fixture promotion requires this record on disk. |
| **ArtifactStore + SqliteIndex** | hard-linked `_store/` per run directory (RFC 0049); `~/.local/share/kayakgen/index.sqlite` (override `KAYAKGEN_INDEX_DB`) | `artifact_hash` (SHA-256 of bytes) per artifact; `run_id` per run | sweep/search/CFD writers route through `FilesystemArtifactStore`; canonical paths and bytes stay byte-stable; missing `_store/` re-derives from canonical on next read with a warning. |

## Value objects

Immutable, equality-by-value, no identity. Defined by Pydantic with
`ConfigDict(extra="forbid")` and a stable `schema_version` literal.

- `LoadCase` (paddler / hull / cargo mass + CG)
- `MeshSolverProfile` (profile name, version, mesh requirements)
- `SolverProfile` (CFD profile metadata)
- `OpenFoamProvenanceProbe` (application/build/API/project_version/env probes)
- `SolverExecutionAudit` (bashrc path, provenance summary, locked
  case-template version, mesh/solve seconds)
- `CheckMeshSummary` (parsed checkMesh output)
- `KayakgenCfdConfig` (persistent opt-in settings)
- `EvaluatorOptions` (sweep evaluator flags)
- `Objective` (metric + direction) plus `ObjectiveMetadata` registry entries
- `SearchSpec` / `SearchAlgorithmSpec` / `SearchConstraint` / `SearchBudget`
- `HighAngleGzDisplay` (display-only comparison row)
- `WebHighAngleGzRows` / `WebHighAngleGzRow` (web read-model view shape)
- All `*Artifact` records (`StlArtifact`, `HighAngleGzArtifact`)

## Domain services

Stateless computations over aggregates and value objects. After Phase 3
of the architecture plan, evaluator orchestration is split across
focused modules under `kayakgen.eval.*` and a new `kayakgen.services`
package hosts the web/CLI application services.

- **Geometry**: `Hull.to_geometry()`,
  `kayakgen.eval.closed_volume.generated_body.generated_hull_plus_deck_body`,
  `kayakgen.eval.closed_volume.diagnostics.diagnose_closed_volume_body`.
- **Hydrostatics + initial stability**:
  `kayakgen.eval.hydrostatics.metrics`,
  `kayakgen.eval.stability.evaluator.evaluate_stability`,
  `kayakgen.eval.stability.evaluator.evaluate_gz_curve`. Public surface
  is re-exported from `kayakgen.eval.stability` so the original imports
  continue to work.
- **Resistance filter**: `kayakgen.eval.resistance.resistance_curve` (raw
  comparative; claim state `uncalibrated_comparative`).
- **Mesh package + readiness**: `kayakgen.eval.mesh_package.write_mesh_package`,
  `closed_volume_solver_readiness_report_from_package`.
- **Evidence binding**: `kayakgen.eval.snappy_hex_mesh.bind_evidence_to_mesh_package`
  (D026 three-hash gate); `snappy_hex_mesh_volume_mesh_diagnostic` translator.
- **CFD dispatch**: `kayakgen.eval.cfd.job_store.prepare_cfd_job`,
  `kayakgen.eval.cfd.job_store.run_cfd_job`,
  `kayakgen.eval.cfd.adapters.openfoam_v2512.OpenFoamLocalAdapter`,
  `kayakgen.eval.cfd.adapters.openfoam_v2512.resolve_real_solver_execution_opt_in`
  (D027 precedence resolver). All public names are also re-exported
  from the `kayakgen.eval.cfd.jobs` compat shim.
- **OpenFOAM execution**: case render
  (`kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render.render_case`),
  meshing (`runner.run_meshing_stage`), solve (`runner.run_solver_stage`).
- **Source review**: `kayakgen.eval.calibration` validators (D025 admissibility).
- **Sweep + search**: `kayakgen.search.sweep.run_sweep`,
  `kayakgen.search.active.runner.run_search`.
- **High-angle GZ read model**: `kayakgen.eval.high_angle_gz.build_high_angle_gz_block`
  (was in CLI; moved Phase 2 of the architecture plan).
- **Comparison**: `kayakgen.search.compare.build_comparison_report`.
- **Identity (RFC 0049 / D030)**: `kayakgen.services.identity`
  (`record_hash`, `design_hash_for_hull`, `run_hash`); `Hull.hash()`,
  `Hull.record_hash()`, `Hull.design_hash()` accessors.
- **ArtifactStore (RFC 0049 / D030)**:
  `kayakgen.services.artifact_store.FilesystemArtifactStore` (hard-link
  mirror under `_store/`), `SqliteIndex` (runs / candidates /
  metrics / artifacts / events), and `index_run_directory` /
  `index_candidates` helpers. Sweep, search, and CFD job writers
  route through the store.
- **Sensitivity (RFC 0052 / D033)**: `kayakgen.services.sensitivity`
  `compute_sensitivity` with auto-step + per-parameter step override.
- **Builder exports (RFC 0051 / D032)**:
  `kayakgen.services.build_export` writers + `write_build_export`
  orchestrator.
- **Calibration artifacts (RFC 0054 / D035)**:
  `kayakgen.services.calibration_artifacts.write_residual_plot`
  (vendored SVG, no matplotlib dependency).
- **Design-report rendering (RFC 0055 / D036)**:
  `kayakgen.services.design_report.render_design_report` (jinja2 +
  optional weasyprint); `FORBIDDEN_COPY_TOKENS` + scrub list named
  constants; `ReportForbiddenCopyError` refusal.
- **Geometry V2 (RFC 0048 / D029)**: `Hull.to_geometry()` dispatches
  on `geometry_kind` to either the existing `LoftedHullGeometry` or
  the new `DistributionV2Geometry`. The hydrostatic cross-check lives
  in `kayakgen.eval.hydrostatics` and emits an advisory note on
  `Hydrostatics` + an optional `V2HydrostaticCrossCheck`.
- **Target workflows (RFC 0050 / D031)**:
  `kayakgen.services.evaluation.solve_target_draft`,
  `solve_target_trim`, `target_draft_load_mismatch`.
- **Application services (Phase 3D)**: `kayakgen.services.design`
  (hull-state composition, presets, validity badges),
  `kayakgen.services.evaluation` (metrics + analysis + resistance view
  models), `kayakgen.services.artifacts` (export orchestration),
  `kayakgen.services.cfd_jobs` (CFD prepare/run/status/logs orchestration),
  `kayakgen.services.comparison` (comparison-report load + read-model
  assembly). The Trame web `controllers.py` and CLI subcommands consume
  services; services consume `kayakgen.eval` and `kayakgen.search`.

## Read models

View shapes consumed by UI or external tooling, not aggregates.

- `EvaluationResult` (combined hydrostatics + resistance + stability + mesh).
- `ComparisonReport` (Pareto frontier + per-candidate display rows).
- `ClosedVolumeSolverReadinessReport` (per-package readiness + blockers).
- `WebStateSchema` and the Trame `WebHighAngleGzRows` view-model.
- `SensitivityResult` (RFC 0052 read model over evaluator outputs)
  and `PairwiseNote` (advisory on `ComparisonReport`).
- `DesignReportResult` (RFC 0055; the rendered HTML + optional PDF
  + the `forbidden_copy_clean` flag).
- `BuildExportSpec`-driven artifact bundle (RFC 0051; one bundle per
  `kayakgen build-export` invocation).
- `TurningMetrics` (RFC 0053; opt-in additive view model on
  `EvaluationResult`).
- `TargetDraftMismatchReport` (RFC 0050).
- `V2HydrostaticCrossCheck` (RFC 0048 advisory on `Hydrostatics`).

## Write surface

The CLI is the canonical write surface. Every persistent mutation goes
through one of the `kayakgen <subcommand>` invocations listed in
`docs/ARCHITECTURE_MAP.md`. The Python API mirrors the CLI and is the entry
point for tests; direct calls into private evaluator helpers from outside
`kayakgen.eval` are refused by `tests/test_import_boundaries.py`.

The web frontend (`kayakgen serve`) and the desktop GUI (`kayakgen view`)
are read-and-edit surfaces over the same evaluators; neither persists state
the CLI cannot also produce. The web frontend's `/api/cfd/*` routes are the
network analog of the CLI's `kayakgen cfd ...` subcommands and respect the
same opt-in resolver (RFC 0046 / D027).

## Durable state stores

Today the project's durable state is the filesystem:

- Hull JSON files (operator-managed paths).
- Sweep/search run directories under operator-chosen `--out` paths.
- CFD job directories under `KAYAKGEN_WEB_CFD_JOBS_ROOT` (or the default
  `.kayakgen-web-cfd-jobs/` when the web frontend is serving).
- Mesh packages under operator-chosen `--out` paths.
- The Edinburgh validation fixture vendored under
  `tests/fixtures/calibration/edinburgh/`.
- The OpenFOAM case templates vendored under
  `kayakgen/eval/cfd/openfoam_v2512_interfoam/templates/`.
- The persistent operator setting at `~/.config/kayakgen/cfd.json`
  (RFC 0046).

Phase 4 of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md` proposes an
`ArtifactStore` to consolidate these stores behind a queryable index.

## Domain events

Today the only persistent event log is the per-run history block on
`SearchRun.search_metadata.history` (RFC 0044). Each `SweepRun` /
`SearchRun` directory implicitly logs candidate transitions through its
`run.json` + `summary.csv` + `failures.jsonl` triple. There is no
cross-run event stream.

CFD jobs implicitly record their lifecycle through `profile.json` →
`job.json` → `run.json` writes; the `CfdRunRecord` carries the terminal
state.

## Adding to the model

When a new concept is introduced:

1. **Glossary first.** Add a `docs/UBIQUITOUS_LANGUAGE.md` entry. The
   `tests/test_vocabulary_coverage.py` regression keeps this honest.
2. **Identify the pattern.** Aggregate, value object, domain service,
   read model, or boundary clarification. Update this file.
3. **Validator next.** Reject unknown values at the write surface with
   `Pydantic ConfigDict(extra="forbid")` and a structured rejection code.
4. **Surface in introspection.** Status, logs, reports show the concept.
5. **Decision row.** `docs/DECISION_LOG.md` cites the glossary entry and
   the rationale. Each named refusal token from code (e.g.
   `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`) gets a row.
6. **No-claim audit.** Confirm no surface advertises a forbidden claim
   (safe, seaworthy, validated, calibrated, final prediction, design
   fitness) for the new concept; add a forbidden-copy test if needed
   (`tests/test_desktop_layout.py`, `tests/test_web_read_models.py`).
