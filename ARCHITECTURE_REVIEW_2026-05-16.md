# Kayakgen Architecture Review

Date: 2026-05-16

Reviewer stance: systems architecture review of the repository as it exists
today. I read the project orientation docs, PRD, roadmap, RFC index, decision
log, design-constraint memo, user guide, core package modules, CLI, search,
web, CFD, mesh, stability, and tests. I also ran the default test suite.

## Verification Snapshot

- The working tree already had unrelated local modifications before this
  report. At the start of review, `git status --short` showed:
  `kayakgen/eval/calibration/__init__.py`,
  `tests/fixtures/calibration/edinburgh_review_packet.json`,
  `tests/test_calibration.py`, and `tests/test_resistance.py`.
- After the test run and report creation, current non-report modifications show
  as `kayakgen/ui/desktop.py` and `tests/test_desktop_layout.py`. I did not
  edit those files as part of this review.
- Test command run: `.venv/bin/python -m pytest -q`
- Result: `566 passed, 2 skipped in 238.37s`
- The skipped tests are the opt-in OpenFOAM-v2512 smoke tests.
- Ruff is declared in the dev optional dependencies, but it is not installed
  in the current `.venv`; `.venv/bin/python -m ruff ...` failed with
  `No module named ruff`.

## Executive Summary

Kayakgen has made a strong transition from a prototype hull generator into a
local-first, evidence-aware generative design pipeline. The most important
early architecture decision was correct: extract a headless Python package with
serializable hull records, reusable evaluators, a CLI, and UI surfaces that
consume the same core. That decision is mostly implemented.

The second important decision is also correct: the project is unusually careful
about claim semantics. It refuses to present raw analytical resistance,
fixture-only CFD, local OpenFOAM output, design advisories, or high-angle GZ as
validated design fitness. This is the right posture for a hydrodynamics tool
that has not yet closed calibration and validation gates.

The main architectural risk now is that the codebase has outgrown the first
package split. Large orchestration modules have become local platforms:
`kayakgen/eval/cfd/jobs.py`, `kayakgen/ui/web/controllers.py`,
`kayakgen/ui/web/app.py`, `kayakgen/eval/stability.py`, and
`kayakgen/eval/closed_volume.py` each carry more than one responsibility. The
system is still test-protected, but dependency direction and domain ownership
are starting to blur.

If I were doing this greenfield, I would still choose Python, Pydantic,
NumPy, local-first CLI, and evidence-gated outputs. I would change the
domain architecture: make hull design, geometry, analysis, evidence, execution,
experiments, persistence, and interfaces first-class bounded contexts rather
than directories inside a broad `eval` package. I would also introduce a real
artifact store earlier, because sweeps/search/CFD naturally want immutable run
records, content-addressed files, resumability, provenance, and queryable
metrics.

## What The Project Is Trying To Be

From `docs/PRD.md`, `docs/ROADMAP.md`, and `AGENTS.md`, the project goal is:

- Generate kayak and surfski hull geometry from naval-architecture parameters.
- Keep hulls serializable and replayable as JSON.
- Provide fast local evaluation: hydrostatics, resistance screening, stability,
  mesh diagnostics, sweeps, comparison, and active search.
- Support desktop, web, and CLI surfaces without making the GUI the core.
- Stage future solver and calibration work behind explicit evidence gates.
- Avoid overclaiming. Current outputs are useful for design exploration, not
  final performance prediction, seaworthiness, safety, production CFD, or
  calibrated fitness.

The project is not merely a CAD exporter. Its real direction is a
human-powered small-craft design lab:

```text
Hull design parameters
  -> geometry / closed-body evidence
  -> hydrostatics, stability, resistance, validity, mesh diagnostics
  -> sweeps, comparison, active search
  -> mesh/solver jobs and future calibrated evidence
  -> local desktop/web/CLI review
```

## Principles I See In The Codebase

### 1. Headless Core First

The package can run from the CLI and tests without a display server. The desktop
and web interfaces call core evaluators rather than owning the model outright.
This is the right direction.

### 2. Evidence Before Promotion

Readiness and claim states are not just comments. They are modeled with
Pydantic contracts:

- `raw_unvalidated`
- `uncalibrated_comparative`
- `validation_fixture`
- `calibration_fixture`
- `calibrated_model`
- `validated_design_fitness`
- `cfd_ready`
- `unvalidated_hydrostatic_comparison`

The project repeatedly rejects partial evidence rather than promoting it. That
is one of the strongest parts of the architecture.

### 3. Determinism And Reproducibility

Sweep candidate keys, run records, fixture outputs, mesh package refs, evidence
hashes, and search seeds are all treated as load-bearing. This is exactly what
a generative pipeline needs.

### 4. RFC-Governed Change

Major decisions land through RFCs and decision-log rows. This has kept
claim boundaries clear as the project expanded quickly.

### 5. Backward Compatibility

Root-level `generator.py`, `gui.py`, and `pyvista_view.py` remain as shims.
Legacy input fields such as symmetric `bow_rake` are seeded forward. This is a
reasonable compatibility posture.

## Architecture As It Exists

### Current Package Shape

```text
kayakgen/
  model/       Hull aggregate, lofted geometry, classes, validity/advisory
  eval/        Hydrostatics, resistance, stability, mesh, CFD, calibration,
               closed body, claim contracts
  search/      Sweep, comparison, Pareto, active NSGA-II search
  io/          JSON/STL persistence helpers
  ui/          PyQt/PyVista desktop, Trame web workspace
  cli/         Typer CLI commands
```

### Core Data Flow

1. `Hull` is the user-owned design aggregate.
2. `Hull.to_geometry()` builds `LoftedHullGeometry`.
3. Evaluators derive read models:
   - hydrostatics from integrated mesh geometry,
   - resistance from ITTC-57 plus Michell,
   - initial and opt-in high-angle stability,
   - design validity metadata,
   - mesh diagnostics and mesh packages.
4. `EvaluationResult` joins read models by `hull_hash`.
5. Sweep/search write candidate records and artifacts.
6. Comparison builds Pareto-style reports.
7. CFD jobs consume mesh package manifests and emit raw run records.
8. Desktop/web/CLI are user-facing adapters.

### Current Size Pressure

The package itself is not large, but some files have become architecture
boundaries by accident:

| Area | File | Approx. lines | Observation |
| --- | --- | ---: | --- |
| CFD orchestration | `kayakgen/eval/cfd/jobs.py` | 2450 | Profiles, schemas, adapters, parsers, validation, subprocess, filesystem, and OpenFOAM branching in one module. |
| Web controllers | `kayakgen/ui/web/controllers.py` | 1602 | UI read models, CFD routes, filesystem access, export, validation, and core evaluation orchestration. |
| Web app shell | `kayakgen/ui/web/app.py` | 1392 | Trame state, layout, event handling, read model binding, and visible copy. |
| Closed volume | `kayakgen/eval/closed_volume.py` | 1444 | Body schemas, generated body construction, topology diagnostics, self-intersection checks. |
| Stability | `kayakgen/eval/stability.py` | 1322 | Initial stability, equilibrium trim, high-angle GZ gates, heeled clipping solver. |
| Mesh package | `kayakgen/eval/mesh_package.py` | 919 | Manifest writing, readiness reports, package evidence binding. |
| Active search | `kayakgen/search/active/runner.py` | 705 | Algorithm orchestration, persistence, evaluation, pending/resume, summary. |

This is not yet a crisis because tests are strong, but these files are where
future changes will become slower and riskier.

## What Is Working Well

### The RFC 0007 Refactor Paid Off

The current code does have the model/eval/search/UI split proposed in RFC 0007.
The core no longer depends on a GUI window. `Hull` is serializable. The CLI can
initialize, generate, evaluate, sweep, search, compare, prepare CFD jobs, and
serve the web UI.

I would not undo this. It is the foundation the rest of the project should keep.

### Claim Hygiene Is A Serious Asset

The code has actual gates for raw CFD, uncalibrated resistance, high-angle GZ
display-only outputs, fixture-only records, and design-fitness refusal. That
protects users and future contributors from turning convenient numbers into
false claims.

In this domain, that is not process overhead. It is product correctness.

### Test Coverage Is Broad And Useful

The suite covers:

- hull JSON round trips,
- golden STL geometry,
- hydrostatics,
- resistance,
- design validity,
- mesh diagnostics and package manifests,
- closed body construction,
- high-angle GZ contracts,
- CFD job routes and OpenFOAM parser/case rendering,
- web state and browser-oriented read models,
- sweep/search/compare behavior.

Passing 566 tests is meaningful. The system has enough tests to support
architectural refactoring if done in small slices.

### The Local-First Posture Is Correct

For a project with optional OpenFOAM, PyVista, Trame, calibration workbooks, and
experimental algorithms, local-first is pragmatic. A hosted service would add
operational concerns before the physics and evidence story is finished.

### The Current Tech Stack Is Reasonable

I would keep:

- Python 3.11+
- NumPy for numerical kernels
- Pydantic v2 for explicit schemas
- Typer for CLI
- PyVista/PyQt for local 3D desktop work
- Trame for server-backed interactive browser work
- OpenFOAM as the first real solver path
- pytest as the main safety net

The bottlenecks here are geometry modeling, validation data, solver evidence,
and architecture boundaries. They are not reasons to switch languages.

## Architectural Risks And Gaps

### 1. The Formal Domain Docs Are Placeholders

`docs/PRD.md`, `docs/ROADMAP.md`, the RFC index, and `docs/DECISION_LOG.md`
carry the real domain model. But the documents intended to be canonical
DDD/SPEC artifacts are still mostly empty:

- `docs/SPEC.md`
- `docs/DDD.md`
- `docs/UBIQUITOUS_LANGUAGE.md`

This matters because the project is explicitly vocabulary-driven. Today, the
vocabulary exists in code, PRD prose, RFCs, tests, and warnings, but not in the
declared glossary.

What I would do:

- Fill `UBIQUITOUS_LANGUAGE.md` with actual terms:
  `Hull`, `HullGeometry`, `Design Hull`, `Generated Closed Body`,
  `Mesh Package`, `Volume Mesh Diagnostic`, `Solver Profile`, `Claim State`,
  `Accepted Use`, `EvaluationResult`, `CandidateRecord`, `SweepRun`,
  `SearchRun`, `HighAngleGzDisplay`, `Calibration Fixture`.
- Fill `DDD.md` with aggregate roots and value objects.
- Fill `SPEC.md` with state stores, invariants, schemas, and write surfaces.
- Add a lightweight test or script that checks the glossary includes each
  claim/readiness vocabulary token used in public JSON and user-facing copy.

### 2. Dependency Direction Is Starting To Drift

The original architectural split says model/eval/search/UI/CLI are distinct.
There are now several small leaks:

- `kayakgen/search/sweep.py` imports `kayakgen.cli.high_angle_gz`.
- `kayakgen/eval/closed_volume.py` reaches into geometry via the private
  `_get_slice_points(..., closed_body_endpoint=True)` helper.
- `kayakgen/eval/snappy_hex_mesh.py` imports `OpenFoamProvenanceProbe` from
  `kayakgen.eval.cfd.jobs`.
- `kayakgen/eval/cfd/openfoam_v2512_interfoam/runner.py` imports
  `CheckMeshSummary` from `kayakgen.eval.snappy_hex_mesh`.
- `kayakgen/ui/web/controllers.py` directly orchestrates core evaluation,
  CFD jobs, mesh package reading, route payloads, and filesystem access.

None of these are fatal. They are signals that the next architecture step
should be dependency-rule enforcement.

What I would do:

- Move `build_high_angle_gz_block` out of `cli/` into an eval or read-model
  module.
- Make closed-body endpoint sections a public `HullGeometry` method or a
  dedicated `ClosedBodyBuilder` protocol.
- Move `OpenFoamProvenanceProbe` and `CheckMeshSummary` to a neutral
  evidence/solver-contracts module.
- Add import-boundary tests. For example:
  - `model` imports nothing from `eval`, `search`, `ui`, or `cli`.
  - `eval` imports nothing from `ui` or `cli`.
  - `search` imports nothing from `ui` or `cli`.
  - `ui` can import application services and read models, not raw low-level
    job internals.

### 3. `eval` Has Become Too Broad

The `eval` package currently includes:

- hydrostatics,
- resistance,
- stability,
- mesh diagnostics,
- mesh packaging,
- closed-volume construction,
- volume-mesh evidence,
- snappyHexMesh evidence,
- CFD dispatch,
- calibration source review,
- claim-state contracts.

That is several bounded contexts under one label. It was reasonable when
everything was "evaluation", but now it obscures ownership.

What I would do:

```text
kayakgen/
  domain/        Hull design aggregate, classes, validity
  geometry/      Geometry kernels, section models, closed-body builders
  analysis/      Hydrostatics, resistance, stability
  evidence/      Claims, readiness, provenance, diagnostics, calibration records
  execution/     CFD jobs, solver adapters, subprocess/container dispatch
  experiments/   Sweep, compare, active search, metrics registry
  persistence/   Artifact store, run records, content-addressed refs
  interfaces/    CLI, web, desktop
```

This is not a rewrite recommendation. It is a target structure for staged
extraction as modules become painful.

### 4. The Hull Aggregate Needs Stronger Identity Semantics

`Hull` is currently mutable and `Hull.hash()` hashes the full JSON dump. That
means fields such as `name` and future metadata can affect the cache key even
when the physical design is unchanged. The RFC 0007 intent says the hash is a
stable cache key for design parameters; the current implementation is simpler
than that.

What I would do:

- Make a canonical `HullDesignParameters` value object.
- Keep user labels and display metadata outside the geometry hash.
- Freeze the design value object.
- Define `design_hash`, `artifact_hash`, and `run_hash` separately.
- Add a migration policy before schema version `1` becomes too overloaded.

Suggested distinction:

```text
design_hash: only physical hull inputs that change geometry/evaluation
record_hash: exact serialized JSON record
artifact_hash: bytes of generated output
run_hash: spec + evaluator versions + environment-relevant inputs
```

### 5. Geometry Is The Strategic Bottleneck

The current loft is useful and well-tested, but it is not expressive enough for
the design space described in `docs/design/kayak_hull_design_constraints.md`.
The code already admits this:

- `LCB_frac` is stored but not honored by the loft.
- `rocker_bow_m` and `rocker_stern_m` are stored but not full geometry controls.
- Cross-section archetypes, chine radius, hard/multi-chine shapes, bow flare,
  and true rocker are not first-class geometry concepts.
- Closed-body generation needs special endpoint semantics outside the ordinary
  surface mesh.

This is the point where I would avoid adding more one-off parameters to
`LoftedHullGeometry`.

What I would do:

- Introduce a geometry v2 representation based on explicit longitudinal
  distributions:
  - waterline half-breadth,
  - draft/keel profile,
  - section area,
  - deck/freeboard,
  - center of buoyancy target,
  - rocker profile,
  - section family.
- Treat cross-section shape as a model, not a coefficient hidden inside a
  formula. For example:
  - round,
  - shallow arch,
  - shallow V,
  - deep V,
  - hard chine,
  - multi-chine.
- Generate one canonical closed evaluation body first, then derive open STL
  inspection surfaces from it, instead of maintaining separate open and closed
  paths that need special reconciliation.
- Consider a CAD/B-rep or spline kernel only when the procedural section model
  blocks real hull forms. I would not adopt OpenCascade just for prestige.

### 6. Hydrostatics Should Become An Explicit Numerical Kernel

The hydrostatics module is small and fast, which is good. It also relies on
mesh-derived volume and a compatibility KG convention. The result is suitable
for the current tool, but I would make the numerical assumptions more explicit
before using it as the foundation for calibrated claims.

Specific concerns:

- The volume integration works over the generated hull surface and depends on
  waterline/end geometry conventions. That is clever, but it should be replaced
  or cross-checked by an explicit section-integration kernel and by closed-body
  integration.
- `GM0_m` uses a default `0.25 m` KG assumption at the hydrostatics level.
  Load-case-aware stability adjusts from there, but the hydrostatics read model
  itself can be mistaken as a final physical value.
- There is no explicit uncertainty or convergence metadata in the base
  hydrostatics output.

What I would do:

- Add convergence diagnostics to hydrostatics:
  stations, section samples, volume residuals, and method version.
- Provide two independent volume calculations:
  section integration and triangle/closed-body integration.
- Require them to agree within tolerance before promoting hydrostatic evidence.
- Keep KG/load-case assumptions out of base hydrostatics or label them as
  compatibility defaults.

### 7. Stability Is Correctly Cautious, But Should Be Split

`kayakgen/eval/stability.py` currently includes:

- design-waterline initial GM,
- centered sinkage equilibrium,
- bounded fixed-body trim,
- GZ result contracts,
- generated-body validation gates,
- heeled section clipping,
- fixture-only synthetic math.

That is too much for one module.

What I would do:

```text
analysis/stability/
  load_case.py
  initial.py
  upright_equilibrium.py
  trim_equilibrium.py
  high_angle_contracts.py
  heeled_section_integrator.py
  warnings.py
```

I would also keep the current warning posture. The project is right to say that
fixed-trim sealed-body GZ is an unvalidated hydrostatic comparison, not a
capsize or seaworthiness claim.

### 8. CFD Has Two Architectures Interleaved

There is a broad `jobs.py` local-dispatch architecture and a newer
`openfoam_v2512_interfoam/` renderer/runner/evidence architecture. They are
both useful, but the boundary between them is not clean yet.

There is also doc/code drift:

- `docs/PRD.md` says the real OpenFOAM path runs when both
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and `KAYAKGEN_OPENFOAM_SMOKE=1` are set.
- `docs/USER_GUIDE.md` says the profile is behind two opt-in environment
  variables, then comments that `KAYAKGEN_OPENFOAM_SMOKE` is required only for
  the smoke test surface.
- Code in `_openfoam_succeeded_path_enabled()` checks
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and OpenFOAM availability. It does not check
  `KAYAKGEN_OPENFOAM_SMOKE`.
- The OpenFOAM profile still includes known-limitations text saying no real
  succeeded record is enabled in the skeleton, even though an env-gated raw
  succeeded path exists.

What I would do:

- Make one authoritative solver-adapter contract:
  `prepare_case`, `run_case`, `collect_outputs`, `bind_evidence`.
- Move profile metadata to declarative config or small profile modules.
- Split the current monolith:
  - `execution/cfd/profiles.py`
  - `execution/cfd/job_store.py`
  - `execution/cfd/manifest_validation.py`
  - `execution/cfd/adapters/fixture.py`
  - `execution/cfd/adapters/openfoam_v2512.py`
  - `execution/cfd/parsers/openfoam_forces.py`
  - `execution/cfd/provenance.py`
- Normalize the env-gating story:
  - operational gate: `KAYAKGEN_OPENFOAM_LOCAL_RUN`
  - test gate: `KAYAKGEN_OPENFOAM_SMOKE`
  - environment source: `KAYAKGEN_OPENFOAM_BASHRC`
- Add a doc/code test for that policy.

Longer term, CFD should be a staged execution pipeline:

```text
Mesh readiness evidence
  -> case render
  -> meshing stage
  -> mesh evidence bind/check
  -> solver stage
  -> parser/post-processing
  -> raw result record
  -> validation/calibration gates
```

The code is close to this already. It just needs to be separated into
composable services.

### 9. Search And Sweep Need A Real Artifact Store

The current filesystem layout is fine for small deterministic runs. For the
documented "10,000 candidates -> hydrostatic filter -> CFD survivors" direction,
flat files will eventually become difficult:

- no query layer,
- no index over metrics,
- no durable event trail,
- no transaction boundary,
- no concurrent worker coordination,
- no easy partial-resume semantics for solver jobs,
- no global artifact de-duplication.

What I would do:

- Introduce `persistence/ArtifactStore`.
- Store records in SQLite or DuckDB plus content-addressed artifact files.
- Keep JSON artifacts as the external interchange format.
- Treat candidate evaluation as an event-sourced or append-only record:
  `planned`, `started`, `completed`, `failed`, `constraint_failed`,
  `superseded`.
- Let sweep, search, compare, web, and CLI all use the same store abstraction.

I would not jump to a service database yet. A local SQLite/DuckDB store would
handle the next order of magnitude cleanly.

### 10. Metrics And Objectives Need One Registry

Objective metadata exists, comparison has objective parsing, search has
admissibility gates, and sweep writes summaries. This is the right idea, but
the metric registry should become the central authority.

What I would do:

- Define every metric once with:
  - name,
  - unit,
  - direction,
  - source evaluator,
  - claim state,
  - accepted uses,
  - availability conditions,
  - default objective eligibility,
  - display formatting,
  - higher/lower-is-better semantics.
- Have sweep/search/compare/web read from that registry.
- Refuse unknown objective metrics unless explicitly marked experimental.

This would reduce scattered special cases around resistance, high-angle GZ,
design fitness, and mesh readiness.

### 11. The Web Surface Is Useful But Too Close To Internals

The Trame app is pragmatic for local operation. The controller layer, however,
currently does too much: it builds read models, calls evaluators, reads mesh
packages, prepares/runs CFD jobs, validates paths, and shapes REST payloads.

What I would do:

- Introduce application services:
  - `DesignService`
  - `EvaluationService`
  - `ArtifactService`
  - `CfdJobService`
  - `ComparisonService`
- Let web controllers call those services instead of low-level modules.
- Keep local filesystem restrictions in a single storage/path policy.
- If hosting is reopened, put the Trame UI behind a small API boundary rather
  than exposing local job semantics directly.

### 12. Documentation Volume Is Both Strength And Cost

There are 48 RFC files, 799 workflow files, and 306 striatum files. The decision
trail is valuable, but onboarding can become expensive if status is not
summarized aggressively.

`AGENTS.md` does a good job of naming the reading order. I would keep that and
add one generated or manually maintained architecture map:

- current modules,
- current aggregate roots,
- current state stores,
- current public JSON schemas,
- current active roadmap gates,
- current no-claim rules.

## What I Would Do Differently Greenfield

### Keep These Choices

- Python as the host language.
- NumPy for numerical geometry/evaluation kernels.
- Pydantic for schemas and boundary validation.
- Local-first operation.
- CLI as a first-class surface.
- Strict claim/readiness gates.
- RFCs for contested, cross-cutting decisions.
- OpenFOAM as the first real free-surface solver target.

### Change The Architecture Shape

I would start with bounded contexts rather than feature folders:

```text
kayakgen/
  domain/
    hull_design.py
    hull_class.py
    load_case.py
    validity.py

  geometry/
    sections.py
    distributions.py
    loft.py
    closed_body.py
    mesh_io.py

  analysis/
    hydrostatics.py
    stability/
    resistance/

  evidence/
    claims.py
    readiness.py
    diagnostics.py
    calibration_sources.py
    provenance.py

  experiments/
    metrics.py
    sweep.py
    pareto.py
    search/

  execution/
    artifacts.py
    jobs.py
    cfd/
      profiles.py
      adapters/
      parsers/

  interfaces/
    cli/
    web/
    desktop/
```

The most important difference: `interfaces` would depend inward on application
services; `analysis` and `geometry` would never import CLI/UI concerns; solver
provenance and readiness contracts would live in neutral packages.

### Introduce An Artifact Store Early

Greenfield, I would not let sweeps/search/CFD settle on ad hoc directory
records as long as this project did. I would still write JSON files for
portability, but I would put a small store abstraction underneath:

```text
ArtifactStore
  put_json(kind, payload) -> ArtifactRef
  put_file(kind, path) -> ArtifactRef
  get(ref) -> bytes/json
  record_event(run_id, event)
  query_candidates(run_id, filters, metrics)
```

Back it with SQLite plus content-addressed files. That would make 10,000+
candidate workflows, resumes, comparisons, web loading, and CFD survivor
selection much simpler.

### Make Geometry V2 The Center Of The Product

The current loft is a good prototype kernel. Greenfield, I would center the
system around a richer geometry model:

- longitudinal volume distribution,
- target displacement solver,
- target LCB solver,
- independent waterline and deck profiles,
- rocker as a first-class curve,
- section-family parameters,
- chine model,
- reserve buoyancy,
- canonical closed body,
- derived inspection surfaces.

This does not require a full CAD kernel on day one. It requires explicit
geometry contracts and a public closed-body builder.

### Separate Read Models From Evaluator Internals

Greenfield, every evaluator would emit:

- payload,
- method version,
- input refs,
- convergence metadata,
- warnings,
- claim metadata,
- admissible uses.

The current project is already partly there. I would make it universal from
the start.

### Treat Solvers As External Execution, Not Evaluators

CFD should not sit under a broad `eval` namespace. It is execution:

- it prepares cases,
- runs external programs,
- parses outputs,
- binds provenance,
- stores logs,
- reports raw results.

Validation/calibration then decides what those results may mean.

## Functionality I Would Add

### 1. Target Displacement / Trim Design Mode

Let the user specify total design load and solve for draft, or specify draft
and report load mismatch. Current tools expose displacement error, but a design
workflow wants the inverse:

```text
given hull shape + target load -> solve draft / sinkage / trim
```

This should become a primary workflow.

### 2. Geometry V2 Controls

Add implemented controls for:

- bow rocker,
- stern rocker,
- LCB position,
- max beam position,
- cross-section family,
- deadrise angle,
- bilge/chine radius,
- bow flare,
- foredeck/freeboard distribution,
- stern volume distribution.

Reserved fields should either affect geometry or be moved to explicit
unsupported metadata.

### 3. Section And Station Exports For Builders

Even though finished build assembly is out of scope, builder-useful outputs are
not the same thing as full structural CAD. I would add:

- station mold DXF/SVG,
- offsets table,
- waterline/shear/keel curves,
- section area curve,
- printable station sheets.

These are natural outputs for independent kayak builders and do not imply
structural adequacy.

### 4. Sensitivity And Uncertainty Views

For uncalibrated tools, uncertainty communication is a feature. Add:

- local sensitivity around current hull parameters,
- tornado chart for resistance/stability sensitivities,
- discretization convergence flags,
- "nearby candidates are indistinguishable" warnings when differences are
  below numerical/model uncertainty.

### 5. Better Stability Modes

Add staged modes:

- free-trim heeled equilibrium,
- cockpit/downflooding geometry,
- load-component CG visualization,
- sealed vs flooded body comparison,
- generated GZ with convergence report,
- comparison against measured inclining-campaign data when available.

Keep all safety/seaworthiness no-claim language until evidence exists.

### 6. Turning And Edged-Waterline Metrics

The design-constraints memo correctly names maneuverability as a major tradeoff.
Add geometric approximations for:

- effective waterline length at 10/15/25 degrees heel,
- lateral plane shift,
- yaw moment proxy,
- rocker-derived turning tendency.

These would be useful early filters before CFD.

### 7. Calibration Campaign Tooling

Since public kayak-envelope data appears blocked, make the project ready to
accept commissioned or community measurements:

- tank-test fixture schema,
- inclining-test schema,
- raw measurement ingestion,
- uncertainty metadata,
- source rights checklist,
- fit workflow,
- residual plots,
- validity envelope generation.

### 8. Solver Readiness Wizard

For the CLI/web:

```text
selected hull -> mesh package -> readiness blockers -> exact next command
```

The code already has structured blockers. Surface them as a guided workflow.

### 9. Project Workspace

A local project/workspace concept would help users keep related artifacts:

- hull designs,
- sweeps,
- comparisons,
- selected candidates,
- mesh packages,
- CFD jobs,
- exported station files.

This can be backed by the ArtifactStore.

### 10. Report Export

Generate a self-contained design report:

- hull parameters,
- rendered views,
- hydrostatics,
- stability,
- resistance warnings,
- mesh/readiness status,
- comparison position,
- artifacts and hashes,
- claim-state explanations.

This would make the current evidence discipline visible to users.

## Suggested Refactor Roadmap

### Phase 1: Stabilize Boundaries, No Behavior Change

1. Fill `SPEC.md`, `DDD.md`, and `UBIQUITOUS_LANGUAGE.md`.
2. Move high-angle GZ read-model construction out of `cli/`.
3. Add import-boundary tests.
4. Define canonical `design_hash` semantics and keep `Hull.hash()` compatible
   until callers migrate.
5. Normalize OpenFOAM env-gate documentation and profile limitation text.
6. Install or pin dev tooling so `ruff` and `mypy` commands actually run in the
   documented dev environment.

### Phase 2: Split The Largest Modules

1. Split `kayakgen/eval/cfd/jobs.py`.
2. Split `kayakgen/eval/stability.py`.
3. Split `kayakgen/eval/closed_volume.py` into schemas, builder, diagnostics,
   and self-intersection.
4. Split web controllers into services plus route glue.
5. Move shared solver/evidence contracts out of CFD adapter modules.

Acceptance: tests stay green and public JSON remains compatible.

### Phase 3: Introduce Persistence

1. Add `ArtifactStore`.
2. Keep existing directory layout as a compatibility adapter.
3. Write sweep/search run records through the store.
4. Add metric indexes and query helpers.
5. Let comparison consume the store rather than directly walking files.

### Phase 4: Geometry V2

1. Define a new geometry schema and public geometry protocol.
2. Implement section-family and rocker/LCB controls.
3. Build one canonical closed body first.
4. Cross-check hydrostatics across section and closed-body integrations.
5. Keep `geometry_kind="lofted"` for old hulls.

### Phase 5: Evidence And Solver Expansion

1. Promote ordinary generated packages only when volume-mesh evidence binds.
2. Make OpenFOAM run configuration per-job rather than environment-only.
3. Containerize OpenFOAM for reproducibility if local-source variability becomes
   painful.
4. Add validation/calibration workflows only after accepted data exists.

## Top Recommendations

If I had to prioritize only five things:

1. Fill the formal domain docs and glossary so the project's real model is not
   scattered across RFCs, tests, and warning strings.
2. Add import-boundary tests and remove the current CLI/search/eval/private
   geometry leaks.
3. Split the CFD, stability, closed-volume, and web-controller monoliths into
   contracts, services, adapters, and read models.
4. Define canonical hash and artifact-store semantics before search/CFD runs
   become large enough to make migration painful.
5. Start geometry v2 as the next major product architecture effort, because
   shape expressiveness is the real limiter once the evidence gates are in
   place.

## Final Assessment

Kayakgen's foundation is better than a normal research prototype. It has a
headless core, schemas, artifacts, tests, a CLI, two UIs, real no-claim gates,
and an emerging solver evidence path. Those are the hard habits to retrofit,
and they are already present.

The next failure mode is not "the code does not work." The tests say it works.
The next failure mode is architectural drag: too many responsibilities in a few
modules, too much domain vocabulary living outside the formal domain docs, and
too many future workflows depending on file-based records without a real store.

I would keep the product direction and most of the technology choices. I would
now invest in bounded contexts, artifact persistence, geometry v2, and explicit
application services before adding many more solver, optimization, or UI
features.
