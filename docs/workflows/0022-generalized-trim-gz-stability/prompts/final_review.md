Review the completed generalized trim/GZ implementation and produce
`striatum/0022-generalized-trim-gz-stability/final/FINAL_REVIEW.md`.

Use:

- author line: `author: operator [self-declared: operator-final-review]`
- verdict
- coverage table mapping ledger findings to evidence
- verification commands and results
- final gate result

Accept only if:

- tests pass and `git diff --check` is clean;
- forward/aft load-position behavior is tested against the stated sign
  convention;
- trim results expose residuals, convergence status, iteration count, and
  warnings;
- existing compact load cases and current equilibrium-sinkage behavior remain
  compatible or have an accepted migration note;
- RFC/readme/operator-report artifacts accurately reflect what landed;
- unsupported high-angle GZ is unavailable with a clear reason rather than
  placeholder curves.
