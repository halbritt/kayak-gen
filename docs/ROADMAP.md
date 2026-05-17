# Roadmap

Updated: 2026-05-17

This roadmap is the contributor-facing reconciliation point for the current
RFC index, the older deferred workflow queue, and the workflow 0048 successor
RFC backlog. The RFC index remains authoritative for RFC status. The PRD and
user guide remain authoritative for current user-facing behavior. This file
answers a narrower planning question: what work is still outstanding, what is
blocked, and how should future Striatum implementation batches be cut?

## Status Vocabulary

- `ready-now`: dependencies and scope are clear enough for a focused Striatum
  workflow.
- `partial`: a safe slice landed, but remaining acceptance criteria or parity
  work are still open.
- `evidence-gated`: a workflow may prepare structure or review packets, but
  product promotion requires named evidence such as source rights, diagnostic
  hashes, fixture manifests, or accepted fit records.
- `blocked`: a design, source, solver, operations, or infrastructure decision
  is required before implementation should start.
- `background`: useful context retained for traceability, not the current
  implementation target.
- `superseded`: replaced by a successor RFC or workflow path; stale jobs should
  not be claimed.
- `completed-history`: landed work retained only to explain how the roadmap got
  here.

Queue dispositions use the same language, with `still-open` meaning an old
queue item has residual work mapped to a current track below.

## No-Claims Rules

Future roadmap and workflow text must preserve these boundaries unless a later
accepted RFC and implementation artifact provide evidence:

- Resistance output is `uncalibrated_comparative`, a raw comparative filter,
  not a calibrated model, final prediction, design-fitness score, or default
  optimization objective.
- CFD output is local dispatch state, `raw_unvalidated` output, `fixture_only`
  records, or explicit unavailable/failed state. There is no accepted
  OpenFOAM, SU2, Docker, hosted-worker, or other real solver success path.
- Open hull/deck STLs and ordinary generated mesh packages are inspection or
  open-surface candidate artifacts. Only the narrow fixture-backed handoff path
  can report `cfd_ready`; production volume meshing and ordinary watertight
  solver readiness remain roadmap work.
- Generated closed bodies are evaluation evidence, not production solver input,
  unless matching body diagnostics, self-intersection evidence, volume-mesh
  evidence, hashes, artifacts, and solver profile gates all pass.
- High-angle `GZ`, `GZ_max`, range-of-positive-stability, capsize-range, and
  secondary-stability metrics are unavailable for real generated kayaks until
  a generated-body evidence gate and accepted heeled integration model land.
- Class validity, advisory badges, and design warnings are not proof of
  seaworthiness, safety, calibrated performance, final design fitness, or
  solver readiness.
- The web frontend is local/browser-capable with runbook coverage, not a
  completed public hosted demo, full dashboard parity, hosted CFD system, or
  desktop parity rewrite.

## Workflow 0050 Decision Posture

Workflow 0050 resolved the open design panels by strict two-of-three majority
rule. These are decisions about sequencing and admissibility, not delivered
runtime capability:

- Solver readiness starts with an RFC 0040 readiness report, then structured
  volume-mesh diagnostics, blocker/warning records, evidence hashes, boundary
  metadata, and generated-body hardening. Current `cfd_ready` remains the
  narrow fixture-backed path only.
- The first external CFD solver target is OpenFOAM.com OpenFOAM-v2512
  `interFoam`, profile `openfoam-v2512-interfoam-local`, behind
  `watertight_solid_resistance_v1` / `cfd_ready` evidence. A real
  `succeeded` path remains blocked until matching volume-mesh evidence exists.
- Resistance source work starts with source-review packets and source-use
  mapping tests. No current source is promoted to validation or calibration
  fixture by the decision.
- Calibrated resistance remains blocked behind RFC 0042 source acceptance and
  a later accepted-fit workflow with immutable model version, fit metrics,
  residuals, and validity envelope checks.
- High-angle stability v1 is a fixed-upright-trim hydrostatic comparator over
  `generated_hull_plus_deck_closed_body_v1`; real generated-kayak values stay
  unavailable until the model, per-heel diagnostics, and user-surface gates
  land.
- Browser hosting may proceed only as a narrow server-backed exploratory demo
  using `kayakgen serve` or the repo Docker path, with an operator owner,
  budget/cap, hosted smoke, bounded persistence, and no production or hosted
  CFD claims.
- The Trame web workspace is the primary UI composition target. The desktop GUI
  remains supported for local launch, implemented sliders, 3D preview, STL
  export, and no-claim/status maintenance; full native parity is not a goal.
- Sweep/comparison defaults remain `GM0_m`, `displacement_error_kg`, and
  `mesh_problem_count` when present. Raw resistance is explicit exploratory
  comparison only, and optimizer work waits for RFC 0009's remaining deltas
  plus objective metadata.

## Workflow 0052 Decision Posture

Workflow 0052 resolved the successor panels by strict two-of-three majority
rule. These are follow-up design and sequencing decisions, not delivered
runtime capability:

- The first production volume-mesher candidate for RFC 0040 is
  OpenFOAM.com OpenFOAM-v2512 `snappyHexMesh`, under a profile such as
  `openfoam-v2512-snappyhexmesh-watertight-v1`, implemented first as a
  deterministic evidence harness over
  `generated_hull_plus_deck_closed_body_v1`. It must record `checkMesh`,
  patch, artifact-hash, and dispatch evidence; it does not promote ordinary
  packages or enable real solver success.
- `openfoam-v2512-interfoam-local` remains unable to return `succeeded` until
  one run record binds accepted OpenFOAM-readable volume-mesh evidence,
  OpenFOAM.com v2512 provenance, deterministic case smoke, a v2512-correct
  `force.dat` parser, and raw-unvalidated no-claims payloads.
- The first full resistance source-review packet is the University of
  Edinburgh DataShare Pacific-canoe hydrodynamics dataset, capped at
  `validation_fixture`; it is explicitly not a calibration fixture.
- Fixed-trim generated-body v1 high-angle `GZ` may be surfaced only through a
  staged opt-in path: CLI JSON first, opt-in sweep artifacts next,
  display-only comparison/web read models after that, and minimal desktop
  support last. Defaults and objective/frontier behavior remain unchanged.
- Public browser operation remains deferred. Once operator and budget evidence
  exists, the authorized path is one fixed-size managed container running the
  existing `kayakgen serve --host 0.0.0.0 --port 8080` or repo Docker path,
  with no public-service SLA, production hosting, or hosted CFD claim.
- Workflow 0053 lands the RFC 0009 `pending` candidate lifecycle state:
  `pending_count`, resume preservation, and visible-but-frontier-ineligible
  comparison rows are now present. Sweep-side STL artifacts and active
  optimizer/search remain later work.

## Dependency Tracks

| Track | Current state | Roadmap status | Next work |
| --- | --- | --- | --- |
| Docs, status, and claim hygiene | PRD, user guide, RFC index, changelog, and this roadmap describe current limits. | `ready-now` | Keep these files synchronized after each RFC/workflow landing. Reconcile stale RFC labels before using them as implementation authority. |
| UI and web maintenance | RFCs 0033-0035 landed conservative UI slices; RFCs 0036-0039 landed in the 2026-05-15 cowboy pass (Trame listener proof, subtitle-only export schema, disabled-copy polish, shared web snapshot schema). Workflow 0050 makes the web workspace primary and desktop supporting. | `completed-history` | Reserve future UI cleanup as small, narrow batches only. Do not fund full native desktop parity unless a later decision records a need. |
| Browser hosting and parity | RFC 0008 is partial; RFC 0032 landed local browser acceptance and hosted-demo docs; workflows 0050 and 0052 keep public operation narrow and evidence-gated. | `partial` / `blocked` | Keep public operation deferred until owner, budget/cap, deployment revision, hosted smoke, persistence limits, cleanup receipt, and public no-claims wording are recorded. If those gates pass, use one fixed-size managed container on the existing serve/Docker path. Static/Pyodide and production hosted app paths require separate RFCs. |
| Geometry and mesh evidence | RFCs 0021-0023 and 0028 landed diagnostics, generated-body, fixture-handoff, and plumb-stem safe slices; workflow 0051 landed a readiness report; cowboy 2026-05-15 landed RFC 0040 generated-body parameter-matrix hardening (55-case test surface), the `snappyHexMesh` evidence-harness contract, and the real `snappyHexMesh` executor under `kayakgen/eval/cfd/openfoam_v2512_interfoam/`. With `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` the harness binds real polyMesh artifact checksums, real `CheckMeshSummary`, and real v2512 provenance; without the env knob the contract still rejects partial evidence. | `partial` / `evidence-gated` | Measured/validated CFD output, hosted execution, and watertight `cfd_ready` promotion of ordinary generated packages remain later workflows. |
| CFD dispatch and real adapter | All of D012 has landed: RFC 0015 local dispatch, RFC 0018 local web routes, RFC 0026 fixture-local-command, the workflow 0051 OpenFOAM skeleton, the cowboy 2026-05-15 case-template lock + provenance probe + parser, AND the real `openfoam-v2512-interfoam-local` `succeeded` path under opt-in env knobs (`KAYAKGEN_OPENFOAM_LOCAL_RUN=1`). `kayakgen/eval/cfd/openfoam_v2512_interfoam/` renders the case from `OpenFoamCaseSpec`; `runner` executes mesh + solve via the OpenFOAM bashrc; `evidence` binds dict hashes, polyMesh artifact checksums, real `CheckMeshSummary`, patches, and `OpenFoamProvenanceProbe` into a `SnappyHexMeshEvidence(dispatch_state="evidence_recorded")`. End-to-end smoke takes ~10.7s on a default hull. | `partial` | `claim_state` stays `raw_unvalidated`; defaults are unchanged. Measured validation, calibration, drag-convergence sanity, and hosted execution remain later workflows. |
| Resistance evidence and calibration | RFC 0005 landed only as raw filter; RFC 0025/0027 landed claim gates; workflows 0050 and 0052 preserve the calibration no-promotion gate; cowboy 2026-05-15 landed RFC 0042 source-review packet validators, downloaded and vendored the Edinburgh DataShare bundle (DOI 10.7488/ds/3785, CC BY 4.0) under `tests/fixtures/calibration/edinburgh/`, and rewrote the extractor against the real workbook schema. The Edinburgh packet now binds the workbook SHA-256 and reports `is_validation_fixture_ready() = True`. | `partial` / `evidence-gated` | Calibration fixture promotion still waits for an in-envelope measured kayak/surfski source plus an accepted-fit workflow per decision D006. Edinburgh remains capped at validation-fixture eligibility by `outside_sea_kayak_calibration_envelope`. |
| Stability and high-angle `GZ` | RFC 0011 landed load cases; RFC 0014 landed upright trim; RFC 0024 landed structured unavailable/fixture-only handoff; workflow 0051 landed generated-body v1 evaluator plumbing; cowboy 2026-05-15 landed RFC 0043 stages 1-3 (CLI JSON opt-in, sweep `high_angle_gz` evaluator and artifacts, comparison-side display-only read model with `HighAngleGzObjectiveRefusedError` gate, and Trame web comparison surface). Stage 4 desktop is intentionally minimal (D021). | `partial` / `evidence-gated` | Defaults, frontiers, and objectives stay on the current conservative posture; high-angle GZ remains `unvalidated_hydrostatic_comparison` until measured validation lands. |
| Sweeps, comparison, and search | `kayakgen sweep` and `compare` are user-facing. RFC 0009 is partial landed; RFC 0013 has a landed report/web slice; workflow 0051 added objective metadata; workflow 0053 landed `pending` lifecycle; cowboy 2026-05-15 landed sweep-side STL artifact emission; cowboy 2026-05-16 landed RFC 0044 v1 NSGA-II and RFC 0047 v2 EHVI (vendored Cholesky GP + EHVI for 1-3 objectives) under the additive opt-in `kayakgen search` CLI; cowboy 2026-05-17 landed RFC 0049 ArtifactStore + identity normalization (`Hull.{record,design}_hash`, `FilesystemArtifactStore`, `SqliteIndex`, `kayakgen runs` sub-app) and Phase 5 metric-registry centralization (display formatting, admissibility helpers, `display_only` role). | `landed` | Future RFCs cover v3 successor algorithms (transfer-learning, library-level surrogate reuse) and any registry expansions. |
| Inverse design and reporting | Not in the original track list; landed cowboy 2026-05-17. RFC 0050 `kayakgen target-draft` / `target-trim` solve inverse load-from-draft and trim-from-load. RFC 0051 `kayakgen build-export` writes builder-oriented offsets/DXF/SVG artifacts under `kayakgen[builder]` extras. RFC 0052 `kayakgen sensitivity` writes a central-difference Jacobian and adds a within-evaluator-noise advisory to the comparison report. RFC 0053 `--turning` flag + sweep evaluator emits an opt-in display-only `TurningMetrics` block. RFC 0055 `kayakgen design-report` renders a self-contained HTML (+ optional PDF) under `kayakgen[report]` extras. | `landed` | Future RFCs may add Monte-Carlo uncertainty propagation, multi-sheet plot layouts, additional metric registries, or a non-jinja2 renderer. |
| Geometry V2 distribution model | RFC 0048 landed cowboy 2026-05-17 as `geometry_kind="distribution_v2"` on `Hull` plus a `DistributionV2Spec` with six cross-section families, explicit LCB / deadrise / chine-radius / bow-flare controls, an advisory hydrostatic cross-check (1% volume/Aw/LCB, 0.5% GM0), and a `kayakgen migrate-geometry` CLI. Default lofted hull behaviour is byte-stable. | `landed` | Future RFCs may widen chine count beyond 4, add cross-section families, or supersede `distribution_v2` with a `v3` that adds explicit waterline-fairness controls. |
| Calibration-campaign tooling | RFC 0054 landed cowboy 2026-05-17 as `kayakgen calibration` sub-app (ingest-tank-test, ingest-inclining-test, accept-fit, residual-plot) plus tank/inclining/AcceptedFitRecord schemas and the validator wiring that resolves `accepted_fit_ref` on disk. | `landed` (on-disk plumbing) / still operator-blocked for D006 | The schemas are ready; an actual operator-run measurement campaign (Pendergast/Gomes outreach or commissioned tank time) is the unblocking action. RFC 0056 sketches the strain-gauged moment-arm rig design for high-angle GZ measurements (D007/D014). |

## Future Striatum Batches

### Batch A: Roadmap And Status Maintenance

Status: `ready-now`

Scope: keep `docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/rfcs/README.md`,
`docs/ROADMAP.md`, `CHANGELOG.md`, and workflow-local reports aligned after
each landing. This includes correcting stale RFC status labels and moving old
queue entries to completed, background, superseded, or still-open disposition.

Exit criteria: docs distinguish delivered behavior from roadmap deferrals and
do not claim calibrated resistance, real CFD success, production volume
meshing, final prediction, design fitness, or real high-angle stability.

### Batch B: UI Cleanup Successors

Status: `completed-history` (landed 2026-05-15)

Scope: RFCs 0036-0039. Workflow 0050 also settles the broader UI strategy:
the web workspace is primary for new UI composition, while the desktop GUI
remains a supported local surface.

- RFC 0036: prove the Trame same-seed preset listener path through browser
  automation or remove it with equivalent regression coverage.
- RFC 0037: collapse export-row guidance to canonical `subtitle` ownership.
- RFC 0038: polish disabled Mesh package export copy after or with RFC 0037.
- RFC 0039: unify web snapshot keys and CFD alias metadata while preserving
  public REST payload shapes.

Exit criteria: behavior, export availability, backend capability, and no-claim
copy remain unchanged except for explicitly accepted visible copy polish.
No workflow in this batch should reopen a full native desktop rewrite or
desktop deprecation.

### Batch C: Browser Hosting And Parity

Status: `partial` / `blocked`

Scope: RFC 0008, RFC 0030, RFC 0032, and the unresolved UI parity portions of
RFC 0033. Workflow 0050 chose a narrow server-backed exploratory public demo as
the only current hosting posture; workflow 0052 keeps public operation deferred
until owner, budget, hosted-smoke, persistence, and cleanup evidence exists.

Work should be split into small workflows:

- public hosted demo operation using one fixed-size managed container running
  the documented local command/Docker path, but only after an operator owner,
  budget/cap or hard limit, provider/account/region/tier, deployment revision,
  hosted smoke, persistence limits, cleanup receipt, and
  no-SLA/no-hosted-CFD wording are recorded;
- console-clean and Lighthouse acceptance upkeep;
- full plot/dashboard parity beyond compact analysis;
- desktop shell or embedding work only if a later workflow records a user or
  operator need; full native desktop parity is not the current goal;
- mobile/view-only acceptance only after the desktop browser path is stable.

Exit criteria: each workflow states exactly which browser or parity criterion
it closes and does not imply hosted CFD workers, web-side mesh-package
authoring, real solvers, calibrated outputs, production hosting, static/Pyodide
runtime support, or public-service SLA.

### Batch D: Geometry Evidence And Solver Readiness

Status: `partial` / `evidence-gated` (steps 1-3 landed 2026-05-15; ordinary-package promotion still gated)

Scope: RFC 0040 over RFCs 0010, 0016, 0021, 0022, 0023, 0028, and related
partials from RFCs 0004/0006.

Progress and remaining order:

1. Generated-body parameter-matrix hardening (`tests/test_generated_closed_body_hardening.py`)
   covers default, plumb, mixed-rake, `beam_wl_m != beam_oa_m`, draft, `Cp`,
   and `Cm` cases.
2. Add the OpenFOAM-v2512 `snappyHexMesh` evidence harness profile
   `openfoam-v2512-snappyhexmesh-watertight-v1` or its accepted successor.
3. Render deterministic meshing cases from generated closed-body evidence and
   record body refs, diagnostic hashes, OpenFOAM.com v2512 provenance,
   dictionary hashes, patch metadata, `checkMesh`, quality summaries,
   artifact checksums, warnings, and blockers.
4. Gate mesh-package handoff and dispatch preparation on matching
   OpenFOAM-readable evidence.

Exit criteria: ordinary generated packages still remain below
watertight-required solver-profile acceptance unless matching evidence exists.
Any fixture evidence is labeled as fixture evidence, and a passing meshing
harness run is OpenFOAM-readable evidence, not validated CFD or solver success.

### Batch E: Real CFD Adapter Decision And Implementation

Status: `landed` (real `openfoam-v2512-interfoam-local` `succeeded` path under opt-in env knobs landed 2026-05-15; raw_unvalidated)

Scope: RFC 0041, with RFC 0017 as background and RFC 0026 as the landed
fixture boundary. Workflow 0050 selected OpenFOAM.com OpenFOAM-v2512
`interFoam` as the first external solver target.

Prerequisites and success gate:

- selected solver profile `openfoam-v2512-interfoam-local`;
- required mesh profile `watertight_solid_resistance_v1` and readiness
  `cfd_ready`;
- case-template version `openfoam-v2512-interfoam-dtchull-v1`;
- accepted OpenFOAM-readable volume-mesh evidence from the selected RFC 0040
  profile;
- OpenFOAM.com v2512 provenance from application/build/API probes, not only
  `$WM_PROJECT_VERSION`;
- deterministic v2512 `interFoam` smoke with a real `polyMesh`, two-phase
  properties, required fields, and a `forces` object over the mapped hull patch;
- a corrected parser for the v2512 `postProcessing/forces/**/force.dat` schema;
- Linux primary platform note, with macOS/Windows optional Docker/WSL/source
  routes;
- required tests that do not require the solver binary.

Exit criteria: until all gate items bind in one run record, parser-readable
output remains `solver_success_blocked`. After the gate opens, `succeeded`
means only local solver execution plus raw artifact parsing; successful records
remain `raw_unvalidated` and carry no validation, calibration, final
prediction, design-fitness, or broad readiness claim.

### Batch F: Resistance Source Evidence

Status: `partial` / `evidence-gated` (Edinburgh data acquisition + real extractor + checksum-bound packet landed 2026-05-15; calibration still envelope-blocked)

Scope: RFC 0042, with RFC 0019 as background and RFC 0027 as the claim-gate
authority. Workflow 0050 selected source-review-first and kept calibrated
resistance in the current no-promotion state.

Recommended order:

1. Complete the first full source-review packet for the Edinburgh DataShare
   Pacific-canoe source, binding locators, access dates, checksums, license,
   attribution, extraction script, units, Froude basis, and uncertainty notes.
2. Cap Edinburgh's positive outcome at `validation_fixture` and preserve
   `outside_sea_kayak_calibration_envelope` or an equivalent calibration
   blocker.
3. Add source-use mapping checks so `rejected` stays a review outcome, not a
   runtime fixture source-use value.
4. Pursue K1, sea-kayak, or surfski sources only after rights, measured rows,
   geometry/load metadata, and uncertainty evidence are accepted.
5. Add calibration fixture ingest only after a kayak-envelope measured source
   is accepted.
6. Defer fitting and calibrated-output wording to a separate accepted-fit
   workflow with immutable model version, fit metrics/residuals, and validity
   envelope membership.

Exit criteria: current curves keep `uncalibrated_comparative` warnings until a
named model version has accepted fit evidence, calibration fixture IDs, fit
metrics, and a validity envelope that contains the evaluated hull and speed.

### Batch G: High-Angle Stability Design Gate

Status: `partial` / `evidence-gated` (stages 1-3 landed 2026-05-15; stage 4 desktop intentionally minimal per D021)

Scope: RFC 0043, preserving RFC 0024's structured unavailable handoff.
Workflow 0050 selected fixed-trim generated-body v1 as the first real model
design; workflow 0052 selects staged, explicit product surfacing.

Prerequisites:

- generated-body evidence accepted for stability use;
- `generated_hull_plus_deck_closed_body_v1` as the v1 body profile;
- default 0-90 degree heel grid by 5 degrees, with caller-supplied strictly
  increasing grids echoed exactly;
- fixed upright trim with per-heel sinkage/displacement solve and unsolved
  longitudinal-moment residuals;
- hull-fixed passive CG convention;
- waterline clipping/capping diagnostics distinct from body diagnostics;
- per-heel status/residual/iteration metadata;
- sealed-body, deck-immersion, flooding/downflooding-not-modeled, active
  paddler-not-modeled, and no-safety/no-seaworthiness warnings.

Product surfacing order:

1. Add explicit CLI JSON output while default `kayakgen stability` remains
   unchanged.
2. Add an opt-in sweep evaluator that writes artifacts without adding numeric
   high-angle fields to default summaries or frontiers.
3. Add display-only comparison and web read models with body/load/trim
   provenance and warnings adjacent to any plot or table.
4. Keep desktop support minimal and behind shared read models.

Exit criteria: until all surface gates pass, defaults continue to show
unavailable results rather than numeric high-angle `GZ` or secondary-stability
summaries. Fixture-only math tests cannot satisfy user-facing stability claims
or ranking. Once surfaced, v1 results are unvalidated hydrostatic comparison
curves, not safety, seaworthiness, capsize, validation, design-fitness, or
solver-readiness claims.

### Batch H: Sweep, Comparison, And Optimization

Status: `landed` (pending lifecycle, sweep-side STL artifacts, and RFC 0044 v1 NSGA-II active search all landed; successor algorithms remain future-RFC scope)

Scope: RFC 0009, RFC 0013, future search/optimization RFCs.

RFC 0009 is now reconciled with the current user-facing sweep command and
run-record behavior. Workflow 0053 landed the `pending` candidate lifecycle:
candidate records for planned work, additive `pending_count`, explicit
transition/resume semantics, and visible-but-frontier-ineligible pending rows.
The 2026-05-15 cowboy session landed sweep-side STL artifact emission with
`stl_artifacts` records (path/bytes/sha256). The 2026-05-16 cowboy session
landed RFC 0044 v1 active search: a `kayakgen search` CLI subcommand
backed by a vendored NSGA-II implementation in `kayakgen/search/active/`,
seeded determinism, exploratory-mode tagging, and a hard
claim-admissibility gate (token
`RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`). Successor algorithms
(Bayesian optimization with GP surrogates, EHVI, MOEA/D) require a future
RFC; v1 is multi-objective NSGA-II only.

Exit criteria: candidate comparison can use only metrics whose claim state and
availability are explicit. Optimization must not silently treat raw resistance,
raw CFD, advisory validity, pending candidates, or unavailable stability as
final design fitness. Default Pareto objectives remain `GM0_m`,
`displacement_error_kg`, and `mesh_problem_count` when present; raw resistance
is explicit exploratory comparison only.

## Current RFC Disposition

| RFCs | Current disposition | Roadmap status |
| --- | --- | --- |
| 0004, 0028 | Historical plumb-bow and current plumb-stem closure semantics are partial safe slices. Independent `stern_rake` and generated closed-body cap/ring semantics exist, but open STLs remain inspection surfaces and broader solver readiness maps to RFC 0040. | `partial` |
| 0005, 0012, 0019, 0025, 0027, 0042 | Raw analytical resistance landed; source registries and claim gates exist; workflow 0050 chose source-review-first, and workflow 0052 selected the Edinburgh DataShare source for validation-only full packet review. Calibrated-resistance promotion remains blocked. | `evidence-gated` |
| 0006, 0029, 0031 | Canonical constraints, presets, validity metadata, and surfacing slices landed. RFC 0029 is background superseded by RFC 0031. Future shape parameters and any remaining desktop/manual surfacing stay open only as focused follow-ups. | `partial` / `background` |
| 0008, 0030, 0032, 0033 | Local Trame shell, compact analysis, comparison loading, local browser acceptance, hosted-demo docs, and workspace safe slices landed. Workflow 0052 keeps public operation deferred until owner/budget/smoke/cleanup evidence exists, then allows only a fixed-container serve/Docker path. | `partial` / `blocked` |
| 0009, 0013 | RFC 0009 is now a partial landed sweep-run-record slice with `pending` candidate status, `pending_count`, and resume preservation; RFC 0013 comparison reports keep pending rows visible but frontier-ineligible. Workflow 0051 added objective metadata, and workflow 0052 selected `pending` lifecycle as the next delta before STLs or optimizer/search. | `partial` |
| 0011, 0014, 0020, 0024, 0043 | Load cases and upright trim landed; high-angle `GZ` is structured unavailable or fixture-only on default product surfaces. Cowboy 2026-05-15 landed RFC 0043 stage 1 opt-in CLI JSON surfacing (`kayakgen stability --high-angle-gz`); defaults, sweep summaries, web read models, and desktop surfaces are unchanged. | `partial` / `evidence-gated` |
| 0015, 0017, 0018, 0026, 0041 | Local dispatch, local web routes, unavailable/mock states, fixture-local-command, and the OpenFOAM skeleton landed. Cowboy 2026-05-15 landed RFC 0041 partial: case-template lock (`openfoam-v2512-interfoam-dtchull-v1`), `OpenFoamProvenanceProbe` with injectable runner that refuses env-only evidence, and a v2512-strict force.dat parser. `succeeded` is still blocked until matching mesh evidence binds. | `partial` / `evidence-gated` |
| 0010, 0016, 0021, 0022, 0023, 0040 | Mesh packages, synthetic diagnostics, self-intersection checks, generated body construction, and fixture handoff landed. Cowboy 2026-05-15 landed RFC 0040 generated-body parameter-matrix hardening (55-case test surface) without widening solver readiness. The `snappyHexMesh` evidence harness remains the next step. | `partial` / `evidence-gated` |
| 0034, 0035 | Workspace follow-up and UI cleanup safe slices landed. Residual workflow 0047 final-review findings became RFCs 0036-0039, and workflow 0053 added browser initial-query regression coverage without changing UI backend capability. | `completed-history` |
| 0036, 0037, 0038, 0039 | Landed as small UI-maintenance safe slices: RFC 0036 retained `_state_matches_preset_seed` with a Trame-state listener proof, RFC 0037's `EXPORT_MENU_ROWS` schema is subtitle-only, RFC 0038 polished the disabled mesh-package label, and RFC 0039 collapsed snapshot/CFD aliases onto `WebStateSchema`. No backend or capability changes. | `completed-history` |

## Deferred Queue Reconciliation

`docs/workflows/0018-deferred-backlog/QUEUE.md` is historical. It still frames
0026-0031 as the active queue, but current planning runs through RFC 0043.
Use this table instead of claiming the stale queue prompts directly.

| Old queue item | Disposition | Current mapping |
| --- | --- | --- |
| 0019 legacy RFC partial closure | `completed-history` with residual `still-open` work | Safe package/core slices landed. Later RFC 0028 addressed independent rake and generated closed-body plumb semantics. Production solver readiness maps to RFC 0040. |
| 0020 browser acceptance and demo | `partial` / `still-open` | Headless, browser smoke, local browser acceptance, and hosted-demo docs advanced. Public hosted operation, console-clean/Lighthouse upkeep, full plot/dashboard parity, and desktop parity rewrite stay in browser/parity batches. |
| 0021 web plots and comparison UI | `completed-history` | Compact web analysis/comparison and report loading landed. Richer dashboard work is new UI/browser scope. |
| 0022 generalized trim and GZ stability | `partial` / `still-open` | Load components and upright trim landed. Real high-angle stability maps to RFC 0043. |
| 0023 resistance calibration dataset vetting | `background` | Pacific-canoe metadata remains validation-only source context. Fixture promotion maps to RFC 0042. |
| 0024 watertight solid mesh profile | `partial` / `still-open` | Blocked profile and fixture-backed handoff exist. Production volume meshing and real solver-readiness promotion map to RFC 0040. |
| 0025 CFD solver dispatch and jobs | `partial` / `still-open` | Local job/profile/run plumbing landed. Real solver execution, Docker/container execution, hosted workers, and validated outputs map to RFC 0041 and later validation/calibration work. |
| 0029 web CFD job routes history entry | `partial` / `still-open` | Local `/api/cfd/*` routes and panel landed. Hosted queues, auth, cancellation guarantees, web-side mesh-package creation, and real solver success remain future scope. |
| 0026 docs roadmap and user guide | `completed-history` | User-facing docs reconciliation landed. Workflow 0049 replaces the stale queue with this roadmap. |
| 0027 closed-volume geometry contract | `superseded` as a queue prompt, with residual `still-open` work | Safe slices landed across RFCs 0021-0023 and 0028. Future production solver-readiness evidence maps to RFC 0040. |
| 0028 real CFD solver adapter | `superseded` / `still-open` | The fixture adapter landed under RFC 0026. External solver work now maps to RFC 0041 and remains blocked on solver/profile decisions. |
| 0029 web CFD job routes queued section | `completed-history` for local route slice, residual `still-open` work | Duplicate of the history entry. Keep the local-web-dispatch summary and map hosted/real-solver web concerns to browser parity and RFC 0041. |
| 0030 resistance calibration fixture | `superseded` / `evidence-gated` | RFC 0042 narrows this to source review and fixture promotion before any calibration or fit workflow. |
| 0031 high-angle `GZ` and secondary stability | `superseded` / `blocked` | RFC 0024 landed structured unavailable handoff. RFC 0043 is the successor design gate for any real generated-kayak high-angle `GZ`. |

## Scheduling Guidance

- Start with `ready-now` UI cleanup and docs/status maintenance when the goal is
  fast backlog burn-down.
- Do not parallelize two batches that write the same UI schema/copy surface
  unless one workflow explicitly owns integration; RFC 0037 and RFC 0038 are
  the known dependency pair.
- Do not start real solver success work before OpenFOAM-readable mesh evidence,
  v2512 provenance, deterministic smoke, corrected parser semantics, and
  raw-unvalidated payload gates are written down and implemented together.
- Do not start public-demo operation before owner, budget/cap, deployment,
  hosted-smoke, bounded-persistence, cleanup, and no-claims evidence exists.
- Do not surface high-angle `GZ` outside the staged opt-in path. Fixture-only
  numerical tests may precede product output only if every artifact is labeled
  `fixture_only`.
- Do not start calibrated resistance fitting before at least one kayak-envelope
  measured source is accepted as a calibration fixture with rights, extraction,
  units, fit metadata, and validity envelope.
- Implement `pending` lifecycle before sweep-side STL artifacts or active
  optimizer/search. Treat optimization/search as a later consumer of evidence,
  not as a shortcut around missing calibration, stability, or solver-readiness
  decisions.
