# RFC 0023: Watertight Volume Mesh and `cfd_ready` Handoff

Status: landed fixture-handoff
Date: 2026-05-13
Context: builds on RFC 0010 mesh readiness, RFC 0015 solver dispatch, RFC
0016 closed-volume geometry, and the workflow 0027 safe slice that rejects
forged watertight readiness.

## Problem

The project now has an explicit synthetic closed-volume diagnostic path and a
watertight-required solver profile boundary, but generated kayak bodies still
cannot become `cfd_ready` solver handoff artifacts. The missing contract is the
handoff between a generated closed body, a volume mesher, the mesh package
manifest, and dispatch gating.

Without this handoff contract, a manifest can appear to be solver-ready even
when the referenced geometry is only an open display surface, a synthetic math
fixture, or a hand-edited readiness label with no matching evidence.

## Goals

- Define when a generated closed body may become a solver handoff artifact.
- Require volume-meshing evidence before `cfd_ready` is emitted for
  `watertight_solid_resistance_v1`.
- Keep generated-body diagnostics, self-intersection diagnostics, volume-mesh
  diagnostics, and manifest readiness traceable to the same body.
- Permit narrow manifest/readiness extensions needed for a real handoff.
- Continue rejecting forged or stale readiness evidence.

## Non-Goals

- Selecting or integrating a production CFD solver.
- Claiming CFD force accuracy, calibration, or validation.
- Promoting explicit synthetic closed-volume fixtures to real kayak CFD input.
- Replacing the open wetted-surface package profile.
- Hiding unresolved generated-body closure or self-intersection failures.

## Dependencies

- A generated closed body contract from RFC 0016 Step 5 or a successor RFC.
- Body-level manifold, signed-volume, and tolerance diagnostics for that body.
- Self-intersection diagnostics over the generated closed body.
- RFC 0010 mesh package manifest and solver profile concepts.
- RFC 0015 dispatch gating and evidence-based rejection behavior.

## Proposal

A generated closed body may become a solver handoff artifact only when all of
these gates pass for the same `body_ref`:

- `body_type` is a generated kayak body, not
  `explicit_synthetic_triangle_mesh`;
- generated-body diagnostics report `closed_volume`;
- raw and tolerance-welded body-level boundary edges are zero;
- raw and tolerance-welded body-level nonmanifold edges are zero;
- signed volume is positive under the declared outward-normal convention;
- self-intersection diagnostics ran under recorded tolerances and report no
  blocking intersections;
- closure policy records bow/stern caps, deck/sheer join behavior, waterline
  semantics, normal orientation, and all tolerances;
- a volume-mesh artifact is generated from that exact body and passes the
  selected volume-mesh quality gates.

The first accepted handoff profile is `watertight_solid_resistance_v1`.
`cfd_ready` under that profile means "ready for a watertight-solid solver
adapter to consume as input," not "validated CFD physics."

## Volume-Meshing Evidence

The mesh package must reference a volume-mesh diagnostic artifact. The
diagnostic must include:

- `body_ref`, `source_hull_hash`, and generated-body diagnostic hash;
- volume mesher name, version, command/config digest, and deterministic inputs;
- output artifact references and checksums;
- units and coordinate-system echo from RFC 0010;
- cell count, boundary face count, boundary patch names, and exterior surface
  identity;
- invalid, inverted, zero-volume, and nonfinite cell counts;
- minimum volume, aspect/skewness or equivalent quality summaries available
  from the mesher;
- whether the body surface used by the mesher still matches the accepted
  generated-body diagnostic;
- readiness result with reasons and warnings.

The initial implementation may keep quality thresholds conservative and
profile-specific. Missing metrics must be reported as warnings unless the
profile marks them blocking.

## Manifest and Readiness Changes

Allowed manifest additions are limited to traceability:

- `body_ref`;
- `closed_volume_diagnostic`;
- `self_intersection_diagnostic`;
- `volume_mesh_artifacts`;
- `volume_mesh_diagnostic`;
- `evidence_hashes`;
- `readiness_authority`.

`MeshReadinessLevel.cfd_ready` may be emitted for
`watertight_solid_resistance_v1` only when the manifest references passing
generated-body, self-intersection, and volume-mesh diagnostics. The package
writer must derive readiness from evidence in memory or from verified referenced
artifacts; it must not accept a caller-supplied readiness string as authority.

Open-surface packages remain capped at their existing readiness. Synthetic
closed-volume fixtures remain useful for diagnostics tests, but their policy
continues to say `never_claim_cfd_ready`.

## Forged Readiness Rejection

Dispatch preparation must reject all of these cases:

- manifest readiness is hand-edited to `cfd_ready` with no diagnostics;
- diagnostics reference a different `body_ref`, hull hash, profile, or
  tolerance set;
- generated-body diagnostics fail closure, signed volume, or self-intersection
  gates;
- volume-mesh diagnostics are missing, malformed, stale, or below profile
  thresholds;
- synthetic closed-volume diagnostics are supplied for a generated-body
  watertight handoff;
- manifest artifacts or checksums do not match the referenced diagnostics.

The error path should name the rejected evidence class rather than silently
falling back to an unavailable solver status.

## Acceptance Criteria

- Generated open-surface packages cannot be promoted to
  `watertight_solid_resistance_v1` or `cfd_ready`.
- A generated closed body with passing self-intersection diagnostics but no
  volume-mesh diagnostic remains below `cfd_ready`.
- A passing volume-mesh diagnostic can promote only the matching generated body
  and matching profile.
- Dispatch rejects forged, stale, cross-body, and synthetic evidence.
- Manifest output records `body_ref`, diagnostic refs, evidence hashes,
  warnings, and raw/unvalidated CFD result semantics.
- Tests cover successful handoff fixtures, missing volume mesh evidence,
  self-intersection blockers, stale hashes, and synthetic evidence rejection.

## Open Questions

- Which volume mesher should define the first concrete quality fields?
- Should `cfd_ready` require a volume mesh, or should surface-only watertight
  solvers get a separate readiness profile?
- What self-intersection tolerance is acceptable for generated kayak bodies?
- Should readiness evidence be embedded, referenced, or both?

## Implementation Path

- Step 1 - Define generated-body diagnostic refs and self-intersection evidence
  as manifest extensions without changing current package readiness.
- Step 2 - Add volume-mesh diagnostic models and synthetic/generated fixtures.
- Step 3 - Add package-writer promotion logic for
  `watertight_solid_resistance_v1` based only on verified evidence.
- Step 4 - Extend dispatch validation to compare body refs, hashes, profiles,
  checksums, and diagnostic readiness.
- Step 5 - Add CLI/JSON output that explains why a package is below
  `cfd_ready`.

## Domain Modeling

The generated closed body is the source-of-truth domain artifact. A volume mesh
is a solver handoff artifact derived from that body. The manifest is an
evidence index, not the authority that decides physical readiness.
