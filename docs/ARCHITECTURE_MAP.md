# Architecture Map

Date: 2026-05-16

Snapshot of the current kayakgen architecture for new contributors. Read
`AGENTS.md` first for orientation. Read this file second to learn package
layout, public surfaces, durable artifacts, claim/readiness vocabulary, and
the no-claim rules. Then dive into `docs/UBIQUITOUS_LANGUAGE.md` for term
definitions and `docs/DDD.md` for aggregate ownership.

## Package map

```
kayakgen/
├── cli/                      # Typer subcommands; thin glue
│   ├── main.py                  init / generate / evaluate / mesh-check
│   │                            / mesh-package / mesh-evidence / stability
│   │                            / view / serve / sweep / search / compare / cfd
│   └── high_angle_gz.py         compat shim for kayakgen.eval.high_angle_gz
├── eval/                     # Domain evaluators, evidence records, claim gates
│   ├── calibration/             RFC 0042 source-review packets, registry,
│   │                            extractors (Edinburgh DataShare)
│   ├── cfd/                     (Phase 3A split; jobs.py is now a thin shim)
│   │   ├── jobs.py              compat shim re-exporting from the new modules
│   │   ├── records.py           CfdRunStatus, SolverProfile, CfdJobSpec,
│   │   │                        CfdRunRecord, SolverExecutionAudit,
│   │   │                        PreparedSolverCase, SolverAdapter
│   │   ├── profiles.py          built-in SolverProfile factories + warnings
│   │   ├── job_store.py         prepare_cfd_job, run_cfd_job, load_run_record
│   │   ├── manifest_validation.py mesh-package + watertight handoff checks
│   │   ├── provenance.py        OpenFoamProvenanceProbe + probe runner
│   │   ├── config.py            ~/.config/kayakgen/cfd.json loader
│   │   ├── fixture_command.py   legacy fixture-local-command entry point
│   │   ├── parsers/
│   │   │   └── openfoam_forces.py  parse_openfoam_force_dat + sample types
│   │   ├── adapters/
│   │   │   ├── unavailable.py   UnavailableSolverAdapter
│   │   │   ├── mock.py          MockFailingLocalCommandAdapter
│   │   │   ├── fixture.py       FixtureLocalCommandAdapter
│   │   │   └── openfoam_v2512.py OpenFoamLocalAdapter +
│   │   │                        resolve_real_solver_execution_opt_in
│   │   └── openfoam_v2512_interfoam/
│   │       ├── case_render.py   OpenFoamCaseSpec + byte-deterministic render
│   │       ├── runner.py        bashrc-sourced subprocess, meshing/solve stages
│   │       ├── evidence.py      SnappyHexMeshEvidence binder
│   │       └── templates/       15 vendored case-dict templates
│   ├── closed_volume/           (Phase 3C split)
│   │   ├── __init__.py          re-exports the original public surface
│   │   ├── schemas.py           ClosedVolumeBody, ClosedVolumeDiagnostics,
│   │   │                        ClosedVolumeReadiness, policies
│   │   ├── generated_body.py    generated_hull_plus_deck_body + variants
│   │   ├── topology.py          edge/face/topology diagnostics
│   │   ├── self_intersection.py RFC 0021 algorithms (deterministic)
│   │   └── diagnostics.py       diagnose_closed_volume_body composition
│   ├── stability/               (Phase 3B split)
│   │   ├── __init__.py          re-exports original public surface
│   │   ├── load_case.py         load-case utilities
│   │   ├── initial.py           initial stability (GM0, KB, BM)
│   │   ├── upright_equilibrium.py upright sinkage solver
│   │   ├── trim_equilibrium.py  bounded fixed-body trim solve
│   │   ├── high_angle_contracts.py GZCurve, GeneratedBodyGZCurve schemas
│   │   ├── heeled_section_integrator.py heeled-volume integration
│   │   ├── warnings.py          RFC 0024 warning constants
│   │   └── evaluator.py         evaluate_stability / evaluate_gz_curve
│   ├── evidence/                Phase 2 step 5 neutral evidence facade
│   │   ├── openfoam.py          re-exports OpenFoamProvenanceProbe
│   │   ├── check_mesh.py        re-exports CheckMeshSummary
│   │   └── claims.py            re-exports ClaimMetadata + helpers
│   ├── claims.py                claim_state + accepted_uses contract
│   ├── contract.py              EvaluationResult, GZCurve, StabilityResult
│   ├── generated_closed_body.py builds generated_hull_plus_deck_closed_body_v1
│   ├── high_angle_gz.py         build_high_angle_gz_block (moved Phase 2)
│   ├── hydrostatics.py          displaced volume, GM0, LCB, waterplane
│   ├── mesh_diagnostics.py      per-part edge/face/topology diagnostics
│   ├── mesh_package.py          manifest writer + readiness report + binder
│   ├── resistance.py            Michell + ITTC raw-comparative filter
│   ├── snappy_hex_mesh.py       SnappyHexMeshEvidence + bind helper
│   ├── sweep_artifacts.py       sweep-side STL + high_angle_gz artifact writers
│   └── volume_mesh.py           VolumeMeshDiagnostic + watertight handoff
├── io/                       # STL writer; nothing else
├── model/                    # Hull, geometry, presets — no eval/ui/cli imports
│   ├── advisory.py
│   ├── geometry.py              HullGeometry + section_for_closed_body
│   ├── hull.py
│   └── presets.py
├── search/                   # Sweep + compare + Pareto + active search
│   ├── active/
│   │   ├── spec.py              SearchSpec, SearchAlgorithmSpec union
│   │   ├── nsga2.py             v1 multi-objective (SBX + polynomial mutation)
│   │   ├── ehvi.py              v2 EHVI for 1-3 objectives
│   │   ├── gp.py                vendored Cholesky GP + Nelder-Mead
│   │   ├── constraints.py       SearchConstraint enforcement
│   │   └── runner.py            algorithm dispatch + run-record writer
│   ├── compare.py               ComparisonReport + high_angle_gz_display
│   ├── objectives.py            OBJECTIVE_METADATA registry
│   ├── pareto.py                Objective gates + RFC 0043/0044 refusal tokens
│   └── sweep.py                 SweepSpec, CandidateRecord, pending lifecycle
├── services/                 # Phase 3D application services (no UI/CLI deps)
│   ├── design.py                hull-state assembly, presets, validity badges
│   ├── evaluation.py            metrics + analysis + resistance view models
│   ├── artifacts.py             STL / hydro / stability JSON / package export
│   ├── cfd_jobs.py              CFD prepare/run/status/logs/raw-result orchestration
│   └── comparison.py            comparison-report load + read-model assembly
└── ui/                       # Trame web + PyQt desktop; consumes read models
    ├── desktop.py               PyQt6 + matplotlib desktop GUI
    ├── gui_params.py
    ├── pv_window.py             PyVista 3D preview
    ├── theme.py
    └── web/
        ├── app.py               Trame app + state
        ├── controllers.py       thin route/state glue (~300 lines after Phase 3D)
        ├── read_models.py       view-model adapters (high-angle GZ etc.)
        └── state.py             WebStateSchema + alias maps
```

## Public CLI commands

| Command | Purpose | Writes |
|---|---|---|
| `kayakgen init <out>` | default Hull JSON | `out.json` |
| `kayakgen generate <hull>` | open hull + deck inspection STLs | `<stem>_{hull,deck}.stl` |
| `kayakgen evaluate <hull>` | EvaluationResult JSON | `<out>.eval.json` |
| `kayakgen mesh-check <hull>` | per-part diagnostics | `<out>.mesh.json` |
| `kayakgen mesh-package <hull>` | manifest + STLs + diagnostics | package dir |
| `kayakgen mesh-package ... --bind-evidence <path>` | attach SnappyHexMeshEvidence; promotes to `cfd_ready` if matched | package dir with bound diagnostic |
| `kayakgen mesh-evidence <hull>` | snappy + checkMesh evidence | evidence.json + polyMesh + provenance |
| `kayakgen stability <hull>` | StabilityResult JSON | `<out>.stability.json` |
| `kayakgen stability --high-angle-gz` | opt-in display-only GZ block | adds `high_angle_gz` to JSON |
| `kayakgen view [hull]` | desktop GUI | — |
| `kayakgen serve [hull]` | Trame web frontend | — |
| `kayakgen sweep <spec>` | deterministic JSON grid sweep | run dir |
| `kayakgen search <spec>` | NSGA-II / EHVI active search | run dir |
| `kayakgen compare <run>` | Pareto comparison report | `compare.json` |
| `kayakgen cfd profiles` | list dispatch profiles | stdout |
| `kayakgen cfd prepare ...` | prepare local job | job dir |
| `kayakgen cfd prepare ... --allow-real-solver-execution` | per-job real-solver opt-in flag | job dir with `allow_real_solver_execution=true` |
| `kayakgen cfd status <job>` | print job state | stdout |
| `kayakgen cfd run <job>` | invoke adapter | updates run.json |

## Durable artifact types

- **Hull JSON**: `kayakgen.model.hull.Hull` record. Stable schema; SHA-256 via
  `Hull.hash()`.
- **STL**: `kayakgen.io.stl` binary writer; not used as a test oracle (see
  `tests/golden/` for goldens).
- **EvaluationResult JSON**: `kayakgen.eval.contract.EvaluationResult`.
- **StabilityResult JSON**: `kayakgen.eval.contract.StabilityResult` (+ opt-in
  `high_angle_gz` block).
- **Mesh package**: directory with `manifest.json`, hull JSON, per-part STL,
  quality reports.
- **SnappyHexMeshEvidence JSON**: serialized
  `kayakgen.eval.snappy_hex_mesh.SnappyHexMeshEvidence`.
- **CFD job dir**: `profile.json`, `job.json`, `run.json`, optional
  `raw-result.json`, optional `postProcessing/forces/<t>/force.dat`.
- **CfdOpenFoamRawResult**: `claim_state=raw_unvalidated`, locked
  `case_template_version`.
- **Sweep run dir**: `spec.json`, `run.json`, `summary.csv`, `failures.jsonl`,
  `candidates/<key>/{record.json, eval.json, mesh.json, hull.json, stl, high_angle_gz.json}`.
- **Search run dir**: same shape as sweep, plus `search_metadata` block in
  `run.json`.
- **Comparison report JSON**: `kayakgen.search.compare.ComparisonReport`
  (with optional `high_angle_gz_display` and `high_angle_gz_columns`).
- **Edinburgh validation fixture**: vendored under
  `tests/fixtures/calibration/edinburgh/`; SHA-256-bound in the source-review
  packet.

## Public JSON records

Every record uses Pydantic `ConfigDict(extra="forbid")` and is version-pinned
with a `schema_version` literal. JSON round-trip lossless.

- `Hull`
- `EvaluationResult`, `StabilityResult`, `GZCurve`
- `MeshDiagnostic`, `MeshPackageManifest`, `ClosedVolumeBody`,
  `ClosedVolumeDiagnostics`, `ClosedVolumeReadiness`,
  `ClosedVolumeSolverReadinessReport`, `VolumeMeshDiagnostic`
- `SnappyHexMeshEvidence`, `CheckMeshSummary`
- `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, `SolverExecutionAudit`,
  `CfdOpenFoamRawResult`, `CfdOpenFoamForceDatResult`,
  `CfdOpenFoamForceDatSample`, `OpenFoamProvenanceProbe`
- `ResistanceCurve`, `ResistanceSourceRecord`, `ResistanceSourceReviewPacket`
- `KayakgenCfdConfig`
- `SweepSpec`, `CandidateRecord`, `EvaluatorOptions`, `StlArtifactSet`,
  `HighAngleGzArtifact`
- `SearchSpec`, `SearchAlgorithmSpec` (Nsga2 | Ehvi),
  `SearchMetadata`, `SearchConstraint`, `SearchBudget`, `SearchLimits`
- `ComparisonReport`, `CandidateSummary`, `HighAngleGzDisplay`
- `WebStateSchema`, `WebHighAngleGzRows`

## Claim states

Tokens that govern what an evaluator's output may claim. All preserved
verbatim across all surfaces; no surface may rewrite a record's claim state
without going through the corresponding gate.

| Token | Meaning | Where |
|---|---|---|
| `uncalibrated_comparative` | raw ITTC + Michell screening filter | `ResistanceCurve` |
| `raw_unvalidated` | real OpenFOAM forces parsed; no validation | `CfdOpenFoamRawResult` |
| `fixture_only` | synthetic / fixture math; never user-facing claim | `GZCurve.fixture_only=True` |
| `unvalidated_hydrostatic_comparison` | fixed-trim generated-body v1 high-angle GZ | `GeneratedBodyGZCurve.result_semantics` |
| `validation_candidate` | source-review packet stage; not yet a fixture | `ResistanceSourceReviewPacket.review_verdict` |
| `validation_fixture` | accepted validation source; not calibration | (Edinburgh, D025) |
| `calibration_fixture` | accepted-fit-bound calibration source | (none today; D006 gate) |

## Readiness states

| Token | Meaning |
|---|---|
| `cfd_surface_candidate` | open-surface inspection mesh; not solver input |
| `closed_volume` | passes RFC 0021 self-intersection + RFC 0016 topology |
| `cfd_ready` | watertight + matching `VolumeMeshDiagnostic` + solver profile evidence |
| `solver_unavailable` | profile is permanently unavailable |
| `solver_success_blocked` | adapter ran but no opt-in or no evidence to admit `succeeded` |
| `succeeded` | real-solver path returned; payload is `raw_unvalidated` |

## No-claim rules

Preserved verbatim from `docs/ROADMAP.md`. Future doc changes must respect:

- Resistance output is `uncalibrated_comparative` — not a calibrated model,
  not a final prediction, not a design-fitness score, not a default
  optimization objective.
- CFD output is local dispatch state or `raw_unvalidated` real output, or
  `fixture_only` records, or explicit unavailable/failed state. No accepted
  validated CFD path exists.
- Ordinary generated mesh packages stay below `cfd_ready` unless explicitly
  bound to passing volume-mesh evidence (RFC 0023 fixture or RFC 0045
  generated path).
- High-angle GZ surfaces remain `unvalidated_hydrostatic_comparison`;
  the values are not safety, seaworthiness, capsize-range, validation,
  design-fitness, or solver-readiness claims. High-angle GZ metrics are
  refused as Pareto/search objectives (RFC 0043 token
  `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`).
- The web frontend is local/browser-capable; the public hosted demo is
  indefinitely deferred per D023.
- Class validity and advisory badges are not proof of seaworthiness,
  calibrated performance, or final design fitness.

## Dependency rules

Enforced by `tests/test_import_boundaries.py` and
`tests/test_services_boundaries.py`:

- `kayakgen.model` imports nothing from `eval`, `search`, `ui`, or `cli`.
- `kayakgen.eval` imports nothing from `ui` or `cli`.
- `kayakgen.search` imports nothing from `ui` or `cli`.
- `kayakgen.services` imports nothing from `ui` or `cli`.
- `kayakgen.cli` imports services and read models, not private helpers.
- `kayakgen.ui` imports services and read models, not private evaluator
  helpers.

## Read this map after

- `AGENTS.md` (entry-point reading list)
- `docs/PRD.md` (audience + delivered/roadmap split)
- `docs/ROADMAP.md` (tracks, batches, deferrals)

## Read these next

- `docs/UBIQUITOUS_LANGUAGE.md` (canonical term definitions)
- `docs/DDD.md` (aggregate ownership)
- `docs/SPEC.md` (invariants and schemas)
- `docs/DECISION_LOG.md` (D001-D028)
- `docs/rfcs/README.md` (RFC index)
