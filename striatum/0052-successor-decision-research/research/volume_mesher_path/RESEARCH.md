---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-007
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_fb178e3f119c4d63a577788128a04303
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_volume_mesher_path
lease: lease_fd4be182c76d4aafa7388b79f029521f
date: 2026-05-14

# Research - Volume-Mesh Production Path

## Decision Question

Should the next RFC 0040 slice select a production volume-mesher path, continue
fixture-only diagnostics, use OpenFOAM/snappyHexMesh, Gmsh, cfMesh, or another
tool, and what evidence gates are required before solver readiness?

## Local Constraints And No-Claims Boundaries

- Current user-facing packages remain open hull/deck inspection surfaces unless
  verified generated-body and volume-mesh evidence is attached. `cfd_ready`
  under `watertight_solid_resistance_v1` means solver-input readiness only, not
  solver success or validated CFD physics (`docs/PRD.md`,
  `docs/USER_GUIDE.md`, `docs/rfcs/0010-cfd-ready-mesh-contract.md`,
  `docs/rfcs/0023-watertight-volume-mesh-handoff.md`).
- RFC 0040 requires a ladder: inspection surfaces, synthetic diagnostic bodies,
  generated closed evaluation bodies, volume-mesh handoff evidence, and only
  then solver dispatch prerequisites. It explicitly does not select a
  production mesher or authorize ordinary package promotion to `cfd_ready`
  (`docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md`).
- Workflow 0050/D003 chose readiness-report-first, with structured volume-mesh
  diagnostics and hashes as follow-up. D004 selected OpenFOAM.com
  OpenFOAM-v2512 `interFoam` as the first real solver target, gated by
  `watertight_solid_resistance_v1` and `cfd_ready`
  (`docs/DECISION_LOG.md`, `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`).
- Workflow 0051 landed the readiness report, fixture volume-mesh evidence,
  and OpenFOAM adapter skeleton. The skeleton still blocks real `succeeded`
  runs with `solver_success_blocked` until OpenFOAM-readable volume-mesh
  evidence exists (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`).
- The current implementation already has the right evidence shape:
  `VolumeMeshDiagnostic` records body refs, diagnostic hashes, mesher metadata,
  deterministic input digests, artifacts/checksums, patch metadata, cell and
  quality summaries, readiness reasons, and warnings
  (`kayakgen/eval/volume_mesh.py`, `kayakgen/eval/mesh_package.py`,
  `kayakgen/eval/cfd/jobs.py`).
- No option below authorizes calibrated resistance, validated CFD, final design
  fitness, hosted workers, browser-side meshing, or high-angle stability claims.

## External Evidence

| Source | Accessed | Claim supported |
| --- | --- | --- |
| OpenFOAM.com v2512 release notes, https://www.openfoam.com/news/main-news/openfoam-v2512 | 2026-05-14 | OpenFOAM-v2512 is a current Keysight/OpenCFD release, GPL-distributed, with Linux packages, Windows routes, Docker, source, and GitLab-hosted repositories. This supports pinning a concrete OpenFOAM.com release rather than a generic "OpenFOAM" dependency. |
| OpenFOAM.com current release page, https://www.openfoam.com/current-release | 2026-05-14 | The current OpenFOAM.com release is v2512, released 2025-12-22. |
| OpenFOAM v2512 DTCHull `Allrun`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/Allrun | 2026-05-14 | The maintained OpenFOAM.com DTCHull free-surface tutorial path copies a hull STL, runs `surfaceFeatureExtract`, `blockMesh`, repeated `refineMesh`, `snappyHexMesh`, `setFields`, and then `interFoam`. |
| OpenFOAM v2512 DTCHull `controlDict`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/controlDict | 2026-05-14 | The same tutorial runs `interFoam` and configures a `forces` function object on the `hull` patch, supporting the existing parser focus on `postProcessing/forces/**/force.dat`. |
| OpenFOAM v2512 DTCHull `snappyHexMeshDict`, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/tutorials/multiphase/interFoam/RAS/DTCHull/system/snappyHexMeshDict | 2026-05-14 | The tutorial names the STL-derived hull surface as a wall patch, uses castellation, snapping, layer addition, `locationInMesh`, and mesh-quality controls. This is close to kayakgen's desired hull-resistance handoff. |
| OpenFOAM Foundation v13 User Guide, snappyHexMesh, https://doc.cfd.direct/openfoam/user-guide-v13/snappyhexmesh | 2026-05-14 | `snappyHexMesh` is a supplied OpenFOAM mesh generator for 3D hex/split-hex meshes from STL/OBJ tri-surfaces, using a background hex mesh, surface snapping, optional layers, and mesh-quality controls. Quality entries include non-orthogonality, skewness, concavity, minimum volume, determinant, face weight, and volume ratio. |
| OpenFOAM Foundation v13 User Guide, mesh description, https://doc.cfd.direct/openfoam/user-guide-v13/mesh-description | 2026-05-14 | OpenFOAM finite-volume meshes are arbitrary polyhedral cells with explicit patch boundaries, closed cell topology, and outward boundary face normals. This supports making OpenFOAM patch/marker evidence first-class in kayakgen diagnostics. |
| OpenFOAM v2512 `checkMesh` source, https://gitlab.com/openfoam/core/openfoam/-/raw/OpenFOAM-v2512/applications/utilities/mesh/manipulation/checkMesh/checkMesh.C | 2026-05-14 | `checkMesh` checks mesh validity, can apply user-defined `system/meshQualityDict`, and can write selected mesh-quality fields/check data. This supports making `checkMesh` a required evidence gate, not an optional log. |
| Gmsh official site, https://gmsh.info | 2026-05-14 | Gmsh 4.15.2 is the stable release as of 2026-03-24, available cross-platform and by `pip`, distributed under GPL with a linking exception. |
| Gmsh reference manual, https://gmsh.info/doc/texinfo/ | 2026-05-14 | Gmsh is a 3D finite-element mesh generator with CAD, command-line, and Python APIs; it supports OpenCASCADE geometry, discrete entities such as STL with reparametrization, conformal elements including tetrahedra/hexahedra/prisms/pyramids, and physical groups that affect exported mesh contents. |
| OpenFOAM `gmshToFoam` man page, https://www.openfoam.com/documentation/guides/v1912/man/gmshToFoam.html | 2026-05-14 | OpenFOAM has a utility to convert Gmsh `.msh` files to OpenFOAM format, making a Gmsh path possible but conversion/marker semantics become part of the evidence contract. |
| CF-MESH+ and cfMesh FAQ, https://cfmesh.com/faq/ | 2026-05-14 | CF-MESH+ can run in console mode but requires a license; the open-source cfMesh product is described by its vendor as no longer maintained and provided as-is. |
| cfMesh overview, https://cfmesh.com/cfmesh-a-novel-library-for-automatic-mesh-generation/ | 2026-05-14 | cfMesh was designed as an OpenFOAM-framework mesh-generation library with Cartesian, tetrahedral, polyhedral, boundary-layer, patch-transfer, and parallel meshing features. This makes it technically relevant but weaker as a default because of maintenance and licensing posture. |

Inference from the external evidence: since D004 already selected
OpenFOAM.com v2512 `interFoam`, the lowest-integration-risk volume-mesh path is
the OpenFOAM-native path used by the official DTCHull tutorial:
triSurface/STL input, `blockMesh` background domain, `snappyHexMesh`,
`checkMesh`, named patches, and force output on the `hull` patch. Gmsh remains
credible as a standalone mesher, but it adds a conversion boundary before the
already-selected OpenFOAM solver. cfMesh/CF-MESH+ is technically adjacent, but
its open-source maintenance status and/or commercial licensing make it a poor
default for this repo's first production-evidence path.

## Viable Options

### Option A - Conservative Default: OpenFOAM-v2512 `snappyHexMesh` Evidence Harness

Select OpenFOAM.com v2512 `snappyHexMesh` as the first production-mesher
candidate for RFC 0040, but land it only as a deterministic evidence-producing
diagnostic harness. Do not promote ordinary generated packages, do not enable
real OpenFOAM `succeeded` records, and do not treat one passing mesh as
validated CFD.

Scope for the next slice:

- add a new volume-mesh profile name such as
  `openfoam-v2512-snappyhexmesh-watertight-v1`;
- render an OpenFOAM meshing case from `generated_hull_plus_deck_closed_body_v1`
  evidence, not from open hull/deck display STLs;
- write deterministic `blockMeshDict`, `snappyHexMeshDict`,
  `surfaceFeatureExtractDict`, `meshQualityDict`, body tri-surface artifact,
  and command metadata;
- optionally run installed `surfaceFeatureExtract`, `blockMesh`,
  `snappyHexMesh -overwrite`, and `checkMesh -allTopology -allGeometry
  -meshQuality`;
- parse or record `checkMesh` evidence, `constant/polyMesh` artifacts, boundary
  patches, quality summaries, logs, command argv, OpenFOAM version, and
  SHA-256 checksums into `VolumeMeshDiagnostic`;
- keep required CI solver-free by using fixtures/fake commands, with optional
  installed-OpenFOAM smoke only behind an explicit environment flag.

Why it wins:

- It aligns with D004's selected solver and official DTCHull-style workflow.
- It preserves OpenFOAM patch names and `checkMesh` quality semantics without a
  Gmsh conversion layer.
- It reuses the current `VolumeMeshDiagnostic`, manifest, dispatch, and
  OpenFOAM skeleton boundaries.
- It advances beyond fixture-only diagnostics while keeping readiness blocked
  until evidence gates pass.

Main risk: `snappyHexMesh` setup can become an implicit solver-readiness
authority. The next RFC must state that `snappyHexMesh` output is only evidence
until kayakgen verifies body refs, hashes, patch metadata, quality summaries,
and profile-specific gates.

### Option B - Continue Fixture-Only Diagnostics

Continue hardening fixture volume-mesh diagnostics, generated-body matrix
coverage, and forged-evidence rejection without selecting a production mesher.

Why it remains viable:

- It is safest for claim hygiene and CI.
- It can broaden negative tests before external dependencies land.
- It avoids mixing generated-body hardening with installed OpenFOAM setup.

Why it should not be the whole next step:

- Workflow 0051 has already landed the readiness report and fixture handoff
  evidence.
- RFC 0041/OpenFOAM adapter work is now blocked specifically on
  OpenFOAM-readable volume-mesh evidence.
- More fixture-only work will not answer patch naming, background-domain,
  layer, `checkMesh`, or artifact-format questions needed for solver dispatch.

Use this only if generated-body diagnostics are still failing across the
default/plumb/mixed-rake/class-envelope matrix. Otherwise keep fixtures as
required tests inside Option A rather than as the primary path.

### Option C - Gmsh First, Then Convert To OpenFOAM

Select Gmsh as the first production volume mesher, generate `.msh`, and convert
with `gmshToFoam` before OpenFOAM dispatch.

Why it is viable:

- Gmsh is current, scriptable from Python, cross-platform, and has mature CAD
  and discrete-entity workflows.
- Physical groups can represent boundary roles if kayakgen owns strict naming
  and export rules.
- The Python API may fit kayakgen's existing Python implementation better than
  OpenFOAM dictionary rendering.

Why it loses as first default:

- The selected solver is OpenFOAM.com v2512, so Gmsh adds conversion,
  physical-group, patch-orientation, and `.msh` version gates before the solver
  sees a native mesh.
- Boundary-layer and wall-adjacent evidence would need separate acceptance
  against OpenFOAM `checkMesh`.
- It does not reuse the official DTCHull tutorial pattern as directly as
  `snappyHexMesh`.

This is a good fallback if `snappyHexMesh` cannot produce repeatable acceptable
meshes from kayakgen's closed body, or if a future solver decision needs a
solver-neutral mesher.

### Option D - cfMesh / CF-MESH+ Or Another Mesher

Keep cfMesh/CF-MESH+ and other tools as future candidates, not the next default.

Why it is technically relevant:

- cfMesh is OpenFOAM-adjacent and was designed for automatic OpenFOAM
  polyhedral/tetrahedral/Cartesian meshing with boundary-layer support.
- CF-MESH+ has console operation and a product path with stronger support.

Why it loses now:

- The vendor FAQ says open-source cfMesh is no longer maintained and is
  provided as-is.
- CF-MESH+ introduces license-manager and commercial/trial-license gates that
  do not fit required CI or open-repo reproducibility.
- Choosing it would add operational questions while not being the documented
  path of the selected OpenFOAM DTCHull-style solver target.

Treat this as later comparative research only if OpenFOAM-native meshing fails.

## Required Quality And Evidence Gates Before Solver Readiness

These gates are for the first OpenFOAM/snappyHexMesh profile. They are
profile-specific, not universal kayak-gen quality thresholds.

### Source Body Gates

- `body_type == generated_hull_plus_deck_closed_body`.
- `profile_name == generated_hull_plus_deck_closed_body_v1`.
- Same `body_ref`, source hull hash, coordinate system, tolerance hash, and
  closed-volume diagnostic hash across body, package, mesher input, and volume
  diagnostic.
- Closed-volume diagnostics pass: zero raw/welded boundary edges, zero
  raw/welded nonmanifold edges, no degenerate/nonfinite/invalid geometry,
  positive signed volume, outward normals, serialized cap/join/waterline
  policy, and passed self-intersection status.
- Generated-body matrix coverage exists for default, plumb bow/stern,
  mixed-rake, `beam_wl_m != beam_oa_m`, low/high draft, representative `Cp`
  and `Cm`, and structured unsupported/invalid cases.

### Mesher Provenance Gates

- Mesher profile is explicit, for example
  `openfoam-v2512-snappyhexmesh-watertight-v1`.
- OpenFOAM version probe records OpenFOAM.com v2512 or records an unavailable
  state; a Foundation/OpenFOAM.org version must not silently satisfy a
  `.com v2512` profile.
- Case-template version, command argv, working directory, environment summary,
  `blockMeshDict`, `snappyHexMeshDict`, `surfaceFeatureExtractDict`,
  `meshQualityDict`, background-domain bounds, `locationInMesh`, layer settings,
  refinement settings, and tri-surface input all have SHA-256 digests.
- Required outputs exist under relative package refs only:
  `constant/polyMesh/*`, mesher logs, `checkMesh` output, and any simplified or
  generated surface files.
- Required boundary patches are present and role-tagged at minimum:
  `hull`/`generated_hull_plus_deck` as `wetted_body`, plus accepted farfield,
  inlet/outlet, free-surface, atmosphere, or symmetry roles as the case template
  defines them. Missing or renamed patches block readiness.

### Mesh Quality Gates

Hard blockers for the first profile:

- `checkMesh` fails topology, geometry, or `meshQualityDict` checks.
- zero cells, missing `polyMesh`, missing boundary file, or missing hull patch;
- nonfinite point/cell values;
- invalid, inverted, or zero-volume cells;
- non-positive minimum cell volume;
- body-surface mismatch or stale/cross-body checksums;
- patch face counts do not sum to recorded boundary face count;
- artifact checksums differ from manifest evidence.

Draft starter thresholds should come from OpenFOAM mesh-quality controls and be
stored in the profile's `meshQualityDict`, not hidden in prose. A defensible
initial profile can require:

- `maxNonOrtho <= 65`;
- `maxBoundarySkewness <= 20`;
- `maxInternalSkewness <= 4`;
- `maxConcave <= 80`;
- `minVol > 0` with a profile-specific absolute floor;
- `minDeterminant >= 0.001`;
- `minFaceWeight >= 0.05`;
- `minVolRatio >= 0.01`;
- no failed layer-addition checks on the hull patch when layers are enabled.

Those values are OpenFOAM-style solver-input quality gates, not proof of
hydrodynamic accuracy. Any relaxation must be recorded in the diagnostic and
remain a warning or blocker according to the profile.

### Package And Dispatch Gates

- `MeshPackageManifest.readiness_authority ==
  verified_watertight_volume_mesh_evidence`.
- Manifest evidence hashes include closed-volume diagnostic,
  self-intersection diagnostic, volume-mesh diagnostic, and every mesher output
  artifact consumed by dispatch.
- Dispatch rejects missing, malformed, absolute-path, `..`, stale, cross-body,
  cross-profile, synthetic, or hand-edited evidence before any solver command
  runs.
- `cfd_ready` can be emitted only for the selected profile and only after all
  source-body, mesher-provenance, mesh-quality, package, and dispatch gates
  pass.
- Even after `cfd_ready`, OpenFOAM solver output remains `raw_unvalidated`.
  Solver success, calibration, validation, and design-fitness claims remain
  separate later decisions.

## Recommendation

The evidence supports Option A: select OpenFOAM.com v2512 `snappyHexMesh` as
the first production-mesher path for RFC 0040, but implement it as a
diagnostic/evidence harness first. This is the narrowest path that matches the
already accepted OpenFOAM.com v2512 `interFoam` solver target, reuses the
official DTCHull-style workflow, and answers the current blocker without
pretending that a generated body or fixture mesh is production solver input.

The next slice should not continue fixture-only diagnostics as the primary
track unless generated-body matrix hardening is still failing. It should not
choose Gmsh or cfMesh as the first default unless `snappyHexMesh` fails the
repeatability or quality gates. The first successful `snappyHexMesh` package
should still be described as OpenFOAM-readable volume-mesh evidence for one
profile, not as validated CFD, calibrated resistance, final prediction, or
design fitness.
