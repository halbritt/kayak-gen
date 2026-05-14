---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote - CFD Solver Path

Vote: Conservative OpenFOAM v2512 `interFoam`, watertight-gated

## Decision Sentence

Select OpenFOAM.com/OpenCFD OpenFOAM-v2512 `interFoam` as kayak-gen's first
real external CFD solver target, exposed as local profile
`openfoam-v2512-interfoam-local` with required mesh profile
`watertight_solid_resistance_v1`, case template
`openfoam-v2512-interfoam-dtchull-v1`, and a raw `forces` parser; do not enable
a real solver `succeeded` path until matching RFC 0040/RFC 0023 watertight
volume-mesh evidence satisfies the selected profile.

## Evidence

- The solver-path research packet recommends OpenFOAM.com v2512 `interFoam`
  because it has the strongest maintained hull/free-surface evidence among the
  reviewed options: the OpenFOAM v2512 DTCHull tutorial uses a DTC hull STL,
  `surfaceFeatureExtract`, `blockMesh`, repeated refinement,
  `snappyHexMesh`, `setFields`, and then the case application; its
  `controlDict` runs `interFoam` and configures a `forces` function object on
  the `hull` patch. Citation: `striatum/0050-decision-panel-research/research/solver_path/RESEARCH.md`.
- The local roadmap and RFC spine make the profile gate non-negotiable. Current
  CFD support is job/profile/run plumbing plus unavailable, mock, and fixture
  local-command states, not OpenFOAM, SU2, hosted workers, Docker solvers, or
  validated output. Citation: `docs/PRD.md`, `docs/USER_GUIDE.md`,
  `docs/ROADMAP.md`, `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md`, and
  `docs/rfcs/0026-first-real-cfd-fixture-adapter.md`.
- RFC 0041 requires the first real adapter decision to name one solver target,
  version command, mesh profile, case-template version, expected raw outputs,
  install/platform notes, and CI that does not require the external binary. It
  also says a watertight-required solver profile must reject packages without
  matching evidence before execution. Citation:
  `docs/rfcs/0041-real-cfd-adapter-successor.md`.
- RFC 0040 and RFC 0023 say generated closed bodies remain below
  watertight-required solver-profile acceptance until volume-mesh diagnostics
  reference the same generated body, hull hash, diagnostic hashes, solver
  profile, artifacts, and checksums. Citation:
  `docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md` and
  `docs/rfcs/0023-watertight-volume-mesh-handoff.md`.
- Independent external check: OpenFOAM's current release page identifies
  OpenFOAM-v2512 as the current release, released 2025-12-22, with Linux
  package, Docker/Mac, Windows Docker/MinGW/WSL, and source install routes.
  The v2512 release notes also state OpenFOAM is GPL-distributed and describe
  the migration of core repositories to GitLab. Sources accessed 2026-05-14:
  https://www.openfoam.com/current-release and
  https://www.openfoam.com/news/main-news/openfoam-v2512.
- Independent external check: the OpenFOAM v2512 DTCHull `Allrun` file copies a
  DTC hull STL into `constant/triSurface`, runs `surfaceFeatureExtract`,
  `blockMesh`, refinement, `snappyHexMesh`, `setFields`, and then the selected
  application. Its `controlDict` sets `application interFoam` and defines a
  `forces` object for the `hull` patch with water density. Sources accessed
  2026-05-14:
  https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun
  and
  https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict.
- Independent external check: OpenFOAM `snappyHexMesh` consumes triangulated
  surfaces under `constant/triSurface` and supports STL/STLB/OBJ/VTK-style
  triangulated inputs, which fits kayak-gen's manifest/artifact direction but
  still does not create readiness authority by itself. Source accessed
  2026-05-14:
  https://www.openfoam.com/documentation/guides/latest/doc/guide-meshing-snappyhexmesh-geometry.html.
- SU2 remains a credible later option, but the evidence supports it less well
  for the first kayak-relevant free-surface path. SU2 8.5.0 has cross-platform
  binaries and clean history outputs, and its docs cover incompressible
  Navier-Stokes/RANS plus `DRAG`/`FORCE_X/Y/Z` fields. Its mesh docs also show
  native `.su2` or CGNS volume-mesh/marker-tag requirements, which shifts the
  first-adapter burden toward a new converter/marker contract. Sources accessed
  2026-05-14: https://github.com/su2code/SU2,
  https://su2code.github.io/docs_v7/Theory/,
  https://su2code.github.io/docs_v7/Custom-Output/, and
  https://su2code.github.io/docs_v7/Mesh-File/.

## Rejected Alternatives

- Reject an incremental OpenFOAM open-surface adapter as the first accepted
  real solver path. It could exercise a real external command earlier, but it
  would require a new, explicit physical boundary-semantics argument for
  `open_wetted_surface_resistance_v1`. Without that decision it risks making
  ordinary inspection surfaces look like kayak-resistance CFD input.
- Reject SU2 as the first solver path. Its install story and parser surface are
  attractive, but the current primary-source evidence reviewed here points to
  generic incompressible/external-flow capability rather than a maintained
  ship/free-surface hull-resistance template comparable to OpenFOAM DTCHull.
- Reject deferring solver selection entirely. Deferral would minimize overclaim
  risk, but RFC 0041 specifically needs a solver/profile/template/parser
  decision before implementation can be cut. The safer sequencing is to choose
  OpenFOAM now while keeping the success path blocked on mesh evidence.

## Implementation Gates

- Pin the distribution line to OpenFOAM.com/OpenCFD OpenFOAM-v2512; do not use
  a generic `openfoam` profile name.
- Register `openfoam-v2512-interfoam-local` only with
  `result_semantics="raw_unvalidated"`.
- Require `watertight_solid_resistance_v1` and `cfd_ready` evidence before
  real OpenFOAM execution. The adapter may land unavailable/failed states,
  deterministic case rendering, and parser fixtures before that evidence, but
  not a real `succeeded` path.
- Treat `snappyHexMesh` and any OpenFOAM meshing work as evidence-producing
  workflow scope, not as readiness authority hidden inside the solver adapter.
- Parse only stable raw artifacts at first: solver/version provenance, logs,
  and `postProcessing/forces/**/force.dat`. Normalize `drag_force_n` only by an
  accepted force-vector/velocity-axis convention. Defer force coefficients,
  wave profiles, convergence validity, calibrated drag, and final resistance.
- Required CI must use fake commands plus checked-in `force.dat`/log fixtures.
  Installed OpenFOAM smoke tests must be optional, skipped unless an explicit
  environment flag and OpenFOAM environment are present.
- Do not vendor OpenFOAM tutorial files verbatim without license review. Use a
  project-owned deterministic template with source URLs recorded.

## No-Claims Language

All OpenFOAM adapter output remains `raw_unvalidated`. A successful run would
mean only that the dependency was available, the command exited cleanly, and the
accepted raw files parsed. It is not calibrated CFD, not calibrated analytical
resistance, not a final prediction, not design fitness, not a Pareto-default
objective, not proof of seaworthiness, and not evidence that ordinary generated
open hull/deck packages are watertight or solver-ready.

## Confidence

High. The solver choice is well supported by current primary-source evidence
and by the local RFC gates. The confidence is high for selecting OpenFOAM as
the target and medium for the eventual runnable case details because real
success still depends on RFC 0040/RFC 0023 volume-mesh evidence.
