---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_41e10bae97ba448eaf752253baf367a4
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_openfoam_success_gate_codex
lease: lease_e3f724c1856b4d07bf34822c60f71e33

# Vote - OpenFOAM Success Gate

Vote: Option A - Full Evidence Gate Before Success.

## Decision Sentence

Keep `openfoam-v2512-interfoam-local` unable to return `succeeded` until one
run record binds accepted OpenFOAM-readable `watertight_solid_resistance_v1` /
`cfd_ready` volume-mesh evidence, OpenFOAM.com v2512 `interFoam` provenance, a
real deterministic v2512 case smoke, a v2512-correct `force.dat` parser, and
raw-unvalidated no-claims payloads. After the gate opens, `succeeded` means only
that the selected local solver executed and the adapter parsed raw artifacts;
it is not validation, calibration, final prediction, design fitness, or solver
readiness for other hulls.

## Evidence

The local decision trail already fixes the conservative boundary. D004 selects
OpenFOAM.com OpenFOAM-v2512 `interFoam` under
`openfoam-v2512-interfoam-local`, with required mesh profile
`watertight_solid_resistance_v1`, readiness `cfd_ready`, case template
`openfoam-v2512-interfoam-dtchull-v1`, and raw `forces` parser scope, but it
explicitly says no real OpenFOAM `succeeded` path is authorized until matching
RFC 0040/RFC 0023 OpenFOAM-readable volume-mesh evidence exists
(`docs/DECISION_LOG.md:37`). The roadmap repeats the same two constraints:
there is no accepted real solver success path today, and the selected
OpenFOAM target remains blocked until matching volume-mesh evidence exists
(`docs/ROADMAP.md:41-47`, `docs/ROADMAP.md:71-74`,
`docs/ROADMAP.md:191-216`). The user guide still describes CFD as job-state
plumbing with unavailable or test adapters, not real solver execution
(`docs/USER_GUIDE.md:327-332`, `docs/USER_GUIDE.md:432-442`,
`docs/USER_GUIDE.md:467-473`).

Workflow 0051 implemented only the skeleton that D004 allowed. The final review
records that the OpenFOAM skeleton has the selected profile, mesh gate, version
probe, raw parser, and `solver_success_blocked`, while ordinary packages stay
below `cfd_ready` (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:46-47`).
It also confirms there is no real `succeeded` path: parser-readable fake output
returns `error_kind="solver_success_blocked"`, and the adapter enforces
`required_mesh_profile="watertight_solid_resistance_v1"` plus readiness
`cfd_ready` before it runs
(`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:122-126`).
The stale-output must-fix from that workflow is instructive: even blocked fake
runs needed explicit cleanup of `postProcessing/forces/**` and
`openfoam-raw-result.json` before reruns, with a preserved boundary that fake
parser-readable output must remain failed/raw-unvalidated until a later
accepted workflow supplies mesh and solver evidence
(`striatum/0051-implementation-burndown-stage1/ledger/FINDINGS_LEDGER.md:40-56`).

The current code matches that posture. The profile constant names
`openfoam-v2512-interfoam-local`, OpenFOAM.com v2512 `interFoam`,
`openfoam-v2512-interfoam-dtchull-v1`, and
`postProcessing/forces/0/force.dat` (`kayakgen/eval/cfd/jobs.py:44-52`). The
profile requires `cfd_ready`, `watertight_solid_resistance_v1`, `interFoam`,
`foamVersion`, `v2512`, and records that no production OpenFOAM-readable mesh
evidence or real succeeded run record is enabled
(`kayakgen/eval/cfd/jobs.py:480-515`; `tests/test_cfd_jobs.py:255-274`).
`OpenFoamLocalAdapter` says it intentionally does not report a real
`succeeded` state, writes only deterministic skeleton files, clears stale
OpenFOAM outputs before command execution, and converts parser-readable output
into `failed/error_kind="solver_success_blocked"` rather than `succeeded`
(`kayakgen/eval/cfd/jobs.py:925-930`, `kayakgen/eval/cfd/jobs.py:1008-1026`,
`kayakgen/eval/cfd/jobs.py:1146-1175`; `tests/test_cfd_jobs.py:1202-1238`,
`tests/test_cfd_jobs.py:1242-1296`).

My independent external check supports the same gate. The OpenFOAM.com current
release page identifies OpenFOAM-v2512 as the current release, released on
2025-12-22, and the v2512 announcement identifies it as the December 2025
OpenFOAM.com release
(https://www.openfoam.com/current-release,
https://www.openfoam.com/news/main-news/openfoam-v2512, accessed
2026-05-14). The GitLab tag list has a protected `OpenFOAM-v2512` tag at
commit `87ed40d2`
(https://gitlab.com/openfoam/core/openfoam/-/tags, accessed 2026-05-14). The
v2512 `interFoam/createFields.H` source reads `p_rgh`, `U`, and
`transportProperties`, so a runnable smoke needs more than a one-viscosity
skeleton
(https://gitlab.com/openfoam/core/openfoam/-/blob/OpenFOAM-v2512/applications/solvers/multiphase/interFoam/createFields.H,
accessed 2026-05-14). The v2512 DTCHull tutorial builds a real case through
surface feature extraction, `blockMesh`, topology/refinement steps,
`snappyHexMesh`, field initialization, decomposition, `interFoam`, and
reconstruction, and its `controlDict` drives a `forces` object over patch
`hull`
(https://gitlab.com/openfoam/core/openfoam/-/blob/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun,
https://gitlab.com/openfoam/core/openfoam/-/blob/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict,
accessed 2026-05-14).

The parser is a hard blocker. The workflow research packet notes that v2512
`forces.C` writes force rows as time, total vector, pressure vector, viscous
vector, and optional porous vector, while the current kayakgen parser treats
the first three vectors as pressure, viscous, and porous and then sums them
(`striatum/0052-successor-decision-research/research/openfoam_success_gate/RESEARCH.md:159-190`).
I checked the v2512 source directly: its header writes `total`, `pressure`,
`viscous`, optional `porous`, and `writeIntegratedDataFile()` writes current
time, `pres + vis + internal`, `pres`, and `vis`
(https://gitlab.com/openfoam/core/openfoam/-/blob/OpenFOAM-v2512/src/functionObjects/forces/forces/forces.C#L430-477,
accessed 2026-05-14). The current parser still assigns values 1-3 to
`pressure`, values 4-6 to `viscous`, values 7-9 to `porous`, and sums those as
the total (`kayakgen/eval/cfd/jobs.py:1189-1252`), with the checked-in fixture
using the older `pressure viscous porous` header
(`tests/fixtures/openfoam/force.dat:1-5`). Enabling success before correcting
this would mislabel or double-count real v2512 force output.

The research packet's recommended gate is therefore the right one: keep real
`succeeded` impossible until the run record has production OpenFOAM-readable
volume-mesh evidence, v2512 solver provenance beyond a weak environment string,
a real deterministic v2512 `interFoam` case smoke, a corrected v2512 parser,
and raw-unvalidated payloads across CLI, REST/web, persisted records, and
artifacts
(`striatum/0052-successor-decision-research/research/openfoam_success_gate/RESEARCH.md:326-346`).

## Why Rejected Alternatives Lose

Option B, a fixture-only success profile, may be useful later for UI/API
success-state exercise, but it should be a separately named non-production
profile. It cannot justify `succeeded` for `openfoam-v2512-interfoam-local`
because fixture `cfd_ready` evidence is sufficient only for parser and
dispatch tests, not for enabling real OpenFOAM success on the selected profile
(`striatum/0052-successor-decision-research/research/openfoam_success_gate/RESEARCH.md:103-106`).

Option C, an intermediate installed-solver smoke status, is acceptable only as
diagnostic state or a separate capability flag. It does not satisfy the
profile's production mesh, case, parser, and provenance gates, and it adds
state-machine complexity on surfaces that already have a history of stale CFD
status copy.

Option D, deterministic case generation first, is a good implementation slice
but not a success gate. The current skeleton already demonstrates why: it can
write dictionaries and fields, probe versions, and parse fake output, yet it
still lacks a verified OpenFOAM `polyMesh`, an accepted hull patch mapping, a
v2512-correct parser, and installed-solver smoke evidence.

Immediate success on command completion or parser-readable `force.dat` loses
outright. It conflicts with D004, the roadmap, current tests, the stale-output
remediation boundary, and the official v2512 force-file schema.

## Implementation Gates And No-Claims Language

- Require a job-local `watertight_solid_resistance_v1` / `cfd_ready` mesh
  package bound to the same body ref, hull hash, body hash, tolerance hash,
  units, coordinate system, manifest, and solver profile as the prepared job.
- Require verified OpenFOAM-readable mesh evidence: `constant/polyMesh` or an
  equivalent conversion manifest with SHA-256 checksums, mesher/config/version
  provenance, cell and boundary summaries, quality summaries, warnings,
  blockers, and path containment checks.
- Require an explicit wetted-body wall patch mapping to the case `forces`
  patch, initially `hull`; generic `generated_hull_plus_deck` evidence must
  not pass without a checksum-backed OpenFOAM patch-name mapping.
- Run `checkMesh` or an equivalent OpenFOAM mesh-validity smoke on the prepared
  case and retain command, exit status, version/build provenance, summary, and
  logs.
- Probe installed solver provenance with `interFoam -help-full` and parseable
  release/API/build evidence such as `wmake -build-info` and/or
  `foamEtcFile -show-api/-show-patch`; record command paths and executable
  hashes when feasible. Version-family mismatch is a hard unavailable/failure
  state.
- Render a real deterministic v2512 `interFoam` case with `application
  interFoam`, two-phase water/air properties, required `U` and `p_rgh` fields,
  phase initialization, gravity, turbulence/settings, a real `polyMesh`, and a
  `forces` object over the mapped hull patch.
- Run only bounded, isolated local smoke execution behind explicit developer
  opt-in or environment gating; default CI continues to use fake commands and
  parser fixtures.
- Fix the parser before any success path: store a declared
  `parser_schema=openfoam-v2512-forces-v1`, accept
  `postProcessing/forces/**/force.dat`, reject ambiguous multiple force
  streams unless configured, parse total/pressure/viscous/optional porous in
  v2512 order, record selected time, row count, checksum, units, coordinate
  convention, function-object name, and reject malformed, nonfinite, empty, or
  schema-mismatched files.
- Preserve explicit failure states for missing/stale/synthetic/cross-body/
  cross-hull/cross-tolerance/malformed evidence, missing patch mapping,
  missing `polyMesh`, failed `checkMesh`, solver unavailable, timeout,
  command failure, version mismatch, missing output, malformed output,
  ambiguous output, parser mismatch, stale-output cleanup failure, and raw
  result write failure.
- Keep `solver_success_blocked` for parser-readable output produced without
  the accepted production mesh/case/provenance/parser gate.
- Every successful record after the gate opens must still carry
  `claim_state=raw_unvalidated`, `accepted_uses=[]`, warnings that OpenFOAM
  completion is not validation/calibration/final prediction/design fitness,
  warnings that mesh independence, timestep convergence, turbulence/free-
  surface settings, and measured benchmark comparison are not established, and
  provenance references for mesh, case template, solver, parser, logs, and raw
  output.

Confidence: high
