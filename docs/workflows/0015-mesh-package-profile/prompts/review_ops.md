Read `docs/workflows/0015-mesh-package-profile/SOURCES.md`, especially current
CLI, mesh diagnostics, STL writing, and tests.

Produce `striatum/0015-mesh-package-profile/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- where manifest/package code should live;
- `kayakgen mesh-package hull.json --out dir` behavior;
- deterministic filenames and relative manifest paths;
- test fixtures for manifest, hull/deck quality reports, STL outputs, and CLI;
- avoiding new dependencies and geometry golden churn.
