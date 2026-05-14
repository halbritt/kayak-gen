# Patch Summary - Workflow 0034 Watertight Volume Mesh Handoff

## Findings Addressed

- F-001: Added an explicit RFC 0023 watertight dispatch accept path for
  matching generated-body, self-intersection, volume-mesh diagnostic, artifact,
  profile, tolerance, and checksum evidence.
- F-002: Extended `MeshPackageManifest` with optional RFC 0023 traceability
  fields while preserving the existing open-surface manifest shape.
- F-003: Added typed volume-mesh diagnostic, artifact, readiness, reason, and
  checksum models with fixture-backed generated-body handoff helpers.
- F-004: Added package-local ref validation for manifest artifacts and
  checksum validation for every RFC 0023 diagnostic/handoff artifact ref.
- F-005: Added focused positive and negative tests for matching handoff,
  missing volume mesh, stale checksum, forbidden path refs, synthetic evidence,
  failed self-intersection, and evidence-sensitive job identity.
- F-006: Added CLI readiness reasons/blocker lines for `mesh-package` and a
  stable `blocker_class` line for `cfd prepare` failures.

## Files Changed

- `kayakgen/eval/volume_mesh.py`
- `kayakgen/eval/mesh_package.py`
- `kayakgen/eval/cfd/jobs.py`
- `kayakgen/cli/main.py`
- `tests/test_mesh_package.py`
- `tests/test_closed_volume.py`
- `tests/test_cfd_jobs.py`
- `tests/test_cli.py`
- `striatum/0034-watertight-volume-mesh-handoff/implementation/PATCH_SUMMARY.md`

## Verification

- `PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_mesh_package.py tests/test_cfd_jobs.py tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_cli.py`
  - Result: blocked in the base shell because `pytest` was not installed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_mesh_package.py tests/test_cfd_jobs.py tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_cli.py`
  - Result: blocked in the base shell because `pytest` was not installed.
- `python3 -m compileall -q kayakgen tests`
  - Result: passed.
- Temporary verification environment:
  - `python3 -m venv /tmp/kayakgen-0034-venv && /tmp/kayakgen-0034-venv/bin/pip install -q -e . pytest`
  - `PYTHONDONTWRITEBYTECODE=1 /tmp/kayakgen-0034-venv/bin/pytest -q -p no:cacheprovider tests/test_mesh_package.py tests/test_cfd_jobs.py tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_cli.py`
  - Result: `90 passed in 42.29s`.
- `git diff --check`
  - Result: passed.

## Residual Risks And Deferrals

- The positive `cfd_ready` path is fixture-backed volume-mesh evidence only; it
  does not integrate a production mesher or solver.
- CFD job/run/result semantics remain raw and unvalidated.
- Surface-only watertight solver readiness remains deferred.
- Open-surface packages, watertight packages without volume mesh, generated
  closed bodies without volume mesh, and explicit synthetic closed-volume
  fixtures remain below `cfd_ready`.
- The temporary virtualenv lives outside the worktree at
  `/tmp/kayakgen-0034-venv` and is not part of the patch.

## Proposed Root CHANGELOG.md Wording

```markdown
- Land RFC 0023 watertight volume-mesh handoff slice: add typed manifest,
  diagnostic, artifact, hash, and path-bound evidence records; preserve
  conservative open-surface behavior; allow `cfd_ready` only for matching
  generated-body fixture volume-mesh evidence; and surface structured CLI/JSON
  rejection reasons for missing, stale, synthetic, mismatched, and unsafe
  handoff evidence.
```
