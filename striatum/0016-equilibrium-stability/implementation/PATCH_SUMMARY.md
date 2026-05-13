author: operator [self-declared: operator-implementer]

# Patch summary - 0016 equilibrium stability

## Files changed

- `kayakgen/eval/contract.py`
- `kayakgen/eval/stability.py`
- `kayakgen/cli/main.py`
- `tests/test_stability.py`
- `tests/test_cli.py`
- `docs/rfcs/0011-hydrostatic-stability-load-cases.md`
- `docs/rfcs/README.md`
- `docs/workflows/0016-equilibrium-stability/OPERATOR_REPORT.md`
- `docs/workflows/0016-equilibrium-stability/prompts/final_review.md`

## Findings addressed

- F-001: added additive equilibrium stability evaluator and CLI flag while
  preserving design-waterline default behavior.
- F-002: extended `StabilityResult` with equilibrium method/status, draft,
  sinkage, trim assumption, tolerance, and iteration fields.
- F-003: kept generalized trim explicitly deferred; equilibrium mode reports
  zero trim only under the centered/symmetric-load assumption.
- F-004: waterline-relative KG references are normalized against solved
  equilibrium draft.
- F-005: equilibrium mass balance uses `LoadCase.seawater_density_kg_m3`.
- F-006: bisection is bounded and returns `not_converged` for out-of-bracket
  loads.
- F-007: RFC 0011 and the RFC index now describe the landed
  equilibrium-sinkage slice.

## Verification

- `.venv/bin/python -m pytest tests/test_stability.py tests/test_cli.py -q`
  -> 20 passed.
- `.venv/bin/python -m pytest -q` -> 121 passed.
- `git diff --check` -> clean.
- `ruff` was not run because it is not installed in the current virtualenv.
