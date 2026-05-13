author: operator [self-declared: operator-final-review]

# Final review - 0022 generalized trim and GZ stability

Run id: `run_4c71cf541cdf43d693cb7cda9258954e`  
Job: `final_review`  
Verdict: `accept`

## Coverage

| Finding | Evidence | Result |
| --- | --- | --- |
| F-001 compatible longitudinal components | `LongitudinalLoadComponent` and `LoadCase` normalization helpers landed in `kayakgen/eval/contract.py`, with compact and component round-trip tests. | Accepted |
| F-002 additive trim result fields/sign | `StabilityResult` adds draft-at-midship, load LCG, buoyancy LCB, moment residual/tolerance, and preserves existing fields; tests assert forward LCG gives negative bow-down trim and aft LCG gives positive stern-down trim. | Accepted |
| F-003 bounded upright trim equilibrium | `kayakgen/eval/stability.py` implements a bounded fixed-body station-area trim slice for explicit component loads, with convergence, max-iteration, and out-of-bracket tests. | Accepted |
| F-004 CLI/sweep summaries | CLI supports `--moment-tolerance-kg-m`; opt-in sweep stability summaries and comparison defaults cover trim/stability fields without changing old defaults. | Accepted |
| F-005 GZ boundary | `evaluate_gz_curve` still raises and tests assert the `closed_volume_body_not_defined` boundary; no real GZ values are emitted. | Accepted |
| F-006 precise status docs | RFC 0011, RFC 0014, the RFC index, and the operator report describe the partial trim slice and preserve high-angle GZ/closed-volume deferrals. | Accepted |

## Verification

- `.venv/bin/python -m pytest tests/test_stability.py tests/test_cli.py tests/test_sweep.py tests/test_compare.py -q`
  passed: 44 tests.
- `.venv/bin/python -m pytest -q` passed: 147 tests.
- `git diff --check` passed.
- `striatum --repo . doctor` passed with zero problems after refreshing the
  project Claude/Codex skill bundles and Codex plugin bundle.
- `.venv/bin/python -m ruff check .` was not run because `ruff` is not
  installed in the project virtualenv.

## Gate Result

The workflow accepts a partial RFC 0014 trim slice. The implementation is
truthful about its model: explicit longitudinal component loads can use bounded
upright trim equilibrium on the current hull shape; compact legacy load cases
retain the centered sinkage-equilibrium behavior; and high-angle GZ remains
unavailable until a named closed-volume body is accepted.

Remaining deferred work is correctly documented: high-angle righting-arm
curves, closed-volume body selection, heel spacing, fixed/moving paddler-CG
behavior, validation against measured data, watertight solid readiness, solver
dispatch, and optimizer behavior.
