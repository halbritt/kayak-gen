# Ops review - 0015 mesh package and profile

author: operator [self-declared: operator-ops-review]
run: run_4c00d3da5e7a4420ad44067406bdc27e
job: review_ops
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### O-001 - Package writer should live beside mesh diagnostics

- Severity: medium
- File(s): future `kayakgen/eval/mesh_package.py`
- Statement: Manifest/package writing is evaluator-adjacent and should not be
  buried in CLI code.
- Required action: Add a small module with Pydantic manifest models and
  `write_mesh_package(hull, out_dir, ...)`.

### O-002 - CLI needs deterministic artifact names

- Severity: high
- File(s): `kayakgen/cli/main.py`, future tests
- Statement: Tests and future workers need stable package filenames.
- Required action: Write `manifest.json`, `hull.json`, `quality.hull.json`,
  `quality.deck.json`, `hull.stl`, and `deck.stl`, with manifest paths relative
  to the package directory.

### O-003 - Tests must cover manifest, package files, and CLI

- Severity: high
- File(s): future `tests/test_mesh_package.py`, `tests/test_cli.py`
- Statement: Existing mesh tests cover diagnostics but not package artifacts.
- Required action: Add tests for manifest schema fields, quality report paths,
  STL existence, coordinate metadata, no watertight `cfd_ready`, and CLI output.

### O-004 - Keep geometry and dependencies stable

- Severity: high
- File(s): `pyproject.toml`, geometry/golden files
- Statement: Mesh packaging can reuse existing STL and diagnostics writers.
  Changing geometry or adding dependencies would widen the workflow.
- Required action: Do not change geometry goldens and do not add new runtime
  dependencies.

## Recommendation

Proceed with a focused package module, CLI command, and deterministic tests.
