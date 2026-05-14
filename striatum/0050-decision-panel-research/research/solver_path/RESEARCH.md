---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-007
schema_version: striatum.research.v1
kind: synthesis
logical_name: research
date: 2026-05-14

# Research - CFD Solver Path Decision

## Decision Question

Which first real external CFD solver path should kayak-gen select, and what mesh
profile, readiness gate, case-template version, raw parser scope,
install/platform notes, and CI strategy should bound that path?

## Local Project Constraints

Reviewed local sources: `AGENTS.md`, `docs/PRD.md`, `docs/USER_GUIDE.md`,
`docs/ROADMAP.md`, `docs/DECISION_LOG.md`, `docs/rfcs/README.md`,
`docs/design/kayak_hull_design_constraints.md`,
`docs/workflows/0018-deferred-backlog/QUEUE.md`,
`striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md`,
`striatum/0049-roadmap-reconciliation/integration/PATCH_SUMMARY.md`,
`docs/workflows/0050-decision-panel-research/SOURCES.md`, and RFCs 0010,
0015-0018, 0021-0023, 0025-0026, 0028, 0040, and 0041. I also checked the
current implementation in `kayakgen/eval/mesh_package.py`,
`kayakgen/eval/volume_mesh.py`, and `kayakgen/eval/cfd/jobs.py`.

- Current CFD support is local job/profile/run plumbing plus unavailable,
  mock-failing, and `fixture-local-command` adapters. There is no accepted
  OpenFOAM, SU2, Docker, hosted-worker, or real external-solver success path.
- Current profile names are `open_wetted_surface_resistance_v1` and
  `watertight_solid_resistance_v1` at the mesh-package layer, with CFD profiles
  `unavailable-open-wetted-surface`, `unavailable-watertight-solid`,
  `mock-failing-local-command`, and `fixture-local-command`.
- The existing fixture success path is intentionally tied to
  `open_wetted_surface_resistance_v1`, writes `raw-result.json`, and uses
  `fixture-local-command-v1`. It proves adapter lifecycle, not solver physics.
- Ordinary generated mesh packages emit open hull/deck inspection surfaces and
  are below watertight solver readiness. Only the narrow fixture volume-mesh
  handoff can report `cfd_ready`; production volume meshing remains future work.
- RFC 0041 allows a real adapter only after a solver-selection decision,
  explicit mesh-profile gate, deterministic case-template version, parser
  scope, install/platform notes, and CI strategy that does not require the
  external solver binary.
- RFC 0025 claim gates are binding: all real-solver outputs remain
  `raw_unvalidated`. They are not calibrated resistance, final prediction,
  design fitness, Pareto-default scoring, or proof of seaworthiness.

## External Evidence

Access date for all external sources: 2026-05-14.

| Source | Claim Supported |
| --- | --- |
| OpenFOAM current release page, https://www.openfoam.com/current-release | OpenFOAM.com current release is OpenFOAM-v2512, released 2025-12-22; installation routes include Linux packages, Docker for Mac, Windows Docker/MinGW/WSL, and source. |
| OpenFOAM v2512 release notes, https://www.openfoam.com/news/main-news/openfoam-v2512 | OpenFOAM-v2512 is distributed under GPL; packages are available for Ubuntu 24.04/22.04, openSUSE, Red Hat variants, Windows options, and macOS source or Docker. The repository moved to GitLab, so templates should pin a release line rather than a floating repo path. |
| OpenFOAM v2512 DTCHull `Allrun`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun | The official DTCHull tutorial path is a ship-hull/free-surface style workflow using a DTC hull STL, `surfaceFeatureExtract`, `blockMesh`, repeated `refineMesh`, `snappyHexMesh`, `setFields`, and then the case application. This is strong evidence that OpenFOAM has a maintained template family close to hull resistance work. |
| OpenFOAM v2512 DTCHull `controlDict`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict | The DTCHull case runs `interFoam` and configures a `forces` function object on the `hull` patch with water density. This supports an initial parser centered on `postProcessing/forces/.../force.dat` rather than invented output. |
| OpenFOAM snappyHexMesh geometry guide, https://www.openfoam.com/documentation/guides/latest/doc/guide-meshing-snappyhexmesh-geometry.html | `snappyHexMesh` consumes triangulated surfaces from `constant/triSurface`, including STL/STLB/OBJ/VTK formats, and surface regions become final mesh patches. This supports OpenFOAM case rendering from mesh-package artifacts, but not by itself solver-readiness promotion. |
| OpenFOAM `forceCoeffs` docs, https://doc.openfoam.com/2306/tools/post-processing/function-objects/forces/forceCoeffs/ | OpenFOAM has documented force/coefficient post-processing split into total, pressure, and viscous contributions. This supports an optional later parser extension, but raw force parsing should be the first accepted scope because coefficients need explicit reference area and direction metadata. |
| SU2 GitHub README/releases, https://github.com/su2code/SU2 | SU2 latest listed release is 8.5.0 "Harrier" on 2026-04-27; the project advertises precompiled binaries for Linux, macOS, and Windows, and source builds require C/C++ compiler and Python 3 with Meson/Ninja. |
| SU2 theory docs, https://su2code.github.io/docs_v7/Theory/ | SU2 supports `INC_NAVIER_STOKES` and `INC_RANS` incompressible finite-volume solvers. This is sufficient for a submerged/external-flow raw adapter, but it is not the same evidence as a maintained free-surface ship-resistance template. |
| SU2 history/output docs, https://su2code.github.io/docs_v7/Custom-Output/ | SU2 supports configurable history output with fields such as `DRAG`, `FORCE_X`, `FORCE_Y`, `FORCE_Z`, and residual groups. This makes a narrow CSV/history parser feasible if SU2 is selected. |
| SU2 mesh docs, https://su2code.github.io/docs_v7/Mesh-File/ | SU2 primarily uses native `.su2` mesh files and can use CGNS when compiled with support; marker tags from mesh files drive boundary conditions. This shifts first-adapter complexity toward volume mesh generation/conversion and marker naming. |

Inference from the evidence: OpenFOAM has the stronger maintained, first-party
path for free-surface hull-resistance-style work because the v2512 tree carries
a DTCHull `interFoam` tutorial with force output on the hull patch. SU2 has a
cleaner install story and cleaner history-output parser, but the maintained
sources found here support generic incompressible/external-flow work rather than
a comparable first-party ship/free-surface resistance workflow.

## Viable Options

### Option A - Conservative Default: OpenFOAM.com v2512 `interFoam`, blocked behind watertight evidence

Decision shape:

- Solver target: OpenFOAM.com/OpenCFD OpenFOAM-v2512, local command adapter,
  `interFoam` case family derived from the DTCHull pattern.
- Solver profile name: `openfoam-v2512-interfoam-local`.
- Required mesh profile: `watertight_solid_resistance_v1`.
- Required readiness: `cfd_ready`, backed by matching generated-body,
  self-intersection, and volume-mesh diagnostic evidence. The current fixture
  JSON volume-mesh artifact is not enough for real OpenFOAM success unless a
  later workflow defines it as an OpenFOAM-readable volume-mesh handoff.
- Case-template version: `openfoam-v2512-interfoam-dtchull-v1`.
- Parser scope: parse only version/provenance, logs, and
  `postProcessing/forces/**/force.dat`; normalize `drag_force_n` by projecting
  the accepted force vector onto the job velocity axis; preserve raw artifact
  refs. Pressure/viscous components may be stored only when the file format is
  proven by fixtures. Do not parse or claim wave profiles, convergence
  validity, calibrated drag, or final resistance.
- Install/platform notes: pin OpenFOAM.com v2512. Linux is the primary
  supported platform. macOS and Windows are documented as Docker/WSL/source
  routes but should be optional integration environments, not required CI.
- CI strategy: required CI uses fake commands and fixture `force.dat`/log files
  only. Optional installed-solver smoke tests require an explicit environment
  flag and discovered OpenFOAM environment.

Pros: best domain fit for eventual kayak free-surface resistance; aligns with
official hull tutorial and force output; preserves all local no-claims gates.

Cons: no real `succeeded` path should be enabled until the production
volume-mesh/readiness gate exists. This is a solver-selection decision plus
adapter skeleton path, not an immediate physics result.

### Option B - Incremental OpenFOAM open-surface adapter

Decision shape:

- Solver target: OpenFOAM.com v2512, but require
  `open_wetted_surface_resistance_v1` and `cfd_surface_candidate`.
- Case-template version: `openfoam-v2512-open-wetted-surface-smoke-v1`.
- Parser scope and CI: same raw `forces` parser as Option A, with fake-command
  required CI and optional installed smoke.

Pros: could reuse current mesh-package readiness and expose a real external
command earlier.

Cons: the decision would need to prove the open-surface boundary semantics are
physically and operationally coherent. Without that proof, this risks implying
more than the current open hull/deck surfaces support. It should be labeled
solver smoke or raw external-flow evidence, not kayak resistance.

### Option C - SU2 incompressible external-flow adapter

Decision shape:

- Solver target: SU2 8.5.0 or a pinned successor, `SU2_CFD` with
  `INC_NAVIER_STOKES` or `INC_RANS`.
- Required mesh profile: likely a new SU2/CGNS volume-mesh profile or
  `watertight_solid_resistance_v1` after a converter/marker contract lands.
- Case-template version: `su2-8.5-inc-rans-external-flow-v1`.
- Parser scope: parse `history.csv` or `history.dat` fields for `DRAG`,
  `FORCE_X/Y/Z`, and RMS residuals; store surface/volume output refs if present.
- CI strategy: straightforward fake-command and fixture-history tests; optional
  `SU2_CFD -d` or tiny installed smoke behind an environment flag.

Pros: SU2 has cross-platform binaries, a documented source build, and clean
history-output configuration. Parser fixtures are likely simpler than OpenFOAM
post-processing directories.

Cons: weaker direct evidence for free-surface kayak/ship resistance in current
maintained docs found for this research pass. It still needs a volume mesh and
marker contract. Choosing SU2 first would optimize adapter maintainability over
domain fidelity.

### Option D - Defer real external solver, harden RFC 0040 first

Decision shape:

- Keep `fixture-local-command` as the only successful adapter.
- Land the RFC 0040 readiness report, generated-body hardening matrix, and a
  real volume-mesh diagnostic contract before naming any external solver
  success path.

Pros: lowest overclaim risk; directly attacks the present blocker.

Cons: leaves RFC 0041 solver-selection blocked and does not answer which case
template/parser/install surface future adapter code should target. It is a
reasonable sequencing outcome only if the decision panel is unwilling to name a
solver before volume-mesh evidence exists.

## Implementation Gates

- Pin one solver distribution, release line, and version check. Avoid a generic
  "OpenFOAM" profile because OpenFOAM.com v2512 and OpenFOAM Foundation v13 are
  distinct release lines with different packaging and case drift risk.
- Keep the adapter outside `Hull` and geometry models. It should translate
  existing `CfdJobSpec` plus `MeshPackageManifest` into a case directory and
  translate raw solver outputs back into `CfdRunRecord`/raw-result records.
- Decide whether the first profile is open-surface or watertight before code
  lands. If watertight, no external solver command should run unless
  `prepare` verifies matching body, diagnostic, volume-mesh, profile, and hash
  evidence. If open-surface, the decision must explicitly limit accepted use.
- Treat OpenFOAM meshing as a separate evidence-producing workflow unless the
  solver decision explicitly expands scope. Running `snappyHexMesh` inside the
  adapter must not become the readiness authority by side effect.
- Define the force direction convention. The parser must know whether kayak
  drag is the +X or -X component under kayak-gen's stern-positive X convention
  and the case inlet velocity direction.
- Bound logs and runtime. Stable errors should include at least:
  `solver_unavailable`, `version_check_failed`, `command_failed`, `timeout`,
  `missing_output`, `malformed_output`, `parser_mismatch`,
  `readiness_below_requirement`, and mesh evidence rejection codes already used
  by dispatch.
- Do not vendor OpenFOAM tutorial files verbatim without license review.
  Prefer project-owned deterministic templates informed by the official case
  structure, with source URLs recorded in comments/docs.
- Required tests must not need OpenFOAM or SU2 installed. They should cover
  profile registration, deterministic prepare, readiness rejection, unavailable
  dependency, failed command, timeout, missing output, malformed output,
  parser success from checked-in fixture files, run-record round trip, and
  forbidden claim promotion. Optional installed-solver tests should be skipped
  unless a named flag and binary/environment are present.

## Recommendation

The evidence supports choosing OpenFOAM.com v2512 `interFoam` as the first
external solver target for a kayak-relevant path, with
`openfoam-v2512-interfoam-dtchull-v1` as the case-template version and a raw
`forces` parser as the initial parser scope.

The conservative decision should pair that solver choice with
`watertight_solid_resistance_v1` and `cfd_ready` readiness, not with current
ordinary generated open-surface packages. That means the next implementation
should be allowed to add profile metadata, dependency detection, deterministic
case rendering fixtures, parser fixtures, and unavailable/failed behavior, but
should not enable a real OpenFOAM `succeeded` path until RFC 0040-style
volume-mesh evidence exists for an OpenFOAM-readable handoff.

If the decision panel needs an immediately runnable external binary before
volume-mesh evidence lands, Option B or C can be selected, but the accepted use
should be "raw external-solver smoke/evidence" rather than kayak resistance.
