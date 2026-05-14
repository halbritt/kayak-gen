---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_355a69712a574a189da9f52586a50883
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_volume_mesher_path_codex
lease: lease_24136bd4cf9c4796bedf8b231d269f95

# Vote - Volume-Mesh Production Path

Vote: Option A - OpenFOAM-v2512 `snappyHexMesh` evidence harness

## Decision Sentence

Select OpenFOAM.com OpenFOAM-v2512 `snappyHexMesh` as the first production
volume-mesher path for RFC 0040 follow-up work, implemented first as a
deterministic evidence harness over `generated_hull_plus_deck_closed_body_v1`
with required `checkMesh`, patch, artifact-hash, and dispatch gates; do not
enable ordinary package promotion or real OpenFOAM `succeeded` records until
that OpenFOAM-readable volume-mesh evidence satisfies the selected profile.

## Evidence

The local decision trail points directly at an OpenFOAM-native mesh path.
D003 chose readiness-report-first, with volume-mesh diagnostics, hashes,
boundary metadata, and generated-body coverage as follow-up, while explicitly
leaving ordinary generated packages below watertight solver-profile acceptance
(`docs/DECISION_LOG.md`, `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`).
D004 then selected OpenFOAM.com OpenFOAM-v2512 `interFoam` as the first real
solver target, with profile `openfoam-v2512-interfoam-local`, required mesh
profile `watertight_solid_resistance_v1`, readiness `cfd_ready`, and case
template `openfoam-v2512-interfoam-dtchull-v1`. It also blocked any real
OpenFOAM `succeeded` path until matching RFC 0040/RFC 0023 OpenFOAM-readable
volume-mesh evidence exists, and kept all output `raw_unvalidated`
(`striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`).

The current user-facing docs preserve the same boundary. Generated hull and
deck packages are open-surface inspection/candidate artifacts, not watertight
solver input; `watertight-solid` can report `cfd_ready` only for matching
generated-body fixture volume-mesh evidence with bound diagnostics, hashes, and
paths; no real OpenFOAM, SU2, hosted worker, Docker solver, or calibrated CFD
result is available today (`docs/USER_GUIDE.md`). The roadmap says generated
closed bodies remain evaluation evidence, not production solver input, unless
matching body diagnostics, self-intersection evidence, volume-mesh evidence,
hashes, artifacts, and solver-profile gates all pass (`docs/ROADMAP.md`).

RFC 0040 is the decisive local contract. Its readiness ladder separates open
inspection surfaces, synthetic diagnostic bodies, generated closed evaluation
bodies, volume-mesh handoff evidence, and solver dispatch prerequisites. It
states that generated closed bodies stay below watertight solver readiness
until a volume-mesh diagnostic references the same body, diagnostics, hashes,
tolerances, and selected solver profile, and that a real solver adapter may
consume only a package whose selected solver profile is satisfied by verified
evidence (`docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md`). RFC 0023
adds the matching handoff rule: `cfd_ready` for `watertight_solid_resistance_v1`
requires passing generated-body, self-intersection, and volume-mesh diagnostics
and must not accept caller-supplied readiness strings as authority
(`docs/rfcs/0023-watertight-volume-mesh-handoff.md`).

Workflow 0051 confirms this is now the active blocker rather than an abstract
future concern. The readiness report and OpenFOAM adapter skeleton landed; the
adapter enforces `required_mesh_profile="watertight_solid_resistance_v1"` and
`cfd_ready`, but parser-readable fake OpenFOAM output still returns
`solver_success_blocked`. The final review records that the real `succeeded`
path remains gated on RFC 0040 production volume-mesh evidence
(`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`).

My independent external check supports the research packet's recommendation.
OpenFOAM.com lists OpenFOAM-v2512 as the current release, released
2025-12-22, with Linux packages, Docker routes, Windows routes, source, and
GitLab repositories
(https://www.openfoam.com/current-release,
https://www.openfoam.com/news/main-news/openfoam-v2512; accessed
2026-05-14). The maintained v2512 DTCHull tutorial copies a hull STL into
`constant/triSurface`, runs `surfaceFeatureExtract`, `blockMesh`, repeated
refinement, `snappyHexMesh -overwrite`, `setFields`, and then the selected
application; its `controlDict` uses `interFoam` and a `forces` function object
on the `hull` patch
(https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun,
https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict;
accessed 2026-05-14). The same tutorial's `snappyHexMeshDict` treats the STL
as a `triSurfaceMesh`, names it `hull`, assigns wall patch metadata, uses
castellation, snapping, layer addition, feature extraction, and
`locationInMesh`
(https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/snappyHexMeshDict;
accessed 2026-05-14).

The OpenFOAM documentation also matches the evidence gates this project needs.
The `snappyHexMesh` guide describes a split-hex mesher that reads STL/OBJ/VTK
surfaces, creates a background mesh, extracts surface features, snaps to
triangulated surfaces, and can add prismatic layers under mesh-quality controls
(https://www.openfoam.com/documentation/guides/latest/doc/guide-meshing-snappyhexmesh.html;
accessed 2026-05-14). The current `checkMesh` source documents
`-allGeometry`, `-allTopology`, `-meshQuality`, selected quality-field output,
and explicit `Mesh OK` versus failed-check reporting, which makes `checkMesh`
a proper required evidence gate rather than a log-only convenience
(https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/applications/utilities/mesh/manipulation/checkMesh/checkMesh.C;
accessed 2026-05-14).

Gmsh remains technically credible but is second-best for this decision. Its
official site identifies it as a current 3D finite-element mesh generator with
GUI, command-line, scripting, and Python APIs, stable release 4.15.2 as of
2026-03-24, and GPL distribution with a linking exception (https://gmsh.info/;
accessed 2026-05-14). That is useful if OpenFOAM-native meshing fails, but it
adds a `.msh` export and `gmshToFoam` conversion boundary before the already
selected OpenFOAM solver can consume the mesh. cfMesh/CF-MESH+ loses as a
default because the vendor FAQ says open-source cfMesh is no longer maintained
and provided as-is, while CF-MESH+ introduces license/trial-license operations
that do not fit required CI or open-repo reproducibility
(https://cfmesh.com/faq/; accessed 2026-05-14).

## Why Rejected Alternatives Lose

Continuing fixture-only diagnostics loses as the primary next step. Fixtures
are still required tests, especially for forged-evidence rejection and
generated-body matrix coverage, but workflow 0051 already landed the readiness
report, fixture handoff evidence, and adapter skeleton. The current blocker is
OpenFOAM-readable production volume-mesh evidence, including case templates,
patches, quality summaries, and artifact checksums. Fixture-only work cannot
answer those OpenFOAM-specific handoff questions.

Gmsh-first loses as the default despite being viable. It is current,
scriptable, cross-platform, and strong for general meshing, but the accepted
solver target is OpenFOAM.com v2512 `interFoam`. Starting with Gmsh would add
physical-group, orientation, `.msh` version, and conversion gates before
`checkMesh` and dispatch can prove an OpenFOAM-native package. It should remain
a fallback if `snappyHexMesh` cannot produce repeatable, acceptable meshes from
kayakgen's generated closed body.

cfMesh, CF-MESH+, or another mesher loses now. cfMesh is OpenFOAM-adjacent, but
the open-source product's maintenance posture is weak. CF-MESH+ has a supported
product path, but license-manager, trial, and commercial-use restrictions are
poor first dependencies for deterministic open CI. Other meshers should not be
selected without stronger project-specific evidence than the OpenFOAM-native
DTCHull path already provides.

Immediate solver-readiness promotion loses outright. A successful
`snappyHexMesh` run is not a validated CFD result, not calibrated resistance,
not final design fitness, and not even sufficient by itself for dispatch. It is
one profile's volume-mesh evidence only after body identity, closed-volume
diagnostics, self-intersection status, OpenFOAM version, patches, `checkMesh`,
quality fields, artifacts, and checksums all match the manifest.

## Implementation Gates And No-Claims Language

- Add an explicit volume-mesh profile, for example
  `openfoam-v2512-snappyhexmesh-watertight-v1`.
- Accept only `generated_hull_plus_deck_closed_body_v1` inputs with matching
  body ref, hull hash, closed-volume diagnostic hash, self-intersection
  diagnostic hash, coordinate system, tolerance policy, and cap/join/waterline
  policy.
- Probe and record OpenFOAM.com OpenFOAM-v2512. A Foundation/OpenFOAM.org
  binary or another OpenFOAM.com release must not silently satisfy the v2512
  profile.
- Render deterministic `blockMeshDict`, `snappyHexMeshDict`,
  `surfaceFeatureExtractDict`, `meshQualityDict`, body tri-surface artifact,
  background-domain bounds, `locationInMesh`, refinement settings, layer
  settings, command argv, environment summary, and case-template version.
  Record SHA-256 digests for every input and generated artifact.
- Running installed OpenFOAM commands may be optional and explicitly flagged;
  required CI must stay solver-free with fixtures or fake commands. If commands
  run, the evidence path should include `surfaceFeatureExtract`, `blockMesh`,
  `snappyHexMesh -overwrite`, and `checkMesh -allTopology -allGeometry
  -meshQuality`.
- Require relative package refs only for `constant/polyMesh/*`, mesher logs,
  `checkMesh` output, simplified/generated surfaces, and boundary files.
  Absolute paths, `..`, missing refs, hand-edited refs, stale hashes, or
  cross-body/cross-profile evidence must block readiness.
- Require named and role-tagged OpenFOAM patches. At minimum, the generated
  body patch must resolve to `hull` or `generated_hull_plus_deck` with
  `wetted_body` role, and farfield/inlet/outlet/free-surface/atmosphere or
  symmetry roles must match the case template. Missing or renamed patches block
  readiness.
- Treat `checkMesh` topology, geometry, and `meshQualityDict` failures as hard
  blockers. Also block zero cells, missing `polyMesh`, missing boundary file,
  missing hull patch, nonfinite coordinates, inverted or zero-volume cells,
  non-positive minimum cell volume, body-surface mismatch, inconsistent patch
  face counts, and artifact checksum mismatches.
- Store initial quality thresholds in the profile's `meshQualityDict`, not in
  prose alone. A first profile can use OpenFOAM-style gates such as
  non-orthogonality, boundary/internal skewness, concavity, minimum volume,
  determinant, face weight, and volume ratio, with any relaxation recorded as a
  warning or blocker according to the profile.
- `MeshPackageManifest.readiness_authority` must remain evidence-derived.
  `cfd_ready` may be emitted only for the selected profile after all source
  body, mesher provenance, mesh quality, package, and dispatch gates pass.
- The OpenFOAM adapter may not report a real `succeeded` run until dispatch
  verifies matching OpenFOAM-readable volume-mesh evidence. Even then, solver
  output remains `raw_unvalidated`.
- Do not claim calibrated CFD, calibrated analytical resistance, final
  prediction, design fitness, seaworthiness, safety, hosted worker readiness,
  browser-side meshing, or broad watertight readiness from this decision.

Confidence: high
