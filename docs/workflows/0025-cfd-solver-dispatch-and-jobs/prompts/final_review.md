Review the completed CFD dispatch implementation and produce
`striatum/0025-cfd-solver-dispatch-and-jobs/final/FINAL_REVIEW.md`.

Use:

- author line: `author: operator [self-declared: operator-final-review]`
- verdict
- coverage table mapping ledger findings to evidence
- verification commands and results
- final gate result

Accept only if:

- tests pass and `git diff --check` is clean;
- prepare/status/run records are deterministic and round-trip;
- insufficient mesh readiness is rejected;
- unavailable solver profiles produce `unavailable`, not fake success;
- failed local commands produce failed records with error details;
- docs/status clearly say outputs are raw and unvalidated.
