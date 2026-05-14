---
schema_version: "striatum.patch_summary.v1"
artifact_kind: "patch_summary"
---

author: implementer-codex-gpt-5.5-001
date: 2026-05-14
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_cd01a74e1bcd4958ba6d99f033520006
job: job_run_c6989300a86c4c6cb66e44555bb19067_implement_openfoam_skeleton
lease: lease_c6d729b46c0c42348ff2339d4d980b67

# Patch Summary - OpenFOAM Adapter Skeleton

## Scope

Implemented the RFC 0041 / D004 first external-solver skeleton for
OpenFOAM.com OpenFOAM-v2512 `interFoam` without enabling a real solver success
path and without requiring OpenFOAM in CI.

## Files Changed

- `kayakgen/eval/cfd/jobs.py`
- `kayakgen/eval/cfd/__init__.py`
- `tests/test_cfd_jobs.py`
- `tests/fixtures/openfoam/force.dat`

## What Landed

- Added built-in solver profile `openfoam-v2512-interfoam-local` with:
  `adapter_name="openfoam_local"`, required mesh profile
  `watertight_solid_resistance_v1`, readiness `cfd_ready`, version command
  `foamVersion`, required version marker `v2512`, case-template version
  `openfoam-v2512-interfoam-dtchull-v1`, expected raw output
  `postProcessing/forces/0/force.dat`, platform/install notes, timeout cap,
  log-size cap, and raw/unvalidated claim metadata.
- Added deterministic OpenFOAM skeleton case rendering under
  `case/openfoam/`, including project-authored metadata JSON and minimal
  dictionary files. The renderer records mesh/package evidence refs, hashes,
  speed/fluid inputs, command provenance, expected raw outputs, limitations,
  and raw/unvalidated warnings.
- Added dependency/version probing and local fake-command execution handling:
  missing version command, version mismatch/failure, missing solver command,
  nonzero solver exit, timeout, missing `force.dat`, and malformed `force.dat`
  persist terminal `unavailable` or `failed` run records with stable
  `error_kind` values.
- Added capped log writing for OpenFOAM runs while preserving existing fixture
  command log behavior.
- Added a raw OpenFOAM `force.dat` parser and normalized raw models for parser
  fixtures and blocked local runs. Parsed force samples remain
  `raw_unvalidated`.
- Added an explicit `solver_success_blocked` failure state for parser-readable
  fake OpenFOAM output so this slice cannot accidentally introduce a real
  `succeeded` run record.
- Exported the OpenFOAM profile, parser, constants, and raw result models from
  `kayakgen.eval.cfd`.

## What Remains Deferred

- No real OpenFOAM `succeeded` path is enabled.
- No production OpenFOAM-readable volume-mesh evidence, boundary-layer meshing,
  Docker/container execution, hosted workers, calibrated CFD, final prediction,
  or design-fitness claim is added.
- Optional installed-solver smoke coverage remains future work behind an
  explicit environment flag and real binary availability.

## Validation

- `python -m py_compile kayakgen/eval/cfd/jobs.py kayakgen/eval/cfd/__init__.py`
- `python -m py_compile tests/test_cfd_jobs.py`
- `pytest tests/test_cfd_jobs.py` - 39 passed
- `python -m pytest tests/test_cfd_jobs.py tests/test_web.py` - 66 passed
- `git diff --check -- kayakgen/eval/cfd/jobs.py kayakgen/eval/cfd/__init__.py tests/test_cfd_jobs.py tests/fixtures/openfoam/force.dat`
- Import smoke:
  `from kayakgen.eval.cfd import OPENFOAM_PROFILE_NAME, solver_profile_by_name`
  returns `openfoam-v2512-interfoam-local openfoam_local raw_unvalidated`.

## Worktree Note

This shared worktree contains unrelated modified files and sibling
`striatum/0051-implementation-burndown-stage1/implementation/*` artifacts from
other implementation lanes. This patch only intentionally edits the files
listed above.
