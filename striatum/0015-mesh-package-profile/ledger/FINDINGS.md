# Findings ledger - 0015

author: operator [self-declared: operator-ledger]
run: run_4c00d3da5e7a4420ad44067406bdc27e
job: findings_ledger
date: 2026-05-13

## Gate result

Proceed with a focused mesh-package implementation. The safe slice is a
deterministic `kayakgen mesh-package` CLI plus manifest/package writer for the
first open wetted-surface profile. Keep current generated surfaces below
watertight `cfd_ready`; do not add solver dispatch, volume meshing, or geometry
changes.

## Stats

- Source findings: 12
- Deduplicated findings: 6
- By severity: high 5 / medium 1
- Actionable now: 6

## Findings

### F-001 - `mesh-package` CLI is missing

- Sources: T-001, O-002
- Severity: high
- Classification: actionable-now
- File(s): `kayakgen/cli/main.py`, `tests/test_cli.py`
- Statement: RFC 0010 requires `kayakgen mesh-package hull.json --out
  mesh-package/`, but only `mesh-check` exists.
- Required remediation: Add a `mesh-package` command that writes stable package
  artifacts and returns non-zero for invalid part/profile inputs.

### F-002 - Mesh package manifest model and writer are missing

- Sources: T-002, O-001
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/eval/mesh_package.py`
- Statement: There is no `MeshPackageManifest` model, package writer, relative
  artifact path contract, or manifest serializer.
- Required remediation: Add Pydantic manifest models and `write_mesh_package`
  that writes `manifest.json`, `hull.json`, `quality.hull.json`,
  `quality.deck.json`, `hull.stl`, and `deck.stl`.

### F-003 - Open wetted-surface solver profile must be explicit

- Sources: T-003, D-001, D-004
- Severity: high
- Classification: actionable-now
- File(s): `kayakgen/eval/mesh_diagnostics.py`, new
  `kayakgen/eval/mesh_package.py`
- Statement: Human decisions selected an open wetted-surface resistance profile,
  but current diagnostics always have `solver_profile=None`.
- Required remediation: Add a named open wetted-surface profile with
  `requires_watertight=False` and expose it in the package manifest without
  claiming watertight solid readiness.

### F-004 - Manifest needs coordinate and waterline metadata

- Sources: D-002, T-002
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/eval/mesh_package.py`
- Statement: Future solver workers need machine-readable coordinates:
  stern-positive x, bow-negative x, port/starboard y, up-positive z, and
  `waterline_z_m = 0.0`.
- Required remediation: Include coordinate-system metadata and units in the
  manifest.

### F-005 - Package readiness must aggregate diagnostics conservatively

- Sources: D-003
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/eval/mesh_package.py`, tests
- Statement: Package readiness must not exceed the quality reports. Boundary,
  nonmanifold, degenerate, or nonfinite issues must remain visible.
- Required remediation: Aggregate hull/deck diagnostics into manifest readiness
  and warnings. Current packages should be `cfd_surface_candidate` at most for
  the open profile and never watertight `cfd_ready`.

### F-006 - RFC status should reflect the landed package/profile slice

- Sources: T-004
- Severity: medium
- Classification: actionable-now
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`, `docs/rfcs/README.md`
- Statement: RFC 0010 is currently `proposed`. If this workflow lands the
  package/profile slice, status should say so while solver dispatch and
  watertight solid readiness stay future.
- Required remediation: Update RFC 0010 and the RFC index after implementation.

## Implementation guidance

Safe now:

- Add `kayakgen/eval/mesh_package.py` with manifest models and
  `write_mesh_package`.
- Add a named open wetted-surface profile with `requires_watertight=False`.
- Add `kayakgen mesh-package hull.json --out mesh-package/`.
- Write deterministic package files: `manifest.json`, `hull.json`,
  `quality.hull.json`, `quality.deck.json`, `hull.stl`, and `deck.stl`.
- Add tests for manifest metadata, relative paths, quality reports, STL files,
  conservative readiness, and CLI behavior.
- Update RFC 0010 and the RFC index status/note.

Do not implement:

- Watertight solid readiness.
- Solver dispatch or external CFD integration.
- Volume mesh generation.
- Geometry/golden changes.
- New runtime dependencies.
