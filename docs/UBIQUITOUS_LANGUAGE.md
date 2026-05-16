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
| **Hull** | A `kayakgen.model.hull.Hull` Pydantic record. Owns dimensions (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`), form coefficients (`Cp`, `Cm`, `deck_flatness`, `center_box_ratio`), end shape (`bow_rake`, `stern_rake`, `rocker_bow_m`, `rocker_stern_m`), reserved future controls (`LCB_frac`), an optional `class_preset`, and an optional `name`. The single durable input for everything downstream; serializable; hashable via `Hull.hash()`. |
| **HullGeometry** | The lofted surface that a `Hull` produces via `Hull.to_geometry()`. Owns longitudinal stations, half-breadths, deck profile, and the open hull/deck triangulations. Not durable on its own; recomputed on demand. |
| **Generated Closed Body** | `kayakgen/eval/generated_closed_body.py:generated_hull_plus_deck_closed_body(hull)` returns a `ClosedVolumeBody` of `body_type="generated_hull_plus_deck_closed_body"` with parts joined at the waterline, exact plumb-stem closure when `bow_rake==0` or `stern_rake==0`, and a `source_hull_hash` binding it back to the input hull. Profile literal `generated_hull_plus_deck_closed_body_v1`. The only closed body usable for evidence-bound CFD readiness or high-angle GZ. |

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
| **CfdRunRecord** | The terminal record for a CFD job. Carries status (`pending` / `running` / `succeeded` / `failed` / `solver_unavailable`), error_kind (e.g. `solver_success_blocked`), claim_state, accepted_uses, optional raw output reference, and (RFC 0046) optional `real_solver_execution_opt_in` + `SolverExecutionAudit`. |
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

## Sweep, search, and comparison

| Term | Definition |
| --- | --- |
| **EvaluationResult** | `kayakgen.eval.contract.EvaluationResult` — the canonical output of `kayakgen evaluate`. Combines hydrostatics, optional resistance curve, optional stability result, optional mesh diagnostics, and design-validity metadata. |
| **CandidateRecord** | One row in a sweep or search run, written to `candidates/<key>/record.json`. Carries status (`complete` / `failed` / `pending` / `skipped` / `constraint_failed`), summary metrics, optional artifact references (`stl_artifacts`, `high_angle_gz_artifact`), and the spec-resolved hull. |
| **SweepRun** | The output of `kayakgen sweep`: a directory containing `spec.json`, `run.json`, `summary.csv`, `failures.jsonl`, and `candidates/<key>/`. Deterministic JSON grid expansion; supports `--resume`. |
| **SearchRun** | The output of `kayakgen search`: same directory shape as `SweepRun`, with `run.json` additionally carrying a `search_metadata` block (algorithm kind, seed, objectives, constraints, realized budget, termination reason, per-generation history). |
| **Pending Candidate** | A `CandidateRecord` with `status == "pending"` representing queued-but-unrun work. Per RFC 0009 + D016 these are visible in `summary.csv` and the comparison report but stay frontier-ineligible. Resume replays pending records first. |
| **HighAngleGzDisplay** | A display-only read-model row in a `ComparisonReport`: body/load/trim provenance, summary metrics (`max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`), warnings, assumptions, optional `unavailable_reason`. High-angle GZ metrics are refused as Pareto/search objectives (token `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`). |
| **Objective Admissibility** | Two gates that govern which metrics may be Pareto/search objectives: `ensure_objectives_not_high_angle_gz` (RFC 0043 token) and `ensure_objectives_claim_admissible_for_search` (RFC 0044 token `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`). The latter refuses `raw_unvalidated` and `uncalibrated_comparative` unless the spec sets `objectives_explicit_exploratory: true`. |

## Readiness states

`Readiness` governs the next operation an artifact may consume. Independent of
claim state. The literal set lives across `MeshPackageManifest.readiness_level`,
`ClosedVolumeReadiness.level`, and `CfdRunRecord.status`.

| Token | Meaning |
| --- | --- |
| `cfd_surface_candidate` | open-surface inspection mesh; not solver input. The default `mesh-package` profile outcome. |
| `closed_volume` | passes RFC 0021 self-intersection + RFC 0016 topology; carries `ClosedVolumeBody` with positive signed volume. Not yet `cfd_ready`. |
| `cfd_ready` | watertight package whose `MeshPackageManifest` is matched by a bound `VolumeMeshDiagnostic`. Only the RFC 0023 fixture path and the RFC 0045 evidence-bound path can produce it. |
| `solver_unavailable` | the `SolverProfile` is permanently unavailable (e.g. `unavailable-watertight-solid`). |
| `solver_success_blocked` | the adapter ran but no opt-in mechanism admitted the real path. Default outcome of `openfoam-v2512-interfoam-local` without RFC 0046 opt-in. |
| `succeeded` | the real-solver path returned; the parsed payload preserves `claim_state="raw_unvalidated"` and the locked case-template version. |

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
