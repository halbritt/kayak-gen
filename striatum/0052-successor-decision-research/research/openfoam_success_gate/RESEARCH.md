---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-003
schema_version: striatum.synthesis.v1
artifact_kind: synthesis
logical_name: research
run_id: run_439eb6df3d1e4f12940bedad37c9a4ac
job_id: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_openfoam_success_gate
session_id: sess_7f61bf03104046358935a8514d1a7bf6
accessed_utc_date: 2026-05-14

# Research - OpenFOAM Success Gate

## Decision Question

What exact evidence and failure boundaries must exist before the
`openfoam-v2512-interfoam-local` profile can ever return `succeeded`
instead of the current blocked raw-failure state?

## Local Constraints And No-Claims Boundary

The local record already fixes the conservative frame:

- `docs/ROADMAP.md` and `docs/DECISION_LOG.md` select
  OpenFOAM.com OpenFOAM-v2512 `interFoam` under profile
  `openfoam-v2512-interfoam-local`, but explicitly block real
  success until matching OpenFOAM-readable volume-mesh evidence exists.
- RFC 0023 and RFC 0040 define `cfd_ready` as evidence-backed readiness
  for a named profile, not as a property of any generated hull. Evidence
  must bind one generated body, one diagnostic set, one volume mesh, and
  one solver profile by hashes, checksums, tolerances, units, coordinate
  system, mesher provenance, and boundary metadata.
- RFC 0025 and RFC 0041 require all CFD outputs to remain
  `raw_unvalidated`. Even after the gate opens, `succeeded` can only
  mean "the selected local solver executed and the adapter parsed its raw
  artifacts." It must not imply validated drag, calibrated resistance,
  accepted design fitness, or comparison to measured kayak data.
- The current adapter intentionally returns
  `failed/error_kind=solver_success_blocked` even when fake
  parser-readable output exists. This is correct until the mesh, case,
  solver, and parser gates below are implemented together.

## External Evidence

| Source | Specific claim supported |
| --- | --- |
| OpenFOAM.com current release page, https://www.openfoam.com/current-release, accessed 2026-05-14 | OpenFOAM.com identifies OpenFOAM-v2512 as the current release line and documents package/source installation paths for that release family. |
| OpenFOAM-v2512 release announcement, https://www.openfoam.com/news/main-news/openfoam-v2512, accessed 2026-05-14 | OpenFOAM-v2512 is the selected release family for this profile and was released as the OpenFOAM.com distribution version `v2512`. |
| OpenFOAM-v2512 GitLab tag list, https://gitlab.com/openfoam/core/openfoam/-/tags, accessed 2026-05-14 | The source tag `OpenFOAM-v2512` exists and maps the selected release to a concrete upstream source revision. |
| OpenFOAM-v2512 README, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/README.md, accessed 2026-05-14 | Official startup guidance uses `etc/bashrc`; the README warns that `$WM_PROJECT_VERSION` alone may not correspond to the release/API and recommends application build info and `foamEtcFile -show-api/-show-patch` for parseable provenance. |
| OpenFOAM-v2512 `etc/bashrc`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/etc/bashrc, accessed 2026-05-14 | The release environment exports `WM_PROJECT_VERSION=v2512` and `WM_PROJECT_DIR`, so environment capture can be part of provenance but cannot be the only gate. |
| OpenFOAM command-line documentation, https://doc.openfoam.com/2306/fundamentals/command-line/, accessed 2026-05-14 | OpenFOAM applications expose `-help-full` output including application, build, and architecture details. The adapter can use this as an installed-solver smoke/provenance probe. |
| OpenFOAM-v2512 `interFoam.C`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/applications/solvers/multiphase/interFoam/interFoam.C, accessed 2026-05-14 | `interFoam` is a VOF solver for two incompressible, isothermal immiscible fluids and runs a PIMPLE pressure-velocity loop, matching the intended free-surface resistance smoke scope. |
| OpenFOAM-v2512 `interFoam/createFields.H`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/applications/solvers/multiphase/interFoam/createFields.H, accessed 2026-05-14 | A valid v2512 case must provide `p_rgh` and `U`; `p` is derived, and phase properties are read through the two-phase mixture setup. |
| OpenFOAM-v2512 DTCHull `Allrun`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun, accessed 2026-05-14 | The upstream DTC hull tutorial builds a real OpenFOAM case by copying STL geometry, running feature extraction, `blockMesh`, topology/refinement steps, `snappyHexMesh`, field initialization, decomposition, solver execution, and reconstruction. A skeleton dictionary set is not a runnable-equivalent smoke. |
| OpenFOAM-v2512 DTCHull `controlDict`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict, accessed 2026-05-14 | The upstream case configures `application interFoam` and a `forces` function object over patch `hull`, with `rhoInf` and timestep-controlled force output. |
| OpenFOAM-v2512 DTCHull `snappyHexMeshDict`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/snappyHexMeshDict, accessed 2026-05-14 | The upstream case maps triangulated hull geometry to an OpenFOAM wall patch named `hull`, applies refinement/layers, and uses mesh quality controls. This supports requiring explicit OpenFOAM boundary patch evidence, not just generic volume-cell counts. |
| OpenFOAM-v2512 DTCHull `transportProperties`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/constant/transportProperties, accessed 2026-05-14 | A v2512 two-phase `interFoam` case needs phase definitions and fluid properties for water and air, not only a single kinematic viscosity value. |
| OpenFOAM forces function-object docs, https://doc.openfoam.com/2212/tools/post-processing/function-objects/forces/forces/, accessed 2026-05-14 | The `forces` function object reports force and moment data over named patches and requires case dictionary entries such as `type forces`, `libs`, `patches`, and density handling for incompressible cases. |
| OpenFOAM function-object docs, https://doc.openfoam.com/2212/tools/post-processing/function-objects/, accessed 2026-05-14 | Runtime function-object outputs are written under `postProcessing/<functionObject>/<time>/...`, supporting a globbed output location rather than only one hard-coded time directory. |
| OpenFOAM-v2512 `forces.H`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/src/functionObjects/forces/forces/forces.H, accessed 2026-05-14 | The official source defines `force.dat` and `moment.dat` as the integrated force/moment files and documents the `p`, `U`, `rho`, `rhoInf`, and patch-list controls. |
| OpenFOAM-v2512 `forces.C`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/src/functionObjects/forces/forces/forces.C, accessed 2026-05-14 | The v2512 writer emits force rows as time, total vector, pressure vector, viscous vector, and optional porous vector. The current kayakgen parser assumes pressure, viscous, porous, then totals them, so it is unsafe for real v2512 success. |
| OpenFOAM snappyHexMesh docs, https://doc.openfoam.com/2312/tools/pre-processing/mesh/generation/snappyhexmesh/, accessed 2026-05-14 | `snappyHexMesh` is a batch-driven hexahedral mesher for triangulated geometry, can run checks, and can handle imperfect input surfaces. That capability does not replace kayakgen's own watertight/readiness evidence because OpenFOAM can proceed with inputs that are still outside this project's claim gate. |
| OpenFOAM `checkMesh` manpage, https://www.openfoam.com/documentation/guides/v2112/man/checkMesh.html, accessed 2026-05-14 | `checkMesh` is the maintained OpenFOAM mesh-validity command family, supporting a required solver-side mesh-quality smoke before adapter success. |

## Required Gate Before `succeeded`

### 1. Mesh Evidence

The success gate should require a job-local mesh package that satisfies
both the existing kayakgen readiness contract and OpenFOAM-specific
readability:

- The mesh evidence must be for profile
  `watertight_solid_resistance_v1` and readiness `cfd_ready`, with the
  same `body_ref`, body hash, hull hash, tolerance hash, units, and
  coordinate system as the prepared job.
- The manifest must include mesher name/version, deterministic input
  digest, config digest, generated artifact list, SHA-256 checksums,
  cell count, boundary face count, boundary patch names, patch roles,
  patch markers, quality summaries, warnings, and blockers.
- The OpenFOAM handoff must identify the actual OpenFOAM mesh artifact,
  preferably a case-local `constant/polyMesh` tree or an equivalent
  conversion manifest whose checksums are verified before dispatch.
- A wetted-body wall patch must be present and mapped to the case's
  `forces` patch, initially `hull` to align with the upstream DTC case.
  Evidence using only kayakgen's generic
  `generated_hull_plus_deck` marker should not pass unless the adapter
  records an explicit, checksum-backed patch-name mapping.
- Solver-side mesh evidence should include `checkMesh` command, exit
  status, OpenFOAM version/build provenance, and retained summary/log
  artifacts. If `snappyHexMesh` or conversion is part of the pipeline,
  capture its command, version, input geometry checksums, generated
  `polyMesh` checksums, and quality summary.
- The gate must reject missing, stale, synthetic, cross-body, cross-hull,
  cross-tolerance, hand-edited, path-escaping, malformed, checksum
  mismatched, or below-readiness evidence before rendering/running a
  solver case.

Fixture `cfd_ready` evidence is sufficient for parser and dispatch tests.
It is not sufficient for enabling real OpenFOAM `succeeded` unless the
decision explicitly defines a fixture-only success profile separate from
`openfoam-v2512-interfoam-local`.

### 2. Installed-Solver Smoke Scope

The minimum installed-solver smoke should run only under an explicit local
flag or developer opt-in, not in default CI:

- Resolve the OpenFOAM environment explicitly, recording whether the run
  came from a sourced `etc/bashrc`, package environment, container, or
  user-provided command path.
- Probe `interFoam -help-full` and capture application name, build,
  architecture, and exit status.
- Probe parseable release/API metadata using `wmake -build-info` and/or
  `foamEtcFile -show-api` / `foamEtcFile -show-patch`, because upstream
  documentation warns that `$WM_PROJECT_VERSION` alone is not a reliable
  release/API proof.
- Probe `checkMesh -help` or run `checkMesh` on the prepared case before
  solver execution.
- Render a deterministic v2512 case that contains a real `polyMesh`,
  `application interFoam`, two-phase transport properties, required
  fields `U` and `p_rgh`, phase initialization, and a `forces` function
  object over the mapped hull patch.
- Run a bounded tiny smoke case with timeout, log capture, stale-output
  cleanup, and output isolation. The smoke can be computationally coarse,
  but it must exercise OpenFOAM reading the mesh and dictionaries, running
  `interFoam`, and writing `postProcessing/forces/**/force.dat`.

This smoke proves adapter compatibility only. It does not validate the
physics, numerical settings, mesh independence, resistance prediction, or
design ranking.

### 3. Version And Provenance Checks

Before `succeeded`, the run record should capture at least:

- Profile name:
  `openfoam-v2512-interfoam-local`.
- Solver identity:
  OpenFOAM.com `OpenFOAM-v2512` `interFoam`, not Foundation OpenFOAM or
  another release family.
- Command paths and resolved executable hashes when feasible.
- `interFoam -help-full` banner/build/architecture.
- `wmake -build-info` and/or `foamEtcFile -show-api/-show-patch` output.
- `WM_PROJECT_DIR`, `WM_PROJECT_VERSION`, and environment source, marked
  as supporting context rather than sole proof.
- Case template version:
  `openfoam-v2512-interfoam-dtchull-v1`.
- Mesh profile and volume-mesh diagnostic references.
- Force parser schema version tied to v2512 `forces.C`.

Version mismatch should be a hard unavailable/failure state, not a warning
that still permits success.

### 4. Parser Requirements

The current parser is a blocker. OpenFOAM-v2512 source writes integrated
force rows as:

1. time
2. total force vector
3. pressure force vector
4. viscous force vector
5. optional porous force vector

The current kayakgen parser interprets the first three vectors as
pressure, viscous, and porous, then sums them. That would double-count or
mislabel real v2512 output because the first vector is already the total.

Required parser changes before success:

- Parse header/schema variants from v2512 `forces.C` and store
  `parser_schema=openfoam-v2512-forces-v1`.
- Accept `postProcessing/forces/**/force.dat` and select a deterministic
  final usable time row, while rejecting multiple ambiguous force streams
  unless the function-object name is explicitly configured.
- Extract total, pressure, viscous, and optional porous vectors according
  to v2512 order.
- Record force units, coordinate convention, selected time, source file
  checksum, row count, and function-object name.
- Reject empty files, nonfinite values, malformed rows, impossible vector
  counts, duplicate ambiguous outputs, missing hull patch/function-object
  provenance, or files whose header/schema does not match the adapter's
  declared parser version.
- Keep parser fixtures that prove fake parser-readable output remains
  blocked until the mesh/solver gates are all satisfied.

### 5. Failure Modes

The adapter should continue to prefer explicit blocked/failure states over
best-effort success. Required states:

- Prepare-time unavailable/failed:
  missing profile, profile mismatch, below `cfd_ready`, missing volume
  mesh, evidence profile mismatch, stale checksum, forbidden path
  reference, malformed diagnostic, synthetic evidence, cross-body,
  cross-hull, cross-tolerance, failed self-intersection, mesh diagnostic
  not ready, body-surface mismatch, missing OpenFOAM patch mapping, missing
  `polyMesh`, or artifact checksum mismatch.
- Provenance unavailable/failed:
  missing `interFoam`, missing OpenFOAM environment, command timeout,
  command nonzero, version family mismatch, OpenFOAM.com/Foundation
  ambiguity, missing build/API metadata, or unsupported case-template
  version.
- Runtime failed:
  stale output cleanup failure, `checkMesh` failure, `interFoam` nonzero,
  timeout, missing `force.dat`, malformed force output, nonfinite force
  output, ambiguous multiple outputs, parser schema mismatch, or missing
  raw result write.
- Gate blocked:
  keep `solver_success_blocked` for any parser-readable output produced
  without the accepted production mesh/case/provenance gate.

No runtime path should silently fall back to mock commands, fixture output,
analytical resistance, or prior `postProcessing` files.

### 6. Raw-Unvalidated Warnings

Every successful record still needs high-friction warnings:

- `claim_state=raw_unvalidated`.
- `accepted_uses=[]`, or equivalent empty accepted-use list.
- A warning that local OpenFOAM completion is not validation,
  calibration, or design fitness.
- A warning that mesh independence, turbulence/free-surface settings,
  timestep convergence, and measured benchmark comparison are not
  established.
- Provenance references for mesh, case template, solver, parser, and raw
  output.

These warnings should appear in CLI, REST/web payloads, persisted run
records, and artifact manifests.

## Viable Options

### Option A - Conservative Default: Keep Success Blocked Until Full Gate

Keep `openfoam-v2512-interfoam-local` unable to return `succeeded` until
the mesh, OpenFOAM case, installed-solver smoke, provenance, and v2512
parser requirements above are all implemented.

Benefits:

- Matches RFC 0023, RFC 0040, RFC 0041, D004, and the current roadmap.
- Avoids reporting fake or skeleton-case output as real solver success.
- Preserves the no-claims boundary.

Cost:

- Real local OpenFOAM success remains deferred even for developers with
  OpenFOAM installed.

### Option B - Fixture-Only Success Profile

Create a separate non-production profile for fixture parser success,
leaving `openfoam-v2512-interfoam-local` blocked.

Benefits:

- Allows UI/API success-state exercise without weakening the real profile.
- Keeps test coverage deterministic and independent of OpenFOAM installs.

Cost:

- Requires clear naming and warnings so users do not mistake fixture
  success for solver success.

### Option C - Two-Stage Local Smoke Result

Add an intermediate status such as `completed_unvalidated` or a separate
capability flag for "installed solver smoke passed" while still preventing
the selected profile from reporting `succeeded` until production mesh
evidence exists.

Benefits:

- Useful for developer environment diagnostics.
- Separates installation readiness from production CFD readiness.

Cost:

- Adds state-machine complexity and requires careful web/CLI language.

### Option D - OpenFOAM Case Generation First, Solver Success Later

Land deterministic v2512 case rendering and provenance capture now, but
keep runtime output blocked until OpenFOAM-readable mesh evidence and the
parser fix land.

Benefits:

- Advances implementation without changing claim semantics.
- Gives future reviewers concrete case artifacts to inspect.

Cost:

- Still no real `succeeded` result.

## Risks, Unknowns, And Implementation Gates

- The current deterministic case skeleton is not equivalent to the v2512
  DTC-style `interFoam` case. It lacks a real `polyMesh`, two-phase
  transport setup, and likely other required dictionaries for a real run.
- The current parser order conflicts with v2512 `forces.C`. Enabling
  success before fixing this would produce wrong force components.
- OpenFOAM can mesh or run some imperfect inputs; kayakgen still needs
  stricter evidence because the product claim is not "OpenFOAM accepted
  something" but "this named generated body has traceable, solver-ready
  evidence."
- The upstream DTC tutorial uses a `hull` patch. Current kayakgen fixture
  evidence uses `generated_hull_plus_deck`. A deliberate patch-mapping
  decision is required before force extraction can be trusted.
- Solver installation is inherently local. Default CI should continue to
  use fake commands and fixtures, with optional installed-solver smoke
  tests gated by an explicit environment variable.
- A later validation program may change accepted uses, but that is outside
  this decision. The success gate must not wait for validation, and it
  must not imply validation.

## Recommendation

Adopt Option A as the decision for
`openfoam-v2512-interfoam-local`: keep real `succeeded` impossible until
all of the following are true in one run record:

1. A production, OpenFOAM-readable `watertight_solid_resistance_v1`
   volume-mesh package passes the existing RFC 0023/RFC 0040 evidence
   checks and includes verified OpenFOAM `polyMesh` and hull patch
   metadata.
2. The adapter records installed OpenFOAM.com v2512 `interFoam`
   provenance from application/build/API probes, not only
   `$WM_PROJECT_VERSION`.
3. The rendered case is a deterministic v2512 `interFoam` case with
   two-phase properties, required fields, mesh, force function object, and
   bounded smoke execution.
4. The force parser is corrected to the v2512 `force.dat` schema and
   rejects ambiguous or malformed output.
5. The run record, CLI, REST/web payloads, and artifacts continue to mark
   the result as `raw_unvalidated` with no accepted design-use claim.

Until then, the current `solver_success_blocked` outcome is the correct
behavior, even when a fake command writes parser-readable `force.dat`.
