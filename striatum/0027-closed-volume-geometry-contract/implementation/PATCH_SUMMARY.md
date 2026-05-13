author: operator [self-declared: operator-0027-implementer]

# Workflow 0027 Implementation Summary

## Scope

Implemented only the ledger-constrained safe slice. Generated hull-plus-deck
closed bodies, high-angle `GZ`, volume meshing, real CFD readiness, and any
`cfd_ready` handoff remain deferred.

## Changes

- Added `kayakgen.eval.closed_volume` with serializable explicit synthetic
  triangle-mesh closed-volume body, part, policy, tolerance, readiness, and
  diagnostic models.
- Added body-level diagnostics for raw and tolerance-welded boundary edges,
  raw and tolerance-welded nonmanifold edges, invalid indices, nonfinite data,
  degenerate faces, and positive signed volume with outward normals.
- Added tests for valid synthetic tetrahedron, open synthetic body,
  nonmanifold synthetic body, reversed orientation, and out-of-range indices.
- Hardened CFD dispatch so watertight solver profiles require profile-scoped
  closed-volume diagnostic evidence instead of trusting hand-edited manifest
  readiness.
- Added regressions for forged `cfd_ready` manifests and forged watertight
  quality-report evidence over current open-surface artifacts.
- Updated RFC 0016, the RFC index, the user guide, the changelog, and operator
  reports to document the safe slice and remaining deferrals.

## Verification

- `.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_cfd_jobs.py tests/test_mesh_package.py -q`
  -> 21 passed.

## Deferred

- Bow/stern cap construction, exact plumb endpoint handling, sheerline/deck
  join semantics including `beam_wl_m != beam_oa_m`, generated-body waterline
  semantics, and generated-body closure tolerances remain open policy work in
  RFC 0016.
