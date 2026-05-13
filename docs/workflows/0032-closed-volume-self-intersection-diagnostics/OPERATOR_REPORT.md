# Operator report - workflow 0032

Updated: 2026-05-13

## Current state

- Scaffolded for RFC 0021 closed-volume self-intersection diagnostics.
- Working branch:
  `striatum/0032-closed-volume-self-intersection-diagnostics`.
- Prepared Striatum run `run_04735e0767704843a93cb507c202231f`.
- The findings ledger session/lease was already claimed by the operator; no
  Striatum publish, verdict, complete, block, or `.striatum` mutation command
  was run during ledger consolidation.
- Read the workflow prompt, runbook, source index, RFCs 0004/0016/0021,
  workflow 0027 operator report, current closed-volume diagnostics/tests, and
  all three review artifacts:
  - traceability review: `accept_with_findings`;
  - domain review: `accept_with_findings`;
  - ops/test review: `accept_with_findings`.
- Consolidated review findings into an accepted diagnostic safe slice:
  serialized self-intersection evidence, assembled-body authority,
  conservative adjacency/tolerance policy, deterministic fixtures, bounded
  example reporting, documentation, and regression coverage.
- Scope remains diagnostics only. This workflow must not construct generated
  hull-plus-deck closed bodies, repair geometry, reinterpret display STL
  overlap as physical readiness, or promote generated hulls or synthetic
  diagnostics to `cfd_ready`.

## Findings recorded

- Ledger written to
  `striatum/0032-closed-volume-self-intersection-diagnostics/ledger/FINDINGS.md`
  by `operator-0032-ledger`.
- Gate result: `accept_with_findings` for the conservative RFC 0021 diagnostic
  safe slice.
- Accepted implementation scope:
  - add self-intersection status, algorithm identity, tolerance, pair count,
    and bounded example pairs to closed-volume diagnostics;
  - preserve RFC 0016 compatibility honestly with `not_checked`, while any new
    RFC 0021 profile requires `passed`;
  - run checks on the assembled body, including cross-part failures;
  - define conservative adjacency, vertex-only contact, coplanar,
    near-contact, and inconclusive semantics before readiness can pass;
  - add deterministic pass/fail/cross-part/blocking/performance/serialization
    and `cfd_ready` rejection tests;
  - document algorithm limits and distinguish diagnostics from repair and
    solver readiness.
- Explicitly deferred: generated hull-plus-deck closed-body construction,
  geometry repair, volume meshing, exact plumb-stem/end-cap policy resolution,
  high-angle `GZ` handoff, real CFD adapters, calibrated drag, final design
  fitness, validated solver output, and every `cfd_ready` promotion.

## Checks

- `git diff --check -- striatum/0032-closed-volume-self-intersection-diagnostics/ledger/FINDINGS.md docs/workflows/0032-closed-volume-self-intersection-diagnostics/OPERATOR_REPORT.md`
  passed for the tracked diff.
- `git diff --check --no-index /dev/null striatum/0032-closed-volume-self-intersection-diagnostics/ledger/FINDINGS.md`
  produced no whitespace diagnostics for the new untracked ledger file
  (expected nonzero no-index diff exit because the file is new).
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -p no:cacheprovider tests/test_closed_volume.py tests/test_cfd_jobs.py -q`
  passed: 23 tests.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -p no:cacheprovider -q`
  passed: 175 tests.
- `git diff --check` passed for the implementation diff.
- `git diff --check --no-index /dev/null striatum/0032-closed-volume-self-intersection-diagnostics/implementation/PATCH_SUMMARY.md`
  produced no whitespace diagnostics for the new patch-summary file.

## Next action

- Implemented the ledger's conservative RFC 0021 diagnostic slice without
  crossing the generated-body or `cfd_ready` boundaries.

## Implementation update

- Added serialized self-intersection fields to closed-volume diagnostics:
  status, algorithm identity, tolerance, pair count, and bounded example
  triangle-pair references.
- Preserved `explicit_synthetic_closed_volume_v1` as the RFC 0016 compatibility
  profile with `self_intersection_status: not_checked`.
- Added `explicit_synthetic_closed_volume_self_intersection_v1` for RFC 0021;
  its `closed_volume` readiness requires `self_intersection_status: passed`.
- Implemented the deterministic assembled-body checker
  `assembled_welded_aabb_triangle_pairs_v1` with welded-topology adjacency,
  vertex-fan handling for ordinary manifold vertices, blocking vertex-only
  pinches, failed non-adjacent contact/crossing, inconclusive near-contact, and
  eight capped example pairs.
- Added tests for valid RFC 0021 diagnostics, closed edge-manifold
  self-intersection failure, cross-part failure, vertex-only pinch failure,
  inconclusive near-contact blocking, example capping, broad-phase separated
  components, serialization gating, and continued watertight `cfd_ready`
  rejection.
- Updated `docs/USER_GUIDE.md`, RFC 0021, the RFC index, and `CHANGELOG.md` to
  describe the diagnostic status values, algorithm/tolerance semantics, bounded
  examples, and deferred repair/generated-body/solver-readiness work.
