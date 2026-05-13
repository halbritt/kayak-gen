Read `docs/workflows/0014-comparison-reports/SOURCES.md`, especially current
CLI, sweep, Pareto, and test files.

Produce `striatum/0014-comparison-reports/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- concrete findings with IDs `O-001`, `O-002`, ...
- required action for each finding

Focus on implementation and test shape:

- where comparison report models should live;
- how `kayakgen compare <run-dir> --out <file>` should read current sweep
  outputs;
- deterministic tiny fixtures for tests;
- Typer CLI error behavior for missing/invalid runs;
- avoiding new dependencies and avoiding broad UI work.
