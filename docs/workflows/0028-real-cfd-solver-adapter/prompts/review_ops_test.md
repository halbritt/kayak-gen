Read `docs/workflows/0028-real-cfd-solver-adapter/SOURCES.md`, especially the
existing CFD job code, CLI code, and tests.

Produce `striatum/0028-real-cfd-solver-adapter/ops_test/REVIEW_OPS_TEST.md`
with:

- author line: `author: operator [self-declared: operator-ops-test-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- solver binary detection and truthful `unavailable` states;
- local execution isolation, command construction, stdout/stderr capture, and
  exit-status handling;
- deterministic case directories and JSON records;
- missing or malformed solver-output failure modes;
- fixture tests and optional installed-solver tests that keep CI usable without
  external solver binaries.
