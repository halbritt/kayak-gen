# Patch summary - 0015

author: operator [self-declared: operator-implementer-temp]
run: run_4c00d3da5e7a4420ad44067406bdc27e
job: implement_findings
date: 2026-05-13

## Summary

Implemented the mesh package/profile slice from the 0015 findings ledger.
`kayakgen mesh-package` now writes a deterministic package directory containing
a manifest, hull JSON, hull/deck quality reports, and hull/deck STL surfaces.
The manifest exposes the first open wetted-surface profile and keeps current
packages below watertight `cfd_ready`.

## Findings addressed

- F-001: added `kayakgen mesh-package hull.json --out mesh-package/`.
- F-002: added `MeshPackageManifest`, coordinate metadata, and
  `write_mesh_package` in `kayakgen.eval.mesh_package`.
- F-003: added `open_wetted_surface_profile()` with
  `requires_watertight=False`.
- F-004: manifest records units, stern-positive coordinates, and waterline z.
- F-005: package readiness aggregates diagnostics conservatively and remains
  `cfd_surface_candidate` for the open profile.
- F-006: RFC 0010 and the RFC index now state that only the package/profile
  slice has landed.

## Files changed

- `kayakgen/eval/mesh_package.py`
- `kayakgen/cli/main.py`
- `tests/test_mesh_package.py`
- `tests/test_cli.py`
- `docs/rfcs/0010-cfd-ready-mesh-contract.md`
- `docs/rfcs/README.md`
- `docs/workflows/0015-mesh-package-profile/OPERATOR_REPORT.md`

## Verification

- `.venv/bin/python -m pytest tests/test_mesh_package.py tests/test_mesh_diagnostics.py tests/test_cli.py -q` -> 16 passed
- `.venv/bin/python -m pytest -q` -> 116 passed
- `git diff --check` -> clean
- `.venv/bin/ruff check kayakgen tests` -> not run; `ruff` is not installed in the current virtualenv
