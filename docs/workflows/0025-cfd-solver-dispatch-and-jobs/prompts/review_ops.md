Read `docs/workflows/0025-cfd-solver-dispatch-and-jobs/SOURCES.md`,
especially the CLI, mesh package code, and tests.

Produce `striatum/0025-cfd-solver-dispatch-and-jobs/ops/REVIEW_OPS.md`
with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- deterministic local job directories and JSON records;
- prepare/status/run CLI ergonomics and failure modes;
- readiness rejection for insufficient mesh packages;
- unavailable solver behavior that requires no solver binary;
- tests for round-trips, readiness rejection, unavailable, and failed command
  states.
