author: operator [self-declared: operator-0032-implementer]

# Patch Summary - Workflow 0032

## Findings addressed

- F-001/F-004: added serialized self-intersection status, algorithm identity,
  tolerance, pair count, and bounded example-pair evidence. The RFC 0021
  profile requires `passed`; `not_checked`, `failed`, and `inconclusive` block
  that profile.
- F-002/F-003: implemented assembled-body diagnostics using welded topology for
  adjacency, including cross-part failures and vertex-only pinch coverage.
- F-005: added deterministic broad-phase AABB filtering, stable pair ordering,
  full pair counts, and an eight-example serialization cap.
- F-006/F-008: preserved `never_claim_cfd_ready`, kept diagnostics explicit
  synthetic only, and added a regression proving a passed RFC 0021 diagnostic
  still cannot satisfy watertight `cfd_ready` dispatch.
- F-007: updated user/status/RFC documentation to describe status values,
  algorithm limits, tolerance semantics, bounded examples, and deferred repair,
  generated-body, volume-mesh, high-angle `GZ`, and solver-readiness work.

## Files changed

- `kayakgen/eval/closed_volume.py`
- `tests/test_closed_volume.py`
- `tests/test_cfd_jobs.py`
- `docs/USER_GUIDE.md`
- `docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md`
- `docs/rfcs/README.md`
- `docs/workflows/0032-closed-volume-self-intersection-diagnostics/OPERATOR_REPORT.md`
- `CHANGELOG.md`
- `striatum/0032-closed-volume-self-intersection-diagnostics/implementation/PATCH_SUMMARY.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -p no:cacheprovider tests/test_closed_volume.py tests/test_cfd_jobs.py -q`
  passed: 23 tests.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -p no:cacheprovider -q`
  passed: 175 tests.
- `git diff --check` passed.
- `git diff --check --no-index /dev/null striatum/0032-closed-volume-self-intersection-diagnostics/implementation/PATCH_SUMMARY.md`
  produced no whitespace diagnostics for the new patch-summary file.
