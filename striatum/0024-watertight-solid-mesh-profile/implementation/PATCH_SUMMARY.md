# Patch summary - watertight solid mesh profile

author: operator [self-declared: operator-implementer]
run: run_877488bcf83244479df1d95d7b420a65
job: implement_findings
date: 2026-05-13

## Scope implemented

- Added `watertight_solid_profile()` with stable profile name
  `watertight_solid_resistance_v1`.
- Preserved the default `open_wetted_surface_resistance_v1` package behavior.
- Made watertight-selected packages remain below `cfd_ready` with explicit
  blocked reasons for boundary edges, lack of a closed combined hull/deck
  volume, and separate open surfaces.
- Added `kayakgen mesh-package --solver-profile watertight-solid`.
- Added focused tests for the profile fields, package readiness, and CLI
  selected-profile manifest output.
- Updated RFC 0010, RFC 0015, and the RFC index to describe the profile
  boundary without claiming watertight geometry.

## Scope intentionally not implemented

- No end caps were generated.
- No combined hull/deck solid writer was added.
- No current generated package can emit `cfd_ready` under the watertight
  profile.
- No solver dispatch or adapter code was added.

## Sub-agent use

No implementation sub-agents were spawned. The accepted patch had one tightly
coupled integration surface across profile construction, package readiness,
CLI selection, and focused tests; splitting it would not have produced useful
disjoint write scopes.

## Verification

- `.venv/bin/python -m pytest tests/test_mesh_package.py tests/test_mesh_diagnostics.py tests/test_cli.py -q`
  -> 23 passed.
- `.venv/bin/python -m pytest -q` -> 150 passed.
- `striatum --repo . doctor` -> clean.
- `git diff --check` -> clean.
