---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

## Vote
Vote: Option A (Conservative Default: Readiness Report First)

## Concrete Decision Sentence
Implement the RFC 0040 readiness report as an explanatory read model to surface structured gate status and formalize the profile-scoped volume-mesh diagnostic schema with strict evidence hashing, deferring concrete quality thresholds and real-solver promotion until a specific production mesher is selected.

## Evidence and Citations
- **Local Policy constraints:** RFC 0040 explicitly requires staging this work as a readiness report, generated-body hardening, and explicit package gates rather than an atomic "make generated packages `cfd_ready`" leap (`docs/ROADMAP.md`).
- **External Mesh Quality findings:** External documentation from OpenFOAM (`meshQualityControls`, `checkMesh`), Gmsh, and SU2 confirm that cell quality measures and boundary patch semantics (e.g., markers/tags) are highly solver-specific. Adopting a universal set of kayak-gen thresholds would introduce false precision.
- **Current Architecture validation:** The current fixture-backed evidence path in `kayakgen/eval/volume_mesh.py` and `kayakgen/eval/mesh_package.py` correctly links body references, diagnostic hashes, and artifact SHA-256 checksums, proving the viability of a strict, profile-scoped evidence contract without needing a real production mesher immediately.

## Rejected Alternatives
- **Option C (Choose A Production Mesher/Solver Threshold Profile Now) loses because** it forces premature coupling. Selecting a production mesher and universal thresholds prior to resolving the external solver adapter decision (RFC 0041) risks embedding operations constraints that violate the architecture's solver-agnostic intent and limits.
- **Option D (Add A Separate Surface-Only Solver Profile) loses because** it conflates open-surface mesh readiness with the strict generated closed-body constraints required for `watertight_solid_resistance_v1`, distracting from the core goal of establishing reliable watertight solver evidence.

## Implementation Gates and No-Claims Language
- **No-Claims:** The `cfd_ready` status must remain purely solver-input-ready; it must never imply or claim "solver ran", "validated drag", "calibrated resistance", "final prediction", or "design fitness".
- **Raw Outputs:** All CFD solver output dispatch states remain strictly `raw_unvalidated`, `fixture_only`, or unavailable.
- **Evidence Requisites:** Production `cfd_ready` promotion is strictly barred unless there is matching generated-body, self-intersection, volume-mesh, artifact, and checksum evidence for the same package.
- **Test Gates:** Implementation must add direct negative tests for `cross_body`, `cross_hull`, `cross_tolerance`, `evidence_profile_mismatch`, `malformed_diagnostic`, `body_surface_mismatch`, and `artifact_checksum_mismatch` before any production handoff work begins.
- **Fixture Boundary:** Existing fixture evidence must continuously be labeled as fixture-only and cannot bypass the production `cfd_ready` rules.

## Confidence
High
