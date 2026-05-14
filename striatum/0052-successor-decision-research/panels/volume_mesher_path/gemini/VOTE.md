---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-009
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_c19292d510e346738c5601d5de85f3f6
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_volume_mesher_path_gemini
lease: lease_ead6f46dbb194192912367fa9e191311
date: 2026-05-14

# Panel Vote - Volume-Mesh Production Path (Gemini)

## Vote

**Vote: Option A - OpenFOAM-v2512 `snappyHexMesh` evidence harness.**

## Decision Sentence

Select OpenFOAM.com OpenFOAM-v2512 `snappyHexMesh` as the first production
volume-mesher path for RFC 0040. Implement this path strictly as a deterministic
evidence harness over `generated_hull_plus_deck_closed_body_v1` that requires
`checkMesh` outputs, patch metadata, and artifact-hash gates before solver dispatch.
Do not promote ordinary generated packages to `cfd_ready` and do not enable real
OpenFOAM `succeeded` execution records until verifiable OpenFOAM-readable volume-mesh
evidence exists and passes all gates.

## Evidence

The recommendation aligns completely with the research packet and local constraints.
Decision D003 instituted the readiness-report-first policy, explicitly restricting
generated packages below `watertight_solid_resistance_v1` without comprehensive
diagnostic evidence. Decision D004 selected OpenFOAM.com OpenFOAM-v2512 `interFoam`
as the real solver target, enforcing a gate that blocks actual `succeeded` paths
until OpenFOAM-readable volume-mesh evidence exists.

Workflow 0051 implemented the readiness report and OpenFOAM adapter skeleton,
but the skeleton still explicitly blocks with `solver_success_blocked` because
no verifiable mesh evidence is provided. Option A directly unblocks this
adapter without loosening readiness restrictions.

Externally, the official OpenFOAM-v2512 DTCHull tutorial employs `snappyHexMesh`
directly against a `triSurface` background, providing an exact template for the
required `hull` forces patch workflow without translation boundary layers. OpenFOAM's
native `checkMesh -allTopology -allGeometry -meshQuality` provides the authoritative
evidence required to support kayakgen's `VolumeMeshDiagnostic` validations.

## Why Rejected Alternatives Lose

- **Option B (Continue Fixture-Only Diagnostics):** Fixture-only diagnostics
  have already been successfully completed in Workflow 0051. The current remaining
  blocker is specifically the lack of OpenFOAM-readable mesh evidence. Continued
  fixture-only work will not provide the required `.polyMesh` diagnostics or patch
  metadata needed to advance real solver integration.
- **Option C (Gmsh First, Then Convert):** Although Gmsh is a mature, capable mesher
  with a Python API, adding an unnecessary format conversion boundary (`gmshToFoam`)
  to an already-selected OpenFOAM solver degrades determinism. OpenFOAM-native layer
  and topology validation (`checkMesh`) cannot fully cover a converted mesh without
  extra adaptation. This path should only serve as a fallback if `snappyHexMesh`
  fails to produce consistent, acceptable quality over the generated-body matrix.
- **Option D (cfMesh / CF-MESH+ Or Another Mesher):** Open-source cfMesh has a poor
  maintenance posture, being provided strictly as-is. CF-MESH+ carries commercial
  licensing constraints that compromise the open CI/CD testing baseline required
  by kayakgen.

## Implementation Gates And No-Claims Language

1. Introduce an explicit profile name (e.g., `openfoam-v2512-snappyhexmesh-watertight-v1`).
2. Accept only closed-body inputs matching `generated_hull_plus_deck_closed_body_v1`
   with verifiable and consistent source body hashes.
3. Validate OpenFOAM version probes explicitly for OpenFOAM.com v2512; silently
   passing Foundation/OpenFOAM.org variants or other unselected releases must
   be rejected.
4. Render and preserve SHA-256 digests for deterministic case definitions
   (`blockMeshDict`, `snappyHexMeshDict`, `surfaceFeatureExtractDict`,
   `meshQualityDict`), initial `triSurface` artifacts, background bounds, and
   command environment settings.
5. Emphasize `checkMesh -allTopology -allGeometry -meshQuality` as authoritative
   evidence rather than a discretionary log. Failures on topology, geometry, or
   defined `meshQualityDict` checks must register as hard blockers.
6. Enforce rigorous open boundary patch checks. The target body patch must
   map to `hull` or `generated_hull_plus_deck` under the `wetted_body` role,
   consistent with the defined case template.
7. Package dispatch and promotion to `cfd_ready` remains gated strictly behind
   validated `verified_watertight_volume_mesh_evidence` without exceptions for
   malformed or hand-edited inputs.
8. Retain all no-claims boundaries: successful mesh synthesis, dispatch, and solver
   execution remain strictly `raw_unvalidated`. They do not claim calibrated CFD
   physics, final resistance predictions, or any degree of seaworthiness.

Confidence: High
