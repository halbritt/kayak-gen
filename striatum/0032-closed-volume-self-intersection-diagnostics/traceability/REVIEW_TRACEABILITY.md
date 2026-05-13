author: operator [self-declared: operator-0032-traceability]

# Workflow 0032 Traceability Review

Verdict intent: accept_with_findings

## Scope

This review maps RFC 0016 and RFC 0021 against the current closed-volume
diagnostics, tests, documentation, and deferral ledger. It verifies that the
self-intersection slice remains diagnostic-only: no generated hull-plus-deck
closed-body construction is implied, and no synthetic or generated body is
promoted to `cfd_ready`.

## Traceability Map

RFC 0016's safe slice is implemented as an explicit synthetic triangle-mesh
contract. `ClosedVolumeBody` is restricted to
`explicit_synthetic_triangle_mesh`; `ClosedVolumePolicy` records
`explicit_synthetic_closed_volume_v1`, metadata-only waterline semantics,
non-applicable cap/deck policies, outward positive signed volume, serialized
tolerances, and `never_claim_cfd_ready`. `ClosedVolumeDiagnostics` reports
body-level raw and welded boundary/nonmanifold edges, degenerate/nonfinite
geometry, signed volume, warnings, readiness, and `cfd_ready: false`.

RFC 0016 closure readiness is covered by `tests/test_closed_volume.py`: valid
tetrahedron serialization, open-body boundary rejection, nonmanifold rejection,
reversed-orientation rejection, and invalid face-index rejection. Dispatch
separation is covered by `tests/test_cfd_jobs.py`: watertight profile
preparation rejects current packages below `cfd_ready`, forged manifest
readiness, and forged quality-report evidence.

The docs and workflow ledger are aligned with that boundary. RFC 0016 says the
workflow 0027 safe slice must not claim generated hull-plus-deck closure or
`cfd_ready` handoff. The workflow 0027 operator report records the landed scope
as explicit synthetic contract models/diagnostics, forged watertight dispatch
rejection, and no generated closure or `cfd_ready` promotion. The user guide
describes generated mesh packages as open-surface artifacts and synthetic
closed-volume diagnostics as never building generated kayak closed bodies or
watertight solver handoffs.

RFC 0021 is not yet implemented in the current diagnostic model. The current
`ClosedVolumeDiagnostics` schema has no `self_intersection_status`,
`self_intersection_algorithm`, `self_intersection_tolerance_m`,
`self_intersection_pair_count`, or bounded triangle-pair examples. The current
tests do not include a deliberate self-intersecting closed synthetic body.
That is acceptable as pre-implementation state, but it is the core gap this
workflow must close.

Known deferrals remain explicit: generated hull-plus-deck closed-body
construction is RFC 0022 work; watertight volume-mesh and `cfd_ready` handoff
are RFC 0023 work; high-angle `GZ` generated-body handoff is RFC 0024 work;
real CFD adapters, calibrated drag, and final design fitness remain outside
this workflow. RFC 0004 plumb-stem/end-cap semantics also remain deferred and
must not be silently solved by this diagnostic slice.

## Findings

### T-001 - RFC 0021 needs a new self-intersection diagnostic record, not an implicit pass through the RFC 0016 profile

Current RFC 0016 diagnostics can report `closed_volume` for a valid synthetic
tetrahedron using only closure, nonmanifold, degeneracy, finiteness, and
positive signed-volume evidence. RFC 0021 changes the evidence required for
any new profile that adopts self-intersection diagnostics: a checked body must
serialize status, algorithm identity, tolerance, and pair count, and `failed`
or `inconclusive` must block readiness.

Required action: add explicit serialized self-intersection fields and a stable
policy/profile boundary. Existing RFC 0016 fixtures may remain honest under
the older `explicit_synthetic_closed_volume_v1` profile only if the diagnostic
record makes the absence of a self-intersection check explicit; any new RFC
0021 profile must require a successful check before reporting
`closed_volume`.

### T-002 - Self-intersection readiness must be body-level and cross-part

RFC 0016 already assembles parts before applying body-level closure and
manifold checks. RFC 0021 requires the same authority for self-intersection:
a crossing between triangles from different parts is a body failure even if
each part is locally manifold.

Required action: run self-intersection diagnostics on the assembled body,
preserve per-part summaries only as debugging context, and add tests for both
a valid non-self-intersecting synthetic body and a closed synthetic body with
a deliberate self-intersection. A detected or inconclusive result must block
the new closed-volume diagnostic profile.

### T-003 - The workflow must not construct generated closed bodies

RFC 0016 explicitly separates the synthetic safe slice from future generated
body construction. RFC 0021's non-goals repeat that generated hull-plus-deck
closed-body construction is out of scope, and the workflow 0032 operator
report limits scope to self-intersection diagnostics for explicit synthetic
closed bodies and future generated bodies. Current code has no generated
`Hull` to `ClosedVolumeBody` builder, which is the correct baseline.

Required action: keep workflow 0032 changes inside diagnostic schema,
algorithm, policy, and explicit synthetic fixtures. Do not add a generated
closed-body builder, do not reinterpret display STL overlap as physical-body
readiness, and do not relabel generated mesh packages as `closed_volume`.

### T-004 - Passing self-intersection diagnostics must not become `cfd_ready`

The current contract is strict: `ClosedVolumePolicy.cfd_readiness_policy` is
`never_claim_cfd_ready`, `ClosedVolumeDiagnostics.cfd_ready` is literally
`False`, `dispatch_evidence_satisfies_profile()` returns false for
`cfd_ready`, and dispatch tests reject forged watertight evidence. RFC 0021
says self-intersection success is necessary future evidence, not sufficient
solver-readiness evidence.

Required action: preserve the existing `cfd_ready` rejection semantics while
adding self-intersection diagnostics. A body that passes closure, signed
volume, and self-intersection checks may only satisfy the relevant
closed-volume diagnostic profile; solver-specific `cfd_ready` remains deferred
to RFC 0023 and later evidence gates.

### T-005 - Documentation must distinguish diagnostics from repair and solver readiness

RFC 0021 requires documentation to separate self-intersection diagnostics from
geometric repair and solver readiness. Current user-facing documentation
already makes the RFC 0016 synthetic boundary clear, but it does not yet
describe self-intersection status, algorithm limits, or ambiguous-case
behavior because those fields do not exist.

Required action: when the implementation lands, update status/user-facing
documentation to describe the self-intersection status values, recorded
tolerance and algorithm identity, bounded example reporting, and the rule that
`failed` or `inconclusive` blocks only the closed-volume diagnostic profile,
not by itself any future solver handoff.

## Checks

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_closed_volume.py tests/test_cfd_jobs.py -q` did not run because `.venv/bin/python` does not exist in this worktree.
- `python -m pytest --version` did not run because `python` is not installed on PATH.
- `python3 -m pytest --version` found Python 3.12.3 but no installed `pytest` module.

No Striatum publish, verdict, complete, block, or `.striatum` mutation command
was run.
