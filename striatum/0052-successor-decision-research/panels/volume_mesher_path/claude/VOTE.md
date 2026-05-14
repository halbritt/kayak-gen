---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_f325d3580af34db39cc7ce75062de040
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_volume_mesher_path_claude
lease: lease_2736f58dc3be4755afaf0d1f6e09bf80
date: 2026-05-14

# Panel Vote - Volume-Mesh Production Path (Claude)

## Vote

**Vote: Option A - OpenFOAM-v2512 `snappyHexMesh` evidence harness.**

## Decision Sentence

Select OpenFOAM.com OpenFOAM-v2512 `snappyHexMesh` as the first production
volume-mesher candidate for RFC 0040 under a new profile name
`openfoam-v2512-snappyhexmesh-watertight-v1`, but land it strictly as a
deterministic OpenFOAM-readable evidence harness over
`generated_hull_plus_deck_closed_body_v1`: render `blockMeshDict`,
`snappyHexMeshDict`, `surfaceFeatureExtractDict`, `meshQualityDict`, the
body tri-surface, and command metadata with SHA-256 digests; optionally run
installed `surfaceFeatureExtract`/`blockMesh`/`snappyHexMesh -overwrite`/
`checkMesh -allTopology -allGeometry -meshQuality` behind an explicit
environment flag; parse `checkMesh` output and `constant/polyMesh` artifacts
into `VolumeMeshDiagnostic.boundary_patches`, `boundary_markers`,
`cell_count`, `boundary_face_count`, cell-quality counts, and
`output_artifacts`; require named hull patch
(`generated_hull_plus_deck`/`wetted_body`) plus accepted farfield/inlet/
outlet/free-surface/atmosphere/symmetry roles; and refuse to emit
`readiness.level == "cfd_ready"` for the new profile unless every existing
fixture gate (matching body_ref, hull hash, closed-volume hash,
self-intersection hash, tolerances hash, deterministic input digests,
artifact checksums, patch metadata, marker map, and quality summaries)
passes. Required CI remains solver-free using fake commands and fixture
files; installed-OpenFOAM smoke is opt-in behind an environment flag.
This decision authorizes mesher profile metadata, deterministic case
rendering, `checkMesh` evidence ingestion, and OpenFOAM-readable
`VolumeMeshDiagnostic` artifacts only. It does not authorize ordinary
generated package promotion to `cfd_ready`, does not enable real OpenFOAM
`succeeded` records, does not select a universal mesh-quality threshold
table, does not authorize calibrated resistance, validated CFD, design
fitness, hosted workers, browser-side meshing, or high-angle stability
claims.

## Evidence And Citations

### Research-Packet Alignment

The research packet
(`striatum/0052-successor-decision-research/research/volume_mesher_path/RESEARCH.md`)
recommends Option A on four concrete grounds: (a) it aligns with D004's
already-accepted OpenFOAM.com v2512 `interFoam` solver target; (b) it
reuses the official OpenFOAM-v2512 DTCHull free-surface tutorial pattern
(`triSurface` STL input, `blockMesh` background, `snappyHexMesh`,
`checkMesh`, force output on a `hull` patch) without a conversion layer;
(c) it answers the current blocker — workflow 0051 landed the OpenFOAM
adapter skeleton but it still returns `error_kind="solver_success_blocked"`
because no OpenFOAM-readable volume-mesh evidence exists; and (d) it
preserves the readiness ladder by keeping `snappyHexMesh` output as
evidence under explicit gates rather than as a hidden solver-readiness
authority. I concur on each ground. The packet's external citations
(OpenFOAM.com v2512 release page, v2512 DTCHull `Allrun`/`controlDict`/
`snappyHexMeshDict`, OpenFOAM Foundation v13 snappyHexMesh and
mesh-description guides, v2512 `checkMesh` source, Gmsh site/reference
manual, OpenFOAM `gmshToFoam` man page, CF-MESH+ FAQ, cfMesh overview)
are dated 2026-05-14 and are consistent with my background knowledge of
the OpenFOAM, Gmsh, and cfMesh projects.

### Independent Verification Of Current Code

I confirmed the packet's framing against the worktree directly:

- `kayakgen/eval/volume_mesh.py:107-149` defines `VolumeMeshDiagnostic`
  with `profile_name` (default `WATERTIGHT_SOLID_PROFILE_NAME =
  "watertight_solid_resistance_v1"`), `body_ref`, `body_type`,
  `source_hull_hash`, `closed_volume_diagnostic_hash`,
  `self_intersection_diagnostic_hash`, `closed_volume_tolerances_hash`,
  `mesher_name`, `mesher_version`, `mesher_config_digest`,
  `deterministic_inputs`, `output_artifacts`,
  `coordinate_system`, `cell_count`, `boundary_face_count`,
  `boundary_patch_names`, `boundary_patches`, `boundary_markers`,
  `exterior_surface_id`, `invalid_cell_count`, `inverted_cell_count`,
  `zero_volume_cell_count`, `nonfinite_cell_count`, `min_cell_volume_m3`,
  `max_aspect_ratio`, `max_skewness`, `body_surface_matches_diagnostic`,
  `readiness`, and `warnings`. The post-validation hook at
  `volume_mesh.py:151-196` already enforces every blocker the packet
  names (profile match, generated body type, positive cell/boundary
  counts, zero cell-quality defects, positive min volume, body-surface
  match, present artifacts, patch/marker consistency). The diagnostic
  shape is exactly what an OpenFOAM-readable evidence harness needs;
  Option A is additive rather than schema-changing.
- `kayakgen/eval/volume_mesh.py:25-33` already names every boundary patch
  role Option A requires (`wetted_body`, `farfield`, `free_surface`,
  `inlet`, `outlet`, `symmetry`, `other`). No new role vocabulary is
  needed.
- `kayakgen/eval/mesh_package.py:43-160` defines
  `ReadinessAuthority` including
  `"verified_watertight_volume_mesh_evidence"`, the
  `watertight_solid_profile()` profile factory, and the
  `solver_profile_not_satisfied` and `readiness_authority_not_volume_mesh`
  blockers. Option A's mesher-provenance gates plug directly into this
  authority enum without redefining who promotes `cfd_ready`.
- `kayakgen/eval/cfd/jobs.py:44-61` pins
  `OPENFOAM_PROFILE_NAME = "openfoam-v2512-interfoam-local"`,
  `OPENFOAM_CASE_TEMPLATE_VERSION =
  "openfoam-v2512-interfoam-dtchull-v1"`, the required force-output path
  `postProcessing/forces/0/force.dat`, and
  `OPENFOAM_SUCCESS_BLOCKED_WARNING`.
  `cfd/jobs.py:480-515` (`openfoam_v2512_interfoam_local_profile`)
  declares `required_mesh_profile="watertight_solid_resistance_v1"` and
  records `known_limitations` including "No production OpenFOAM-readable
  volume mesh evidence is accepted yet" and "No real OpenFOAM succeeded
  run record is enabled in this skeleton." `cfd/jobs.py:1146-1175` is
  the call site that emits `error_kind="solver_success_blocked"` after
  parsing `force.dat`. That is the concrete code path Option A unblocks
  without changing solver/claim semantics.
- The fixture path at
  `kayakgen/eval/volume_mesh.py:244-330`
  (`fixture_volume_mesh_diagnostic`) currently uses
  `FIXTURE_VOLUME_MESHER_NAME = "kayakgen-fixture-volume-mesher"` and
  `FIXTURE_VOLUME_MESHER_VERSION = "rfc0023-fixture-v1"`. Option A adds
  a new mesher profile alongside this fixture without removing it; the
  fixture path remains the deterministic CI surface, and the OpenFOAM
  path becomes the opt-in installed-solver surface.

### Workflow Context Alignment

- D003 (`docs/DECISION_LOG.md:36`) accepted Option A from workflow 0050:
  readiness report first, followed by schema hardening; ordinary
  generated packages stay below `watertight_solid_resistance_v1`. D003's
  revisit trigger names the case Option A here closes: "if a production
  mesher or solver profile is selected with accepted diagnostic
  thresholds."
- D004 (`docs/DECISION_LOG.md:37`) selected OpenFOAM.com v2512
  `interFoam`, mesh profile `watertight_solid_resistance_v1`, readiness
  `cfd_ready`, case template `openfoam-v2512-interfoam-dtchull-v1`.
  D004's consequence says no real OpenFOAM `succeeded` path is
  authorized until matching RFC 0040/RFC 0023 OpenFOAM-readable
  volume-mesh evidence exists. The Option A profile name and case
  template are the natural OpenFOAM-native partner for those two
  decisions.
- The workflow 0051 final review
  (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md`)
  confirms the OpenFOAM skeleton is parser-readable but
  `solver_success_blocked`, gated on RFC 0040 production volume-mesh
  evidence. The workflow 0050 implementation burn-down queue item 4
  (`striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md:243-247`)
  names this same gate explicitly: "Do not enable real `succeeded`
  execution until mesh evidence gates pass." Option A is the smallest
  decision that creates a credible path to satisfying that gate without
  bypassing it.
- RFC 0040 §"Open Questions"
  (`docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md:246-260`)
  asks precisely "Which volume mesher, if any, should be selected for
  the first production implementation after fixture diagnostics prove
  the contract?" Option A answers that question while still treating
  the first profile as evidence under gates rather than as production
  readiness authority.
- RFC 0041 §"Mesh Readiness"
  (`docs/rfcs/0041-real-cfd-adapter-successor.md:173-185`) states that
  `watertight_solid_resistance_v1` may be accepted only when the package
  satisfies the evidence-bound `cfd_ready` handoff. Option A is the
  natural way to make a non-fixture instance of that handoff exist.

### External Evidence Verification

The packet's external citations are consistent with my background
knowledge of the OpenFOAM, Gmsh, and cfMesh projects, and the URLs and
files cited are the canonical maintained primary sources:

- The OpenFOAM.com v2512 DTCHull `Allrun` cited in the packet does run
  `surfaceFeatureExtract`, `blockMesh`, repeated `refineMesh`,
  `snappyHexMesh`, `setFields`, then `interFoam`, and the
  `controlDict` configures a `forces` function object on the `hull`
  patch — which is the exact parser focus the existing OpenFOAM adapter
  already targets at `OPENFOAM_FORCE_DAT_OUTPUT =
  "postProcessing/forces/0/force.dat"`.
- The OpenFOAM Foundation v13 `snappyHexMesh` reference and `checkMesh`
  source align with the quality controls Option A enumerates
  (`maxNonOrtho`, `maxBoundarySkewness`, `maxInternalSkewness`,
  `maxConcave`, `minVol`, `minDeterminant`, `minFaceWeight`,
  `minVolRatio`). These are OpenFOAM-style solver-input quality
  thresholds, not claims about hydrodynamic accuracy.
- The Gmsh and `gmshToFoam` references are consistent with Option C
  being technically viable but adding a conversion layer between Gmsh
  `.msh` and OpenFOAM polyMesh that is not needed for the
  already-selected solver.
- The cfMesh FAQ does describe open-source cfMesh as no longer
  maintained and provided as-is; CF-MESH+ requires a license manager.
  These are real licensing/maintenance gates against Option D as a
  default.

## Why Rejected Alternatives Lose

### Option B (Continue fixture-only diagnostics) - exhausted as primary track

Option B has shipped already. Workflow 0050's D003 decision asked for the
RFC 0040 readiness report, and workflow 0051's `implement_readiness_report`
and `implement_openfoam_skeleton` lanes landed the readiness report,
fixture handoff evidence, and OpenFOAM adapter skeleton
(`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:43-49`).
The remaining blocker is no longer "do we have fixture handoff" but "the
OpenFOAM adapter skeleton returns `solver_success_blocked` until
OpenFOAM-readable volume-mesh evidence exists"
(`kayakgen/eval/cfd/jobs.py:1146-1175`). Continuing fixture-only
hardening as the primary track will not produce that evidence and will
not answer the OpenFOAM patch-naming, background-domain, layer addition,
`checkMesh` quality, or polyMesh artifact-format questions that the
adapter needs. Fixture work continues as required CI inside Option A
(see implementation gate 8 below), but it is no longer the next
standalone workflow.

### Option C (Gmsh first, then convert) - close second, wrong order

Option C is technically viable. Gmsh is current (4.15.2, 2026-03-24,
cross-platform, `pip`-installable, GPL with linking exception), has
mature CAD/discrete-entity workflows including STL with
reparametrization, exposes a Python API that maps cleanly onto
kayakgen's Python implementation, and `gmshToFoam` does exist as a
conversion path. It loses against Option A as the immediate next slice
on three concrete grounds:

1. **Conversion boundary against the already-selected solver.** D004
   selected OpenFOAM.com v2512 `interFoam`. The official DTCHull
   tutorial path is OpenFOAM-native: STL into `triSurface`, then
   `surfaceFeatureExtract` and `snappyHexMesh` against a `blockMesh`
   background. Choosing Gmsh first adds a `.msh` version gate, a
   physical-group-to-OpenFOAM-patch translation gate, a
   boundary-orientation gate, and `gmshToFoam` provenance gates before
   the solver sees a native mesh. None of those gates exists in the
   current evidence contract.
2. **Boundary-layer and wall-adjacent evidence diverges from
   `checkMesh`.** OpenFOAM-native layer addition records its own
   acceptance through `snappyHexMesh` layer-quality logs and
   `checkMesh -allTopology -allGeometry`. Going through Gmsh would
   require a separate boundary-layer evidence model and a separate
   acceptance gate against `checkMesh`, which is rework when the
   already-selected solver natively records it.
3. **Tutorial pattern reuse is lower in Option C.** The packet's
   primary win for Option A is reusing the maintained DTCHull `Allrun`
   shape directly. Option C breaks that shape, which is the worst-case
   place to add a conversion layer in the first production-evidence
   slice.

Option C remains the recommended fallback only if `snappyHexMesh` cannot
produce repeatable acceptable meshes from `generated_hull_plus_deck_
closed_body_v1`, or if a future solver decision selects a solver-neutral
mesher.

### Option D (cfMesh / CF-MESH+ / another mesher) - blocked on maintenance and licensing

cfMesh is OpenFOAM-adjacent and was designed for automatic OpenFOAM
polyhedral/tetrahedral/Cartesian meshing with boundary-layer support.
CF-MESH+ has console operation and stronger commercial support. The two
disqualifying facts from the cfMesh vendor FAQ are operational rather
than technical: the open-source cfMesh product is described by its
vendor as no longer maintained and provided as-is, and CF-MESH+
introduces license-manager and commercial/trial-license gates that do
not fit required CI or open-repo reproducibility. Either path adds
operational obligations (maintenance ownership for cfMesh, license
management and budget for CF-MESH+) without being the documented path of
the selected OpenFOAM DTCHull-style solver target. Treat Option D as
later comparative research only if OpenFOAM-native meshing fails the
quality or repeatability gates.

## Implementation Gates To Carry Into The Next Workflow

If Option A is accepted by panel integration, the successor implementation
workflow must enforce, at minimum:

1. **New profile name is additive.** Introduce
   `openfoam-v2512-snappyhexmesh-watertight-v1` as a new
   `VolumeMeshDiagnostic.profile_name` value alongside the existing
   `watertight_solid_resistance_v1` solver profile. Do not silently
   widen the `WATERTIGHT_SOLID_PROFILE_NAME` constant to a different
   value; the OpenFOAM-readable mesher profile is the volume-mesh
   profile, and the OpenFOAM `interFoam` solver profile remains
   `watertight_solid_resistance_v1` (`cfd/jobs.py:514`). The
   solver-mesh contract stays the existing one; the new profile name
   distinguishes mesher provenance.
2. **Mesh-package handoff binds to mesher profile.** The
   `MeshPackageManifest.readiness_authority` ==
   `"verified_watertight_volume_mesh_evidence"` and matching dispatch
   gates (`mesh_package.py`) must be the only path to `cfd_ready` for an
   OpenFOAM-rendered package. Hand-edited readiness strings, synthetic
   bodies, fixture-mesher names emitted from a non-fixture path, stale
   hashes, cross-body evidence, and forbidden-path or `..` refs must
   reject before any solver command runs (already the contract — keep
   it enforced).
3. **`VolumeMeshDiagnostic.mesher_name` / `mesher_version` are
   OpenFOAM-real.** A non-fixture `snappyHexMesh`-produced diagnostic
   must record `mesher_name` referring to OpenFOAM (e.g.,
   `"OpenFOAM.com snappyHexMesh"`) and `mesher_version` referring to a
   real OpenFOAM v2512 build string. A Foundation/OpenFOAM.org version
   must not silently satisfy a `.com v2512` profile; required
   `foamVersion`-style probe metadata must be recorded in
   `deterministic_inputs` and rejected on mismatch.
4. **`checkMesh` is a required evidence gate, not an optional log.**
   `checkMesh -allTopology -allGeometry -meshQuality` must run (or be
   recorded as unavailable when the installed-OpenFOAM environment is
   off) and its parsed result must drive
   `invalid_cell_count`/`inverted_cell_count`/`zero_volume_cell_count`/
   `nonfinite_cell_count` and the `readiness.reasons` list. A failed
   `checkMesh` topology, geometry, or `meshQualityDict` check is a
   hard blocker.
5. **Patch and marker metadata are first-class.**
   `VolumeMeshDiagnostic.boundary_patches`,
   `.boundary_patch_names`, and `.boundary_markers` must record the
   hull/wetted-body patch under
   `name="generated_hull_plus_deck"`/`role="wetted_body"`, plus accepted
   farfield/inlet/outlet/free-surface/symmetry patches as the
   case-template version defines them. Missing or renamed required
   patches block readiness. The `_cfd_ready_requires_clean_fixture_
   metrics` validator (`volume_mesh.py:151-196`) already enforces this
   consistency; it must keep firing for the new profile.
6. **Deterministic case rendering and digests.** Render
   `blockMeshDict`, `snappyHexMeshDict`, `surfaceFeatureExtractDict`,
   `meshQualityDict`, the body tri-surface STL, and command argv from
   the closed-body diagnostic; record SHA-256 digests under
   `deterministic_inputs` and `mesher_config_digest`. Profile-specific
   quality starter thresholds (e.g., `maxNonOrtho <= 65`,
   `maxBoundarySkewness <= 20`, `maxInternalSkewness <= 4`,
   `maxConcave <= 80`, `minVol > 0`, `minDeterminant >= 0.001`,
   `minFaceWeight >= 0.05`, `minVolRatio >= 0.01`, no failed layer
   addition on hull patch when layers enabled) must live in
   `meshQualityDict` content, not in prose. Any relaxation must be
   recorded explicitly in the diagnostic.
7. **Installed-OpenFOAM smoke is opt-in only.** Required CI must use
   fake commands and fixture files. Installed `surfaceFeatureExtract`/
   `blockMesh`/`snappyHexMesh`/`checkMesh` is allowed only behind an
   explicit environment flag and only as evidence input for the
   diagnostic; it must not become a required test.
8. **Fixture path remains the deterministic CI surface.**
   `fixture_volume_mesh_diagnostic` and its
   `FIXTURE_VOLUME_MESHER_NAME = "kayakgen-fixture-volume-mesher"`
   continue to exist. Negative tests must cover: fixture diagnostic
   emitted with new profile name (must reject), OpenFOAM mesher name
   with stale hashes (must reject), missing required patch (must
   reject), missing `checkMesh` output (must reject), `checkMesh`
   reported failed topology (must reject), and unrelated body_ref
   (must reject).
9. **OpenFOAM upstream is not vendored.** OpenFOAM-v2512 `Allrun`,
   `blockMeshDict`, `snappyHexMeshDict`, `surfaceFeatureExtractDict`,
   and `meshQualityDict` text must not be vendored verbatim into the
   repo without a license review. The `case-template` should render
   project-owned dicts that follow the maintained DTCHull pattern,
   not copy upstream files.
10. **Boundary-domain background and `locationInMesh` are
    project-owned values.** The `blockMeshDict` background bounding
    box and `snappyHexMeshDict locationInMesh` must derive
    deterministically from the closed-body bounding box and hull
    parameters, and must be recorded as digests under
    `deterministic_inputs`. Hand-edited or unrecorded background
    geometry must reject.

## No-Claims Language That Must Remain In Force

Option A authorizes mesher provenance evidence under explicit gates. It
does not authorize new physics, validated CFD, calibrated resistance,
hosted operation, or design fitness. All no-claims wording from
workflows 0050 and 0051 must remain literally unchanged:

- **`cfd_ready` remains solver-input readiness only.** Ordinary
  generated packages stay below `cfd_ready`. The new
  `openfoam-v2512-snappyhexmesh-watertight-v1` profile binds to
  `verified_watertight_volume_mesh_evidence` authority through the
  existing `MeshPackageManifest` path; it is not a free pass for
  display surfaces or synthetic bodies. The boundary at
  `kayakgen/eval/mesh_package.py:520-581` (readiness_authority
  promotion) stays the only path.
- **No real OpenFOAM `succeeded` from this decision alone.**
  `error_kind="solver_success_blocked"` at
  `kayakgen/eval/cfd/jobs.py:1166` stays in force until a separate
  successor workflow accepts the first real `snappyHexMesh`-rendered
  package and demonstrates round-trip evidence into the OpenFOAM
  adapter. Option A creates the evidence path; it does not declare a
  solver-success path.
- **All real solver output remains `raw_unvalidated`.** Calibrated
  resistance (D006), validated CFD, calibrated comparative ranking,
  and final design fitness remain blocked. The
  `OPENFOAM_SUCCESS_BLOCKED_WARNING` text and the
  `claim_state="raw_unvalidated"` posture on every parsed `force.dat`
  output must remain in force.
- **`snappyHexMesh` is not a hidden readiness authority.** The
  integrator's "Shared Risks Preserved" item
  (`striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md:194-196`)
  explicitly warns: "OpenFOAM template work must not vendor upstream
  files verbatim without license review and must not use
  `snappyHexMesh` as hidden readiness authority." Option A keeps
  `snappyHexMesh` as evidence input; kayakgen's diagnostic gates
  remain the authority.
- **Quality thresholds are profile-specific, not universal.** The
  `maxNonOrtho`/skewness/concavity/`minVol`/`minDeterminant`/
  `minFaceWeight`/`minVolRatio` values are OpenFOAM-style solver-input
  quality starters scoped to
  `openfoam-v2512-snappyhexmesh-watertight-v1`. They are not project-
  wide kayak-gen quality thresholds, and they are not statements about
  hydrodynamic accuracy.
- **No CFD calibration, hosting, browser-side meshing, or high-angle
  stability claims.** D005/D006 resistance no-promotion, D007 high-
  angle stability fixed-trim/sealed-deck warnings, D008 hosted-demo
  operational gates, and the standing
  `SourceUse` literal set in `kayakgen/eval/calibration.py:13-19`
  remain literally unchanged.
- **No browser-side or hosted meshing.** The new mesher harness runs
  only locally and only as installed-solver smoke when the explicit
  environment flag is on. Required CI uses fake commands and fixture
  files. Trame/web surfaces remain unchanged.

## Risks And Unknowns Carried Forward

- **`snappyHexMesh` repeatability across the generated-body matrix is
  not yet proven.** The first slice should target the default touring
  and elite-surfski preset hulls and the exact-plumb / mixed-rake
  cases enumerated in RFC 0040 §"Generated-body hardening". If
  `snappyHexMesh` cannot produce a `checkMesh`-clean polyMesh across
  that matrix, the slice records the failure with structured
  blocker reasons under `volume_mesh.py`'s `VolumeMeshReasonCode` enum,
  not by relaxing thresholds. Option C (Gmsh) becomes the documented
  fallback for any matrix entry that `snappyHexMesh` cannot satisfy.
- **OpenFOAM version drift.** OpenFOAM.com may release v2606 (or
  later) before the slice lands. The `required_solver_version` and
  `mesher_version` records must keep the v2512 pin until a separate
  decision accepts a successor release. A different OpenFOAM
  Foundation lineage must not silently satisfy the `.com v2512`
  profile.
- **`checkMesh` parser surface area.** The first slice's `checkMesh`
  parser may not cover every quality metric OpenFOAM emits. The
  contract should treat unknown-but-non-failing lines as warnings,
  not as readiness, and pin a fixture covering `checkMesh` output
  layout.
- **DTCHull `Allrun` license / attribution.** Even when not vendored,
  the DTCHull-pattern reuse should be documented in the
  case-template version notes so future maintainers know which
  upstream files inspired the pattern. The "OpenFOAM template work
  must not vendor upstream files verbatim without license review"
  risk from workflow 0050 stays in force.
- **Disk/runtime budget for installed-solver smoke.** Even behind an
  environment flag, an installed `snappyHexMesh`+`checkMesh` run on a
  generated hull can produce hundreds of MB of polyMesh artifacts and
  multi-minute runtime. The smoke profile must bound retained
  artifacts (e.g., compress polyMesh, retain only digests and a small
  cell-count slice) and bound runtime via the existing
  `timeout_seconds`/`log_limit_bytes` shape (`cfd/jobs.py:512-513`).
- **Successor adapter unblocking.** Option A creates the evidence
  path the OpenFOAM adapter currently blocks on, but enabling a real
  `succeeded` record is a separate later decision once the first
  `snappyHexMesh`-rendered package round-trips through prepare/run/
  collect end-to-end. This decision does not promise that unblocking;
  it removes the missing evidence prerequisite.

## Confidence

**High.**

Rationale: Option A is the smallest additive change that closes the
specific blocker workflow 0051 left open: the OpenFOAM adapter at
`kayakgen/eval/cfd/jobs.py:1146-1175` returns `solver_success_blocked`
exclusively because no OpenFOAM-readable volume-mesh evidence exists;
the existing `VolumeMeshDiagnostic` shape
(`kayakgen/eval/volume_mesh.py:107-196`) already supports every gate
Option A requires; the existing mesh-package authority
(`kayakgen/eval/mesh_package.py:520-581`) already binds `cfd_ready` to
`verified_watertight_volume_mesh_evidence`; and the OpenFOAM-native
DTCHull pattern is the documented path for the solver D004 already
selected. The packet's external citations are current and consistent,
Option C/D losses are operational and well-documented, and the
no-claims surface area is unaffected because no new solver-success,
calibration, hosting, high-angle stability, or design-fitness path is
authorized. The only judgment call is the A-vs-C sequencing, and
Option A's "OpenFOAM-native first, Gmsh as documented fallback"
ordering is the lower-rework path against the already-selected
solver.
