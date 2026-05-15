---
schema_version: "striatum.patch_summary.v1"
artifact_kind: "patch_summary"
---

author: operator [self-declared: operator-0053-openfoam]
date: 2026-05-14
run: run_0053_stage2_openfoam_adapter
session: sess_7763ae15abe747dfaf7800abb8cdaf55
job: implement_openfoam_adapter
lease: openfoam_adapter_stage2

# Patch Summary - OpenFOAM Adapter Gate

## Scope

Published the RFC 0041 OpenFOAM-v2512 `interFoam` adapter gate summary for
the already-landed raw/unvalidated slice. This packet did not widen scope,
did not add a succeeded solver path, and did not change any runtime files.

## Files Changed

- `striatum/0053-implementation-burndown-stage2/implementation/openfoam_adapter/PATCH_SUMMARY.md`

## What Landed

- Confirmed the OpenFOAM profile contract in `kayakgen/eval/cfd/jobs.py`:
  `openfoam-v2512-interfoam-local`, `adapter_name="openfoam_local"`,
  `required_mesh_readiness="cfd_ready"`,
  `required_mesh_profile="watertight_solid_resistance_v1"`,
  `solver_version_command=["foamVersion"]`,
  `required_solver_version="v2512"`,
  deterministic case-template metadata, expected raw force output, timeout
  cap, and log-size cap.
- Confirmed deterministic OpenFOAM case rendering is present under
  `case/openfoam/` with project-authored metadata, command provenance, and
  raw/unvalidated warnings.
- Confirmed dependency and version probing persist stable `unavailable`
  records for missing commands, version mismatches, and version-check
  failures.
- Confirmed command execution persists stable `failed` records for nonzero
  exits, timeouts, missing `force.dat`, and malformed `force.dat`.
- Confirmed the parser fixture path stays raw/unvalidated and does not
  promote parser-readable output to a real succeeded solver record.
- Confirmed `tests/test_cfd_jobs.py` covers the OpenFOAM profile contract,
  deterministic case rendering, dependency gating, log caps, timeout
  handling, parser success from the checked-in fixture, and the
  forbidden-claim `solver_success_blocked` branch.

## What Remains Deferred

- No real OpenFOAM `succeeded` path is enabled.
- No production OpenFOAM-readable volume-mesh evidence, boundary-layer
  meshing, container execution, hosted workers, calibrated CFD, final
  prediction, or design-fitness claim is added.
- Optional installed-solver smoke coverage remains future work behind an
  explicit environment flag and a real solver binary.

## Validation

- `.venv/bin/pytest -q tests/test_cfd_jobs.py -k openfoam`
  - `13 passed in 9.63s`

## Worktree Note

- The current worktree already contained the OpenFOAM adapter implementation
  slice when this packet was published. This artifact records the accepted
  state without modifying the runtime code paths.
