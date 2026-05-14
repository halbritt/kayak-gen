---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_6c9c6483443b47eab07f2e1448585069
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_solver_readiness_claude
lease: lease_f0dcc616ce4d46eb895ddea520553011

# Panel Vote — Solver Readiness Evidence

## Vote

**Option A (Readiness Report First), with Option B as the immediate
implementation follow-up. Defer Option C. Keep Option D separated from
watertight readiness.**

## Decision Sentence For `docs/DECISION_LOG.md`

Adopt a profile-scoped, evidence-derived solver-readiness contract for
kayak-gen. The contract is staged as: (1) an explanatory readiness report over
the existing generated-body, self-intersection, volume-mesh, manifest, and
dispatch evidence; (2) schema hardening of the volume-mesh diagnostic
(structured boundary patches/markers, structured blocker and warning records
with `code`/`message`/`evidence_ref`/`severity`, explicit hash-algorithm
fields, and direct negative tests for the existing rejection codes); (3)
generated-body hardening across the RFC 0040 case matrix. The only positive
`cfd_ready` path remains the existing narrow fixture-backed
`watertight_solid_resistance_v1` evidence chain, labeled as fixture evidence.
No production mesher or solver threshold profile is selected by this decision,
and no surface-only real-solver profile is created under
`watertight_solid_resistance_v1`.

## Evidence

### Research-Packet Evidence

- `striatum/0050-decision-panel-research/research/solver_readiness/RESEARCH.md`
  recommends Option A as the conservative default and Option B as the immediate
  follow-up, citing OpenFOAM `meshQualityControls`, OpenFOAM `checkMesh`,
  OpenFOAM patch-based boundaries, SU2 mesh markers, Gmsh element quality,
  PyVista cell quality, and Python `hashlib` as primary sources for why
  thresholds and boundary semantics must stay profile-scoped rather than
  universal.
- Local project boundaries the research packet anchors to:
  - `docs/PRD.md` keeps open hull/deck STLs as inspection surfaces and reserves
    `cfd_ready` to a narrow fixture-backed volume-mesh evidence path.
  - `docs/ROADMAP.md` lines 44-50 (no-claims rules on watertight/`cfd_ready`
    and generated bodies) and Batch D (`:124-143`) explicitly stage RFC 0040 as
    `readiness report → generated-body hardening → volume-mesh diagnostic
    contract → package and dispatch gates`, not as one `make generated
    packages cfd_ready` feature.
  - `docs/rfcs/README.md` confirms RFC 0010 has only landed the
    `display`/`stl_surface`/`cfd_surface_candidate`/`cfd_ready` ladder, RFC
    0023 landed only as fixture handoff, RFC 0040 is `proposed roadmap/gated
    scope`, and RFC 0041 is `proposed gated successor` requiring an
    independent solver-selection decision.

### Independent Check On Current Code

I verified directly that the evidence the research packet relies on already
exists in `kayakgen/`:

- `kayakgen/eval/closed_volume.py`, `kayakgen/eval/generated_closed_body.py`,
  `kayakgen/eval/volume_mesh.py`, and `kayakgen/eval/mesh_package.py` are all
  present.
- `kayakgen/eval/cfd/jobs.py` already emits the structured rejection codes the
  research packet calls out as the test-coverage gap:
  `evidence_profile_mismatch` (lines 854, 1048, 1122), `cross_body` (lines
  1053, 1063, 1132), `cross_hull` (lines 1058, 1068, 1137), `cross_tolerance`
  (lines 1075, 1152), `body_surface_mismatch` (line 1169), and
  `artifact_checksum_mismatch` (lines 1174, 1180, 1185).

So the evidence model the decision adopts is not speculative — the runtime
contract is already shaped this way, the rejection codes already exist as
strings in dispatch validation, and the missing pieces are (i) direct negative
tests per rejection code, (ii) a structured readiness *report*, and (iii)
formal schema records around what is today plain string lists. That makes
Option A a documentation/read-model slice over real diagnostics, not a new
claim, and makes Option B an internal-schema hardening pass with no
user-visible readiness promotion.

### Independent Domain Check

`docs/design/kayak_hull_design_constraints.md §10` is consistent with the
posture: it explicitly recommends that cheap geometric and hydrostatic filters
run before any CFD cycles, and that real solver work be the final stage. That
matches a stance where solver-input readiness is gated by evidence rather than
asserted from open inspection surfaces. Nothing in the constraints doc argues
for accepting an open-surface watertight claim.

### External-Source Check

The research packet's external sources were accessed 2026-05-14 and the
claim-to-source mapping is sound on its face: OpenFOAM exposes
profile-specific quality controls (`meshQualityControls`, `relaxed`) and
patch-based boundary handling; SU2 binds boundary conditions through marker
tags; Gmsh and PyVista expose mesher-/cell-specific quality measures. Those
facts directly support the decision to keep thresholds and boundary semantics
profile-scoped and the choice not to import any single mesher's threshold set
as universal kayak-gen truth. I did not re-fetch the URLs from this session
(`WebFetch` is not loaded in the current tool surface); the citations are
plausible and consistent with the published documentation as I recall it, and
nothing in the local code or roadmap contradicts them.

## Why Rejected Alternatives Lose

### Option C — Choose A Production Mesher/Solver Threshold Profile Now

Loses because:

- It smuggles RFC 0041's solver-selection and operations decisions into the
  readiness decision. `docs/ROADMAP.md` Batch E (`:145-164`) lists
  solver-target selection, installation/version/platform notes, mesh-profile
  gate, deterministic case-template version, expected raw outputs, parser
  scope, and CI tests that do not require the solver binary as prerequisites
  *before* implementation; none of those are in scope here.
- The external evidence shows OpenFOAM, SU2, Gmsh, VTK/PyVista each emit
  different measures with different cell-type assumptions. Adopting any one
  vendor's thresholds globally would be false precision and would either
  exclude valid evidence from other meshers or quietly redefine accepted
  meshes when the production mesher changes.
- The current code already supports profile-scoped acceptance
  (`MeshSolverProfile`, fixture profile, `watertight_solid_resistance_v1`
  blocked profile); adopting a universal threshold set would regress that.

### Option D — Add A Separate Surface-Only Solver Profile

Loses *for this decision* because:

- It is a solver-mode decision, not a readiness-contract decision. The
  research packet correctly notes it must not reuse
  `watertight_solid_resistance_v1` and must not imply watertight readiness.
- There is no accepted external adapter and no accepted surface-mode physics
  envelope today. Defining a new profile in this workflow would create a
  capability surface ahead of RFC 0041's required solver-selection and
  case-template gates.
- Nothing in the current code or roadmap blocks such a profile from being
  defined *later*, in its own RFC, gated on actual solver choice and physics
  envelope. So rejecting it here costs nothing; accepting it here pre-commits
  the project to a path it has no evidence for.

### Pure-Option-B-Only (Skip Option A)

Loses (compared to A+B in sequence) because schema hardening with no
user-visible readiness report leaves users and reviewers unable to see *why*
ordinary generated packages remain below watertight solver acceptance.
Workflow 0034's final review already flagged the test-coverage gap; the
report makes the same information visible without changing capability or
copy. A bare schema pass would still be useful but would defer the
operator-visible value to a later docs workflow for no real reason.

### Pure-Option-A-Only (Skip Option B)

Loses (compared to A+B in sequence) because the schema and rejection-code
tests are the load-bearing trust mechanism. Without Option B, the readiness
report describes a contract the runtime only partially enforces with direct
tests. Stopping at Option A risks the report drifting from the implementation
the moment a refactor changes a string list to a structured record.

## Implementation Gates That Must Remain In Force

These gates must not be relaxed by any workflow consuming this decision:

1. **Generated-body gate.** A closed body may feed a volume-mesh diagnostic
   only when: body type is `generated_hull_plus_deck_closed_body_v1` (not
   synthetic fixture); source hull hash matches the package hull hash; closure
   policy records cap/join/waterline/normal-orientation/tolerance settings;
   raw and welded body-level boundary edges are zero; raw and welded
   body-level nonmanifold edges are zero; degenerate, nonfinite, and invalid
   counts are zero; signed volume is positive under the outward-normal
   convention; self-intersection status is `passed` (not `not_checked`,
   `failed`, or `inconclusive`); and the exact tolerance set is recorded.
2. **Volume-mesh diagnostic identity.** A volume-mesh diagnostic must record
   schema version, profile name, profile version, `body_ref`, body type,
   source hull hash, closed-volume diagnostic hash, self-intersection
   diagnostic hash, tolerance hash, mesher name/version, command/config
   digest, deterministic inputs, artifact refs with SHA-256 checksums and
   media types, units/coordinate echo, boundary patch names with face counts
   and roles, body-surface-match status, hard counts (invalid, inverted,
   zero-volume, nonfinite), profile-specific quality summaries, structured
   blocker reasons, structured warnings, and resulting readiness level.
3. **Universal blocker set (solver-independent).** Invalid, inverted,
   zero-volume, or nonfinite cell counts must be zero; minimum cell volume
   must be positive when reported; boundary patch set must satisfy the
   selected profile; body surface must match the accepted generated-body
   diagnostic; required metrics for the selected profile must be present;
   self-intersection must be `passed`.
4. **Hash policy.** Hash every referenced diagnostic and output artifact at
   dispatch time using SHA-256; record the hash algorithm explicitly; hash
   structured payloads in canonical JSON form and binary artifacts by file
   bytes; reject empty, absolute, parent-traversal, and out-of-root refs;
   fold accepted evidence hashes into CFD job identity so changed evidence
   creates a new job record; reject stale, missing, cross-body, cross-hull,
   cross-profile, and cross-tolerance hashes before any solver command runs.
5. **`cfd_ready` promotion.** Permit `cfd_ready` only when manifest solver
   profile, readiness authority (verified volume-mesh evidence — not surface
   diagnostics or caller-supplied text), generated-body diagnostics,
   self-intersection diagnostics, volume-mesh diagnostics, volume-mesh
   artifacts, and evidence hashes all match for the same package, and
   dispatch independently re-verifies the chain before creating a job.
6. **Test-coverage gate.** Before any user-visible readiness-report copy,
   add direct negative tests for `cross_body`, `cross_hull`,
   `cross_tolerance`, `evidence_profile_mismatch`, `malformed_diagnostic`,
   `body_surface_mismatch`, and `artifact_checksum_mismatch`. Narrow or
   document the permissive `_expected_evidence_hash` alias lookup flagged by
   the workflow 0034 final review.
7. **Generated-body hardening matrix.** Before any production handoff,
   exercise the RFC 0040 case matrix: default hull, surfski/touring presets,
   exact plumb bow/stern, mixed rake, `beam_wl_m != beam_oa_m`,
   representative draft/`Cp`/`Cm`, and unsupported/invalid cases that return
   structured diagnostics.

## No-Claims Language That Must Remain In Force

This decision does not relax any of the following, and consuming workflows
must preserve them verbatim where they already appear in `docs/PRD.md`,
`docs/USER_GUIDE.md`, `docs/ROADMAP.md`, and the RFC index:

- `cfd_ready` is a *solver-input* readiness label only. It does not mean
  "solver ran," "validated drag," "calibrated resistance," "final
  prediction," "design fitness," or "seaworthiness."
- Ordinary generated mesh packages remain `cfd_surface_candidate` or below.
  Only the narrow fixture-backed `watertight_solid_resistance_v1` path may
  report `cfd_ready`, and every fixture artifact must be labeled as fixture
  evidence, not as production meshing.
- Synthetic closed-volume fixtures remain barred from generated-kayak
  handoff. Generated body plus self-intersection success without a matching
  volume-mesh diagnostic remains below `cfd_ready`.
- Open hull/deck STLs stay inspection surfaces; changing `bow_rake` or
  `stern_rake` to `0.0` does not by itself make those STLs watertight.
- CFD dispatch records remain `raw_unvalidated`, `fixture_only`, or
  unavailable/failed. No OpenFOAM, SU2, Docker, hosted-worker, or real
  external-solver success claim is created by this decision.
- This decision does not select a production mesher or solver, does not
  define a surface-only real-solver profile under watertight readiness, and
  does not change resistance calibration, high-angle `GZ`, design-fitness,
  Pareto-default scoring, or hosted-demo capability wording.

## Confidence

**High.**

Rationale: the recommended posture is mechanically aligned with `docs/PRD.md`,
`docs/ROADMAP.md` Batch D, the RFC 0010/0015/0016/0021/0022/0023/0040
spine, and the structured rejection codes already present in
`kayakgen/eval/cfd/jobs.py`. The external-source evidence in the research
packet (OpenFOAM, SU2, Gmsh, PyVista, `hashlib`) directly supports the
decision to keep thresholds and boundary semantics profile-scoped rather than
universal. The decision authorizes only documentation-shaped scope (readiness
report) and contract-hardening scope (structured records, negative tests)
that do not promote any open package to `cfd_ready` or pre-commit a solver
selection. The only meaningful unknown — the eventual production mesher and
its threshold profile — is correctly deferred to RFC 0040's later stages and
RFC 0041's solver-selection decision rather than resolved here.

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/ROADMAP.md` (especially No-Claims Rules and Batch D)
- `docs/DECISION_LOG.md`
- `docs/rfcs/README.md` (entries 0010, 0015, 0016, 0017, 0018, 0021, 0022,
  0023, 0026, 0028, 0040, 0041)
- `docs/design/kayak_hull_design_constraints.md` (§10 pipeline strategy)
- `docs/workflows/0018-deferred-backlog/QUEUE.md`
- `docs/workflows/0050-decision-panel-research/SOURCES.md`
- `striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md`
- `striatum/0049-roadmap-reconciliation/integration/PATCH_SUMMARY.md`
- `striatum/0050-decision-panel-research/research/solver_readiness/RESEARCH.md`
- `kayakgen/eval/cfd/jobs.py` (rejection codes — verified)
- `kayakgen/eval/` (closed_volume, generated_closed_body, volume_mesh,
  mesh_package — verified present)

External claims (as cited in the research packet, accessed 2026-05-14;
not re-fetched in this session):

- OpenFOAM `meshQualityControls` — profile-specific thresholds and `relaxed`
  dictionary support profile-scoped rather than universal thresholds.
- OpenFOAM `checkMesh` — user-defined criteria via `system/meshQualityDict`
  support recording exact criteria as diagnostic artifacts.
- OpenFOAM boundary handling — patch-based with patch type and face counts.
- SU2 mesh markers — boundary marker names as first-class.
- Gmsh element quality — mesher-native quality summaries vary.
- PyVista cell-quality info — quality metadata varies by cell type and
  measure.
- Python `hashlib` — supports continuing SHA-256 with explicit algorithm
  recording.

## Sub-Agent Help

No sub-agents were spawned. Verification of code references and panel
directory state was performed inline via direct read-only inspection.
