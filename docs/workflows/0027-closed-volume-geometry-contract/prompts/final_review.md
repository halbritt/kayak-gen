Review the completed closed-volume geometry implementation and produce
`striatum/0027-closed-volume-geometry-contract/final/FINAL_REVIEW.md`.

Use:

- author line: `author: operator [self-declared: operator-final-review]`
- verdict
- coverage table mapping ledger findings to evidence
- verification commands and results
- final gate result

Accept only if:

- tests pass and `git diff --check` is clean;
- RFC 0016 acceptance or amendment is reflected in the implementation scope;
- closed-volume body metadata records closure policy, end caps, deck joins,
  sheerline, and waterline semantics;
- diagnostics reject open and nonmanifold bodies explicitly;
- current open packages remain below watertight/cfd-ready profiles unless new
  tests prove the closed-volume path;
- docs/status do not claim high-angle GZ, real CFD, volume meshing, or
  calibrated/validated physics.
