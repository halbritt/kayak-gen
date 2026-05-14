author: implementer-codex-gpt-5.5-005
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_89f73288752044cca73135782e8dca5f
job: job_run_c6989300a86c4c6cb66e44555bb19067_implement_high_angle_v1
lease: lease_ae6cf8993ff9487d9c01ffa73cc45981
date: 2026-05-14

# Patch Summary - High-Angle Stability V1

## Scope

Implemented the workflow 0051 high-angle stability lane for RFC 0043's
fixed-upright-trim generated-body v1 evaluator slice. The change is limited to
`kayakgen/eval/stability.py`, `tests/test_stability.py`, and this
workflow-local artifact.

The implementation keeps all existing RFC 0024 generated-body gates. Real
generated-kayak `gz_m`, righting moment, and grid-bounded summary values are
emitted only after the generated `generated_hull_plus_deck_closed_body_v1`
body and matching diagnostics pass. Gate failures remain unavailable, with
empty curve arrays and `None` summaries.

## Changes

- Added a scoped `GeneratedBodyGZCurve` subtype and `GZHeelPointMetadata`
  records in `kayakgen/eval/stability.py`. This exposes per-heel status,
  sinkage, displaced mass, displacement residual, iteration count, fixed-trim
  longitudinal moment residual, clipping status, and point warnings to direct
  `evaluate_gz_curve()` callers.
- Implemented fixed-trim generated-body v1 heeled integration over generated
  body station rings using closed 2-D waterline clipping/capping and a per-heel
  sinkage/displacement bisection solve.
- Tightened v1 heel-grid handling to require finite, strictly increasing
  values within `0..90` degrees. The default remains `0, 5, ..., 90`, and
  caller-supplied grids are echoed exactly.
- Added grid-bounded summary semantics. `max_gz_m`, `heel_at_max_gz_deg`,
  range-positive, and area-under-positive summaries are derived only from the
  computed grid points.
- Added generated-body v1 assumptions and warnings for fixed upright trim,
  hull-fixed passive CG, sealed deck/no cockpit opening, deck immersion,
  flooding/downflooding not modeled, active paddler response not modeled, and
  no safety/seaworthiness claim.
- Preserved synthetic fixture behavior: explicit synthetic bodies still cannot
  satisfy real generated-kayak GZ gates, and fixture-only math remains labeled
  `fixture_only`.

## Contract Boundary Note

The canonical base `GZCurve` model lives in `kayakgen/eval/contract.py`, which
is outside this packet's write scope and forbids extra fields. This lane
therefore exposes per-heel metadata through a local `GZCurve` subtype returned
by `evaluate_gz_curve()` for generated-body v1 records. Direct evaluator calls
serialize the metadata, but canonical parent-model serialization through
`StabilityResult` remains a follow-up requiring contract write scope.

## Files Changed

- `kayakgen/eval/stability.py`
- `tests/test_stability.py`
- `striatum/0051-implementation-burndown-stage1/implementation/high_angle_v1/PATCH_SUMMARY.md`

## Validation

- `.venv/bin/python -m pytest tests/test_stability.py -q`
  - Result: 36 passed.
- `.venv/bin/python -m pytest tests/test_stability.py tests/test_generated_closed_body.py -q`
  - Result: 63 passed.
- `.venv/bin/python -m compileall -q kayakgen/eval/stability.py tests/test_stability.py`
  - Result: clean.
- `git diff --check -- kayakgen/eval/stability.py tests/test_stability.py`
  - Result: clean.
- `awk 'length($0) > 100 { ... }' kayakgen/eval/stability.py tests/test_stability.py`
  - Result: no lines over the configured 100-character limit.

Ruff was not run because `.venv/bin/python -m ruff check ...` failed with
`No module named ruff`.

## Sub-Agent Help Used

Popper performed read-only scope analysis and confirmed that canonical per-heel
metadata would require editing `kayakgen/eval/contract.py`, while a scoped
`GZCurve` subtype in `stability.py` can expose metadata to direct evaluator
callers inside the current write scope.

## Worktree Note

The shared worktree contains concurrent edits outside this packet's write
scope, including docs, CFD, calibration, volume-mesh, search, web, fixtures,
and operator-report paths. Those were not modified or reverted by this
high-angle stability lane.
