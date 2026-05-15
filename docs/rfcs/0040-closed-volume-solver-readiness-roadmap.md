# RFC 0040: Closed-Volume Solver Readiness Roadmap

Status: partial landed generated-body-hardening + real snappyHexMesh evidence harness (opt-in env-gated)
Date: 2026-05-14
Context: successor roadmap for the closed-volume and solver-readiness
dependency spine in RFC 0010, RFC 0015, RFC 0016, RFC 0021, RFC 0022,
RFC 0023, RFC 0026, and RFC 0028. It responds to the deferred backlog item for
closed-volume/solver readiness before real solver and watertight-readiness
claims can advance. RFC 0041 is the companion real-adapter successor and should
consume this RFC's profile gate rather than redefining geometry readiness.
Index treatment: this RFC is a proposed roadmap and gated-scope document
layered above the named closed-volume and solver-readiness RFCs. It does not
supersede those RFCs and must not be scheduled as one "make generated packages
`cfd_ready`" implementation packet.

## Problem

The project now has several useful safe slices:

- open hull and deck inspection surfaces with mesh diagnostics and mesh package
  manifests;
- local CFD job/run/profile plumbing with raw and unavailable states;
- explicit synthetic closed-volume diagnostics;
- generated hull-plus-deck closed-body construction and diagnostics;
- self-intersection diagnostics;
- a fixture-level handoff boundary for watertight-required profile evidence;
- a deterministic local-command fixture adapter that proves dispatch plumbing.

Those pieces are necessary but not sufficient for general solver readiness. The
remaining risk is that future work can treat one safe slice as proof for a
stronger claim: a display STL can be mistaken for a closed body, a generated
closed body can be mistaken for a solver volume mesh, a fixture handoff can be
mistaken for production meshing, or a raw adapter run can be mistaken for
validated CFD.

The project needs one roadmap that orders the missing evidence before any real
solver adapter or watertight solver-profile claim depends on it.

## Goals

- Consolidate the closed-volume and solver-readiness dependency order into one
  implementation roadmap.
- Define the evidence required between generated closed-body diagnostics,
  volume-mesh diagnostics, mesh-package manifests, and dispatch preparation.
- Keep open display/export surfaces, synthetic diagnostic fixtures, generated
  evaluation bodies, fixture handoffs, and future production solver inputs
  distinct.
- Make missing evidence visible through structured blocker reasons rather than
  through optimistic readiness labels.
- Give the future real CFD adapter RFC a clear prerequisite boundary.
- Preserve RFC 0025 claim gates: solver results remain raw/unvalidated until a
  separate validation or calibration RFC accepts stronger claims.

## Non-Goals

- No runtime implementation in this RFC.
- No OpenFOAM, SU2, RANS, Docker, hosted worker, or real solver execution.
- No production volume mesher selection or production meshing guarantee.
- No calibrated CFD, calibrated resistance, final prediction, final design
  fitness, or Pareto-default scoring.
- No high-angle `GZ` implementation or secondary-stability numeric claim.
- No change to current open STL display/export behavior.
- No promotion of ordinary generated packages to watertight solver readiness
  without the evidence gates below.
- No new hull parameters, class definitions, or UI scope.

## Dependencies

- RFC 0010 for mesh-package manifests, readiness levels, and solver profiles.
- RFC 0015 for local CFD job/run records and dispatch gating.
- RFC 0016 and RFC 0021 for closed-volume and self-intersection diagnostics.
- RFC 0022 for generated hull-plus-deck closed-body construction.
- RFC 0023 for the watertight volume-mesh handoff evidence model.
- RFC 0025 and RFC 0027 for claim gates that keep solver output raw until
  separate validation or calibration evidence lands.
- RFC 0026 for the fixture-local-command adapter boundary that proves dispatch
  plumbing without real CFD claims.
- RFC 0028 for exact plumb-stem, independent rake, and closed-body cap
  semantics.
- RFC 0041 for the later external-solver adapter that depends on profile
  readiness instead of creating it.

## Proposal

Adopt a readiness ladder and implement it in separate future workflows. Each
level may depend only on evidence from lower levels, and each level must record
why it is unavailable when evidence is missing.

### Readiness ladder

1. **Inspection surfaces.** Current open hull and deck surfaces remain display,
   STL export, and open-surface package artifacts. They may support open
   wetted-surface candidate workflows and fixture-local-command adapter tests.
   They are not closed-volume evidence.
2. **Synthetic diagnostic bodies.** Explicit synthetic triangle meshes remain
   diagnostic and test fixtures. They can prove closure, manifold, signed
   volume, and self-intersection checks. Their policy continues to block
   solver-readiness claims for generated kayaks.
3. **Generated closed evaluation body.** `generated_hull_plus_deck_closed_body_v1`
   is the project-owned closed body derived from `Hull` parameters. It is
   eligible for closed-volume evaluation only when body-level diagnostics pass:
   closure, manifoldness, positive signed volume, outward normals, serialized
   cap/join/waterline/tolerance policy, and non-blocking self-intersection
   results.
4. **Volume-mesh handoff evidence.** A generated closed body is still below
   watertight solver readiness until a volume-mesh diagnostic references the
   same `body_ref`, source hull hash, diagnostic hashes, coordinate system,
   tolerances, and selected solver profile. Missing, stale, synthetic,
   cross-body, or malformed volume-mesh evidence must block the handoff.
5. **Solver dispatch prerequisite.** A real solver adapter may consume only a
   mesh package whose selected solver profile is satisfied by verified
   evidence. Adapter success still produces raw/unvalidated solver records, not
   calibrated or final design claims.

### Readiness evidence report

Add a future read model that explains the ladder for one hull, body, package,
and solver profile without inventing a new readiness authority:

```python
ClosedVolumeSolverReadinessReport(
    hull_hash: str,
    body_ref: str | None,
    body_profile: str | None,
    mesh_package_ref: str | None,
    solver_profile: str,
    generated_body_diagnostic_ref: str | None,
    self_intersection_diagnostic_ref: str | None,
    volume_mesh_diagnostic_ref: str | None,
    evidence_hashes: dict[str, str],
    gate_status: Literal["ready_for_profile", "blocked"],
    blocker_reasons: list[str],
    warnings: list[str],
    input_semantics: Literal["not_solver_input", "profile_input_candidate"],
)
```

The report is an explanation layer over existing diagnostics and manifests. It
must not accept caller-supplied readiness strings as authority. It should be
able to say, for example, that a generated body passed closed-volume
diagnostics but is blocked for a watertight-required solver profile because
volume-mesh evidence is absent. It is not an RFC 0025 solver-result claim state;
actual adapter outputs remain `raw_unvalidated`.

Recommended blocker reasons:

- `open_surface_not_closed_body`;
- `synthetic_body_not_generated_kayak`;
- `generated_body_missing`;
- `generated_body_diagnostics_failed`;
- `self_intersection_not_passed`;
- `volume_mesh_missing`;
- `volume_mesh_stale_or_cross_body`;
- `volume_mesh_quality_failed`;
- `solver_profile_not_satisfied`;
- `raw_solver_output_not_validated`.

### Generated-body hardening

Before a production solver handoff is attempted, generated-body diagnostics
need evidence across the hull parameter envelope that matters for the project:

- default touring and surfski preset hulls;
- exact plumb bow and exact plumb stern;
- mixed plumb/raked bow and stern cases;
- `beam_wl_m != beam_oa_m` sheerline/deck joins;
- low and high design-draft cases within accepted class ranges;
- representative `Cp` and `Cm` values in the documented design envelope;
- explicitly unsupported or invalid hulls returning structured diagnostics.

This hardening does not by itself create solver readiness. It only establishes
that the generated closed body is a stable source artifact for later handoff.

### Volume-mesh diagnostic contract

A future implementation must keep volume meshing evidence separate from
generated-body diagnostics. The volume-mesh diagnostic should record at least:

- generated `body_ref`, source hull hash, and body diagnostic hash;
- self-intersection diagnostic hash;
- solver profile name and volume-mesh profile version;
- mesher name, version, command/config digest, and input artifact hashes;
- cell count, boundary face count, boundary patch names, and coordinate units;
- invalid, inverted, zero-volume, and nonfinite cell counts;
- available quality summaries such as min volume, skewness, aspect ratio, or
  mesher-specific equivalents;
- artifact paths and checksums;
- readiness result, warnings, and blocker reasons.

The first implementation may use deterministic fixtures to test the contract,
but fixture evidence must be labeled as fixture evidence. A production mesher
or real solver remains a separate later decision.

### Package and dispatch gates

Mesh-package and dispatch code may treat a watertight-required solver profile
as satisfied only when all referenced evidence matches:

- same hull hash;
- same generated `body_ref`;
- same body diagnostic and self-intersection diagnostic hashes;
- same volume-mesh diagnostic hash;
- same solver profile;
- matching artifact checksums;
- no blocking diagnostic status.

Rejection paths must identify the failed evidence class. They must not fall
back from a failed watertight-required handoff to an open-surface profile
without an explicit caller request.

### Claim boundary

This roadmap only prepares solver inputs. It does not validate solver outputs.
Even after the handoff gates exist, any real adapter output remains
`raw_unvalidated` until separate calibration or validation work satisfies
RFC 0025/RFC 0027 claim gates. User-facing copy must keep that distinction.

## Acceptance Criteria

- This RFC is indexed as a roadmap/gated scope, not as one ready-to-code
  feature or as authority to promote generated packages to `cfd_ready`.
- A future readiness report can explain, with structured blocker reasons, why
  current open-surface packages are below any watertight-required solver
  profile.
- Synthetic closed-volume fixtures remain barred from generated-kayak solver
  handoff, even when their closure diagnostics pass.
- Generated closed bodies without matching volume-mesh diagnostics remain
  below watertight-required solver-profile acceptance.
- Generated body diagnostic tests cover default, plumb, mixed-rake,
  `beam_wl_m != beam_oa_m`, and representative class-envelope cases.
- Volume-mesh diagnostics include body refs, diagnostic hashes, artifact
  checksums, mesher metadata, cell/quality summaries, warnings, and blocker
  reasons.
- Package promotion and dispatch preparation reject missing, stale, cross-body,
  synthetic, hand-edited, or malformed evidence.
- Any fixture handoff is labeled as fixture evidence and is not documented as
  production volume meshing or real solver execution.
- CLI, web, report, and docs wording keep solver-input readiness separate from
  calibrated or validated CFD results.
- Tests include negative cases for each forbidden promotion: open surface as
  closed body, synthetic body as generated kayak, generated closed body as
  volume mesh, fixture handoff as production meshing, and raw solver output as
  validated prediction.

## Open Questions

- Which volume mesher, if any, should be selected for the first production
  implementation after fixture diagnostics prove the contract?
- Should surface-only real solvers get a separate profile instead of using the
  watertight-required handoff path?
- What minimum quality thresholds are meaningful for kayak-scale displacement
  hull CFD before calibration data exists?
- How broad must the generated-body parameter matrix be before it is acceptable
  as solver-input evidence rather than evaluation-only evidence?
- Should the existing readiness vocabulary remain user-visible, or should UI
  copy use profile-specific phrases such as "ready for watertight-required
  solver input" to avoid overclaiming?
- Should high-angle `GZ` and solver readiness share the same generated-body
  evidence report, or should stability keep a separate report with different
  blocker reasons?

## Implementation Path

1. Add the readiness evidence report as an explanatory read model over existing
   diagnostics and manifests. Keep current package readiness unchanged.
2. Add generated-body hardening fixtures across the accepted parameter cases,
   with explicit unavailable or failed diagnostics for unsupported cases.
3. Add volume-mesh diagnostic models and deterministic fixture artifacts that
   prove matching, stale, malformed, and cross-body evidence behavior.
4. Wire mesh-package handoff logic to derive watertight-required profile
   acceptance only from verified generated-body, self-intersection, and
   volume-mesh evidence.
5. Extend dispatch preparation to compare evidence hashes, profile names,
   artifact checksums, and blocker reasons before any real adapter is allowed
   to run.
6. Update user-facing documentation and status copy only after implementation
   evidence exists, preserving raw/unvalidated solver-output wording.
7. Let the future real CFD adapter RFC depend on this roadmap's accepted
   solver-profile gate rather than redefining closed-volume or volume-mesh
   readiness.

## Domain Modeling

Boundary clarification. The generated closed body remains the source-of-truth
geometry value object derived from `Hull`. A volume mesh is a solver handoff
artifact derived from that body. The readiness report is a read model that
explains evidence and blockers; it is not an aggregate root and not physical
validation.
