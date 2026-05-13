author: operator [self-declared: operator-implementer]

# Patch summary - 0022 generalized trim and GZ stability

Run id: `run_4c71cf541cdf43d693cb7cda9258954e`  
Job: `implement_findings`

## Findings addressed

- F-001: added `LongitudinalLoadComponent` and compatible `LoadCase`
  normalization helpers for explicit component loads while preserving compact
  legacy load fields.
- F-002: added additive trim result fields for draft at midship, load LCG,
  buoyancy LCB, moment residual, moment tolerance, and the explicit
  `trim_angle_deg > 0` stern-down/bow-up convention.
- F-003: implemented a bounded fixed-body upright trim-equilibrium slice for
  explicit component load cases using station-area integration of the current
  hull shape under a trimmed waterplane.
- F-004: added CLI moment-tolerance support and opt-in sweep stability
  evaluation/summaries for trim status, displacement error, trim angle, moment
  error, iterations, and warnings.
- F-005: kept high-angle `GZCurve` unavailable and made the not-implemented
  boundary name `closed_volume_body_not_defined`.
- F-006: updated RFC 0011, RFC 0014, the RFC index, and the operator report to
  describe the landed partial trim slice without claiming high-angle GZ.

## Files changed

- `.claude/skills/striatum-*.md`
- `.codex/agents/striatum-*.md`
- `.striatum/plugins/codex/*`
- `docs/rfcs/0011-hydrostatic-stability-load-cases.md`
- `docs/rfcs/0014-generalized-trim-and-gz-stability.md`
- `docs/rfcs/README.md`
- `docs/workflows/0022-generalized-trim-gz-stability/OPERATOR_REPORT.md`
- `kayakgen/cli/main.py`
- `kayakgen/eval/contract.py`
- `kayakgen/eval/stability.py`
- `kayakgen/search/sweep.py`
- `tests/test_cli.py`
- `tests/test_compare.py`
- `tests/test_stability.py`
- `tests/test_sweep.py`

## Verification

- `.venv/bin/python -m pytest tests/test_stability.py tests/test_cli.py tests/test_sweep.py tests/test_compare.py -q`
  passed: 44 tests.
- `.venv/bin/python -m pytest -q` passed: 147 tests.
- `git diff --check` passed.
- `striatum --repo . doctor` passed with zero problems after refreshing the
  project Claude/Codex skill bundles and Codex plugin bundle.
- `.venv/bin/python -m ruff check .` was not run because `ruff` is not
  installed in the project virtualenv.

## Deferred

- High-angle `GZCurve` values, righting-arm curves, max-GZ, range-positive
  stability, heel spacing, and fixed/moving paddler-CG behavior remain
  deferred until a named closed-volume body is accepted and tested.
- Real solver dispatch, CFD, watertight solid readiness, and optimizer behavior
  remain out of scope.
