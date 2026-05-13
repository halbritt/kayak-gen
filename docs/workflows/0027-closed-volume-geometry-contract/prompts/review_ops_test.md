Read `docs/workflows/0027-closed-volume-geometry-contract/SOURCES.md`,
especially the CLI, mesh package code, CFD job gating, and existing tests.

Produce `striatum/0027-closed-volume-geometry-contract/ops_test/REVIEW_OPS_TEST.md`
with:

- author line: `author: operator [self-declared: operator-ops-test-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- deterministic closed-volume body manifests and diagnostics artifacts;
- synthetic valid closed body, open body, and nonmanifold body fixtures;
- CLI ergonomics and failure modes for opt-in closed-volume checks;
- mesh-package and solver-profile hooks without claiming real solver readiness;
- tests for serialization, diagnostics rejection, profile gating, and status
  wording.
