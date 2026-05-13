Read `docs/workflows/0019-legacy-rfc-partial-closure/SOURCES.md`, especially current
model/geometry/classes, desktop/web UI, CLI, and tests.

Produce `striatum/0019-legacy-rfc-partial-closure/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- whether RFC 0004/0006 behavior is covered by focused tests;
- whether desktop/web parameter propagation is consistent;
- whether CLI/schema/JSON surfaces expose class and bow-rake semantics
  coherently;
- whether status/doc updates are enough or code changes are needed;
- avoiding new dependencies and unnecessary geometry golden churn.
