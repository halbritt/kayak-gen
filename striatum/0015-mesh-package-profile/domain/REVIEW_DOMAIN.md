# Domain review - 0015 mesh package and profile

author: operator [self-declared: operator-domain-review]
run: run_4c00d3da5e7a4420ad44067406bdc27e
job: review_domain
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### D-001 - Open wetted-surface profile must not imply watertight readiness

- Severity: high
- File(s): `kayakgen/eval/mesh_diagnostics.py`, future manifest code
- Statement: The first target profile does not require a complete deck or capped
  hull/deck solid. It should not use global `cfd_ready` semantics intended for
  watertight volume or closed-surface solvers.
- Required action: Name the profile explicitly, keep readiness at
  `cfd_surface_candidate` or lower for open packages, and preserve warnings for
  boundary/open-surface conditions.

### D-002 - Coordinate convention belongs in manifest metadata

- Severity: high
- File(s): future manifest code
- Statement: Human decisions established `+x` stern and `-x` bow. Future CFD
  workers need that convention in machine-readable package metadata.
- Required action: Include coordinate-system fields that state stern-positive
  longitudinal x, port/starboard y, up-positive z, and `waterline_z_m = 0.0`.

### D-003 - Package readiness should aggregate part diagnostics conservatively

- Severity: high
- File(s): future package code
- Statement: A mesh package with hull/deck reports must not be more ready than
  its diagnostics justify. Boundary/nonmanifold/degenerate/nonfinite issues must
  remain visible at the package level.
- Required action: Aggregate per-part diagnostics into manifest warnings and a
  conservative package readiness label.

### D-004 - Watertight solid profile remains future work

- Severity: medium
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`, future package code
- Statement: The queue explicitly reserves watertight solid checks for a future
  profile. This workflow should not infer capping or closed-volume semantics.
- Required action: Document watertight solid profile as deferred and avoid any
  `requires_watertight=True` package readiness pass.

## Recommendation

Proceed with an open-surface package profile and conservative manifest
readiness. Do not implement solver dispatch or watertight solid semantics.
