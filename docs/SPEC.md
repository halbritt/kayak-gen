# SPEC

## Why this file exists

`SPEC.md` is the implementation contract for the project. It records what the
project does, what state it owns, what it deliberately does not model, and
the invariants the codebase enforces. Together with `docs/PRD.md`, it forms
the boundary contract that `docs/DECISION_LOG.md` rows cite.

`docs/DDD.md` is one level up: why the SPEC looks the way it does.
`docs/UBIQUITOUS_LANGUAGE.md` is the glossary.

## What the project does

Given a single Pydantic `Hull` record, kayakgen produces:

- **Geometry**: parametric loft, open hull/deck STL surfaces, optional
  generated closed body.
- **Hydrostatics**: displaced volume, displaced mass, wetted-surface area,
  waterplane area, longitudinal centre of buoyancy, primary metacentric
  height GM₀.
- **Stability**: load-case-aware upright trim equilibrium; opt-in
  high-angle GZ as `unvalidated_hydrostatic_comparison`.
- **Resistance**: raw ITTC-57 friction + Michell thin-ship wave components;
  claim state `uncalibrated_comparative`.
- **Mesh diagnostics**: per-part edge/face/topology checks; readiness
  classification (`cfd_surface_candidate`, `closed_volume`, `cfd_ready`).
- **Mesh packages**: deterministic manifest + STL surfaces; optional
  `--bind-evidence` flag to attach a `SnappyHexMeshEvidence` record (D026).
- **CFD dispatch**: local job records with multiple profiles; opt-in
  real OpenFOAM-v2512 execution (D012 + D027) producing
  `raw_unvalidated` raw forces.
- **Sweeps**: deterministic grid expansion with `pending` lifecycle,
  per-candidate records, optional STL and high-angle-GZ artifacts.
- **Active search**: opt-in NSGA-II (v1, D024) and EHVI (v2, D028); both
  claim-admissibility-gated.
- **Comparison**: Pareto frontier with display-only high-angle-GZ rows.
- **Web frontend**: Trame workspace for design inspection + comparison
  loading; local-only by default (D023 defers public hosted demo).
- **Desktop GUI**: PyQt6 + matplotlib + PyVista; sliders, 3D preview,
  STL export, status segments including the RFC 0043 stage-4 CLI-only
  high-angle GZ pointer.

The complete CLI surface and durable artifact catalogue lives in
`docs/ARCHITECTURE_MAP.md`.

## State the project owns

The project considers durable:

| Location | Contents |
| --- | --- |
| `<operator-path>/<name>.json` | `Hull` records, hand-edited or `kayakgen init`-produced. |
| `<out>.eval.json` | `EvaluationResult` records from `kayakgen evaluate`. |
| `<out>.stability.json` | `StabilityResult` records (with optional `high_angle_gz` block). |
| `<package-dir>/` | `MeshPackageManifest`, per-part STL, mesh-quality reports. |
| `<evidence-dir>/evidence.json` + `polyMesh/` | `SnappyHexMeshEvidence` + raw OpenFOAM polyMesh artifacts produced by `kayakgen mesh-evidence` (D026). |
| `<cfd-job>/` | `profile.json`, `job.json`, `run.json`, optional `raw-result.json`, optional `postProcessing/forces/<t>/force.dat`. |
| `<sweep-run>/` | `spec.json`, `run.json`, `summary.csv`, `failures.jsonl`, `candidates/<key>/...`. |
| `<search-run>/` | Same shape as sweep, plus a `search_metadata` block. |
| `<compare.json>` | `ComparisonReport` (with optional `pairwise_notes` advisory block per RFC 0052). |
| `<run-dir>/_store/` | Hard-link content-addressed mirror of every artifact written through `FilesystemArtifactStore` (RFC 0049 / D030). Mirror is additive; canonical paths and bytes stay byte-stable. |
| `~/.local/share/kayakgen/index.sqlite` (override `KAYAKGEN_INDEX_DB`) | RFC 0049 / D030 cross-run index. Tables: `runs`, `candidates`, `metrics`, `artifacts`, `events`. Auto-created on first write. |
| `<target-out>.json` | `StabilityResult` from `kayakgen target-draft` / `target-trim`, or `TargetDraftMismatchReport` from `target-draft --report-only` (RFC 0050 / D031). |
| `<build-export-dir>/` | `offsets.csv`, `sections.dxf`, `sheer.svg`, `keel.svg`, `waterline.svg`, `deck_centreline.svg`, `station_molds.dxf`, plus a `manifest.json` (RFC 0051 / D032). |
| `<sensitivity-out>.json` | `SensitivityResult` from `kayakgen sensitivity` (RFC 0052 / D033). |
| `<calibration-out>/` | `TankTestCampaign` / `IncliningTestCampaign` / `AcceptedFitRecord` JSON + optional residual-plot SVG (RFC 0054 / D035). Promotion to `calibration_fixture` requires an `AcceptedFitRecord` on disk. |
| `<report.html>` (+ optional `report.pdf`) | Self-contained design report (RFC 0055 / D036; jinja2-rendered with embedded base64 PNG preview; weasyprint-rendered PDF when `kayakgen[report]` extras are installed). |
| `~/.config/kayakgen/cfd.json` | `KayakgenCfdConfig` persistent opt-in settings (D027). |
| `KAYAKGEN_WEB_CFD_JOBS_ROOT` or default `.kayakgen-web-cfd-jobs/` | Web-served CFD job directories. |
| `tests/fixtures/calibration/edinburgh/` | Vendored CC BY 4.0 validation fixture (D018 acquisition; D025 promoted to validation_fixture). |
| `tests/fixtures/openfoam_v2512/` | Force.dat parser fixtures (D012). |
| `kayakgen/eval/cfd/openfoam_v2512_interfoam/templates/` | Vendored case dicts. |
| `tests/fixtures/research_references/` | Read-only research-grade fixtures (Mendeley sailboat). |
| `docs/research/aalborg_kayak_phd.pdf` | Research reference document. |

Anything not listed here is not part of the project's bounded context.

## What the project does NOT model

- **Validated CFD output.** All CFD records are `raw_unvalidated` or
  `solver_success_blocked` or `solver_unavailable`.
- **Calibrated resistance.** Until an accepted-fit workflow lands (D006),
  resistance stays `uncalibrated_comparative`.
- **Measured high-angle GZ.** No measured kayak GZ-vs-heel data exists
  publicly (research finding 2026-05-16); RFC 0043 output stays
  `unvalidated_hydrostatic_comparison`.
- **Production solid hull assembly.** Joining, detailing, thickening,
  bulkheads are CAD operations left to the user.
- **Structural / scantling design.** Wall thicknesses, layup schedules,
  rib placement are out of scope.
- **Outfitting.** Cockpit ergonomics, hatches, seats, rudders, foot
  braces are out of scope.
- **Non-kayak hull forms.** Catamarans, sailing keels, planing hulls,
  cargo vessels are out of scope.
- **Hosted public demo.** D023 defers indefinitely; only local `kayakgen
  serve` and the repo Docker path are supported.
- **Hosted CFD workers, queues, accounts, quotas.** Local dispatch only.
- **Safety, seaworthiness, capsize-range claims.** No surface may
  advertise these; regression-pinned in
  `tests/test_desktop_layout.py` and the web read-model tests.
- **Final design fitness, calibrated prediction wording.** Refused
  alongside the above.

## Invariants

Enforced by Pydantic model validators and regression tests.

- **Hull validity.** Dimensions positive; `Cp`/`Cm` in canonical bands;
  `bow_rake`/`stern_rake` in `[0, 1]`; class preset bounds honored.
- **Claim states never advance silently.** Transitions require a
  documented decision; see RFC 0027 acceptance gates,
  `_validate_calibration_fixture_metadata`, the validator chain in
  `ResistanceSourceReviewPacket._review_verdict_controls_promotion_metadata`,
  and the RFC 0043 / RFC 0044 admissibility gates.
- **CFD case-template lock.** `CfdOpenFoamRawResult.case_template_version`
  is Literal-locked to `"openfoam-v2512-interfoam-dtchull-v1"`; tampering
  fails Pydantic validation.
- **Raw-unvalidated invariant.** Every real OpenFOAM-produced record has
  `claim_state="raw_unvalidated"` and empty `accepted_uses`.
- **OpenFOAM v2512 provenance.** `OpenFoamProvenanceProbe.matches_required`
  refuses env-only evidence; application/build/API evidence is required.
- **Ordinary mesh packages stay below `cfd_ready`** unless explicitly
  bound to passing volume-mesh evidence (RFC 0023 fixture or RFC 0045
  generated path with the three-hash gate from D026).
- **High-angle GZ display-only.** `max_gz_m`, `heel_at_max_gz_deg`,
  `range_positive_stability_deg` are refused as Pareto/search objectives
  via the RFC 0043 token.
- **Active search admissibility.** `raw_unvalidated` and
  `uncalibrated_comparative` objectives are refused unless
  `objectives_explicit_exploratory: true` is set (RFC 0044 token).
- **Validation fixture caveats.** D025 admits exactly two named
  exceptions: `non_promotion_reasons` may describe calibration-fixture
  blockers, and `uncertainty.status="incomplete"` is admitted when
  `uncertainty_notes` is bound AND `warnings` contains
  `uncertainty_documented_caveat`. Both tokens are referenceable
  constants.
- **Pending candidate visibility.** Pending rows appear in
  `summary.csv` + the comparison report but are frontier-ineligible.
- **Constraint failures.** `constraint_failed` rows in active search are
  frontier-ineligible; the failing metric, bound, and actual value are
  recorded.
- **Seed determinism.** A seeded sweep, NSGA-II, or EHVI run produces
  byte-identical `candidates/<key>/record.json` across two independent
  invocations.
- **Hash-bound evidence.** D026 refuses promotion with three structured
  codes (`closed_body_hash_mismatch`, `snappy_evidence_body_mismatch`,
  `polymesh_artifact_drift`) plus two state codes
  (`evidence_not_recorded`, `evidence_translation_failed`).
- **Dependency direction.** Enforced by
  `tests/test_import_boundaries.py`:
  - `kayakgen.model` imports nothing from `eval`, `search`, `ui`, `cli`.
  - `kayakgen.eval` imports nothing from `ui`, `cli`.
  - `kayakgen.search` imports nothing from `ui`, `cli`.
  - CLI/UI must not reach into private (underscore-prefixed) evaluator
    helpers.
- **Vocabulary coverage.** Every `ClaimState`, `SourceUse`,
  `SourceReviewVerdict`, readiness literal, and named decision token
  referenced from code is documented in
  `docs/UBIQUITOUS_LANGUAGE.md` (enforced by
  `tests/test_vocabulary_coverage.py`).
- **Forbidden-copy refusal.** No surface advertises `safe`, `seaworthy`,
  `validated`, `calibrated`, `final prediction`, or `design fitness` —
  regression-pinned in `tests/test_desktop_layout.py` (desktop status),
  `tests/test_web_read_models.py` (Trame web HTML), and
  `tests/test_design_report.py` (RFC 0055 HTML render via
  `FORBIDDEN_COPY_TOKENS` + `FORBIDDEN_COPY_SCRUB_TOKENS` named
  constants; the renderer raises `ReportForbiddenCopyError` rather
  than write a non-clean report).
- **Hull identity (RFC 0049 / D030).** `Hull.hash()` is an alias for
  `Hull.record_hash()` and is byte-stable for every existing hull.
  `Hull.design_hash()` is invariant under rename, class-preset
  changes, and JSON-key-order changes; it differs whenever any
  physical input changes (length / beams / draft / form coefficients
  / rake / rocker / `LCB_frac` / `geometry_kind`).
- **Geometry-V2 admissibility (RFC 0048 / D029).** When
  `geometry_kind="distribution_v2"`, the `Hull` validator requires a
  `DistributionV2Spec` and refuses non-default `bow_rake` /
  `stern_rake`. Hydrostatics computes both section-integration and
  triangle-integration totals and emits an advisory note on
  `Hydrostatics.notes` + an optional
  `Hydrostatics.v2_cross_check` block when drift exceeds 1% (volume
  / Aw / LCB) or 0.5% (GM0). The check never raises.
- **Calibration_fixture promotion (RFC 0054 / D035).**
  `ResistanceSourceReviewPacket._validate_accepted_fit_ref_on_disk`
  resolves a `.json`-pathed `accepted_fit_ref` to an
  `AcceptedFitRecord` and refuses promotion if the file is missing
  (`accepted_fit_unresolved`), unparseable (`accepted_fit_unparseable`),
  or below the recorded threshold (`fit_above_rmse_threshold`,
  `fit_above_mape_threshold`, `fit_below_r2_threshold`). Opaque
  (non-`.json`) refs continue to satisfy the D006 token only — they
  do not bypass the validator chain.
- **Display-only objective refusal (RFC 0053 / D034).** All four
  `turning.*` metrics + the three `high_angle_gz.*` summary metrics
  are registered with `role="display_only"` and refused as
  Pareto/search objectives via
  `ensure_objectives_claim_admissible_for_search` + the RFC 0043
  token.
- **Pairwise within-evaluator-noise advisory (RFC 0052 / D033).**
  `ComparisonReport.pairwise_notes` flags Pareto-front pairs whose
  default-objective metrics differ by less than the registry's
  per-metric `within_evaluator_noise_threshold`. Frontier eligibility
  is unchanged; the flag is informational.

## Schemas

Canonical Pydantic schemas with `ConfigDict(extra="forbid")` and pinned
`schema_version` literals. See `docs/ARCHITECTURE_MAP.md` for the full
list; the load-bearing groups:

- **Geometry**: `Hull`, `HullGeometry`-derived loft (not persisted).
- **Closed volume + mesh evidence**: `ClosedVolumeBody`,
  `ClosedVolumeDiagnostics`, `ClosedVolumeReadiness`,
  `ClosedVolumeSolverReadinessReport`, `MeshPackageManifest`,
  `VolumeMeshDiagnostic`, `SnappyHexMeshEvidence`, `CheckMeshSummary`.
- **CFD**: `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`,
  `SolverExecutionAudit`, `CfdOpenFoamRawResult`,
  `CfdOpenFoamForceDatResult`, `CfdOpenFoamForceDatSample`,
  `OpenFoamProvenanceProbe`, `KayakgenCfdConfig`.
- **Evaluation**: `EvaluationResult`, `StabilityResult`, `GZCurve`,
  `GeneratedBodyGZCurve`, `LoadCase`, `ResistanceCurve`.
- **Calibration**: `ResistanceSourceRecord`,
  `ResistanceSourceReviewPacket`, `ResistanceSourceReviewEvidence`.
- **Sweep + search**: `SweepSpec`, `CandidateRecord`,
  `EvaluatorOptions`, `StlArtifactSet`, `HighAngleGzArtifact`,
  `SearchSpec`, `SearchAlgorithmSpec` (Nsga2 | Ehvi),
  `SearchMetadata`, `SearchConstraint`, `SearchBudget`, `SearchLimits`.
- **Comparison + web**: `ComparisonReport`, `CandidateSummary`,
  `HighAngleGzDisplay`, `PairwiseNote`, `WebStateSchema`,
  `WebHighAngleGzRows`.
- **Identity + persistence (RFC 0049)**: `ArtifactRef`, `ArtifactKind`,
  `RunEvent`; identity hashes are pure SHA-256 strings, not records.
- **Geometry V2 (RFC 0048)**: `DistributionV2Spec`,
  `LongitudinalDistribution` union (`UniformDistribution`,
  `PolynomialDistribution`, `KeyPointsDistribution`),
  `CrossSectionFamily`, `V2HydrostaticCrossCheck`.
- **Target workflows (RFC 0050)**: `TargetDraftMismatchReport`.
- **Builder exports (RFC 0051)**: `BuildExportSpec`; the seven
  artifact files have no Pydantic schema (CSV / DXF / SVG bytes).
- **Sensitivity (RFC 0052)**: `SensitivityRequest`,
  `SensitivityResult`, `ConvergenceFlag`.
- **Turning (RFC 0053)**: `TurningMetrics`.
- **Calibration campaigns (RFC 0054)**: `RightsChecklist`,
  `GeometryReference`, `TankTestRun`, `TankTestCampaign`,
  `IncliningTestRun`, `IncliningTestCampaign`, `AcceptedFitRecord`.
- **Design report (RFC 0055)**: `DesignReportRequest`,
  `DesignReportResult`.
- **CFD stages (Phase 7)**: `CfdRunStage`.

## Initialization

`kayakgen init <out>` writes a default `Hull` JSON. The file is the seed
input for everything else; modify by hand or with another tool and pass
the path to subsequent commands.

There is no project-wide on-disk init beyond this. The persistent operator
setting at `~/.config/kayakgen/cfd.json` is optional and only consulted
by the RFC 0046 opt-in resolver; absence is equivalent to an empty
config.

## Command/write surface

Every persistent mutation flows through one of these:

- `kayakgen init`
- `kayakgen generate`
- `kayakgen evaluate`
- `kayakgen mesh-check`
- `kayakgen mesh-package` (with optional `--bind-evidence` flag)
- `kayakgen mesh-evidence`
- `kayakgen stability` (with optional `--high-angle-gz`/`--heel-grid-deg`)
- `kayakgen sweep` (with optional `--resume`)
- `kayakgen search` (with optional `--resume`)
- `kayakgen compare`
- `kayakgen cfd prepare` (with optional `--allow-real-solver-execution`)
- `kayakgen cfd run`
- `kayakgen cfd status`
- `kayakgen target-draft` (with optional `--report-only --draft N`)
- `kayakgen target-trim`
- `kayakgen migrate-geometry` (writes `<name>.v2.json` sibling)
- `kayakgen build-export` (requires `kayakgen[builder]`)
- `kayakgen sensitivity`
- `kayakgen design-report` (with optional `--pdf` requiring
  `kayakgen[report]` + weasyprint, and optional `--from-run`)
- `kayakgen runs list / query / reindex` (cross-run index)
- `kayakgen calibration ingest-tank-test / ingest-inclining-test /
  accept-fit / residual-plot` (RFC 0054)

`kayakgen view` and `kayakgen serve` open read-and-edit surfaces over the
same evaluators. The web frontend's `/api/cfd/*` routes are the
network analog of the CLI `cfd` subcommands and respect the same opt-in
resolver.

## No-claim boundaries

Preserved verbatim from `docs/ROADMAP.md` and `docs/PRD.md`. Future
SPEC changes must respect these:

- Resistance output is `uncalibrated_comparative`, not a calibrated
  model, final prediction, design-fitness signal, or default
  optimization objective.
- CFD output is local dispatch state, `raw_unvalidated` real output,
  `fixture_only` records, or explicit unavailable/failed state.
- Ordinary mesh packages stay below `cfd_ready` unless explicitly
  bound to passing volume-mesh evidence.
- High-angle GZ surfaces stay `unvalidated_hydrostatic_comparison`;
  the values are not safety, seaworthiness, capsize, validation,
  design-fitness, or solver-readiness claims.
- Class validity / advisory badges are not proof of seaworthiness,
  calibrated performance, or final design fitness.
- The web frontend stays local-only; D023 defers public hosted demo.
