# Operator report - workflow 0033

Updated: 2026-05-13

## Current state

- Scaffolded for RFC 0022 generated hull-plus-deck closed-body construction.
- Suggested branch: `striatum/0033-generated-closed-body-construction`.
- Implementation must use three review lanes before coding:
  traceability, domain geometry, and ops/test.
- Scope is limited to generated closed-body construction and diagnostics for
  evaluation readiness.
- This workflow must keep display STL output separate and must not promote any
  generated body to `cfd_ready`.
- Findings ledger has been written locally at
  `striatum/0033-generated-closed-body-construction/ledger/FINDINGS.md`.
- Ledger verdict intent is `accept_with_findings`.

## Findings recorded

- Consolidated review findings require workflow metadata repair before
  implementation: `SOURCES.md` and `workflow.json` still reference
  `kayakgen/geometry/lofted_hull.py`, `kayakgen/domain/hull.py`, and
  `tests/test_geometry.py`; the live paths are `kayakgen/model/geometry.py`,
  `kayakgen/model/hull.py`, and `tests/test_geometry_lofted.py`. The
  implementation write scope also needs `kayakgen/model/`.
- The conservative implementation slice is RFC 0022 generated closed-body
  construction only: deterministic `generated_hull_plus_deck_closed_body_v1`
  from `Hull`, explicit bow/stern caps, plumb endpoint handling,
  topside/sheerline/deck joins for `beam_wl_m != beam_oa_m`, waterline
  metadata, outward normals, positive signed volume, serialized tolerances,
  RFC 0016/RFC 0021 diagnostics, and generated-body acceptance tests.
- Display STL and mesh-package outputs must remain separate open
  inspection/export artifacts.
- Explicitly deferred: solver-specific meshing, volume meshing,
  `watertight_solid_resistance_v1`, any `cfd_ready` promotion, high-angle
  stability physics, resistance validation, geometry repair, cockpit/flooding
  models, and asymmetric bow/stern controls.
- Ledger used four read-only sub-agents for independent extraction and
  consistency checks: traceability, domain geometry, ops/test, and cross-review
  wording/deferral consistency.

## Next action

- Operator should mechanically validate the ledger artifact, repair or
  authorize repair of the stale workflow metadata/write scope, then publish the
  ledger and complete the findings job before implementation starts.
