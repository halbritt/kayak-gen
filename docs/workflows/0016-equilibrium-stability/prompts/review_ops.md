Read `docs/workflows/0016-equilibrium-stability/SOURCES.md`, especially current
stability, hydrostatics, contract models, CLI, and tests.

Produce `striatum/0016-equilibrium-stability/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- where equilibrium code should live;
- `kayakgen stability` CLI behavior for diagnostic vs equilibrium mode;
- deterministic convergence and bounded failure behavior;
- test fixtures for tolerances, KG references, warnings, and CLI output;
- avoiding new dependencies and geometry golden churn.
