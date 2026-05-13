author: operator [self-declared: operator-final-review]

# Final review - 0016 equilibrium stability

Verdict: accept

## Coverage

| Finding | Evidence | Result |
| --- | --- | --- |
| F-001 equilibrium mode missing | `evaluate_equilibrium_stability()` and `kayakgen stability --equilibrium` added | Pass |
| F-002 result provenance missing | `StabilityResult` now includes method/status, draft, sinkage, trim, tolerance, and iterations | Pass |
| F-003 generalized trim under-specified | Method is `equilibrium_sinkage`; warning `generalized_trim_not_implemented`; no generalized trim claim | Pass |
| F-004 KG draft normalization | Equilibrium evaluator normalizes KG using solved draft; test covers waterline reference | Pass |
| F-005 load-case density | Equilibrium mass comparison uses `LoadCase.seawater_density_kg_m3` | Pass |
| F-006 bounded convergence | Bisection is bounded; out-of-bracket loads return `not_converged` | Pass |
| F-007 status/docs | RFC 0011 and RFC index describe `landed-equilibrium-sinkage` | Pass |

## Verification

- `.venv/bin/python -m pytest tests/test_stability.py tests/test_cli.py -q`
  -> 20 passed.
- `.venv/bin/python -m pytest -q` -> 121 passed.
- `git diff --check` -> clean.
- `ruff` was not run because it is not installed in the current virtualenv.

## Final gate

Accepted. The workflow lands a conservative sinkage-equilibrium stability mode
and preserves design-waterline diagnostics. It does not claim high-angle GZ or
generalized trim; both remain future work.
