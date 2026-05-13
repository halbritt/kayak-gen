author: operator [self-declared: operator-ledger]

# Findings ledger - 0022 generalized trim and GZ stability

Run id: `run_4c71cf541cdf43d693cb7cda9258954e`  
Job: `findings_ledger`  
Gate result: proceed to implementation with a partial trim-equilibrium slice

## Stats

- Source artifacts: 3
- Source findings: 17
- Deduplicated findings: 6
- By severity: high 3 / medium 3 / low 0
- Safe-now findings: 6
- Deferred findings: 5

## Deduplicated Findings

### F-001 - Add compatible longitudinal load components and normalization

- Sources: T-002, D-002, O-001
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/contract.py`, `kayakgen/eval/stability.py`,
  `tests/test_stability.py`
- Statement: Current `LoadCase` has compact mass/KG fields but no
  longitudinal component model. RFC 0014 requires componentized masses and
  positions while preserving legacy compact JSON and existing
  equilibrium-sinkage behavior.
- Required remediation: Add a `LongitudinalLoadComponent` value object and
  `LoadCase` normalization helpers. Preserve existing compact fields and
  round-trips. Normalize total mass, load LCG, and mass-weighted KG. Use named
  default assumptions for compact fields, reject invalid component masses or
  nonfinite positions, and keep zero total mass invalid.

### F-002 - Define additive trim result fields and sign convention

- Sources: T-003, D-001, D-003, D-005, O-001, O-003
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/contract.py`, `kayakgen/eval/stability.py`,
  `tests/test_stability.py`, `tests/test_cli.py`
- Statement: `StabilityResult` can report mass equilibrium but lacks load LCG,
  buoyancy LCB in signed meters, moment residual, moment tolerance, and an
  explicit trim-angle sign convention.
- Required remediation: Add optional/defaulted trim fields without removing or
  renaming existing fields. Define `trim_angle_deg > 0` as stern-down/bow-up
  and `trim_angle_deg < 0` as bow-down/stern-up. Keep `+x` stern/aft and
  `-x` bow/forward in docs/comments and tests. Preserve existing field names
  such as `equilibrium_draft_m`, `sinkage_m`, `trim_angle_deg`, `method`,
  `status`, and `warnings`.

### F-003 - Implement bounded upright trim equilibrium for explicit component loads

- Sources: T-003, D-003, D-004, D-005, O-002, O-005
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/stability.py`, `tests/test_stability.py`
- Statement: Extending the current draft-parameter bisection would falsely
  claim trim by changing hull shape rather than immersing a fixed body under a
  shifted/rotated waterplane. The safe implementation needs a named fixed-body
  upright trim integration and bounded solver, or it must explicitly defer
  nonzero trim.
- Required remediation: Implement a deterministic bounded solver against a
  named evaluation body based on station-area integration of the current hull
  shape under an upright trimmed waterplane. Report mass and moment residuals,
  tolerances, convergence status, iteration count, and warnings. Add tests for
  forward LCG producing negative/bow-down trim, aft LCG producing
  positive/stern-down trim, max-iteration non-convergence, and out-of-bracket
  mass/moment warnings. Keep centered compact-load behavior compatible.

### F-004 - Carry trim through CLI and opt-in sweep summaries

- Sources: T-004, O-003, O-004
- Severity: medium
- Classification: safe-now
- Files: `kayakgen/cli/main.py`, `kayakgen/search/sweep.py`,
  `tests/test_cli.py`, `tests/test_sweep.py`, `tests/test_compare.py`
- Statement: CLI stability JSON currently exposes only selected sinkage fields
  in tests, and sweeps do not evaluate or summarize stability even though
  comparison metrics already reference stability-like fields.
- Required remediation: Add CLI tests for stable default and equilibrium JSON
  fields. Add an opt-in sweep stability evaluator with default-compatible
  settings and deterministic summary fields for status, displacement error,
  trim angle, moment error, iteration count, and warnings. Preserve old sweep
  specs with defaults and keep CSV column names stable.

### F-005 - Keep high-angle GZ unavailable and expand only the unavailable boundary

- Sources: T-001, T-005, D-006, O-001, O-005
- Severity: medium
- Classification: safe-now
- Files: `kayakgen/eval/contract.py`, `kayakgen/eval/stability.py`,
  `tests/test_stability.py`, docs
- Statement: High-angle GZ cannot be safely implemented until a closed-volume
  body, heel angle spacing, and paddler-CG assumptions are accepted. Current
  behavior is safe because `evaluate_gz_curve` raises instead of emitting
  placeholders.
- Required remediation: Keep `evaluate_gz_curve` unavailable with a clearer
  named reason such as `closed_volume_body_not_defined`. Do not emit real
  `gz_curve` values. If the `GZCurve` model is touched, keep it additive and
  do not break strict readers without a deliberate schema decision.

### F-006 - Update RFC/readme/operator-report status precisely

- Sources: T-006
- Severity: medium
- Classification: safe-now
- Files: `docs/rfcs/0011-hydrostatic-stability-load-cases.md`,
  `docs/rfcs/0014-generalized-trim-and-gz-stability.md`,
  `docs/rfcs/README.md`,
  `docs/workflows/0022-generalized-trim-gz-stability/OPERATOR_REPORT.md`
- Statement: A successful workflow 0022 can land generalized upright trim
  equilibrium, but it will not complete high-angle GZ or closed-volume
  decisions.
- Required remediation: Update RFC 0011, RFC 0014, and the RFC index to name
  the exact landed trim slice. Preserve deferrals for high-angle GZ,
  closed-volume selection, heel range/spacing, paddler-CG behavior, and
  broader validation.

## Implementation Guidance

Safe now:

- Add `LongitudinalLoadComponent` and load-case normalization helpers.
- Add additive result fields for `load_lcg_m`, `buoyancy_lcb_m`,
  `moment_error_kg_m`, `moment_tolerance_kg_m`, and
  `draft_at_midship_m`/equivalent draft-at-midship semantics.
- Define `trim_angle_deg > 0` as stern-down/bow-up.
- Implement a bounded fixed-body upright trim integration/solver for explicit
  component loads. A station-area integration slice is acceptable for this
  workflow if the method name, assumptions, and warnings are explicit.
- Preserve existing centered compact-load sinkage behavior and JSON field
  names.
- Add focused stability, CLI, sweep, and comparison tests.
- Update RFC/status docs and this operator report.

Do not implement:

- High-angle `GZCurve` values, righting-arm curves, max-GZ, range-positive
  stability, heel spacing, or fixed/moving paddler-CG behavior.
- A CFD, watertight mesh, or hull-plus-deck closed-volume solution.
- A hidden unbounded nonlinear solver, optimizer, or expensive default sweep
  path.
- Breaking changes to existing compact `LoadCase`, `StabilityResult`, CLI, or
  sweep JSON without an accepted migration.
