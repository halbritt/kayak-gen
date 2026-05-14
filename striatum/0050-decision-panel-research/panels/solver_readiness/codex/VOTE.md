---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_6907c25df15c443a9c8bcd0d56419aaf
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_solver_readiness_codex
lease: lease_c2360eee16044a60a353115a57d68b69

# Vote - Solver Readiness Evidence Contract

Vote: Option A - Readiness Report First.

## Decision Sentence

Adopt a closed-volume solver-readiness report as the next solver-readiness
contract: it explains hull/body/package/profile gate status, evidence refs,
hashes, blockers, and warnings without changing package readiness; production
`cfd_ready` for `watertight_solid_resistance_v1` remains blocked unless the
same package has verified generated-body diagnostics, passed self-intersection
evidence, matching volume-mesh diagnostics, relative in-package artifacts,
SHA-256 checksums, and solver-profile gates, and every solver result remains
`raw_unvalidated` until separate validation or calibration evidence lands.

## Evidence

The local product boundary already requires this conservative order. The PRD
says open hull/deck STLs are inspection surfaces, only the generated closed-body
path may report `closed_volume` after diagnostics, ordinary generated packages
remain open-surface candidates, the only current `cfd_ready` path is narrow and
fixture-backed, and current CFD support is local job/profile/run plumbing with
no OpenFOAM, SU2, Docker, hosted-worker, or real adapter success path
(`docs/PRD.md:29-42`). The user guide repeats the same user-facing limits:
`mesh-check` does not promote readiness, the `watertight-solid` package profile
can report `cfd_ready` only with matching fixture volume-mesh evidence, and all
CFD run records are raw and unvalidated (`docs/USER_GUIDE.md:168-225`,
`:246-286`, `:421-432`).

The roadmap makes Option A the direct next slice. Its no-claims rules limit
mesh packages to open-surface candidates unless matching body diagnostics,
self-intersection evidence, volume-mesh evidence, hashes, artifacts, and solver
profile gates all pass (`docs/ROADMAP.md:33-59`). Its geometry-evidence track
explicitly says RFC 0040 must be staged as readiness report, generated-body
hardening, volume-mesh diagnostic contract, package gates, and dispatch gates,
not as one "make generated packages `cfd_ready`" feature
(`docs/ROADMAP.md:68`, `:126-143`). Workflow 0049 accepted that roadmap as
complete and evidence-bound, including the same mesh-readiness and raw-output
claims (`striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md`).

The RFC spine supports the same contract. RFC 0010 permits `cfd_ready` only
with a named `MeshSolverProfile` and keeps current open hull/deck surfaces
below watertight readiness (`docs/rfcs/0010-cfd-ready-mesh-contract.md:65-80`,
`:125-131`). RFC 0023 says a generated closed body with passing
self-intersection evidence but no volume-mesh diagnostic remains below
`cfd_ready`, and a volume-mesh diagnostic can promote only the matching body
and matching profile (`docs/rfcs/0023-watertight-volume-mesh-handoff.md:49-80`,
`:131-141`). RFC 0040 is the clearest decision source: the readiness report is
an explanation layer over diagnostics and manifests, generated-body hardening
does not itself create solver readiness, volume-mesh diagnostics stay separate,
and dispatch gates must compare hashes, profiles, artifact checksums, and
blocker reasons before any real adapter runs
(`docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md:89-143`,
`:172-215`, `:218-241`, `:263-277`). RFC 0041 then depends on that gate rather
than redefining mesh truth, and keeps every real-solver output
`raw_unvalidated` (`docs/rfcs/0041-real-cfd-adapter-successor.md:45-66`,
`:175-184`, `:205-234`).

The current implementation already proves useful pieces but not production
meshing. `kayakgen/eval/closed_volume.py` never promotes body diagnostics to
`cfd_ready`; `kayakgen/eval/volume_mesh.py` records fixture volume-mesh
diagnostics with body refs, diagnostic hashes, tolerance hash, artifact refs,
SHA-256 checksums, quality counts, readiness reasons, and warnings; and
`kayakgen/eval/mesh_package.py` promotes `cfd_ready` only when
`include_fixture_volume_mesh=True`. Dispatch re-hashes relative refs, rejects
absolute or parent-traversal paths, checks body/hull/profile/tolerance/artifact
matches, and rejects missing, stale, synthetic, cross-body, cross-hull,
failed-self-intersection, body-surface-mismatch, and below-readiness evidence
before dispatch (`kayakgen/eval/cfd/jobs.py:840-1186`). Workflow 0034 accepted
that fixture-backed path as evidence-derived and profile-scoped, while noting
missing direct tests for several rejection codes and a permissive hash-alias
lookup that should be narrowed or documented
(`striatum/0034-watertight-volume-mesh-handoff/final/FINAL_REVIEW.md:1-62`,
`:149-159`).

The solver-readiness research packet correctly converts that evidence into a
decision posture: choose Option A as the default, then treat Option B as the
immediate hardening follow-up before any production promotion
(`striatum/0050-decision-panel-research/research/solver_readiness/RESEARCH.md`).

My independent external check supports profile-scoped thresholds rather than a
universal kayak-gen threshold table. OpenFOAM's `snappyHexMesh` documentation
lists solver/mesher-specific quality controls such as non-orthogonality,
boundary/internal skewness, concavity, minimum volume, determinant, face weight,
volume ratio, and a relaxed-controls block, and `checkMesh` can check
user-defined `meshQualityDict` criteria:
https://doc.cfd.direct/openfoam/user-guide-v11/snappyhexmesh and
https://cpp.openfoam.org/v12/applications_2utilities_2mesh_2manipulation_2checkMesh_2checkMesh_8C.html.
SU2 makes boundary markers/tags first-class and uses them for boundary
conditions, including when importing CGNS boundary names:
https://su2code.github.io/docs_v7/Mesh-File/. Gmsh exposes quality measures
such as Jacobian determinant, IGE, and ICN, while PyVista/VTK exposes many
measure and cell-type-specific acceptable/normal/full ranges:
https://gmsh.info/doc/texinfo/ and
https://docs.pyvista.org/api/utilities/_autosummary/pyvista.cell_quality_info.html.
Python's standard `hashlib` provides portable SHA-256 hex digests suitable for
file and canonical-JSON evidence hashes:
https://docs.python.org/3/library/hashlib.html. Together, these sources support
recording exact profile criteria and artifact hashes instead of claiming one
generic "CFD-ready" truth.

## Why Rejected Alternatives Lose

Option B - schema hardening with fixture evidence only - should follow
immediately, but it loses as the first decision because users and future
implementors still need a readiness report that explains why current bodies and
packages are blocked. Hardening the fixture schema without the explanatory read
model would leave CLI/web/docs surfaces to keep inferring the same blocker
story in multiple places.

Option C - choose a production mesher or solver threshold profile now - loses
because no solver-selection decision has landed. OpenFOAM, SU2, Gmsh, and
VTK/PyVista expose different mesh concepts, quality metrics, boundary semantics,
and threshold mechanisms. Selecting hard limits now would import a hidden RFC
0041 solver decision and create false precision before the project has chosen
an adapter, case template, boundary-condition model, or validation path.

Option D - add a separate surface-only solver profile - may become valid for a
specific future adapter, but it is not a watertight solver-readiness decision.
It must not reuse `watertight_solid_resistance_v1`, must document why the
surface-only mode is physically and operationally coherent, and must preserve
raw/unvalidated result semantics. That is a separate solver-mode decision, not
the evidence contract for closed-volume readiness.

Promoting generated closed bodies directly to `cfd_ready` loses outright.
Generated-body diagnostics are source-geometry evidence, not volume-mesh
handoff evidence. A body can be closed, manifold, positive-volume, and
self-intersection-passed while still lacking the volume cells, boundary patch
roles, solver profile, artifact checksums, and quality diagnostics a solver
adapter needs.

## Implementation Gates

Before any package or dispatch promotion changes:

1. Add the RFC 0040 readiness report as an explanatory read model over existing
   diagnostics and manifests, with explicit gate status, blockers, warnings,
   evidence refs, evidence hashes, and input semantics.
2. Record a structured blocker/warning code list before CLI, web, or docs copy
   expands; structured records should carry at least code, severity, message,
   and evidence reference while still preserving readable text.
3. Harden generated-body diagnostics across default touring and surfski
   presets, exact plumb bow/stern, mixed rake, `beam_wl_m != beam_oa_m`,
   representative draft, `Cp`, `Cm`, and unsupported or invalid cases with
   structured diagnostics.
4. Formalize the volume-mesh diagnostic contract with body refs, diagnostic
   hashes, tolerance hashes, mesher metadata, deterministic inputs, structured
   boundary patch or marker metadata, quality summaries, artifact refs, media
   types, SHA-256 checksums, warnings, and blockers.
5. Add direct negative tests for `cross_body`, `cross_hull`,
   `cross_tolerance`, `evidence_profile_mismatch`, `malformed_diagnostic`,
   `body_surface_mismatch`, and `artifact_checksum_mismatch`, and decide
   whether `_expected_evidence_hash` aliases are compatibility surface or
   should be narrowed to canonical keys.
6. Keep fixture `cfd_ready` fixture-labeled and profile-scoped only; do not
   describe it as production meshing, real solver execution, calibrated drag,
   final prediction, design fitness, or proof of a generated package's ordinary
   readiness.
7. Require dispatch to independently re-verify refs, hashes, body/hull/profile
   identity, tolerance identity, artifact checksums, and no-blocker readiness
   before any adapter command runs.

No-claims language that must remain in force: open hull/deck STLs and ordinary
generated packages are inspection or open-surface candidate artifacts;
generated closed bodies are evaluation evidence until matching volume-mesh
evidence exists; `cfd_ready` means profile-scoped solver input readiness only,
not solver success; solver outputs are `raw_unvalidated`; fixture evidence is
fixture-only; and no current path provides calibrated CFD, final resistance
prediction, final design fitness, production volume meshing, or high-angle
stability claims.

Confidence: high.
