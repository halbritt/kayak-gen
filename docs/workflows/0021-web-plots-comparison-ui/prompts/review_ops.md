Read `docs/workflows/0021-web-plots-comparison-ui/SOURCES.md`, especially
`kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`,
`kayakgen/search/compare.py`, `kayakgen/cli/main.py`, `pyproject.toml`, and
web/comparison tests.

Produce `striatum/0021-web-plots-comparison-ui/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- state management and API shape for report loading and candidate reload;
- fixture size/provenance and deterministic comparison report tests;
- browser/headless coverage for new analysis views;
- performance risk from plot generation or large report rendering;
- avoiding heavy frontend dependencies unless the ledger proves they are needed.
