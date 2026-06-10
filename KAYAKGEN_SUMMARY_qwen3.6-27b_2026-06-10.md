# KAYAKGEN_SUMMARY_qwen3.6-27b_2026-06-10.md

## 0. Files reviewed

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Agent/contributor entry-point reading list |
| `docs/PRD.md` | Product boundary, audience, delivered vs roadmap |
| `docs/rfcs/README.md` | RFC index (65 accepted/proposed RFCs) |
| `pyproject.toml` | Package metadata, dependencies, CLI entry point |
| `README.md` | One-paragraph project description |
| `kayakgen/__init__.py` | Package-level re-exports |
| `kayakgen/cli/main.py` | CLI entry point — 20+ subcommands |
| `kayakgen/cli/design_report_cli.py` | `kayakgen design-report` subcommand |
| `kayakgen/cli/high_angle_gz.py` | High-angle GZ CLI helpers |
| `kayakgen/cli/migrate_geometry_cli.py` | `kayakgen migrate-geometry` subcommand |
| `kayakgen/cli/runs_cli.py` | `kayakgen runs` sub-app |
| `kayakgen/cli/sensitivity_cli.py` | `kayakgen sensitivity` subcommand |
| `kayakgen/cli/stability_cli.py` | `kayakgen stability` sub-app |
| `kayakgen/cli/target_workflows.py` | `kayakgen target-draft` / `target-trim` |
| `kayakgen/model/hull.py` | `Hull` aggregate root — Pydantic model |
| `kayakgen/model/geometry.py` | `HullGeometry` ABC, `LoftedHullGeometry`, `DistributionV2Geometry` |
| `kayakgen/model/distribution_v2.py` | RFC 0048 distribution model schemas |
| `kayakgen/model/classes.py` | Hull class presets |
| `kayakgen/model/advisory.py` | Advisory/constraint record types |
| `kayakgen/model/validity.py` | Design validity evaluation |
| `kayakgen/model/schema.py` | Schema utilities |
| `kayakgen/eval/hydrostatics.py` | Integrated hydrostatics from geometry mesh |
| `kayakgen/eval/resistance.py` | ITTC-57 viscous + Michell wave-making resistance |
| `kayakgen/eval/contract.py` | `EvaluationResult`, `ResistanceMetadata`, `LoadCase` |
| `kayakgen/eval/claims.py` | Claim-state literals and fit-status types |
| `kayakgen/eval/high_angle_gz.py` | High-angle GZ surface computation |
| `kayakgen/eval/turning.py` | Turning and edged-waterline metrics |
| `kayakgen/eval/mesh_diagnostics.py` | Surface mesh quality diagnostics |
| `kayakgen/eval/mesh_package.py` | Mesh package manifest + solver profiles |
| `kayakgen/eval/snappy_hex_mesh.py` | SnappyHexMesh evidence binding |
| `kayakgen/eval/closed_volume/` (6 files) | Generated closed-body construction, diagnostics, topology |
| `kayakgen/eval/stability/` (12 files) | Stability evaluators, trim equilibrium, GZ registry, measured fixtures |
| `kayakgen/eval/cfd/` (15+ files) | CFD job plumbing, solver profiles, OpenFOAM adapter, parsers |
| `kayakgen/eval/cfd/openfoam_v2512_interfoam/` (4 files) | Real OpenFOAM case rendering, evidence, runner |
| `kayakgen/eval/calibration/` (4 files) | Calibration campaigns, Edinburgh extractor, rights |
| `kayakgen/eval/sweep_artifacts.py` | Sweep-side STL and GZ artifact writers |
| `kayakgen/eval/volume_mesh.py` | Volume mesh utilities |
| `kayakgen/search/sweep.py` | Deterministic sweep spec + runner |
| `kayakgen/search/pareto.py` | Pareto frontier computation |
| `kayakgen/search/compare.py` | Comparison report generation |
| `kayakgen/search/objectives.py` | Objective metadata registry |
| `kayakgen/search/active/` (7 files) | NSGA-II, EHVI, GP, search runner, spec |
| `kayakgen/services/artifact_store.py` | Content-addressed artifact store + SQLite index |
| `kayakgen/services/artifacts.py` | Artifact utilities |
| `kayakgen/services/build_export.py` | Builder-oriented DXF/SVG/offsets export |
| `kayakgen/services/calibration_artifacts.py` | Calibration residual-plot writer |
| `kayakgen/services/cfd_jobs.py` | CFD job services |
| `kayakgen/services/comparison.py` | Comparison services |
| `kayakgen/services/design.py` | Design services |
| `kayakgen/services/design_report.py` | Design report HTML/PDF rendering |
| `kayakgen/services/evaluation.py` | Evaluation services |
| `kayakgen/services/generative_jobs.py` | In-process + subprocess job managers |
| `kayakgen/services/generative_jobs_fork.py` | Generative job fork utilities |
| `kayakgen/services/generative_jobs_runner.py` | Generative job runner |
| `kayakgen/services/identity.py` | Hull identity hash functions |
| `kayakgen/services/sensitivity.py` | Sensitivity analysis |
| `kayakgen/ui/desktop.py` | PyQt6 desktop GUI |
| `kayakgen/ui/desktop_slider_ranges.py` | Desktop slider range definitions |
| `kayakgen/ui/gui_params.py` | GUI parameter mappings |
| `kayakgen/ui/hydrostatics_metadata.py` | Hydrostatics row metadata registry |
| `kayakgen/ui/parameter_metadata.py` | Hull parameter metadata registry |
| `kayakgen/ui/pv_window.py` | PyVista 3D window |
| `kayakgen/ui/theme.py` | Shared theme tokens |
| `kayakgen/ui/web/app.py` | Trame web app factory |
| `kayakgen/ui/web/controllers.py` | Web controllers (HullStore, CfdWebStore) |
| `kayakgen/ui/web/generate_panel.py` | Generate panel mixin |
| `kayakgen/ui/web/generate_spec_form.py` | Search spec form builder |
| `kayakgen/ui/web/generate_state_listener.py` | Generate state listener |
| `kayakgen/ui/web/generate_frontier_view.py` | 2D Pareto scatter view |
| `kayakgen/ui/web/generate_fork_button.py` | Fork-with-seed button |
| `kayakgen/ui/web/handlers.py` | Web request handlers |
| `kayakgen/ui/web/layout.py` | Three-region workspace layout |
| `kayakgen/ui/web/presentation.py` | Presentation constants and CSS |
| `kayakgen/ui/web/read_models.py` | Read models for web |
| `kayakgen/ui/web/scene.py` | 3D scene management |
| `kayakgen/ui/web/state.py` | Trame state management |
| `kayakgen/io/json.py` | Hull/evaluation JSON I/O |
| `kayakgen/io/stl.py` | STL export |
| `kayakgen/metadata/` (2 files) | Metadata utilities |
| `generator.py` | Legacy KayakGenerator shim |
| `gui.py` | Legacy GUI shim |
| `pyvista_view.py` | Legacy PyVista view shim |
| `tests/conftest.py` | Test fixtures |
| `tests/` (92 test files) | Test suite (sampled representative files) |

Skipped: Individual test files (92 total — sampled for patterns, not read in full), `docs/` subdirectories beyond PRD/rfc index (RFC bodies, workflows, audits, research notes — read only when cited), `__pycache__/`, `*.stl` artifacts.

## 1. One-paragraph description

Kayakgen is a parametric kayak hull generator and evaluation pipeline. You give it dimensions (length, beam, draft) and naval-architecture form coefficients (prismatic coefficient, midship section coefficient, etc.), and it produces 3D hull and deck geometry as STL surfaces, computes hydrostatic properties (displacement, wetted surface, metacentric height), estimates paddling-speed resistance (viscous + wave-making), and optionally runs CFD jobs against a local OpenFOAM installation. It exposes everything through a CLI (`kayakgen`), a PyQt6 desktop GUI, and a browser-based Trame web workspace. It also supports batch sweeps, multi-objective optimization (NSGA-II, EHVI Gaussian-process Bayesian search), and cross-run artifact inspection via a content-addressed store and SQLite index. The project is a single Python package (~40K LOC) with 92 test files, authored by Heath Albritton, version 0.1.0.

## 2. Problem it solves

An independent kayak builder or naval-architecture enthusiast wants to design a custom kayak hull from first principles — specifying key dimensions and form coefficients rather than sculpting geometry manually in CAD. Without kayakgen, they would need to: (a) model the hull in CAD by hand, (b) export to a separate tool for hydrostatic analysis, (c) run a separate resistance estimation, and (d) repeat the loop manually for each design variant. Kayakgen collapses this into a single parametric pipeline: change a slider or JSON field, get updated geometry, hydrostatics, and resistance estimates in seconds, with 3D visualization and the ability to batch-sweep hundreds of variants or run automated multi-objective searches.

## 3. Architecture overview

```
                        +----------------+
                        |   Frontend     |
                        +----------------+
                        |  CLI (typer)   | <-- kayakgen generate/evaluate/sweep/search/serve/...
                        |  Desktop GUI   | <-- PyQt6 + matplotlib + PyVista
                        |  Web (Trame)   | <-- Vuetify + VTK + matplotlib
                        +-------+--------+
                                |
         +----------------------+----------------------+
         |                      |                      |
  +------+------+      +-------+--------+      +-------+--------+
  |  Services   |      |   Model        |      |   Eval         |
  +-------------+      +----------------+      +----------------+
  | artifacts   |      | Hull (Pydantic)|      | hydrostatics   |
  | build_export|      | HullGeometry   |      | resistance     |
  | calibration |      |  +Lofted       |      | stability      |
  | cfd_jobs    |      |  +DistributionV2|     | high_angle_gz  |
  | comparison  |      | classes        |      | turning        |
  | design      |      | validity       |      | mesh_diagnostics|
  | design_report|     | advisory       |      | mesh_package   |
  | evaluation  |      | distribution_v2|      | closed_volume/ |
  | gen_jobs    |      +----------------+      | stability/     |
  | identity    |              |               | cfd/           |
  | sensitivity |              |               | calibration/   |
  +------+------+              |               +----------------+
         |                     |                        |
         +---------------------+------------------------+
                                |
                         +------+------+
                         |    I/O      |
                         +-------------+
                         | json.py     |
                         | stl.py      |
                         +-------------+
```

**Runtime model:** Primarily a CLI tool and a locally-run web server. No daemon, no external service dependency (beyond optional OpenFOAM for CFD). State is disk-only: Hull JSON, evaluation JSON, STL files, sweep run directories, and a user-level SQLite index at `~/.local/share/kayakgen/index.sqlite`.

**Component responsibilities:**

- **`kayakgen/model/`** — Domain model. `Hull` is the aggregate root: a Pydantic model of design parameters. `HullGeometry` is the strategy-pattern ABC with two implementations (`LoftedHullGeometry` for the original parametric loft, `DistributionV2Geometry` for the RFC 0048 explicit distribution model).
- **`kayakgen/eval/`** — Evaluators. Each submodule computes something from a `Hull`: hydrostatics (integrated from mesh triangles), resistance (ITTC-57 + Michell integral), stability (initial GM, trim equilibrium, high-angle GZ), turning metrics, mesh diagnostics, CFD dispatch, and calibration campaign tooling.
- **`kayakgen/search/`** — Batch and optimization. Deterministic sweeps (parameter grid expansion), Pareto frontier computation, comparison reports, and active search (NSGA-II v1, EHVI/GP v2).
- **`kayakgen/services/`** — Orchestration and persistence. Artifact store with content-addressed storage and SQLite index, builder exports, design report rendering, sensitivity analysis, generative job management.
- **`kayakgen/ui/`** — Presentation. Desktop GUI (PyQt6), web frontend (Trame), shared theme tokens, parameter metadata registries.
- **`kayakgen/cli/`** — CLI surface. Typer-based with 20+ subcommands organized into apps (`cfd`, `calibration`, `runs`, `stability`).
- **`kayakgen/io/`** — Serialization. JSON round-trip for Hull and EvaluationResult; STL export for geometry.

## 4. Key data flows

### 4a. Generate STL from Hull JSON

1. `kayakgen generate hull.json --stl-out myboat` (`kayakgen/cli/main.py:69-83`)
2. `load_hull()` reads JSON, validates into `Hull` (`kayakgen/io/json.py`)
3. `write_stl(hull, "hull", path)` calls `hull.to_geometry()` -> `LoftedHullGeometry(hull)` (`kayakgen/model/hull.py:145-153`)
4. `LoftedHullGeometry.mesh("hull")` iterates 150 stations, computes cross-section rings via `_get_slice_points()`, triangulates between adjacent stations (`kayakgen/model/geometry.py:269-297`)
5. `kayakgen/io/stl.py:write_stl()` writes binary STL from vertices + faces arrays

### 4b. Evaluate a hull (hydrostatics + resistance)

1. `kayakgen evaluate hull.json` (`kayakgen/cli/main.py:85-133`)
2. `evaluate_hydrostatics(hull)` (`kayakgen/eval/hydrostatics.py:evaluate()`):
   - Calls `hull.to_geometry().mesh("hull")` to get vertices + faces
   - Computes displaced volume via signed-volume integration over triangles
   - Computes wetted surface from triangle areas
   - Computes waterplane area, LCB, Cp_actual, Cm_actual, GM0 from the mesh
3. `resistance_curve(hull)` (`kayakgen/eval/resistance.py:resistance_curve()`):
   - Samples half-breadth grid: `hull.to_geometry().half_breadth_grid(800, 40)`
   - Computes viscous resistance via ITTC-57 friction line over wetted surface
   - Computes wave-making resistance via Michell thin-ship integral (polar form) over the half-breadth grid
   - Returns `ResistanceCurve` with speed, total/viscous/wave resistance at each speed point
4. Results assembled into `EvaluationResult` and written as JSON

### 4c. Active search (NSGA-II)

1. `kayakgen search spec.json --out results/` (`kayakgen/cli/main.py:702-749`)
2. `load_search_spec()` parses `SearchSpec` with algorithm config, budget, objectives, search space
3. `run_search()` (`kayakgen/search/active/runner.py`):
   - Initializes population via `_hull_from_genome()` — flat-overlays genome values onto base hull JSON
   - Evaluates each candidate: hydrostatics + whichever evaluators the spec enables
   - Runs NSGA-II non-dominated sort + crowding-distance selection
   - Offspring generated via simulated binary crossover + polynomial mutation
   - Loop until budget (max evaluations or wall clock) exhausted
   - Writes candidate records, run metadata, and Pareto frontier to output directory

## 5. Entry points

| Surface | Invocation | Notes |
| --- | --- | --- |
| **CLI** | `kayakgen <command>` | Console script entry point: `kayakgen.cli.main:app` (Typer). 20+ subcommands: `init`, `generate`, `evaluate`, `view`, `serve`, `sweep`, `search`, `compare`, `mesh-check`, `mesh-package`, `mesh-evidence`, `build-export`, `design-report`, `sensitivity`, `target-draft`, `target-trim`, `migrate-geometry`, plus `cfd {prepare,status,run,profiles}`, `calibration {ingest-tank-test,ingest-inclining-test,accept-fit,residual-plot}`, `runs {list,query,reindex}`, `stability legacy` |
| **Desktop GUI** | `kayakgen view [hull.json]` | Requires `kayakgen[desktop]` extras. Opens PyQt6 window with sliders, 2D previews, and PyVista 3D view |
| **Web frontend** | `kayakgen serve [hull.json]` | Requires `kayakgen[web]` extras. Starts Trame server on `127.0.0.1:8080`. Optional `--jobs-in-process` flag |
| **Library import** | `from kayakgen import Hull, HullGeometry, LoftedHullGeometry` | Package `__init__.py` re-exports the core model classes |
| **Legacy shims** | `from generator import KayakGenerator` | Root-level `generator.py` (57 lines), `gui.py` (11 lines), `pyvista_view.py` (7 lines) re-export canonical classes under pre-refactor names |

## 6. Core abstractions

1. **`Hull`** (`kayakgen/model/hull.py:16`) — Pydantic aggregate root. Owns all design parameters (length, beam, draft, Cp, Cm, rake, rocker, geometry_kind, distribution_v2, hull_class). JSON-serializable, round-trip stable. `to_geometry()` dispatches to the correct `HullGeometry` strategy.

2. **`HullGeometry`** (`kayakgen/model/geometry.py:36`) — Abstract base class for geometry derivation. Defines the contract: `section()`, `mesh()`, `waterplane()`, `keel_line()`, `deck_centreline()`, `section_area()`, `half_breadth_grid()`. Two implementations: `LoftedHullGeometry` (original parametric loft) and `DistributionV2Geometry` (RFC 0048 explicit distributions).

3. **`LoftedHullGeometry`** (`kayakgen/model/geometry.py:72`) — The original parametric loft. Computes cross-section rings from Cp-derived area curve, Cm-controlled section shape, deck flatness exponent, and bow/stern rake. 150 stations, 40 points per ring. Produces open hull and deck surfaces.

4. **`DistributionV2Geometry`** (`kayakgen/model/geometry.py:660`) — RFC 0048 distribution model. Consumes explicit longitudinal distributions (half-breadth, draft, section area, deck freeboard, rocker) and a cross-section family literal (`round`, `shallow_arch`, `shallow_v`, `deep_v`, `hard_chine`, `multi_chine`). Canonical closed body is source of truth; open inspection surfaces are derived from it.

5. **`Hydrostatics`** (`kayakgen/eval/hydrostatics.py:59`) — Integrated hydrostatic results: displaced volume, mass, wetted surface, waterplane area, LCB, actual Cp/Cm, GM0. Computed from the triangulated mesh, not from formula envelopes.

6. **`ResistanceCurve`** (`kayakgen/eval/contract.py`) — Speed sweep of total, viscous, and wave resistance. Carries `ResistanceMetadata` with claim-state (`uncalibrated_comparative`), accepted uses, and warnings.

7. **`EvaluationResult`** (`kayakgen/eval/contract.py:81`) — Integration object joining hydrostatics, resistance, design validity, and turning metrics. The canonical output of `kayakgen evaluate`.

8. **`FilesystemArtifactStore` + `SqliteIndex`** (`kayakgen/services/artifact_store.py`) — Content-addressed artifact store with hard-link mirrors and a cross-run SQLite index. Enables `kayakgen runs list/query/reindex` for inspecting sweep/search results across runs.

9. **`SearchSpec` + search runner** (`kayakgen/search/active/spec.py`, `runner.py`) — Active search configuration (algorithm, budget, objectives, search space) and the execution engine supporting NSGA-II (v1) and EHVI/GP Bayesian (v2).

10. **`HullStore`** (`kayakgen/ui/web/controllers.py`) — Web frontend state manager. Wraps a `Hull`, manages parameter changes, triggers re-evaluation, and drives the Trame UI updates.

## 7. External dependencies

| Dependency | Purpose | Notes |
| --- | --- | --- |
| **numpy** | Numerical arrays, geometry math, integration | Core, always required |
| **numpy-stl** | Binary STL read/write | Core, always required |
| **pydantic >=2.5** | Data validation, schemas, JSON serialization | Core — all models are Pydantic |
| **typer >=0.12** | CLI framework | Core — `kayakgen` console script |
| **PyQt6** | Desktop GUI toolkit | Optional `[desktop]` |
| **matplotlib** | 2D plots (resistance curves, etc.) | Optional `[desktop]` |
| **pyvista + pyvistaqt** | 3D rendering (desktop) | Optional `[desktop]` |
| **trame + trame-vuetify + trame-vtk + trame-matplotlib** | Web frontend framework | Optional `[web]` |
| **vtk** | 3D rendering (web) | Optional `[web]` |
| **playwright** | Browser acceptance testing | Optional `[browser]` |
| **openpyxl** | Calibration CSV/Excel ingest | Optional `[calibration]`, `[dev]` |
| **jinja2 + weasyprint** | Design report HTML/PDF | Optional `[report]` |
| **ezdxf** | Builder DXF export | Optional `[builder]` |
| **pytest + pytest-benchmark + ruff** | Testing and linting | Optional `[dev]` |

No database, no web framework beyond Trame, no cloud SDK. The project is deliberately local-first. OpenFOAM is an external binary toolchain, not a Python dependency.

## 8. Configuration and extension

**Hull JSON** is the primary configuration surface. A Hull JSON file contains all design parameters. `kayakgen init out.json` writes a default. Users edit it directly or via the GUI/web sliders.

**Sweep specs** are JSON files defining parameter expansions (explicit values or linspace ranges) and which evaluators to run per candidate. `kayakgen sweep spec.json --out results/` executes them.

**Search specs** are JSON files extending sweep specs with algorithm config (NSGA-II or EHVI), budget (max evaluations, wall clock), objectives (metric + direction), and constraints. `kayakgen search spec.json --out results/` executes them.

**CFD configuration** is three-fold:
- `kayakgen cfd prepare --allow-real-solver-execution` writes a profile.json opt-in
- `~/.config/kayakgen/cfd.json` for persistent settings
- `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` env var for the `mesh-evidence` command
- `KAYAKGEN_OPENFOAM_BASHRC` to locate the OpenFOAM toolchain

**SQLite index** location: `~/.local/share/kayakgen/index.sqlite` (override `KAYAKGEN_INDEX_DB`).

**Extension points:**
- New evaluator: add a function in `kayakgen/eval/` that takes a `Hull` and returns a Pydantic model; wire into `EvaluationResult` and the CLI
- New geometry kind: implement `HullGeometry` ABC, add to `Hull.to_geometry()` dispatch, add `geometry_kind` literal
- New CFD solver adapter: implement the adapter protocol in `kayakgen/eval/cfd/adapters/`, register a solver profile
- New search algorithm: implement in `kayakgen/search/active/`, register in the runner
- New CLI command: add a Typer command to `kayakgen/cli/main.py`
- Web UI panel: add to `kayakgen/ui/web/`, wire into `app.py` controller

## 9. What is missing or implicit

- **No versioned migration path for Hull schema.** `schema_version` is hardcoded to `"1"`. If the Hull model changes incompatibly, there is no migration framework — the `migrate-geometry` CLI only handles lofted -> distribution_v2, not general schema evolution.

- **Calibration is plumbing without data.** The `kayakgen calibration` sub-app and the RFC 0054 schemas are fully implemented, but no measured kayak resistance or GZ data exists in the repository. The project explicitly tracks this as operator action (D006 author outreach, D007/D014 commissioned campaign). Resistance estimates remain `uncalibrated_comparative`.

- **CFD succeeded path is env-gated.** The real OpenFOAM path works but requires `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and a sourced OpenFOAM-v2512 toolchain. Without these, CFD jobs remain in `unavailable` or `mock_failed` state. The `claim_state` of any succeeded CFD result stays `raw_unvalidated`.

- **`LCB_frac` on `Hull` is reserved but not honored.** The field exists (RFC 0006) but the loft does not yet use it to shift longitudinal centre of buoyancy. The field is documented as "Reserved by RFC 0006; not yet honoured by the loft."

- **Desktop GUI is a secondary surface.** Per D009, full desktop parity with the web workspace is "intentionally not a goal." The desktop GUI has feature gaps vs the web frontend (e.g., missing constraint surfacing, no generative search panel).

- **Root-level shims are legacy.** `generator.py`, `gui.py`, `pyvista_view.py` at repo root are thin re-export shims (57, 11, 7 lines) for backwards compatibility. They exist so legacy scripts and tests that import from the old locations continue to work.

- **No hosted public demo.** Per D023, the public hosted demo is deferred indefinitely. The web frontend is local-only (`127.0.0.1:8080`).

- **`distribution_v2` refuses non-default rake.** When `geometry_kind='distribution_v2'`, `bow_rake` and `stern_rake` must be 1.0 or the model raises. Rake is controlled by the explicit distributions in v2, not the legacy loft parameters. This is a validation that may surprise users migrating hulls.

- **Test suite is large but not read in full.** 92 test files exist. The conftest.py (14K) suggests substantial fixture infrastructure including golden tests. The project maintains byte-stable golden output for the lofted geometry.
