---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_c8c122cd9ec1436eb02e8e357e579829
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_openfoam_success_gate_claude
lease: lease_0742b402d08d4de8896f24d2f9497e93

# Panel Vote — OpenFOAM Success Gate

## Vote

**Option A — Keep `openfoam-v2512-interfoam-local` unable to return `succeeded`
until every named gate (production OpenFOAM-readable volume-mesh evidence;
installed-solver provenance from `interFoam -help-full` / build-info / API
probes, not `$WM_PROJECT_VERSION` alone; deterministic v2512 `interFoam` case
with real `polyMesh`, two-phase properties, required fields, and `forces`
function object; corrected v2512 `force.dat` parser; and persistent
`raw_unvalidated` / `accepted_uses=[]` labeling) is satisfied in one run
record. Reject Options B (fixture-only success profile), C (two-stage smoke
result with a separate "completed_unvalidated" status), and D (case-generation
first, success later) as the *first* decision.**

The five gate conditions named here are the same five conditions the research
packet recommends; the vote is to make them the explicit, machine-checkable
exit criteria of D004's "no real `succeeded`" clause, not a successor refinement.

## Decision Sentence For `docs/DECISION_LOG.md`

The `openfoam-v2512-interfoam-local` profile must not return `succeeded` until
all of the following are simultaneously true in one run record: (1) the prepared
job carries `watertight_solid_resistance_v1` / `cfd_ready` evidence whose volume
mesh is an OpenFOAM-readable `polyMesh` (or an equivalent conversion manifest
with checksum-verified `polyMesh` output), bound by `body_ref`, body hash, hull
hash, tolerance hash, units, coordinate system, mesher provenance, OpenFOAM
boundary patch names, patch roles/markers (including an explicit
checksum-recorded mapping of the wetted-body wall patch to the case's `forces`
patch — initially `hull` to match the upstream DTC case), quality summaries,
warnings, and blockers, plus `checkMesh` evidence (command, version/build
provenance, exit status, retained summary/log artifacts); (2) the run record
captures installed OpenFOAM.com v2512 `interFoam` provenance from application
banner/build (`interFoam -help-full`), parseable release/API metadata
(`wmake -build-info` and/or `foamEtcFile -show-api`/`-show-patch`), resolved
executable paths/hashes when feasible, and environment-capture metadata
(`WM_PROJECT_DIR`, `WM_PROJECT_VERSION`, environment-source) marked as
supporting context only — `WM_PROJECT_VERSION` alone is not the gate; (3) the
rendered case is the deterministic
`openfoam-v2512-interfoam-dtchull-v1` `interFoam` case with a real `polyMesh`,
`application interFoam`, two-phase transport properties (water and air),
required initialized fields `U` and `p_rgh`, `alpha.water` phase initialization,
and a `forces` function object over the mapped hull patch, run under explicit
local-only opt-in (`KAYAKGEN_ENABLE_OPENFOAM=1` or an equivalent named flag),
with output isolation and bounded timeout/log caps; (4) the force parser is
corrected to the v2512 `force.dat` schema — total, pressure, viscous, optional
porous — and stamped with `parser_schema=openfoam-v2512-forces-v1`, accepts
`postProcessing/forces/**/force.dat` (selecting a deterministic final usable
time row), rejects ambiguous multiple force streams, empty files, nonfinite
values, malformed rows, impossible vector counts, missing hull-patch/
function-object provenance, and any header whose schema does not match the
declared parser version; and (5) the resulting run record, CLI output,
REST/web payloads, and persisted artifacts continue to carry
`claim_state=raw_unvalidated`, `accepted_uses=[]`, and explicit warnings that
local OpenFOAM completion is not validation, calibration, mesh independence,
turbulence/free-surface settling, timestep convergence, measured-benchmark
comparison, design fitness, safety, or seaworthiness — together with
provenance references for mesh, case template, solver, parser, and raw output.
Until all five are true in the same run record,
`error_kind="solver_success_blocked"` (the current behavior at
`kayakgen/eval/cfd/jobs.py:1166-1175`) is the correct outcome, including when a
fake command writes parser-readable `force.dat`. Version family mismatch,
OpenFOAM.com / Foundation ambiguity, missing build/API metadata,
unsupported case-template version, missing `polyMesh`, missing
hull-patch mapping, missing `interFoam`, command timeout/nonzero exit,
`checkMesh` failure, missing `force.dat`, parser schema mismatch, and
artifact-checksum mismatch must remain hard unavailable/failed states, not
warnings that still permit success. This decision authorizes implementation of
the corrected parser and the named provenance probes, but does not by itself
authorize promotion of any mesh, evidence path, or fitting workflow; mesh
production remains gated on RFC 0040 and the existing RFC 0023 handoff. No
fixture-only `succeeded` profile is created.

## Evidence

### Research-Packet Evidence

`striatum/0052-successor-decision-research/research/openfoam_success_gate/RESEARCH.md`
enumerates the local constraints
(`docs/ROADMAP.md`, `docs/DECISION_LOG.md`, RFCs 0023/0025/0027/0040/0041) and
external evidence (OpenFOAM.com release page, OpenFOAM-v2512 release
announcement, GitLab tag list, README, `etc/bashrc`, command-line docs,
`interFoam.C`, `interFoam/createFields.H`, DTCHull `Allrun`, DTCHull
`controlDict`, DTCHull `snappyHexMeshDict`, DTCHull `transportProperties`, the
`forces` function-object docs, function-object output convention,
`forces.H`, `forces.C`, `snappyHexMesh` docs, and `checkMesh` manpage, all
accessed 2026-05-14) and recommends Option A with five must-hold gate clauses.
The packet's table of v2512 source citations is internally consistent and
supports each gate clause. The decision sentence above adopts those five
clauses verbatim as machine-enforceable exit criteria of D004's current
"no real `succeeded`" wording.

### Independent Check On Current Code

Every load-bearing claim about local behavior was re-verified by direct
read-only inspection in this session:

- **Profile identity matches D004.** `OPENFOAM_PROFILE_NAME =
  "openfoam-v2512-interfoam-local"` at `kayakgen/eval/cfd/jobs.py:44`;
  `OPENFOAM_SOLVER_NAME = "OpenFOAM.com OpenFOAM-v2512 interFoam"` at `:45`;
  `OPENFOAM_REQUIRED_VERSION = "v2512"` at `:46`;
  `OPENFOAM_CASE_TEMPLATE_VERSION = "openfoam-v2512-interfoam-dtchull-v1"` at
  `:47`. `openfoam_v2512_interfoam_local_profile()` at `:480-515` returns a
  `SolverProfile` with `required_mesh_readiness="cfd_ready"`,
  `required_mesh_profile="watertight_solid_resistance_v1"`,
  `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
  `command_template=["interFoam", "-case", OPENFOAM_CASE_ROOT]`,
  `solver_version_command=["foamVersion"]`,
  `supported_speed_range_mps=(0.1, 6.0)`,
  `expected_raw_outputs=[OPENFOAM_FORCE_DAT_OUTPUT]`,
  `timeout_seconds=60.0`, and `log_limit_bytes=65536`. The decision must not
  silently weaken these gates.
- **Success-blocked behavior already exists and is correct.** Even when the
  configured command exits zero and the parser reads `force.dat`,
  `OpenFoamLocalAdapter.run` at `kayakgen/eval/cfd/jobs.py:1146-1175` returns
  `SolverRawResult(status="failed", error_kind="solver_success_blocked",
  ...)` and persists the warning `OPENFOAM_SUCCESS_BLOCKED_WARNING` from
  `:58-61`. The decision must keep this branch as the terminal outcome until
  all five gate clauses pass, not relax it for "completed_unvalidated" or
  "fixture-only success."
- **Parser order is currently wrong for v2512 `forces.C` and must be a hard
  blocker.** `_parse_openfoam_force_dat_line` at
  `kayakgen/eval/cfd/jobs.py:1225-1248` extracts
  `pressure = values[1:4]`, `viscous = values[4:7]`, `porous = values[7:10]`,
  and computes `total = pressure + viscous + porous`. OpenFOAM-v2512
  `forces.C` (per the research packet) writes per-time row as
  `time, total, pressure, viscous, [porous]`, with the *first* vector after
  time being the total. The current parser therefore reads the v2512 total
  vector as pressure, the v2512 pressure vector as viscous, and the v2512
  viscous vector as porous, then sums them and reports the result as
  `total_force_n` and `drag_force_n = total[0]` (`:1240-1247`). Promoting
  this adapter to `succeeded` before the parser is corrected and stamped
  with `parser_schema=openfoam-v2512-forces-v1` would publish meaningless
  drag numbers under a `raw_unvalidated` label that downstream readers would
  still interpret as "OpenFOAM said." The decision must make this parser
  correction an explicit precondition.
- **Expected-output path is currently a single hard-coded time directory.**
  `OPENFOAM_FORCE_DAT_OUTPUT = "postProcessing/forces/0/force.dat"` at
  `kayakgen/eval/cfd/jobs.py:51`, and the profile's
  `expected_raw_outputs=[OPENFOAM_FORCE_DAT_OUTPUT]` at `:502` pins exactly
  the `0/` time directory. OpenFOAM's documented function-object output
  layout is `postProcessing/<functionObject>/<time>/...` (research packet),
  so any real run that writes to a non-zero time (the common case for the
  upstream DTC `Allrun`) will fall through to `missing_output` today, and a
  fake command targeting `0/force.dat` will be parsed even when the real
  case writes elsewhere. The decision authorizes loosening
  `expected_raw_outputs` to a globbed `postProcessing/forces/**/force.dat`
  pattern with deterministic final-usable-time-row selection — but only
  paired with the corrected parser schema and a check that rejects ambiguous
  multiple streams.
- **Mesh evidence gating is wired but holds open the synthetic loophole.**
  `prepare_local_job` (and the readiness ladder
  `READINESS_ORDER` at `:63-69`) require `cfd_ready` and the
  `watertight_solid_resistance_v1` mesh profile before the OpenFOAM adapter
  can be selected (`:1648`, `:1682-1685`). Today, only the
  fixture-backed RFC 0023 handoff produces `cfd_ready`. The decision must
  hold that line: a fixture `cfd_ready` package is sufficient for parser /
  dispatch / route tests, but it is *not* sufficient to enable a real
  `succeeded` outcome on the local profile. Workflow 0051 confirmed this
  posture: the OpenFOAM adapter skeleton landed without enabling
  `succeeded`, and the final review at
  `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:108-126`
  records that ordinary generated packages stay below `cfd_ready` and the
  fake parser-readable path remains `solver_success_blocked`.
- **Stale-output reuse is the single highest-risk regression path and is
  already prevented.** Workflow 0051 MF1 added
  `_clear_openfoam_run_outputs(case)` at `kayakgen/eval/cfd/jobs.py:1014`
  with `error_kind="output_cleanup_failed"` on cleanup failure, and the
  regression test at `tests/test_cfd_jobs.py:1242-1296` (per the workflow 0051
  final review) pins the second-run `missing_output` outcome. This decision
  must not authorize loosening that cleanup; in particular, an "optional"
  preserve-prior-run mode would re-open the same overclaim path.

### Independent Domain Check

`docs/design/kayak_hull_design_constraints.md` (§3, §4, §9, §10) frames the
project's kayak/surfski displacement-Fn envelope and `Re ~ 10⁶-10⁷` operating
regime, but does **not** authorize a "local OpenFOAM ran cleanly" claim to
substitute for accepted resistance or design-fitness evidence. RFC 0027
acceptance gates (Stage 2/3) and `claim_allows_calibrated_prediction` at
`kayakgen/eval/claims.py:195-210` keep calibrated/validated wording behind a
separate accepted-fit workflow with named calibration fixtures, fit metrics,
residuals, and a validity envelope that contains the evaluated hull and speed.
The current resistance evaluator's `uncalibrated_comparative` warning
(`docs/USER_GUIDE.md:102-104`) remains the authoritative output disposition
for resistance numbers regardless of whether the OpenFOAM adapter eventually
returns `succeeded`. The OpenFOAM success gate does not, and must not,
authorize calibrated wording, design-fitness wording, or final-prediction
wording on its raw force.dat outputs — even when all five gate clauses pass.

Domain note specific to kayak displacement hulls: the DTC tutorial's `hull`
patch and surface-following mesh setup (research packet, DTCHull
`snappyHexMeshDict` row) is well-aligned with kayak-class free-surface
resistance prediction in principle, but a deterministic mesh template alone
is not a calibrated solver setup — turbulence model selection, free-surface
resolution at the bow/stern, timestep choice for the PIMPLE outer loop, mesh
independence, and convergence assessment all sit beyond the gate this
decision opens. The gate authorizes "OpenFOAM read our mesh, ran `interFoam`,
and wrote a parser-readable `force.dat`," not "OpenFOAM produced a
physically meaningful drag prediction."

### External-Source Check

External sources are quoted from the research packet, which was authored
2026-05-14. `WebFetch` was not used in this session; every external citation
was treated as a research-packet quotation. The vote does not depend on a
contested external fact: every load-bearing gate clause is enforceable from
local code or local artifacts:

- The v2512 `force.dat` row order is a load-bearing external claim. It is
  highest-leverage for the integrator to harden by re-reading
  `https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/src/functionObjects/forces/forces/forces.C`
  (cited at research packet, row 16) before authorizing the parser change,
  because the entire D-level decision rests on it being `time, total,
  pressure, viscous, [porous]`. If `forces.C` instead emits the legacy
  pre-v2512 order, the parser correction direction reverses; the
  current code at `kayakgen/eval/cfd/jobs.py:1230-1248` would then be
  *correct* (modulo total-recomputation), and the gate clause would shift
  from "fix parser order" to "stamp parser schema and assert against the
  expected order." Either way, the decision still blocks `succeeded` until
  the parser schema is stamped and verified.
- The DTCHull patch name `hull` (research packet, DTCHull
  `snappyHexMeshDict` row) is the source of the gate's hull-patch-mapping
  clause. If the project ever uses a different generated-body patch name,
  the decision still holds because the requirement is for an explicit
  checksum-recorded mapping, not for the literal string `hull`.
- The OpenFOAM-v2512 startup environment guidance (`etc/bashrc` and README
  rows) supports the gate's "`WM_PROJECT_VERSION` alone is not the gate"
  clause: README explicitly warns that `$WM_PROJECT_VERSION` may not
  correspond to the release/API. This is why provenance must come from
  `interFoam -help-full`, `wmake -build-info`, and
  `foamEtcFile -show-api/-show-patch`.

### Antecedent-Workflow Evidence

- **D004 (workflow 0050) selects this profile and explicitly defers real
  success.** `docs/DECISION_LOG.md:37` and
  `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md:61-77`
  authorize profile metadata, dependency detection, deterministic case
  rendering, unavailable/failed states, and fake-command/fixture parser
  tests, while explicitly stating that "A real OpenFOAM `succeeded` path
  remains blocked until matching RFC 0040/RFC 0023 OpenFOAM-readable
  volume-mesh evidence exists." The five gate clauses are the
  machine-enforceable restatement of that deferral.
- **Workflow 0050 final review preserves the no-claims boundary.**
  `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md:100-105`
  records that "All real-solver output remains `raw_unvalidated`." This
  decision must keep that line; clause (5) of the decision sentence is the
  same statement, mechanized.
- **Workflow 0051 stage 1 burn-down landed the skeleton and MF1.** The lane
  table at
  `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:41-49`
  shows `implement_openfoam_skeleton` mapped to RFC 0041 / D004 with the
  named matches: profile name, mesh-gate, version probe, raw parser, and
  `solver_success_blocked`. MF1 was remediated by stale-output cleanup.
  Both must-fix findings closed at `accept` (`:18-22`). No `succeeded` path
  was enabled. Nothing in workflow 0051 contradicts the gate this decision
  authorizes; it implements the dependency-detection and parser-fixture
  scaffolding that the gate now expands.
- **No prior decision authorizes a fixture-only `succeeded` profile.**
  `docs/DECISION_LOG.md:37` (D004) names exactly one solver profile;
  `docs/ROADMAP.md:191-217` keeps `succeeded` evidence-gated; the
  Workflow 0050 burn-down at
  `integration/DECISION_RESULTS.md:243-247` authorizes "profile metadata,
  dependency/version probing, deterministic case rendering, fake-command
  unavailable/failed flows, raw `force.dat` parser fixtures, log/timeout
  caps, and forbidden-claim tests. Do not enable real `succeeded`
  execution until mesh evidence gates pass." Option B would manufacture a
  parallel `succeeded` path explicitly not authorized by D004.

## Why Rejected Alternatives Lose

### Option B — Fixture-Only Success Profile

Loses on three independent failure modes:

1. **Authorization gap.** D004 named exactly one solver profile and
   explicitly forbade real `succeeded` records until mesh evidence gates
   pass. Creating a separate fixture-only `succeeded` profile would
   manufacture a `succeeded` outcome that no antecedent decision authorized
   and would require its own decision-log row. That row is not on the
   table here.
2. **Downstream reading risk.** `succeeded` is the strongest run-record
   state. Any UI/CLI/REST surface that filters on `status == "succeeded"`
   (CLI exit codes, sweep aggregation, comparison reports, web job panel
   listings) would silently treat the fixture path as a positive result.
   The current `solver_success_blocked` failure mode is doing real work:
   it keeps the fake parser-readable path out of the "things that worked"
   bucket. A fixture `succeeded` would put it back in, and adjacent copy
   "this is fixture only" mitigates the *human* reading risk but does not
   change the *machine* reading risk.
3. **The infrastructure being exercised is already exercised today.** The
   fixture parser/route/CLI tests already run today without enabling
   `succeeded`. `tests/test_cfd_jobs.py` (per workflow 0051) covers
   prepare, run, missing-output, malformed-output, version probing,
   stale-output cleanup, and the parser fixtures. Adding a `succeeded`
   profile does not improve test coverage of any path; it only relabels
   one terminal outcome.

If a future decision wants UI-side `succeeded` state exercised end-to-end
without OpenFOAM installed, the right shape is a documented status alias
in the test layer (or a `--mock-succeeded` debug flag that emits a
warning), not a public `SolverProfile` with `adapter_name="..."` that
serializes through user-facing artifacts.

### Option C — Two-Stage Local Smoke Result

Loses for similar reasons plus state-machine complexity:

- Introducing a `completed_unvalidated` (or equivalent) status adds a
  fourth `status` literal to the existing `succeeded` / `failed` /
  `unavailable` set. Every CLI, web payload, comparison filter,
  forbidden-claim test, and downstream reader has to learn that fourth
  literal, and the gap between `completed_unvalidated` and `succeeded`
  becomes copy-only — the very surface this gate exists to defend.
- The same diagnostic value Option C describes ("installed solver smoke
  passed") is already obtainable as a non-status field: a
  `solver_smoke_status` record alongside the existing `error_kind`
  failure modes, with values like `installed`, `interFoam_help_full_ok`,
  `wmake_build_info_ok`, `checkMesh_ok`, and `force_dat_present`. None
  of these need to be a `status` literal, and none of them need to
  weaken the `succeeded` gate. A successor workflow can add such a
  field without re-opening this decision.
- D006 (`docs/DECISION_LOG.md:39`) and `claim_allows_calibrated_prediction`
  at `kayakgen/eval/claims.py:195-210` already gate calibrated wording
  on a separate accepted-fit workflow. A "completed_unvalidated" intermediate
  status would not change that gate; it would only add a second name
  for what `solver_success_blocked` already conveys.

### Option D — OpenFOAM Case Generation First, Solver Success Later

Loses as a *decision* because it is already what is happening:

- Workflow 0051 already landed deterministic v2512 case rendering
  (controlDict, transportProperties, fvSchemes, fvSolution, gravity,
  turbulence, U, p_rgh, alpha.water, README) at
  `kayakgen/eval/cfd/jobs.py:933-1006`, dependency probing at
  `:1255-1395`, and the fake-command `solver_success_blocked` outcome at
  `:1146-1175`. There is no implementation work that Option D would
  authorize that has not already been authorized by D004 and landed in
  workflow 0051.
- The remaining work is not "render the case"; it is the five gate
  clauses. Adopting Option D as today's *decision* would record only
  what is already true and would defer the gate-clause definition to a
  later decision — exactly the kind of restatement-without-progress
  that workflow 0050's burn-down (`integration/DECISION_RESULTS.md:230-269`)
  is designed to avoid.

### Variant — Option A Without The Parser-Schema Clause

A defensible variant of Option A would treat the parser-schema correction
as implementation detail and omit clause (4). I reject that variant.
`kayakgen/eval/cfd/jobs.py:1230-1248` currently mislabels the
v2512 `force.dat` columns; promoting to `succeeded` before that parser
ships a stamped schema produces nominally-`succeeded` records whose
`drag_force_n` is a misnamed sum of pressure-by-position, viscous-by-position,
and porous-by-position vectors. The decision must make the parser-schema
clause explicit because it is currently the smallest patch that flips
the user-visible outcome — and therefore the most likely path to a
silent regression.

### Variant — Option A With A "Validated" Adjacency Phrase

A second defensible variant would let user-facing copy say "OpenFOAM
completed successfully" once gates pass. I reject this variant because
`succeeded` here means "the adapter parsed raw output." The decision must
not authorize calibrated, validated, or design-fitness wording; clause (5)
keeps the no-claims warnings in CLI, REST/web payloads, persisted run
records, and artifact manifests. Re-using "successful" colloquial language
in product copy where machine-readable state would be `succeeded` is the
exact misreading risk that D004 was built to prevent
(`integration/DECISION_RESULTS.md:189-211` shared-risks item 1).

## Implementation Gates That Must Remain In Force

These gates must not be relaxed by any workflow that consumes this decision:

1. **`solver_success_blocked` is the terminal state until all five
   clauses pass simultaneously.** The branch at
   `kayakgen/eval/cfd/jobs.py:1146-1175` must not be removed, weakened to
   a warning, or reachable behind a "fixture-only" or
   "completed_unvalidated" alias. Any later workflow that enables a
   `succeeded` return path must also remove this branch in the same patch
   and replace it with a positive check on all five clauses.
2. **`required_mesh_readiness="cfd_ready"` and
   `required_mesh_profile="watertight_solid_resistance_v1"` on the
   profile.** `openfoam_v2512_interfoam_local_profile()` at
   `kayakgen/eval/cfd/jobs.py:480-515` must not relax these to
   `cfd_surface_candidate` or `open_wetted_surface_resistance_v1`. The
   readiness ladder at `:63-69` (`READINESS_ORDER`) must continue to
   place `cfd_ready` above `cfd_surface_candidate`.
3. **Fixture `cfd_ready` is sufficient for parser/dispatch/route tests
   only.** Tests may continue to construct a fixture `watertight_solid_resistance_v1`
   `cfd_ready` package. The decision does not authorize using a fixture
   package to satisfy clause (1) in a production-mode run record. A
   future workflow must add an explicit "fixture vs production evidence"
   distinction on the `MeshManifest` (and persist it in
   `SolverRawResult` provenance) before any `succeeded` outcome is
   permitted; until then, `solver_success_blocked` remains the terminal
   state even when the package is `cfd_ready`.
4. **Parser schema must be stamped before any `succeeded` path opens.**
   Adopting the corrected v2512 column order (`time, total, pressure,
   viscous, [porous]`) requires recording `parser_schema=openfoam-v2512-forces-v1`
   on `CfdOpenFoamForceDatResult` and rejecting files whose header or
   column count does not match. A regression test must construct a
   v2512-shaped `force.dat` and confirm the parser distinguishes total
   from pressure (and therefore that `drag_force_n` equals the total
   vector's X component, not a per-position sum of pressure/viscous/porous
   vectors). The current parser fixture at
   `tests/fixtures/openfoam/force.dat` (per workflow 0051) must be
   updated to match v2512's actual row layout, and the existing parser
   path at `kayakgen/eval/cfd/jobs.py:1225-1248` must be rewritten or
   the rewrite must coexist behind a `parser_schema` switch.
5. **Provenance probes must include build-info / API metadata, not only
   `WM_PROJECT_VERSION`.** The current
   `solver_version_command=["foamVersion"]` at
   `kayakgen/eval/cfd/jobs.py:492` is a minimum, not the gate. The
   provenance record on `succeeded` must capture `interFoam -help-full`
   output (application/build/architecture), `wmake -build-info` and/or
   `foamEtcFile -show-api`/`-show-patch`, and resolved executable paths
   (and hashes when feasible). A run that lacks any of these must
   remain `failed` with a specific `error_kind` (e.g.,
   `provenance_unavailable`, `version_check_failed`, or
   `version_mismatch` — the last two already exist at `:1349, :1370`).
6. **Hull-patch-to-`forces`-patch mapping must be evidence, not a
   constant.** The decision authorizes initially mapping the wetted-body
   wall patch to `hull` to match the upstream DTC `Allrun` and DTCHull
   `snappyHexMeshDict`. Any production run must record a
   checksum-bound `body_part → openfoam_patch` mapping in the
   `MeshManifest` or an equivalent `CfdOpenFoamMeshSummary` field;
   evidence using only the kayakgen-side
   `generated_hull_plus_deck` marker, without an explicit patch-name
   record, must not satisfy clause (1).
7. **Globbed `force.dat` discovery must be paired with deterministic
   final-row selection and ambiguous-stream rejection.** Loosening
   `OPENFOAM_FORCE_DAT_OUTPUT` from
   `postProcessing/forces/0/force.dat` (current at
   `kayakgen/eval/cfd/jobs.py:51`) to `postProcessing/forces/**/force.dat`
   must be done in the same patch that (a) selects a deterministic final
   usable time row, (b) rejects ambiguous multiple force-function-object
   streams unless the function-object name is explicitly configured, and
   (c) records the selected time / row count / file checksum / function-object
   name on the `CfdOpenFoamForceDatResult`.
8. **Stale-output cleanup is non-negotiable.** Workflow 0051 MF1
   (`_clear_openfoam_run_outputs` at
   `kayakgen/eval/cfd/jobs.py:1014`) must not be weakened. A "preserve
   prior run" option, even one defaulted off, is not authorized by this
   decision because it re-opens the exact stale-output overclaim path
   MF1 closed.
9. **Local installed-solver smoke runs only under explicit opt-in.**
   Default CI must continue to use fake commands and fixture files (per
   `integration/DECISION_RESULTS.md:67-71`). A successor implementation
   that runs `interFoam` locally must require a named environment flag
   (e.g., `KAYAKGEN_ENABLE_OPENFOAM=1`) plus an explicit
   `--enable-installed-solver` CLI/web flag, and must isolate outputs
   under the job-local case root before invocation.
10. **No silent fallback paths.** No runtime path may substitute mock
    commands, fixture output, analytical resistance, or prior
    `postProcessing` files for a missing or failed real run. The branch
    that returns `solver_success_blocked` for any parser-readable output
    produced without the accepted production gate is the keep — adding a
    "best effort succeeded" branch is forbidden.

## No-Claims Language That Must Remain In Force

This decision relaxes none of the following. Every consuming workflow must
preserve them verbatim where they already appear in `docs/PRD.md`,
`docs/USER_GUIDE.md`, `docs/ROADMAP.md`, RFC 0025, RFC 0027, RFC 0041, and
D004/D005/D006:

- Default resistance output remains `uncalibrated_comparative`
  (`docs/USER_GUIDE.md:102-104`,
  `kayakgen/eval/claims.py:UNCALIBRATED_COMPARATIVE`). A `succeeded`
  OpenFOAM record does not change this default; analytical resistance
  remains the comparative filter regardless of CFD adapter state.
- Resistance output may stop saying uncalibrated *only* under
  `claim_allows_calibrated_prediction` at
  `kayakgen/eval/claims.py:195-210`: a selected named model version with
  `accepted_fit`, accepted `calibration_fixture_ids`, persisted fit
  metrics and residuals, a validity envelope containing the evaluated
  hull and speed, and no `UNCALIBRATED_WARNING_CODES`. An OpenFOAM
  `succeeded` record on its own cannot satisfy this gate.
- CFD output remains `raw_unvalidated` regardless of `status` literal.
  `SolverProfile.result_semantics` at
  `kayakgen/eval/cfd/jobs.py:108` is pinned to `raw_unvalidated`; the
  decision must not authorize a `validated` or `calibrated` value here.
- `CFD_OPENFOAM_RESULTS_WARNING` at
  `kayakgen/eval/cfd/jobs.py:55-57` and
  `OPENFOAM_SUCCESS_BLOCKED_WARNING` at `:58-61` (or the renamed
  positive-state successor warning, once the gate opens) must continue
  to appear in CLI, REST/web payloads, persisted run records, and
  artifact manifests. The user-visible message on a future `succeeded`
  record must include "this is not validation, calibration, mesh
  independence, turbulence/free-surface settling assessment, timestep
  convergence assessment, measured-benchmark comparison, design fitness,
  safety, or seaworthiness."
- Generated bodies remain evaluation evidence, not production solver
  input, unless matching body diagnostics, self-intersection evidence,
  volume-mesh evidence, hashes, artifacts, and the
  `watertight_solid_resistance_v1` / `cfd_ready` solver-profile gates
  all pass (`docs/ROADMAP.md:33-59`). Real `succeeded` from this gate
  does not loosen the closed-body-evidence ladder; in particular,
  passing diagnostics on a generated body remains insufficient unless
  matching production volume-mesh evidence is also accepted (RFC 0040 /
  RFC 0023).
- Workflow 0050 D004 wording stays in force: "Implementation may add
  profile metadata, dependency detection, deterministic case rendering,
  unavailable/failed states, and fake-command/fixture parser tests. No
  real OpenFOAM `succeeded` path is authorized until matching
  RFC 0040/RFC 0023 OpenFOAM-readable volume-mesh evidence exists."
  This decision implements the gate by enumerating the five clauses;
  it does not amend D004.
- This decision does not authorize: hosting an OpenFOAM container in CI
  or a public demo; running `interFoam` in any default CI lane;
  recording any of the proposed user-facing positive states until all
  five clauses pass; using fixture `cfd_ready` evidence to satisfy
  clause (1) in a production run; weakening the `validity_envelope` or
  `accepted_use` gates for resistance; promoting any CFD output to a
  `validation_fixture` or `calibration_fixture` for downstream RFC 0042
  consumers; or implying that a `succeeded` OpenFOAM record validates,
  calibrates, or qualifies the underlying generated body as
  `validated_design_fitness`.
- D008's narrow exploratory-public-demo posture and dissent gates
  (operator owner, budget/cap, hosted smoke, persistence/cleanup
  receipts) remain in force. No hosted CFD worker, hosted OpenFOAM
  queue, or hosted-solver browser surface is authorized; the OpenFOAM
  adapter is a local-only profile and stays local-only under this
  decision.

## Confidence

**High.**

Rationale: every load-bearing clause in the decision is mechanically
verified against the local code, and every external load-bearing claim
is restricted to a single OpenFOAM-v2512 source (`forces.C` row order)
whose direction the integrator can re-verify before authorizing the
parser change. The decision aligns mechanically with:

- D004 at `docs/DECISION_LOG.md:37` and
  `integration/DECISION_RESULTS.md:61-77`;
- Workflow 0050 final review at
  `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md:100-105`;
- Workflow 0051 stage 1 burn-down at
  `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:41-49,
  108-126`;
- The current adapter implementation at
  `kayakgen/eval/cfd/jobs.py:44-69, 480-515, 925-1175, 1186-1248`;
- The readiness ladder at `kayakgen/eval/cfd/jobs.py:63-69` and the
  profile/readiness gate at `:1648, :1682-1685`;
- The No-Claims Rules at `docs/ROADMAP.md:33-59`;
- RFC 0025 / RFC 0027 / RFC 0041 / RFC 0042 (per the RFC index at
  `docs/rfcs/README.md`);
- `claim_allows_calibrated_prediction` at
  `kayakgen/eval/claims.py:195-210`.

The most material remaining unknown — the exact v2512 `force.dat` column
order — is correctly framed as an integrator-verifiable claim; either
verification direction leaves the decision's gate intact (the parser
schema must be stamped and verified before `succeeded` opens, regardless
of which order is correct).

The risk of the chosen option is small and well-bounded: preserving
`solver_success_blocked` is the current behavior and does not add
runtime, test, or product surface. The five gate clauses are
implementation work for a successor workflow; this decision authorizes
that successor's scope without enabling any `succeeded` record today.

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md` (audience, in-scope/out-of-scope, success criteria
  §80-103)
- `docs/USER_GUIDE.md` (resistance claim boundaries §102-104; CFD CLI
  §282-333; current limits §466-477)
- `docs/ROADMAP.md` (No-Claims Rules §34-59; Workflow 0050 Posture
  §62-95; Batch E Real CFD §191-217; Dependency Tracks §97-108;
  Current RFC Disposition §299-311)
- `docs/DECISION_LOG.md` (D003-D010 receipts; D004 row §37)
- `docs/rfcs/README.md` (RFC index; RFC 0017 → RFC 0041 succession;
  RFC 0040 / RFC 0023 / RFC 0026 dispositions)
- `docs/design/kayak_hull_design_constraints.md` (§3 length, §4 beam,
  §9 generator parameter space, §10 CFD objectives)
- `docs/workflows/0018-deferred-backlog/QUEUE.md` (historical; reconciled
  by the roadmap)
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`
  (vote tally §31-41; D004 accepted §61-77; risks §181-211;
  burn-down §230-269)
- `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`
  (verdict §17-22; coverage §40-48; no-claims §90-141)
- `striatum/0051-implementation-burndown-stage1/ledger/FINDINGS_LEDGER.md`
  (MF1 OpenFOAM stale outputs §30-56; MF2 GZCurve metadata §58-92;
  ledger verdict §18-27)
- `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`
  (verdict §18-22; lane table §41-49; MF1 remediation §64-77;
  no-claims §108-145)
- `striatum/0052-successor-decision-research/research/openfoam_success_gate/RESEARCH.md`
  (entire packet; external evidence table §47-67; recommendation §324-347)
- `kayakgen/eval/cfd/jobs.py` (profile constants §40-69; SolverProfile
  schema §85-108; built-in profiles §421-515;
  `OpenFoamLocalAdapter.prepare` §933-1006;
  `OpenFoamLocalAdapter.run` §1008-1176; force.dat parser §1186-1248;
  `_probe_openfoam_version` §1255-1395;
  `_clear_openfoam_run_outputs` §1395; readiness gates §1648, 1682-1685;
  adapter selection §2073)
- `kayakgen/eval/claims.py` (`claim_allows_calibrated_prediction`
  §195-210; `UNCALIBRATED_COMPARATIVE`)
- (Not re-fetched in this session; sourced from the research packet
  accessed 2026-05-14:) OpenFOAM.com current release page; OpenFOAM-v2512
  release announcement; OpenFOAM-v2512 GitLab tag list; OpenFOAM-v2512
  README; OpenFOAM-v2512 `etc/bashrc`; OpenFOAM command-line docs;
  OpenFOAM-v2512 `interFoam.C`; OpenFOAM-v2512 `interFoam/createFields.H`;
  OpenFOAM-v2512 DTCHull `Allrun`, `controlDict`, `snappyHexMeshDict`,
  `transportProperties`; OpenFOAM forces function-object docs;
  OpenFOAM function-object output docs; OpenFOAM-v2512 `forces.H` and
  `forces.C`; OpenFOAM `snappyHexMesh` docs; OpenFOAM `checkMesh`
  manpage.

## Sub-Agent Help

No sub-agents were spawned. Verification of profile constants, the
`OpenFoamLocalAdapter` `prepare`/`run` paths, the `force.dat` parser
column-order, the readiness ladder, the mesh-profile gating, the MF1
stale-output cleanup, and the workflow 0050/0051 dispositions was
performed inline by direct read-only inspection of
`kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/claims.py`,
`docs/DECISION_LOG.md`, `docs/ROADMAP.md`, `docs/rfcs/README.md`, and
the named workflow 0050 / 0051 artifacts. External v2512 source-code
claims were treated as research-packet quotations and not independently
re-fetched in this session.
