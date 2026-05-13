author: operator [self-declared: operator-ops-review]

# Ops review - equilibrium implementation shape

Verdict intent: accept_with_findings

## Findings

### O-001 - Equilibrium belongs in stability, not hydrostatics callers

The existing hydrostatics evaluator is the integrated-geometry primitive. The
load-case logic, convergence policy, and warnings belong in
`kayakgen.eval.stability` so existing hydrostatics tests and callers remain
stable.

Required action: add a stability-layer equilibrium function that evaluates
temporary draft-adjusted hull copies and leaves the public hydrostatics default
unchanged unless a narrow helper is justified.

### O-002 - Bounded bisection is sufficient for sinkage

For the current parameterization, displaced mass is monotonic with draft over a
reasonable positive interval. A deterministic bisection avoids new dependencies
and gives repeatable tolerance behavior.

Required action: use bounded bisection with configurable tolerance and max
iterations, and return a non-converged result instead of raising for ordinary
out-of-bracket loads.

### O-003 - CLI should preserve the default command behavior

Existing tests expect `kayakgen stability hull.json` to write a
`design_waterline_initial` result. A new equilibrium mode should be additive.

Required action: add `--equilibrium` and optional tolerance/iteration flags, or
equivalent explicit mode selection, without changing the default.

### O-004 - Tests must cover equilibrium truthfulness

Current tests cover load-case round trip, KG references, GM0 monotonicity, and
GZ deferral. They do not cover equilibrium convergence, waterline KG at changed
draft, CLI mode selection, or too-heavy failure behavior.

Required action: add focused tests for equilibrium convergence within tolerance,
warnings/method/status, KG normalization at equilibrium draft, CLI output, and a
non-converged bracket failure.

### O-005 - Avoid geometry golden churn

Equilibrium can be implemented by changing the draft input on copied hulls. It
does not require changing the loft, STL writer, waterplane tests, or existing
golden hydrostatics values.

Required action: keep geometry and hydrostatics goldens unchanged unless a test
proves a local helper is needed.
