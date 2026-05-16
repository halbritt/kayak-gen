# Architecture Recommendation Implementation Plan

Date: 2026-05-16

Source review: `ARCHITECTURE_REVIEW_2026-05-16.md`

This plan turns the architecture review recommendations into staged,
testable work. The sequencing is deliberate: first document and enforce the
current model, then split risky modules, then add persistence and geometry
changes, then expand product functionality.

## Operating Rules

1. Keep public behavior stable unless a step explicitly changes it.
2. Preserve existing JSON compatibility until a migration is documented and
   tested.
3. Run the full test suite after every phase.
4. Update `CHANGELOG.md`, roadmap/RFC status, and user docs whenever public
   commands, artifacts, claim wording, or JSON shapes change.
5. Do not promote resistance, CFD, high-angle stability, advisory validity, or
   design-fitness claims without their evidence gates.

## Phase 0: Baseline And Tooling

Goal: make the current state reproducible before architectural edits begin.

1. Record current `git status --short` before starting implementation work.
2. Run the full test suite:

   ```bash
   .venv/bin/python -m pytest -q
   ```

3. Install or sync dev tooling so the documented commands work:

   ```bash
   python -m pip install -e '.[dev]'
   ```

4. Run and record:

   ```bash
   .venv/bin/python -m ruff check kayakgen tests generator.py gui.py pyvista_view.py
   .venv/bin/python -m pytest -q
   ```

5. Add `docs/ARCHITECTURE_MAP.md` with:
   - package/module map,
   - public CLI commands,
   - durable artifact types,
   - public JSON records,
   - claim states and readiness states,
   - current no-claim rules.

Exit criteria:

- Tests pass.
- Ruff is runnable from the documented dev environment.
- The current architecture has one concise map for new contributors.

## Phase 1: Make The Domain Model Explicit

Goal: move the real domain vocabulary out of scattered RFC prose and into the
formal domain docs.

1. Fill `docs/UBIQUITOUS_LANGUAGE.md` with canonical definitions for:
   - `Hull`
   - `HullGeometry`
   - `Generated Closed Body`
   - `Mesh Package`
   - `Volume Mesh Diagnostic`
   - `Solver Profile`
   - `Claim State`
   - `Accepted Use`
   - `EvaluationResult`
   - `CandidateRecord`
   - `SweepRun`
   - `SearchRun`
   - `HighAngleGzDisplay`
   - `Calibration Fixture`

2. Fill `docs/DDD.md` with:
   - aggregate roots,
   - value objects,
   - read models,
   - domain services,
   - write surfaces,
   - durable state stores.

3. Fill `docs/SPEC.md` with:
   - owned state,
   - invariants,
   - schemas,
   - command/write surfaces,
   - artifact layout,
   - no-claim boundaries.

4. Add a lightweight vocabulary coverage test or script that checks public
   claim/readiness tokens used in code are documented.

Exit criteria:

- `docs/SPEC.md`, `docs/DDD.md`, and `docs/UBIQUITOUS_LANGUAGE.md` are no
  longer scaffold placeholders.
- Public claim/readiness vocabulary has a regression check.
- Full test suite passes.

## Phase 2: Enforce Module Boundaries

Goal: make dependency direction explicit before moving large code.

1. Add import-boundary tests. Recommended rules:
   - `kayakgen.model` imports nothing from `eval`, `search`, `ui`, or `cli`.
   - `kayakgen.eval` imports nothing from `ui` or `cli`.
   - `kayakgen.search` imports nothing from `ui` or `cli`.
   - UI layers import services/read models, not private evaluator helpers.

2. Move `build_high_angle_gz_block` out of `kayakgen/cli/high_angle_gz.py`
   into an eval/read-model module.

3. Keep `kayakgen/cli/high_angle_gz.py` as CLI parsing and compatibility glue.

4. Replace closed-volume use of private geometry helper
   `_get_slice_points(..., closed_body_endpoint=True)` with a public geometry
   method or a `ClosedBodyBuilder` protocol.

5. Move shared solver evidence contracts into a neutral module, for example:

   ```text
   kayakgen/eval/evidence/
     openfoam.py
     check_mesh.py
     claims.py
   ```

6. Update imports and compatibility shims.

Exit criteria:

- Import-boundary tests pass.
- No production module outside `model.geometry` reaches into private geometry
  methods.
- Search no longer imports from CLI.
- Full test suite passes.

## Phase 3: Split The Largest Modules

Goal: reduce architectural drag without changing user-visible behavior.

### 3A: CFD

Split `kayakgen/eval/cfd/jobs.py` into:

```text
kayakgen/eval/cfd/
  profiles.py
  records.py
  job_store.py
  manifest_validation.py
  adapters/
    unavailable.py
    mock.py
    fixture.py
    openfoam_v2512.py
  parsers/
    openfoam_forces.py
  provenance.py
```

Keep public imports compatible while migrating.

### 3B: Stability

Split `kayakgen/eval/stability.py` into:

```text
kayakgen/eval/stability/
  load_case.py
  initial.py
  upright_equilibrium.py
  trim_equilibrium.py
  high_angle_contracts.py
  heeled_section_integrator.py
  warnings.py
```

### 3C: Closed Volume

Split `kayakgen/eval/closed_volume.py` into:

```text
kayakgen/eval/closed_volume/
  schemas.py
  generated_body.py
  topology.py
  self_intersection.py
  diagnostics.py
```

### 3D: Web Controllers

Introduce application services:

```text
kayakgen/services/
  design.py
  evaluation.py
  artifacts.py
  cfd_jobs.py
  comparison.py
```

Then make `kayakgen/ui/web/controllers.py` thin route/state glue.

Exit criteria:

- Public CLI commands still work.
- Public JSON shapes remain compatible.
- Tests pass after each sub-split.
- The largest orchestration files are materially smaller and have single
  responsibilities.

## Phase 4: Normalize Identity And Persistence

Goal: prepare sweeps, search, CFD, and comparison for larger runs.

1. Define separate identity concepts:
   - `design_hash`: physical inputs that affect geometry/evaluation.
   - `record_hash`: exact serialized JSON record.
   - `artifact_hash`: output bytes.
   - `run_hash`: spec plus evaluator versions plus relevant environment inputs.

2. Keep `Hull.hash()` backwards compatible at first.

3. Add explicit `Hull.design_hash()` and migrate internal cache/run callers.

4. Introduce `ArtifactStore`:

   ```text
   put_json(kind, payload) -> ArtifactRef
   put_file(kind, path) -> ArtifactRef
   get_json(ref)
   get_file(ref)
   record_event(run_id, event)
   query_candidates(run_id, filters, metrics)
   ```

5. Implement a filesystem-backed store first.

6. Add SQLite or DuckDB indexing for:
   - runs,
   - candidates,
   - metrics,
   - artifacts,
   - events.

7. Migrate sweep/search/compare to use the store while preserving current
   directory layout as a compatibility export.

Exit criteria:

- Existing run directories still load.
- New runs are queryable through `ArtifactStore`.
- Hash semantics are documented and tested.
- Full test suite passes.

## Phase 5: Centralize Metrics And Objective Rules

Goal: make objective admissibility and display semantics consistent.

1. Create a single metric registry with:
   - metric name,
   - unit,
   - direction,
   - source evaluator,
   - claim state,
   - accepted uses,
   - availability conditions,
   - default objective eligibility,
   - display formatting.

2. Move default objective selection to the registry.

3. Make sweep summaries write registry-known metrics.

4. Make comparison reports validate objectives through the registry.

5. Make active search validate objectives through the registry.

6. Make web read models use registry display metadata.

7. Refuse unknown objective metrics unless explicitly marked experimental.

Exit criteria:

- Resistance, high-angle GZ, raw CFD, and design-fitness refusal rules are
  centralized.
- Default Pareto/search objectives remain unchanged.
- Full test suite passes.

## Phase 6: Geometry V2

Goal: make the geometry model expressive enough for the design space described
in `docs/design/kayak_hull_design_constraints.md`.

1. Draft an RFC for `geometry_kind="distribution_v2"`.

2. Define explicit longitudinal distributions:
   - waterline half-breadth,
   - draft/keel profile,
   - section area,
   - deck/freeboard,
   - LCB target,
   - rocker profile.

3. Define cross-section families:
   - round,
   - shallow arch,
   - shallow V,
   - deep V,
   - hard chine,
   - multi-chine.

4. Add implemented controls for:
   - bow rocker,
   - stern rocker,
   - LCB position,
   - max beam position,
   - deadrise angle,
   - bilge/chine radius,
   - bow flare,
   - freeboard distribution.

5. Build one canonical closed body first.

6. Derive open STL inspection surfaces from that canonical body.

7. Cross-check hydrostatics by:
   - section integration,
   - triangle/closed-body integration.

8. Keep `geometry_kind="lofted"` for existing hull JSON.

9. Add migration examples and side-by-side tests.

Exit criteria:

- Old hulls remain valid.
- Geometry v2 can honor rocker and LCB controls.
- Hydrostatic cross-checks agree within documented tolerance.
- Closed-body generation no longer needs private geometry reach-ins.

## Phase 7: Solver And Evidence Pipeline

Goal: make CFD execution a staged evidence pipeline rather than a monolithic
job function.

1. Normalize OpenFOAM gating documentation:
   - `KAYAKGEN_OPENFOAM_LOCAL_RUN`: operational opt-in.
   - `KAYAKGEN_OPENFOAM_SMOKE`: test-only smoke gate.
   - `KAYAKGEN_OPENFOAM_BASHRC`: environment source.

2. Correct OpenFOAM profile limitation text so it matches the env-gated raw
   succeeded path.

3. Make OpenFOAM execution config per-job rather than environment-only.

4. Model CFD stages explicitly:
   - mesh readiness evidence,
   - case render,
   - meshing,
   - mesh evidence binding,
   - solver execution,
   - parser/post-processing,
   - raw result record,
   - validation/calibration gate.

5. Promote ordinary generated packages only when volume-mesh evidence binds.

6. Add containerized OpenFOAM only after the local per-job path is clean.

Exit criteria:

- OpenFOAM docs, tests, and code agree on env gates.
- Job records show stage-level state.
- Raw OpenFOAM output remains `raw_unvalidated`.
- Full test suite passes.

## Phase 8: Product Functionality

Goal: add user-visible capability on top of the cleaner architecture.

1. Add target-displacement and target-trim design workflows:
   - given hull shape and target load, solve draft/sinkage/trim.
   - given draft, report load mismatch.

2. Add builder-oriented exports:
   - station mold DXF/SVG,
   - offsets table,
   - section curves,
   - waterline curve,
   - sheer curve,
   - keel curve.

3. Add sensitivity and uncertainty views:
   - local parameter sensitivity,
   - evaluator convergence metadata,
   - uncertainty warnings when candidate differences are too small.

4. Add turning and edged-waterline metrics:
   - effective waterline length at heel,
   - lateral plane shift,
   - yaw/turning proxy,
   - rocker-derived maneuverability signal.

5. Add calibration-campaign tooling:
   - tank-test fixture schema,
   - inclining-test schema,
   - raw measurement ingestion,
   - uncertainty metadata,
   - source rights checklist,
   - accepted-fit records,
   - residual plots,
   - validity envelope generation.

6. Add design report export:
   - parameters,
   - rendered views,
   - hydrostatics,
   - stability,
   - resistance warnings,
   - mesh/readiness status,
   - comparison position,
   - artifact refs and hashes,
   - claim-state explanations.

Exit criteria:

- New features use shared services, metric registry, and artifact store.
- Reports preserve no-claim boundaries.
- Full test suite passes.

## Phase 9: Release Discipline

Goal: keep architectural progress from becoming another undocumented layer.

1. Land each phase as one RFC or a small set of focused RFCs.

2. For each public behavior change, update:
   - `docs/USER_GUIDE.md`,
   - `docs/PRD.md` if scope/status changes,
   - `docs/ROADMAP.md`,
   - `docs/rfcs/README.md`,
   - `docs/DECISION_LOG.md` when a decision changes,
   - `CHANGELOG.md`.

3. Require full pytest before merge.

4. Require static tooling once Phase 0 installs it.

5. Keep calibrated prediction, final design fitness, seaworthiness, safety,
   production CFD, and hosted-service claims blocked until explicit evidence
   gates pass.

## Recommended First Batch

The first implementation batch should be small and low risk:

1. Install/sync dev tooling.
2. Add `docs/ARCHITECTURE_MAP.md`.
3. Fill `docs/UBIQUITOUS_LANGUAGE.md`.
4. Add claim/readiness vocabulary coverage check.
5. Add import-boundary tests.
6. Move high-angle GZ block construction out of CLI.
7. Run full tests and update docs.

This first batch makes later refactors safer without changing user-visible
behavior.
