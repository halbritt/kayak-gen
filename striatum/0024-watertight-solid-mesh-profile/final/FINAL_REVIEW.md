# Final review - watertight solid mesh profile

author: operator [self-declared: operator-final-review]
run: run_877488bcf83244479df1d95d7b420a65
job: final_review
date: 2026-05-13
verdict: accept

## Review result

Accept.

The implementation matches the ledger: a named watertight-required profile
exists, current generated packages remain below `cfd_ready`, and no geometry
closure or solver dispatch was introduced.

## Coverage

| Finding | Evidence |
|---|---|
| F-001 named watertight profile | `watertight_solid_profile()` emits `watertight_solid_resistance_v1` with `requires_watertight=True`. |
| F-002 blocked current packages | Watertight-selected packages return `stl_surface` with boundary/open-surface blockers. |
| F-003 profile selection | `kayakgen mesh-package --solver-profile watertight-solid` writes a selected-profile manifest. |
| F-004 docs/status | RFC 0010, RFC 0015, and the RFC index describe the profile boundary without claiming watertight geometry. |
| F-005 defer end caps/closure | No mesh generation code or geometry goldens changed. |
| F-006 defer dispatch | No CFD job or adapter code added. |

## Verification

- `.venv/bin/python -m pytest tests/test_mesh_package.py tests/test_mesh_diagnostics.py tests/test_cli.py -q`
  -> 23 passed.
- `.venv/bin/python -m pytest -q` -> 150 passed.
- `striatum --repo . doctor` -> clean.
- `git diff --check` -> clean.

## Residual findings

- The project still needs a future geometry workflow for actual closed
  hull/deck solids, end caps, and `cfd_ready` success.
- Workflow 0025 can proceed with dispatch models and should treat
  `watertight_solid_resistance_v1` as a readiness gate, not a currently
  satisfiable profile.

## Next workflow

Proceed to workflow 0025, CFD solver dispatch and jobs, after this branch is
committed, pushed, and fast-forwarded to `main`.
