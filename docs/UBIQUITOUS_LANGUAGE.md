# UBIQUITOUS LANGUAGE

## Why this file exists

This is the project's domain glossary. Every term here is *load-bearing*: the
codebase, error messages, claim states, readiness gates, and CHANGELOG entries
are expected to use these terms exactly. Drift between code and glossary is a
bug, not a stylistic choice.

A new concept added to the project should land in this glossary *first*, with
a name future contributors can use without ambiguity. New flags, fields, and
schemas land second.

Renaming a term is a `docs/DECISION_LOG.md` row, not an inline edit.

A regression test (`tests/test_vocabulary_coverage.py`) checks that every
claim/readiness/source-use literal exposed in code is documented here.

## Geometry

| Term | Definition |
| --- | --- |
| **Hull** | A `kayakgen.model.hull.Hull` Pydantic record. Owns dimensions (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`), form coefficients (`Cp`, `Cm`, `deck_flatness`, `center_box_ratio`), end shape (`bow_rake`, `stern_rake`, `rocker_bow_m`, `rocker_stern_m`), reserved future controls (`LCB_frac`), geometry selection (`geometry_kind`, optional `distribution_v2`), optional `hull_class`, and optional `name`. The single durable input for everything downstream; serializable; hashable via `Hull.hash()`. |
| **HullGeometry** | The lofted surface that a `Hull` produces via `Hull.to_geometry()`. Owns longitudinal stations, half-breadths, deck profile, and the open hull/deck triangulations. Not durable on its own; recomputed on demand. |
| **Generated Closed Body** | `kayakgen/eval/generated_closed_body.py:generated_hull_plus_deck_closed_body(hull)` returns a `ClosedVolumeBody` of `body_type="generated_hull_plus_deck_closed_body"` with parts joined at the waterline, exact plumb-stem closure when `bow_rake==0` or `stern_rake==0`, and a `source_hull_hash` binding it back to the input hull. Profile literal `generated_hull_plus_deck_closed_body_v1`. The only closed body usable for evidence-bound CFD readiness or high-angle GZ. |
| **geometry_kind** | The `Hull.geometry_kind` literal selecting the geometry strategy: `"lofted"` (today's parametric loft, the default) or `"distribution_v2"` (RFC 0048 explicit-distribution model). `Hull.to_geometry()` dispatches on this literal. When `geometry_kind == "distribution_v2"` the hull must carry a `DistributionV2Spec` and `bow_rake` / `stern_rake` must be at their default values; non-default rake is refused with a structured `ValueError` on construction. |
| **DistributionV2Spec** | `kayakgen.model.distribution_v2.DistributionV2Spec` — the RFC 0048 value object owned by `Hull.distribution_v2`. Carries the explicit longitudinal distributions (`waterline_half_breadth`, `draft_profile`, `section_area_curve`, `deck_freeboard`, `rocker`), the legacy scalar end-rocker fields, `lcb_target_frac` / `max_beam_position_frac`, a `cross_section_family` literal, scalar-or-distribution `deadrise_deg` / `chine_radius_m`, a `bow_flare_deg` scalar, and a `multi_chine_count` parameter (range 2-4, default 2). |
| **LongitudinalDistribution** | The `kayakgen.model.distribution_v2.LongitudinalDistribution` discriminated union of `UniformDistribution`, `PolynomialDistribution`, and `KeyPointsDistribution` (cubic-spline interpolated knots). Every distribution samples in the normalized longitudinal coordinate `xi ∈ [-1, 1]` (bow at -1, stern at +1). |
| **CrossSectionFamily** | The `kayakgen.model.distribution_v2.CrossSectionFamily` literal: `round` / `shallow_arch` / `shallow_v` / `deep_v` / `hard_chine` / `multi_chine`. Selects the per-station section sampler the `DistributionV2Geometry` consults; `multi_chine` parametrizes its facet count via `DistributionV2Spec.multi_chine_count`. |
| **DistributionV2Geometry** | `kayakgen.model.geometry.DistributionV2Geometry` — the V2 successor implementation of `HullGeometry`. Builds one canonical closed-body section ring per station from the `DistributionV2Spec`; both `section_for_closed_body(x, part)` (canonical) and `section(x, part)` (open inspection surface derived from the canonical body) return the same per-station ring so the closed-body diagnostics chain (RFC 0021 + RFC 0023 + RFC 0040 + RFC 0045) needs no separate code path. The RFC 0048 hydrostatic cross-check compares its section-integrated hydrostatics against triangle integration over the canonical closed body and emits advisory notes on `Hydrostatics.notes` when drift exceeds the configured tolerance (1.0 % displaced volume / 1.0 % waterplane area / 1.0 % LCB / 0.5 % GM0). |
| **BuildExportSpec** | `kayakgen.services.build_export.BuildExportSpec` — per-invocation options for `kayakgen build-export` (RFC 0051). Today only carries `n_stations` (default 32) controlling how many evenly-spaced section cuts the writers sample between bow and stern. Default scale is 1:1 mm in the DXF/SVG modelspace. |
| **Build Export Artifact Kind** | One of `offsets_csv`, `sections_dxf`, `sheer_svg`, `keel_svg`, `waterline_svg`, `deck_centreline_svg`, `station_molds_dxf` (RFC 0051). Every artifact carries a header comment with the hull SHA-256 (`Hull.hash()`, later `Hull.record_hash()`) and the kayakgen version pin. `kayakgen build-export` writes the seven artifacts plus a `manifest.json` (`artifact_set: rfc_0051_build_export`) enumerating each with `sha256` + `bytes`. |

## Evaluation and mesh

| Term | Definition |
| --- | --- |
| **Mesh Package** | A directory written by `kayakgen mesh-package` containing `manifest.json`, the original `Hull` JSON, per-part STLs, mesh-quality reports, and a `MeshPackageManifest` that names the solver profile and readiness level. Profile literals: `open_wetted_surface_resistance_v1`, `watertight_solid_resistance_v1`. |
| **Volume Mesh Diagnostic** | `kayakgen.eval.volume_mesh.VolumeMeshDiagnostic` carries the body-ref hash, polyMesh artifact checksums, patch metadata, and an `OpenFoamProvenanceProbe`. Only a fully-bound diagnostic that matches the manifest's body hash can promote a mesh package to `cfd_ready`. Produced by RFC 0023 fixture handoff OR by the RFC 0045 `mesh-evidence` + `--bind-evidence` path. |
| **SnappyHexMeshEvidence** | `kayakgen.eval.snappy_hex_mesh.SnappyHexMeshEvidence`: case-template version, body-ref hash, dictionary hashes (`controlDict`, `snappyHexMeshDict`, `meshQualityDict`, `surfaceFeatureExtractDict`, `blockMeshDict`), patch metadata, `CheckMeshSummary`, polyMesh artifact checksums, `OpenFoamProvenanceProbe`, `dispatch_state ∈ {pending_evidence, fixture_only, evidence_recorded, evidence_rejected}`. Translates to a `VolumeMeshDiagnostic` via `snappy_hex_mesh_volume_mesh_diagnostic`. |
| **CheckMeshSummary** | Parsed output of `checkMesh`: passed flag, cell/face counts, max non-orthogonality, max skewness, max aspect ratio, warnings. |

## CFD job lifecycle

| Term | Definition |
| --- | --- |
| **Solver Profile** | A `kayakgen.eval.cfd.jobs.SolverProfile` declaring the solver name, version, case-template version (Literal-locked), required mesh profile, required readiness, and adapter kind. Public profile names today: `unavailable-open-wetted-surface`, `unavailable-watertight-solid`, `mock-failing-local-command`, `fixture-local-command`, `openfoam-v2512-interfoam-local`. |
| **CFD Job** | A prepared, on-disk directory containing `profile.json`, `job.json`, `run.json`. Written by `kayakgen cfd prepare`. |
| **CfdRunRecord** | The terminal record for a CFD job. Carries status (`queued` / `running` / `succeeded` / `failed` / `unavailable`), error_kind (e.g. `solver_success_blocked` or `solver_unavailable`), claim_state, accepted_uses, optional raw output reference, and (RFC 0046) optional `real_solver_execution_opt_in` + `SolverExecutionAudit`. |
| **CfdOpenFoamRawResult** | Output of a successful real OpenFOAM run. Pydantic Literal pins `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`, `claim_state="raw_unvalidated"`, empty `accepted_uses`. |
| **OpenFoamProvenanceProbe** | Records `interFoam -help` / `foamVersion -build|-api|<bare>` outputs plus `$WM_PROJECT_VERSION`. `matches_required("v2512")` accepts evidence from application/build/API channels; explicitly refuses env-only evidence. |
| **SolverExecutionAudit** | Audit record on a `succeeded` `CfdRunRecord`: bashrc path, provenance summary, locked case-template version, meshing seconds, solve seconds. |

## Claim and source vocabulary

| Term | Definition |
| --- | --- |
| **Claim State** | The truthful interpretation of a numeric evaluator output. The full `kayakgen.eval.claims.ClaimState` literal union is `raw_unvalidated`, `uncalibrated_comparative`, `validation_fixture`, `calibration_fixture_candidate`, `calibration_fixture`, `calibrated_model`, `validated_design_fitness`. `fixture_only` is a separate fixture-record marker (not in the literal union) used for synthetic math that is never a user-facing claim. `unvalidated_hydrostatic_comparison` is a separate high-angle GZ marker on `GeneratedBodyGZCurve`. Claim states never advance silently; a transition requires a documented decision (D006/D012/D014/D025/...). Today no record carries `calibrated_model` or `validated_design_fitness`; those are reserved for future accepted-fit / accepted-validation workflows. |
| **Accepted Use** | A use case the project explicitly admits a number for. Today: `["validation_only"]` on Edinburgh; `[]` on every raw or uncalibrated record. Use cases NOT admitted: calibrated prediction, final design fitness, safety/seaworthiness, validated CFD. |
| **Source Use** | `kayakgen.eval.calibration.SourceUse` — runtime label on a measured source: `citation_only` / `validation_candidate` / `validation_fixture` / `calibration_fixture_candidate` / `calibration_fixture`. `rejected` is a review-only verdict, never a runtime use. |
| **Calibration Fixture** | An accepted measured source bound to a hull-envelope, an accepted-fit workflow record, a validity envelope, and immutable fit metadata. D006 requires the accepted-fit gate; no current source satisfies it. Edinburgh is capped at `validation_fixture` per D013. |
| **Validation Fixture** | A measured source whose row schema is reproducible (`source_checksum_sha256` + `extraction_script_ref` bound, fixture metadata accepted). Per D025 may carry calibration-blocker `non_promotion_reasons` and a documented uncertainty caveat. Edinburgh is the only one today. |
| **Documented Uncertainty Caveat** | Per D025: `validation_fixture` admits `uncertainty.status == "incomplete"` IF `uncertainty_notes` is bound AND `warnings` includes the literal `uncertainty_documented_caveat`. Used when a source publishes averaged rows without per-row repeatability (Edinburgh case). |
| **TankTestCampaign** | `kayakgen.eval.calibration.campaigns.TankTestCampaign` — aggregate root for a commissioned towing-tank drag campaign per RFC 0054. Owns a `RightsChecklist`, a `GeometryReference` (hull binding by `hull_design_hash` per RFC 0049 vocabulary), an `uncertainty_method` literal (`Type_A_repeatability`, `Type_B_uncertainty_budget`, `documented_caveat`), and a list of `TankTestRun` rows. CSV ingest lives in the same module; CLI surface is `kayakgen calibration ingest-tank-test`. |
| **IncliningTestRun** | `kayakgen.eval.calibration.campaigns.IncliningTestRun` — one operating-point row of a commissioned inclining-experiment campaign per RFC 0054. Carries heel angle, applied moment (with optional uncertainty), sealed-body / cockpit-flooded booleans, and a `paddler_state` literal (`absent`, `rigid_manikin`, `active_paddler`). Aggregated into `IncliningTestCampaign`. |
| **AcceptedFitRecord** | `kayakgen.eval.calibration.campaigns.AcceptedFitRecord` — immutable acceptance record for a calibration fit, gating promotion of a `ResistanceSourceReviewPacket` to `calibration_fixture` per D006 and RFC 0054. Pins `fit_id`, an immutable `model_version`, a `fit_metric` literal (`RMSE`, `MAPE`, `R2`), the fit value, a holdout RMS baseline, residuals, a validity envelope, and an accept-by/accept-at audit pair. CLI surface is `kayakgen calibration accept-fit`; the validator strict-resolves a `.json` `accepted_fit_ref` on disk. |
| **MeasuredStabilityFixture** | RFC 0056 measured-stability fixture record under `kayakgen.eval.stability.measured_fixture.MeasuredStabilityFixture`. Pins the per-row `(heel_deg, gz_m)` data from a strain-gauged moment-arm rig run, the rig's calibration evidence, the free-equilibrium evidence, and the rig-design match flag. Schema-only today; no fixture is promoted until stage 4 of RFC 0058 lands D007 / D014 physical rig data. |
| **StabilityFitRecord** | RFC 0058 immutable candidate-or-accepted stability fit at `kayakgen.eval.stability.accepted_fit.StabilityFitRecord`. Binds an `analytical_evaluator_version`, a `HullFamilyScope` (`hull_class` + `design_hash_envelope`), a `valid_heel_range_deg` tuple, one or more `FixtureRef`s, `StabilityFitMetrics` (`rmse_m`, `mape_fraction`, `max_error_m`, `coverage_fraction`), an `acceptance_verdict`, and a `ReviewerSignature`. Default-strict thresholds (`rmse_m <= 0.005`, `mape_fraction <= 0.05`, `max_error_m <= 0.01`, `coverage_fraction >= 0.9`) refuse out-of-band fits unless `strict=false`. CLI surface is `kayakgen stability accept-fit`. |
| **StabilityFixturePromotionPacket** | RFC 0058 review packet at `kayakgen.eval.stability.accepted_fit.StabilityFixturePromotionPacket`. Pins five verdicts (`rights_review`, `hull_identity_review`, `calibration_drift_review`, `hysteresis_review`, `free_equilibrium_review`), `rig_design_match`, and a `promotion_target` literal (`measured_stability_fixture` / `validation_candidate` / `rejected`). The `measured_stability_fixture` target requires every verdict accepted + `rig_design_match=true` + empty rejection reasons. CLI surface is `kayakgen stability promote-fixture`. |
| **AnalyticalClaimLabel** | RFC 0058 stage-2 label resolved by `kayakgen.eval.stability.high_angle_contracts.resolve_analytical_claim_label(hull, fit_registry)`. Literal `Literal["unvalidated_hydrostatic_comparison", "validated_hydrostatic_comparison"]`. Returns the validated label only when an accepted `StabilityFitRecord` in the registry covers the hull's `(hull_class, design_hash)` envelope; defaults to the unvalidated label. Currently called everywhere with an empty `fit_registry=()` per D039, so the validated label is unreachable until stage 4 promotes the first fixture. |
| **cfd_in_loop_evaluator_status** | RFC 0058 stage-2 helper at `kayakgen.services.generative_jobs.cfd_in_loop_evaluator_status(registry, hull_scope)`. Returns `Literal["opt_in_only", "first_class"]`. Defaults to `opt_in_only`; a `first_class` graduation requires both an accepted analytical-stability fit and an accepted CFD-in-loop fit in the registry. A persistent operator opt-out always wins. The Generate-panel form-builder consults this helper to decide whether the CFD-in-loop acknowledgement is required before submission. |

## Sweep, search, and comparison

| Term | Definition |
| --- | --- |
| **EvaluationResult** | `kayakgen.eval.contract.EvaluationResult` — the canonical output of `kayakgen evaluate`. Combines hydrostatics, optional resistance curve, optional stability result, optional mesh diagnostics, and design-validity metadata. Carries the additive RFC 0052 `convergence: list[ConvergenceFlag]` field that auto-populates from the present evaluator outputs (hydrostatics, resistance, upright/trim equilibrium, per-heel GZ) when not supplied explicitly. |
| **ConvergenceFlag** | RFC 0052 value object `kayakgen.eval.contract.ConvergenceFlag(stage: str, status: Literal["converged","not_converged","iteration_cap"], residual: float | None)`. Emitted additively on `EvaluationResult.convergence` — one entry per evaluator stage (e.g. `"upright_equilibrium"`, `"trim_equilibrium"`, `"evaluate_gz_curve@10deg"`, `"hydrostatics"`, `"resistance"`). `residual` is the numeric driver of the check when one exists (`displacement_error_kg`, `moment_error_kg_m`, per-heel `displacement_residual_kg`), `None` for non-iterating stages. |
| **SensitivityResult** | RFC 0052 read model `kayakgen.services.sensitivity.SensitivityResult`: `hull_record_hash`, `step_per_param`, `metric_baseline`, `metric_partials` (keyed by metric, inner key is param), and `non_finite_partials: list[tuple[str, str, str]]`. Produced by `compute_sensitivity(hull, metrics=..., params=..., step=...)` as a *local* finite-difference Jacobian. Auto-step is `1e-4 * baseline_value` per parameter, clamped to `[1e-9, 1e-2]`. Surfaced by `kayakgen sensitivity <hull.json> --metric ... --param ... [--step S] --out OUT`. Explicitly local — not a calibration or validation claim. |
| **within_evaluator_noise_threshold** | Additive `ObjectiveMetadata` field (RFC 0052). Per-metric tolerance read by the comparison report when assembling `pairwise_notes`. Defaults today: `GM0_m` = 0.001 m, `displacement_error_kg` = 0.5 kg, `mesh_problem_count` = 1. `None` opts the metric out of the noise advisory. Tightening the registry is additive: existing comparison records remain valid. |
| **CandidateRecord** | One row in a sweep or search run, written to `candidates/<key>/record.json`. Carries status (`complete` / `failed` / `pending` / `skipped` / `constraint_failed`), summary metrics, optional artifact references (`stl_artifacts`, `high_angle_gz_artifact`), and the spec-resolved hull. |
| **SweepRun** | The output of `kayakgen sweep`: a directory containing `spec.json`, `run.json`, `summary.csv`, `failures.jsonl`, and `candidates/<key>/`. Deterministic JSON grid expansion; supports `--resume`. |
| **SearchRun** | The output of `kayakgen search`: same directory shape as `SweepRun`, with `run.json` additionally carrying a `search_metadata` block (algorithm kind, seed, objectives, constraints, realized budget, termination reason, per-generation history). |
| **Pending Candidate** | A `CandidateRecord` with `status == "pending"` representing queued-but-unrun work. Per RFC 0009 + D016 these are visible in `summary.csv` and the comparison report but stay frontier-ineligible. Resume replays pending records first. |
| **HighAngleGzDisplay** | A display-only read-model row in a `ComparisonReport`: body/load/trim provenance, summary metrics (`max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`), warnings, assumptions, optional `unavailable_reason`. High-angle GZ metrics are refused as Pareto/search objectives (token `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`). |
| **TurningMetrics** | RFC 0053 `kayakgen.eval.turning.TurningMetrics`: opt-in geometric-proxy block attached additively to `EvaluationResult` and to sweep candidate summaries. Carries `heel_deg`, `edged_waterline_length_m`, `upright_waterline_length_m`, `lateral_plane_shift_m`, `rocker_weighted_maneuverability_signal`, and a `method="geometric_proxy_v1"` literal. The four numeric metrics are registered as `display_only` in `OBJECTIVE_METADATA` (`turning.edged_waterline_length_m`, `turning.upright_waterline_length_m`, `turning.lateral_plane_shift_m`, `turning.rocker_weighted_maneuverability_signal`) so they surface as `summary.csv` columns but are refused as Pareto/search objectives by the existing admissibility gate. Activated by `kayakgen evaluate --turning [--turning-heel-deg N]` and by `evaluators.turning_metrics: true` on a `SweepSpec` (with `evaluators.turning_metrics_heel_deg` default `8.0`). |
| **TargetDraftMismatchReport** | `kayakgen.services.evaluation.TargetDraftMismatchReport` — RFC 0050 read model returned by `target_draft_load_mismatch(hull, draft_m, load_case)` and by `kayakgen target-draft --report-only`. Carries `hull_record_hash`, `assumed_draft_m`, `expected_displaced_mass_kg`, `actual_displaced_mass_kg`, signed `mismatch_kg` and `mismatch_percent`, and structured `notes`. Reports the displacement gap for a fixed draft against a load case without solving equilibrium. |
| **Objective Admissibility** | Two gates that govern which metrics may be Pareto/search objectives: `ensure_objectives_not_high_angle_gz` (RFC 0043 token) and `ensure_objectives_claim_admissible_for_search` (RFC 0044 token `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`). The latter refuses `raw_unvalidated` and `uncalibrated_comparative` unless the spec sets `objectives_explicit_exploratory: true`. |
| **DesignReportRequest** | RFC 0055 input record for the design-report renderer: `hull_path`, `html_out`, optional `pdf_out`, optional `from_run` (sweep/search run directory used to compute the Comparison-position section). Lives at `kayakgen.services.design_report.DesignReportRequest`. The renderer is a read-model over existing aggregates; it introduces no new claim state and no new evaluator. |
| **DesignReportResult** | RFC 0055 outcome record returned by `render_design_report`: `html_path`, optional `pdf_path`, `forbidden_copy_clean: bool` (asserted on the rendered HTML by scanning against `FORBIDDEN_COPY_PATTERN` after scrubbing the explicit negated tokens `unvalidated_*`, `uncalibrated_*`, `not_safety_or_seaworthiness_claim`, `raw_unvalidated`), `html_size_bytes`, and `sections` (the ordered RFC 0055 section ids). A failed scan raises `ReportForbiddenCopyError`; no artifact is written. |
| **GenerativeJob** | RFC 0057 aggregate root at `kayakgen.services.generative_jobs.GenerativeJob` representing one generative-search run originating from the Trame Generate panel or `kayakgen runs jobs`. Carries `job_id`, `job_kind` (`sweep` / `search`), a `state` literal (`queued` / `running` / `succeeded` / `failed` / `cancelled` / `resumable`), optional `forked_from` lineage (RFC 0057 fork-with-seed surface), `error.kind` token on failure, `resumable_from_checkpoint: bool`, and a `redacted_logs` reference. Surfaced by `/api/generative-jobs/*` and `kayakgen runs jobs --state ...`. |
| **HullParameterMetadata** | RFC 0060 presentation-layer value object at `kayakgen.ui.parameter_metadata.HullParameterMetadata` (frozen, `extra="forbid"`) carrying `parameter`, `label`, optional `unit`, and `description` for one hull parameter exposed by the web Generate-panel form. The companion `HULL_PARAMETER_METADATA` registry feeds friendly field labels and hover-for-description tooltips to `kayakgen/ui/web/generate_spec_form.py`; the helpers `label_with_unit(parameter)` and `description(parameter)` are the consumer API. The form's submitted JSON payload continues to use the raw parameter name (the registry key), so the registry is purely additive on the wire. Closes audit finding `AUD-O-003`. |

## Readiness, status, and dispatch-blocker tokens

`Readiness` governs the next operation an artifact may consume. Independent of
claim state. The literal set lives across `MeshPackageManifest.readiness_level`,
`ClosedVolumeReadiness.level`, `CfdRunRecord.status`, and CFD
`error_kind` values; not every token below is a status literal.

| Token | Meaning |
| --- | --- |
| `cfd_surface_candidate` | open-surface inspection mesh; not solver input. The default `mesh-package` profile outcome. |
| `closed_volume` | passes RFC 0021 self-intersection + RFC 0016 topology; carries `ClosedVolumeBody` with positive signed volume. Not yet `cfd_ready`. |
| `cfd_ready` | watertight package whose `MeshPackageManifest` is matched by a bound `VolumeMeshDiagnostic`. Only the RFC 0023 fixture path and the RFC 0045 evidence-bound path can produce it. |
| `unavailable` | `CfdRunRecord.status` for a solver profile that is permanently unavailable. |
| `solver_unavailable` | an `error_kind` for unavailable solver profiles (e.g. `unavailable-watertight-solid`). |
| `solver_success_blocked` | the adapter ran but no opt-in mechanism admitted the real path. Default outcome of `openfoam-v2512-interfoam-local` without RFC 0046 opt-in. |
| `succeeded` | the real-solver path returned; the parsed payload preserves `claim_state="raw_unvalidated"` and the locked case-template version. |

## Identity and persistence

`kayakgen.services.artifact_store` (RFC 0049) introduces an
opt-in content-addressed mirror plus a SQLite read model that sits
beside the existing run-directory layout. None of these terms change
default kayakgen behaviour from the operator's perspective; canonical
paths remain byte-stable.

| Term | Definition |
| --- | --- |
| **ArtifactStore** | `kayakgen.services.artifact_store.ArtifactStore` protocol: `put_json`, `put_file`, `get_json`, `get_file`, `record_event`, `query_candidates`. The filesystem implementation (`FilesystemArtifactStore`) writes a `_store/<hash>.<ext>` mirror under each run directory and hard-links the canonical paths into it (copies on Windows with a warning). |
| **ArtifactRef** | Pydantic record returned by every `put_*` call. Carries `kind`, `artifact_hash` (SHA-256 of the on-disk bytes, 64 hex chars), and optional `run_id` / `candidate_key` / `relative_path`. |
| **ArtifactKind** | Closed Literal enum of artifact tags persisted by the store: `hull_json`, `eval_result_json`, `stability_result_json`, `mesh_package_manifest`, `mesh_quality_json`, `hull_stl`, `deck_stl`, `cfd_run_record`, `cfd_raw_result`, `openfoam_force_dat`, `openfoam_polymesh_file`, `snappy_hex_mesh_evidence`, `sweep_run_record`, `sweep_summary_csv`, `sweep_failures_jsonl`, `candidate_record`, `high_angle_gz_artifact`, `search_run_record`, `comparison_report`. |
| **design_hash** | `kayakgen.services.identity.design_hash_for_hull` / `Hull.design_hash()`: SHA-256 over the physical inputs only (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`, `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`, `stern_rake`, `rocker_bow_m`, `rocker_stern_m`, `LCB_frac`, `geometry_kind`). Invariant under renaming the hull or reordering JSON keys. |
| **record_hash** | `kayakgen.services.identity.record_hash` / `Hull.record_hash()`: SHA-256 over the canonical-form JSON of the full record. Differs whenever any field — including `name` — differs. `Hull.hash()` is a backwards-compat alias. |
| **run_hash** | `kayakgen.services.identity.run_hash`: SHA-256 over a canonical `{spec, version}` blob — the sweep/search/CFD spec plus `kayakgen.__version__`. |
| **SqliteIndex** | Machine-wide SQLite read model at `~/.local/share/kayakgen/index.sqlite` (override with `KAYAKGEN_INDEX_DB`). Tables: `runs`, `candidates`, `metrics`, `artifacts`, `events`. Materialised view of the canonical filesystem; rebuildable via `kayakgen runs reindex`. |
| **kayakgen runs** | Three subcommands exposed by `kayakgen/cli/runs_cli.py`: `runs list [--kind ...] [--limit ...]`, `runs query <run_id> [--filter ...] [--metric ...]`, `runs reindex <run_dir>`. Default sweep/search/cfd flows still work without invoking these. |

## Distinctions

Pairs of terms that look similar but mean different things. Distinctions are
where the model's edges live.

| Pair | Distinction |
| --- | --- |
| **Validation vs Calibration** | A `validation_fixture` is a *holdout* check; a `calibration_fixture` *trains* a model. Validation alone never satisfies a calibration claim. |
| **Acceptance vs Validation** | Acceptance is a gate that admits a record (e.g. RFC 0027 acceptance). Validation is comparing a model's output against measured data. A record can be accepted (passes gates) without being validated (no measured comparator). |
| **Readiness vs Claim State** | Readiness governs the next operation that may consume an artifact (e.g. `cfd_ready` permits a solver dispatch). Claim state governs how an output's *numbers* may be interpreted (e.g. `raw_unvalidated`). The two are independent — a `cfd_ready` package can produce `raw_unvalidated` solver output. |
| **Open Surface vs Closed Body** | Open hull/deck STLs are inspection surfaces; they are not closed volumes and never report `cfd_ready` on their own. A generated closed body must pass topology + self-intersection diagnostics before it can host evidence. |
| **Artifact vs Output** | An *artifact* is durable bytes written to a known path with a known schema (e.g. `record.json`, `force.dat`, an STL). An *output* is anything an evaluator returns in-process; only some outputs become artifacts. |
| **Pending vs Failed vs Constraint_failed** | `pending` is queued-but-unrun; `failed` is evaluation error (invalid hull, exception); `constraint_failed` is a structural search-time refusal because explicit constraints rejected the candidate. None are frontier-eligible; only `complete` candidates enter the Pareto front. |
| **Operator vs User** | An *operator* runs `kayakgen` on their workstation and decides whether to opt into real CFD / hosted demos / measurement campaigns. A *user* views design output (currently overlaps with operator; the distinction matters for future hosted surfaces). |
| **Profile Flag vs Persistent Setting vs Env Knob** | Three RFC 0046 opt-in mechanisms (D027). Profile flag lives in a prepared job's `profile.json` (most explicit); persistent setting lives in `~/.config/kayakgen/cfd.json` (per-workstation); env knob is `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` (test/scripted). Precedence: profile_flag > persistent_setting > env_knob. |
| **Local vs Hosted** | Local is `kayakgen serve` on the operator's workstation, optionally containerized via the repo Dockerfile. Hosted is a public URL; D023 indefinitely defers it. |
| **NSGA-II vs EHVI** | Two `kayakgen.search.active` algorithm families. NSGA-II (RFC 0044 v1) is evolutionary, cheap per evaluation, multi-objective only by design. EHVI (RFC 0047 v2) is Bayesian, GP-surrogate-based, expensive per evaluation, supports 1-3 objectives (`EhviDimensionError` for 4+). 1-objective EHVI reduces to expected-improvement Bayesian opt. |

## Tokens recorded under decisions

The following named tokens are referenced from code and may appear in
structured errors or rejection codes. Each is documented in a DECISION_LOG
row; the row is authoritative.

- `CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT` (D006)
- `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY` (D014 / D019)
- `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY` (D024)
- `VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS` (D025)
- `VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT` (D025)
- `closed_body_hash_mismatch`, `snappy_evidence_body_mismatch`,
  `polymesh_artifact_drift`, `evidence_not_recorded`,
  `evidence_translation_failed` (D026)
- `cfd_config_malformed_json`, `cfd_config_schema_mismatch` (D027)
- `EhviDimensionError` (D028)
