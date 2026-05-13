Review the completed mesh-package implementation and produce
`striatum/0015-mesh-package-profile/final/FINAL_REVIEW.md`.

Use:

- author line: `author: operator [self-declared: operator-final-review]`
- verdict
- coverage table mapping ledger findings to evidence
- verification commands and results
- final gate result

Accept only if:

- tests pass and `git diff --check` is clean;
- `kayakgen mesh-package` writes deterministic manifest/hull/quality/STL
  artifacts;
- manifest coordinate/profile metadata reflects stern-positive and open
  wetted-surface decisions;
- current surfaces are not falsely promoted to watertight `cfd_ready`;
- RFC/readme/operator-report artifacts accurately reflect what landed.
