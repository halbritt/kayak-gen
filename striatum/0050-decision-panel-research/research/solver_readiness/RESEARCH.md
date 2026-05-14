---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-008
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14

# Solver Readiness Evidence Research

## Decision Question

What evidence contract should kayak-gen require before a generated kayak body,
volume mesh, mesh package, or dispatch profile may be promoted to solver-input
readiness, including diagnostics, thresholds, hashes, blocker/warning
semantics, and `cfd_ready` rules?

## Local Project Constraints

The local no-claims boundary is strict. The PRD says open hull/deck STLs are
inspection surfaces; only the generated closed-body path may report
`closed_volume` after diagnostics, and only a narrow fixture-backed
volume-mesh evidence path can report `cfd_ready` (`docs/PRD.md`). Current CFD
support is job/profile/run plumbing with unavailable or fixture states, not
OpenFOAM, SU2, Docker, hosted workers, or any real CFD adapter.

The roadmap keeps ordinary generated packages below watertight-required solver
acceptance unless matching body diagnostics, self-intersection evidence,
volume-mesh evidence, hashes, artifacts, and solver-profile gates all pass
(`docs/ROADMAP.md`). It also says RFC 0040 must be staged as readiness report,
generated-body hardening, volume-mesh diagnostic contract, package gates, and
dispatch gates, not as one "make generated packages `cfd_ready`" feature.

RFC 0010 defines the existing mesh-readiness ladder: `display`,
`stl_surface`, `cfd_surface_candidate`, and `cfd_ready`; `cfd_ready` requires a
named `MeshSolverProfile`, while current open hull/deck output must not be
silently promoted. RFC 0015 makes solver dispatch depend on mesh package
readiness and keeps every run record raw and unvalidated. RFCs 0016, 0021, and
0022 define closed-volume diagnostics, self-intersection status, and generated
hull-plus-deck closed-body construction, but all three keep CFD readiness out
of scope. RFC 0023 defines the first handoff rule: generated body diagnostics
alone are insufficient; `watertight_solid_resistance_v1` needs matching
volume-mesh evidence. RFC 0040 is the current roadmap that turns those rules
into an evidence ladder and structured readiness report. RFC 0041 says the
future real CFD adapter must consume this readiness gate rather than creating
its own geometry truth.

The current implementation already has useful local evidence:

- `kayakgen/eval/closed_volume.py` records generated-body policy, body-level
  boundary/nonmanifold counts, degenerate/nonfinite/invalid counts, signed
  volume, self-intersection status, tolerances, warnings, and
  `cfd_ready: false`.
- `kayakgen/eval/volume_mesh.py` records fixture volume-mesh diagnostics:
  body ref, source hull hash, diagnostic hashes, tolerance hash, mesher
  metadata, deterministic inputs, artifact refs and SHA-256 checksums, cell
  and boundary counts, invalid/inverted/zero/nonfinite cell counts, optional
  quality summaries, body-surface-match status, structured readiness reasons,
  and warnings.
- `kayakgen/eval/mesh_package.py` extends manifests with body refs,
  diagnostic refs, volume-mesh refs, evidence hashes, and
  `readiness_authority`; it promotes fixture `cfd_ready` only when
  `include_fixture_volume_mesh=True`.
- `kayakgen/eval/cfd/jobs.py` re-hashes referenced evidence, rejects absolute
  or parent-traversal refs, checks body/hull/profile/tolerance/hash/artifact
  matches, and rejects synthetic, stale, malformed, cross-body, cross-hull,
  failed self-intersection, body-surface mismatch, and below-readiness
  evidence before dispatch.
- `striatum/0034-watertight-volume-mesh-handoff/final/FINAL_REVIEW.md`
  accepted the current fixture-backed path as evidence-derived and
  profile-scoped, while noting missing direct tests for several rejection
  codes and that production meshing remains deferred.

## External Evidence

External sources were accessed on 2026-05-14.

| Source | Claim supported |
| --- | --- |
| [OpenFOAM mesh quality controls](https://doc.openfoam.com/2312/tools/pre-processing/mesh/generation/snappyhexmesh/meshquality/) | OpenFOAM exposes solver/mesher-specific quality controls such as non-orthogonality, boundary/internal skewness, concavity, minimum volume, determinant, face weight, and volume ratio, with concrete example limits and a `relaxed` dictionary. This supports profile-scoped thresholds rather than universal kayak-gen thresholds. |
| [OpenFOAM `checkMesh` manual](https://www.openfoam.com/documentation/guides/latest/man/checkMesh.html) | `checkMesh` checks mesh validity and can read user-defined mesh quality criteria from `system/meshQualityDict`. This supports treating external solver/mesher checks as explicit diagnostic artifacts with the exact criteria recorded. |
| [OpenFOAM boundary documentation](https://www.openfoam.com/documentation/user-guide/4-mesh-generation-and-conversion/4.2-boundaries) | OpenFOAM boundary handling is patch-based, with patch type and face counts in `constant/polyMesh/boundary`. This supports recording boundary patch names, roles, and counts in volume-mesh diagnostics. |
| [SU2 mesh file documentation](https://su2code.github.io/docs_v7/Mesh-File/) | SU2 uses mesh markers/tags for boundaries and uses CGNS boundary names as marker tags when importing CGNS. This supports making boundary marker names and roles first-class in any solver-readiness schema. |
| [Gmsh documentation](https://gmsh.info/doc/texinfo/) | Gmsh exposes element-quality measures including determinant, scaled Jacobian, condition-related measures, edge lengths, and volume. This supports recording mesher-native quality summaries and not assuming every mesher emits the same fields. |
| [PyVista cell quality documentation](https://docs.pyvista.org/api/utilities/_autosummary/pyvista.cell_quality_info.html) | PyVista/VTK quality metadata varies by cell type and measure, and includes acceptable, normal, full, and unit-cell ranges. This supports profile-specific warning/blocker policy per metric and cell type. |
| [Python `hashlib` documentation](https://docs.python.org/3/library/hashlib.html) | Python provides SHA-256 and `hexdigest()` for portable hex digest exchange. This supports continuing to use SHA-256 for file and canonical-JSON evidence hashes, with the algorithm recorded explicitly. |

## Evidence Model Findings

### Generated-Body Diagnostics

The generated-body diagnostic is necessary evidence, not solver input by
itself. The decision should keep `generated_hull_plus_deck_closed_body_v1` as
the source geometry record and require all of these before it can feed a
volume-mesh diagnostic:

- body type is generated kayak body, not synthetic fixture;
- source hull hash matches the package hull hash;
- closure policy records cap, join, waterline, normal-orientation, and
  tolerance settings;
- raw and welded body-level boundary edges are zero;
- raw and welded body-level nonmanifold edges are zero;
- degenerate, nonfinite, and invalid geometry counts are zero;
- signed volume is positive under the outward-normal convention;
- self-intersection status is `passed`, not `not_checked`, `failed`, or
  `inconclusive`;
- diagnostics include the exact tolerance set used.

Generated-body hardening should be treated as a prerequisite evidence workflow,
not as promotion. The matrix in RFC 0040 is the right minimum: default hulls,
surfski/touring presets, exact plumb bow/stern, mixed rake, `beam_wl_m !=
beam_oa_m`, representative draft, `Cp`, and `Cm`, plus unsupported or invalid
cases that return structured diagnostics.

### Volume-Mesh Diagnostic Schema

The current `VolumeMeshDiagnostic` is a good base but should be made explicit
as a profile-scoped schema before any production mesher is selected. Minimum
fields:

- identity: schema version, profile name, volume-mesh profile version,
  `body_ref`, body type, source hull hash;
- provenance: closed-volume diagnostic hash, self-intersection diagnostic
  hash, tolerance hash, mesher name/version, command/config digest,
  deterministic inputs;
- artifacts: relative artifact refs, SHA-256 checksums, media type, artifact
  role, and output manifest/checksum if a mesher emits one;
- coordinate echo: units, coordinate system, design waterline metadata when
  relevant;
- topology and boundaries: cell count, boundary face count, boundary patch
  names, face counts by patch, patch roles/marker names, exterior surface ID,
  and body-surface-match status;
- hard quality counts: invalid, inverted, zero-volume, and nonfinite cells;
- profile quality summaries: min cell volume, max skewness, max aspect ratio,
  non-orthogonality or scaled-Jacobian equivalents when emitted by the selected
  mesher;
- readiness: structured blocker reasons, structured warnings, and resulting
  readiness level.

Patch names and roles should not stay as a plain list once a real adapter is
selected. OpenFOAM and SU2 both bind boundary conditions through named
patches/markers, so a future schema should record a structured boundary block
such as `{name, role, face_count, source_surface_id, solver_marker_type}`.

### Quality Thresholds

Universal blocker thresholds should stay minimal and solver-independent:

- invalid cell count must be zero;
- inverted cell count must be zero;
- zero-volume cell count must be zero;
- nonfinite cell count must be zero;
- minimum cell volume must be positive when reported;
- boundary patch set must satisfy the selected solver profile;
- body surface must match the accepted generated-body diagnostic;
- required metrics missing for the selected profile are blockers.

Everything else should be profile-specific until a solver and mesher are
selected. If the first production path is OpenFOAM-like, OpenFOAM's published
`meshQualityControls` provide a defensible starting profile: non-orthogonality,
boundary/internal skewness, concavity, determinant, face weight, volume ratio,
and minimum volume should be recorded with the exact limits used. But those
limits should not be imported into the generic kayak-gen schema as universal
truth. Gmsh, VTK/PyVista, OpenFOAM, and SU2 expose different measures and
different cell-type assumptions.

Recommended threshold policy:

- hard blockers are attached to a named solver profile and profile version;
- missing optional metrics are warnings, not blockers;
- missing required metrics are blockers;
- threshold relaxations are warnings unless the profile declares a relaxed
  limit as accepted for that run;
- quality summaries should include observed values even when they do not block
  readiness, so later calibration or solver-debug work has provenance.

### Artifact Hashes

The current SHA-256 approach is appropriate. The decision should formalize it:

- hash every referenced diagnostic and output artifact at dispatch time;
- record the hash algorithm explicitly, either as `sha256:<hex>` values or as
  `{algorithm: "sha256", hexdigest: "..."}`;
- hash structured diagnostic payloads in canonical JSON form where possible;
- hash binary or native mesh artifacts by file bytes;
- keep refs relative to the package root and reject empty, absolute,
  parent-traversal, out-of-root, or missing refs;
- fold accepted evidence hashes into CFD job identity so changed evidence
  creates a new job record;
- reject stale, missing, cross-body, cross-hull, cross-profile, and
  cross-tolerance hashes before any solver command runs.

The current code mostly does this; the follow-up risk from workflow 0034 is
that permissive alias lookup in `_expected_evidence_hash` should either be
documented as supported compatibility or narrowed to canonical keys.

### Blocker And Warning Semantics

Blockers should be machine-readable reasons that make a readiness gate
`blocked` or a volume mesh `invalid`. Warnings should be machine-readable
disclosures that do not change the gate result.

Use blockers for:

- open surface supplied where a generated closed body is required;
- synthetic fixture supplied as generated kayak evidence;
- missing generated body;
- failed generated-body diagnostics;
- self-intersection not passed;
- missing, malformed, stale, cross-body, cross-hull, cross-profile, or
  cross-tolerance volume-mesh evidence;
- missing required artifact hash or artifact checksum mismatch;
- invalid, inverted, zero-volume, or nonfinite cells;
- required quality metrics missing or below profile threshold;
- boundary patch set incompatible with selected solver profile;
- solver profile not satisfied.

Use warnings for:

- fixture evidence accepted only as fixture evidence;
- raw/unvalidated CFD result semantics;
- optional quality metrics unavailable;
- profile threshold relaxations that are explicitly accepted;
- high aspect ratio or skewness values that are near but not beyond the
  selected blocking threshold;
- generated closed body available for evaluation but not yet volume-meshed;
- package ready for one profile but not another.

The current string lists are sufficient for display, but the decision should
prefer structured records with at least `code`, `message`, `evidence_ref`, and
`severity`. That preserves CLI/web readable text while making tests and future
dispatch decisions less brittle.

### `cfd_ready` Promotion Rules

`cfd_ready` should remain profile-scoped and solver-input-only. It must never
mean "solver ran," "validated drag," "calibrated resistance," "final
prediction," or "design fitness."

For `watertight_solid_resistance_v1`, promotion should be allowed only when
all of the following are true for the same package:

- manifest solver profile is `watertight_solid_resistance_v1`;
- readiness authority is verified volume-mesh evidence, not surface
  diagnostics or caller-supplied text;
- manifest references generated-body diagnostics, self-intersection
  diagnostics, volume-mesh diagnostics, volume-mesh artifacts, and evidence
  hashes;
- generated-body diagnostics pass the generated-body gate above;
- volume-mesh diagnostics reference the same body ref, source hull hash,
  tolerance hash, closed diagnostic hash, self-intersection hash, profile, and
  artifacts;
- all referenced paths are relative, in-package, present, and hash-matching;
- volume-mesh readiness is `cfd_ready` with no blockers;
- dispatch validation independently re-verifies the evidence before creating a
  job or running an adapter.

Generated body plus self-intersection success without a matching volume-mesh
diagnostic remains below `cfd_ready`. Synthetic closed-volume fixtures remain
barred from generated-kayak handoff. Fixture volume-mesh evidence may keep
exercising the positive path only if every artifact and warning labels it as
fixture evidence.

## Viable Options

### Option A - Conservative Default: Readiness Report First

Add the RFC 0040 readiness report as an explanatory read model over existing
diagnostics and manifests. It explains body/package/profile gate status,
blockers, warnings, evidence refs, and hashes without changing package
readiness or production promotion.

This is the safest next step. It closes the user-visible evidence question and
supports CLI/web/report surfaces, while leaving production thresholds and
mesher choice deferred.

### Option B - Schema Hardening With Fixture Evidence Only

Formalize the volume-mesh diagnostic schema, structured blocker/warning
records, SHA-256 hash policy, boundary patch schema, and rejection-code tests.
Keep the only positive `cfd_ready` path fixture-backed and labeled
fixture-only.

This is viable after or alongside Option A. It turns the accepted workflow 0034
fixture handoff into a durable contract without selecting a production mesher.

### Option C - Choose A Production Mesher/Solver Threshold Profile Now

Select a concrete production mesher or solver target, such as an OpenFOAM-like
volume-mesh path, and define hard quality thresholds now.

This is viable only after a solver/mesher selection decision. It risks
smuggling RFC 0041 solver choice and operations constraints into the readiness
decision. It should not be the conservative default.

### Option D - Add A Separate Surface-Only Solver Profile

Define a surface-only real-solver profile instead of making every future solver
wait for `watertight_solid_resistance_v1`.

This might be useful if the first external adapter has a physically coherent
open-surface mode, but it is a separate solver-mode decision. It must not reuse
`watertight_solid_resistance_v1` or imply watertight readiness.

## Recommended Posture

Choose Option A as the default and Option B as the immediate implementation
follow-up. Defer Option C until the panel selects a production mesher/solver
target and defers or accepts concrete quality limits for that target. Keep
Option D separate from watertight readiness.

The evidence clearly supports a profile-scoped contract:

1. Add a readiness report that explains why today's open packages and
   generated bodies are blocked for watertight solver input.
2. Harden the generated-body diagnostic matrix before treating generated
   bodies as stable source artifacts.
3. Formalize volume-mesh diagnostics with structured boundary patch metadata,
   structured blockers/warnings, and explicit hash algorithm fields.
4. Keep current fixture `cfd_ready` as fixture-only evidence.
5. Permit production `cfd_ready` only after a selected profile has matching
   generated-body, self-intersection, volume-mesh, artifact, and checksum
   evidence.

## Risks And Unknowns

- OpenFOAM, SU2, and Gmsh expose different mesh quality measures; adopting one
  threshold set globally would be false precision.
- Current fixture diagnostics prove contract wiring, not production meshing.
- Boundary patch requirements are under-modeled for real adapters; a plain list
  of patch names will not be enough once boundary-condition roles matter.
- Some rejection-code paths exist but lack direct tests, per workflow 0034
  final review.
- Hash alias lookup is permissive in current dispatch validation; it should be
  narrowed or documented before manifests become a long-lived contract.
- A positive `cfd_ready` input gate can still be misread by users as validated
  CFD output unless CLI/web/docs keep raw/unvalidated solver-output wording
  adjacent to it.
- High-angle stability may reuse generated-body evidence, but it has different
  integration and warning semantics; do not collapse stability readiness into
  solver readiness without a separate design gate.

## Implementation Gates Before Any Work

- Decide whether workflow 0050 is only selecting posture or also authorizing
  an implementation workflow for Option A/B.
- Record the readiness report schema and blocker/warning code list before UI
  or CLI copy changes.
- Add direct negative tests for `cross_body`, `cross_hull`,
  `cross_tolerance`, `evidence_profile_mismatch`, `malformed_diagnostic`,
  `body_surface_mismatch`, and `artifact_checksum_mismatch`.
- Add generated-body hardening cases from RFC 0040 before production handoff
  work.
- Add structured boundary patch/marker metadata before selecting a real solver
  adapter.
- Keep every solver result record at `raw_unvalidated`; do not modify
  calibration, final-prediction, Pareto-default, or design-fitness wording.

## Sub-Agent Help

No spawned sub-agents were used. I used parallel read-only local inspections
and current primary-source research.
