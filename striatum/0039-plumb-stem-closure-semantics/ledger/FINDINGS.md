# Findings Ledger: 0039 Plumb-Stem Closure Semantics

Ledger identity: independent Striatum ledger role for workflow
`0039-plumb-stem-closure-semantics`, lane `codex / GPT-5.5`, session
`sess_13f79672adca4075b9aae4f45350fa76`, job
`job_run_53f17f26285941c3a3992705772ce07d_findings_ledger`, lease
`lease_e9857f98cdb74b21b88e6fe1585515af`.

Gate result: `accept_with_findings`

## Stats

- Review artifacts consolidated: 3
  (`domain/REVIEW_DOMAIN.md`, `traceability/REVIEW_TRACEABILITY.md`,
  `ops/REVIEW_OPS.md`).
- Ledger prompt artifacts reviewed: 3 workflow instruction files plus
  `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md`.
- Read-only sub-agents used by this ledger: 4.
- Duplicate finding clusters collapsed: 5.
- Conflicting-claim clusters resolved: 2, both non-blocking.
- Deduplicated findings recorded below: 9.
- Functional implementation blockers before RFC 0028 can be considered landed:
  5.
- Non-blocking or adjacent findings: 4.
- Verification evidence inherited from `ops/REVIEW_OPS.md`: the focused venv
  subset passed with 29 tests in 1.24s, and a broader focused subset reported
  38 tests passing in 2.29s. The ledger pass did not rerun tests.

## Sub-Agent Help Used

The operator requested the maximal useful sub-agent or parallel-worker help.
This ledger used four read-only explorer sub-agents with disjoint scopes:

- Domain extraction: read `domain/REVIEW_DOMAIN.md` and extracted the domain
  gate, geometric assumptions, and the closed-body winding caveat.
- Traceability extraction: read `traceability/REVIEW_TRACEABILITY.md` and
  extracted the RFC 0004 deferral map, acceptance-criteria coverage, and
  traceability findings.
- Ops extraction: read `ops/REVIEW_OPS.md` and extracted serialization, CLI,
  diagnostics, readiness, and test findings.
- Consistency check: read all three review artifacts plus the ledger prompt and
  reported duplicate clusters, apparent conflicts, safe-now scope, and deferred
  scope.

All sub-agents were read-only. None called `striatum`, edited project files,
published artifacts, completed the job, pushed branches, or updated
`OPERATOR_REPORT.md`.

## Consolidated Result

The workflow can proceed with findings. RFC 0028 cleanly closes the four RFC
0004 deferrals at the design level:

- Exact endpoint area for plumb stems maps to RFC 0028 AC3 and AC4.
- Independent bow/stern rake maps to AC1 and AC5.
- Coordinate and sign conventions map to AC2.
- Closed-body ownership and open-surface readiness boundaries map to AC6 and
  AC7.

No reviewer found a current path that labels generated open hull/deck STL
surfaces as watertight or `cfd_ready`. The remaining work is to implement and
test the safe plumb-stem closure slice without expanding the claim surface.

## Deduplicated Findings

### F-001: Workflow source list points at stale code paths

Severity: minor workflow hygiene.

`docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md` lists
`kayakgen/geometry/loft.py` and `kayakgen/mesh/diagnostics.py`, but the live
paths are `kayakgen/model/geometry.py` and `kayakgen/eval/mesh_diagnostics.py`.
This duplicates `TRACE-001` and `OPS-001`.

Required action: update the workflow source list before the next review cycle
so reviewers land on the active loft and diagnostics code.

### F-002: Independent `stern_rake` is not implemented in the model

Severity: functional blocker for RFC 0028.

RFC 0028 requires independent bow/stern rake while preserving legacy
`bow_rake` compatibility (`docs/rfcs/0028-plumb-stem-closure-semantics.md`
lines 67-80 and 124-125). Current `Hull` has only `bow_rake`
(`kayakgen/model/hull.py` line 43) and forbids unknown fields
(`kayakgen/model/hull.py` line 27), so JSON containing `stern_rake` is rejected.

Required action: add compatibility-preserving `stern_rake` validation and
round-trip tests. Legacy input containing only `bow_rake` must seed both ends
without changing geometry. If both `bow_rake` and `stern_rake` are supplied,
they must be independent.

### F-003: Mixed bow/stern rake is not represented in geometry

Severity: functional blocker for RFC 0028.

The loft still uses one symmetric scalar through `self.hull.bow_rake` and
`abs(x)`-based decay (`kayakgen/model/geometry.py` lines 131-164 and 246-279).
RFC 0028 requires mixed cases such as plumb bow plus raked stern to produce
asymmetric geometry without changing the default hull
(`docs/rfcs/0028-plumb-stem-closure-semantics.md` lines 132-133).

Required action: implement side-specific rake selection under the documented X
convention: bow at `x = -length_m / 2`, stern at `x = +length_m / 2`. Add tests
for the default hull, legacy symmetric behavior, explicitly symmetric behavior,
and mixed asymmetric behavior.

### F-004: Exact endpoint and cap semantics are still absent from generated bodies

Severity: functional blocker for RFC 0028.

RFC 0028 requires the generated closed-body path to keep non-zero terminal bow
and stern sections at exact plumb ends and cap them deterministically
(`docs/rfcs/0028-plumb-stem-closure-semantics.md` lines 82-103 and 128-131).
The current open loft intentionally collapses endpoints through
`_get_area_fraction()` and `_end_decay()` (`kayakgen/model/geometry.py` lines
122-153), and `mesh()` builds open strips without caps
(`kayakgen/model/geometry.py` lines 215-244). The existing test named
`test_plumb_section_at_end_has_nonzero_area` samples `-0.45 * L`, not the exact
endpoint (`tests/test_plumb_bow.py` lines 55-61).

Required action: implement endpoint section and cap behavior in the generated
closed-body builder, not by silently changing the open inspection mesh contract.
Add bow cap, stern cap, exact endpoint section, zero body-level boundary-edge,
positive signed-volume, and mixed-rake tests. Rename or clarify the existing
near-end test so it does not imply exact endpoint coverage.

### F-005: Closed-body winding and signed-volume handling must be explicit

Severity: functional blocker for the closed-body builder.

The domain review confirmed that the coordinate convention aligns with the
current implementation, but also flagged a construction hazard:
`LoftedHullGeometry.mesh()` emits current open hull faces with winding suitable
for inspection surfaces, not automatically for a closed positive-volume body.
The new builder must not inherit those windings blindly. RFC 0028 requires
stable cap ordering, outward normals, positive signed body volume, no
body-level boundary edges, and mirrored bow/stern cap orientation
(`docs/rfcs/0028-plumb-stem-closure-semantics.md` lines 96-102).

Required action: make face orientation an owned part of closed-body assembly.
Reverse or otherwise explicitly normalize the open hull surface winding as
needed, then verify positive signed volume and outward-facing normals.

### F-006: Coordinate conventions and user-facing rake wording need explicit pins

Severity: required documentation and test coverage.

RFC 0028 now pins X increasing bow-to-stern, bow at `-L/2`, stern at `+L/2`,
Z upward, implicit port/starboard symmetry, and rake as dimensionless fullness
in `[0, 1]` (`docs/rfcs/0028-plumb-stem-closure-semantics.md` lines 46-66).
The current implementation matches those conventions, but they are mostly
implicit in code and tests. The user guide lists only `bow_rake`
(`docs/USER_GUIDE.md` lines 52-55) and does not explain `stern_rake`, the
coordinate convention, or the historical symmetric meaning of `bow_rake`.

Required action: add docs and tests that pin bow/stern coordinate direction,
cap winding, and signed-volume expectations. Update user-facing wording for
`stern_rake` and preserve the existing caveats that generated packages are open
surfaces and not `cfd_ready` (`docs/USER_GUIDE.md` lines 194-198, 240-242, and
342-347).

### F-007: Open-surface readiness boundaries are mostly correct, but finite bad meshes can still read as `stl_surface`

Severity: adjacent readiness correctness gap.

The positive readiness check is important: no review found a current generated
open hull/deck path that claims watertight or `cfd_ready`. The code also states
that synthetic closed-volume diagnostics do not build generated closed bodies
or promote `cfd_ready` (`kayakgen/eval/closed_volume.py` lines 1-5). However,
`_readiness()` records degenerate and non-manifold reasons but still returns
`stl_surface` whenever values are finite (`kayakgen/eval/mesh_diagnostics.py`
lines 240-267). RFC 0010 defines `stl_surface` as finite and nondegenerate.

Required action: add finite degenerate-only and finite nonmanifold-only tests.
Then either demote those cases below `stl_surface` or explicitly document that
the current readiness level is weaker than RFC 0010's stricter wording. This is
adjacent to plumb-stem closure and should not be used to expand RFC 0028 into a
full readiness overhaul.

### F-008: CLI watertight-profile failure details are discoverable only in the manifest

Severity: non-blocking UX improvement.

`kayakgen mesh-package --solver-profile watertight-solid` correctly keeps
current packages at `stl_surface`, and tests assert a manifest warning for
separate open surfaces (`tests/test_cli.py` lines 151-173). CLI stdout prints
only the manifest path and readiness level (`kayakgen/cli/main.py` line 129),
so users must inspect JSON for why the watertight profile did not pass.

Required action: consider echoing concise warning lines for non-ready
watertight profiles. This is not a blocker because the manifest and tests
already preserve the readiness gate.

### F-009: RFC traceability and editorial cleanup remain

Severity: non-blocking traceability cleanup.

The reviews disagree only in emphasis: the domain review says RFC text changes
are not required, while traceability recommends editorial pins. The ledger
classifies those as useful but non-blocking:

- `docs/rfcs/0004-plumb-bow.md` lines 155-158 still say asymmetric rake is
  deferred to RFC 0006, but RFC 0028 is now the actual successor.
- RFC 0028 acceptance criteria define the required behavior but do not name
  expected test modules or fixtures.
- RFC 0028's open question about applying endpoint area below a threshold
  (`docs/rfcs/0028-plumb-stem-closure-semantics.md` lines 144-146) should be
  hardened to exact `rake == 0.0` semantics or removed as decided.
- The default golden geometry pin in `tests/test_plumb_bow.py` lines 23-30
  should be reaffirmed after adding `stern_rake` defaults.

Required action: handle these as traceability notes when RFC 0028 lands. They
do not block implementation if the tests and docs pin the behavior directly.

## Safe-Now Implementation Slice

The safe plumb-stem closure work is:

1. Add `stern_rake` to `Hull` with `[0, 1]` validation while preserving legacy
   `bow_rake`-only JSON and programmatic inputs as symmetric rake.
2. Keep `bow_rake` as the compatibility field. If only `bow_rake` is supplied,
   seed both bow and stern. If both fields are supplied, respect them
   independently.
3. Add side-specific rake selection in the loft using the existing X convention,
   with no default geometry change.
4. Implement exact non-zero terminal sections only for `rake == 0.0` in the
   generated closed-body path.
5. Build deterministic bow and stern cap polygons in the closed-body builder,
   with no duplicate ring vertices except an intentional fan center if used.
6. Explicitly manage surface and cap winding during closed-body assembly, then
   test positive signed volume, outward normals, and zero body-level boundary
   edges.
7. Preserve the existing open hull/deck STL inspection surfaces and their
   labels unless a closed-body command or profile is explicitly selected.
8. Keep diagnostics, not rake settings, as the only source of closed-volume or
   watertight-readiness claims.
9. Add focused tests for legacy round-trip behavior, default golden geometry,
   symmetric legacy geometry, mixed plumb-bow/raked-stern geometry, endpoint
   bow/stern sections, cap winding, signed volume, and readiness boundaries.
10. Update user-facing documentation for `stern_rake`, the coordinate
    convention, and the historical symmetric meaning of `bow_rake`.

## Future or Deferred Scope

Keep the following out of the immediate plumb-stem closure implementation:

- Manufacturing stem thickness or production-export solid modeling.
- Reverse rake or values outside `[0, 1]`.
- New flare, tumblehome, multi-chine, rocker expansion, or broader hull-form
  controls.
- Applying exact non-zero endpoint semantics to arbitrary low rake thresholds
  such as `rake < 0.05`; this workflow should use exact `rake == 0.0`.
- Full solver-readiness or `cfd_ready` claims for generated bodies.
- General CFD-quality guarantees beyond diagnostics-backed mesh metadata.
- Replacing existing hull/deck inspection STL surfaces.
- CLI warning verbosity improvements, unless chosen as a small UX follow-up.
- A broad RFC 0010 readiness overhaul for finite degenerate or non-manifold
  meshes, unless that cleanup is explicitly assigned.

## Recommendation

Proceed with recorded findings. The implementation path should stay narrow:
model and serialize independent rake, make geometry side-specific, build exact
plumb endpoint caps only in the generated closed-body path, and strengthen
tests/docs around winding and readiness. Do not convert this workflow into
manufacturing geometry, new hull-form controls, or solver-readiness promotion.
