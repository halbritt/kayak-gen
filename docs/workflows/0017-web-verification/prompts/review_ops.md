Read `docs/workflows/0017-web-verification/SOURCES.md`, especially
`kayakgen/cli/main.py`, `Dockerfile`, `.dockerignore`, `pyproject.toml`, and web
tests.

Produce `striatum/0017-web-verification/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- whether `kayakgen serve` is scriptable enough for smoke checks;
- whether Docker/deployment docs can be reproduced;
- whether optional dependencies and skipped browser tooling are clear;
- whether REST/STL/share helpers have enough test coverage;
- avoiding new heavy dev dependencies unless already available.
