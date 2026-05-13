# Ops review - 0014 comparison reports

author: operator [self-declared: operator-ops-review]
run: run_98b5ec4a7a31461bbdc78bbc00179aad
job: review_ops
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### O-001 - Comparison report models are missing

- Severity: high
- File(s): future `kayakgen/search/compare.py`
- Statement: `kayakgen/search/pareto.py` has pure dominance utilities, but
  there is no `ComparisonReport`, `CandidateSummary`, report loader, or writer.
- Required action: Add a small Pydantic report module that reads `run.json`,
  maps candidate summaries to `CandidatePoint`s, computes the Pareto front, and
  serializes a stable JSON report.

### O-002 - CLI has no `compare` command

- Severity: high
- File(s): `kayakgen/cli/main.py`, `tests/test_cli.py`
- Statement: RFC 0013 acceptance requires `kayakgen compare <run-dir> --out
  comparison.json`, but the Typer app currently exposes only init, generate,
  evaluate, mesh-check, stability, view, serve, and sweep.
- Required action: Add a `compare` command that validates the run directory,
  writes the report path, and returns a non-zero CLI error for missing/invalid
  run inputs.

### O-003 - Tests need deterministic sweep-backed fixtures

- Severity: high
- File(s): future `tests/test_compare.py`, `tests/test_cli.py`
- Statement: Existing Pareto tests are synthetic and sweep tests cover run
  writing, but no test joins the two surfaces through a real sweep directory.
- Required action: Add tiny sweep-backed tests for deterministic report output,
  missing metric warnings, failed candidate visibility, default resistance
  exclusion, and CLI writing.

### O-004 - Keep implementation dependency-free

- Severity: medium
- File(s): `pyproject.toml`, future comparison code
- Statement: Report generation does not need pandas, scipy, YAML, databases, or
  web dependencies. Adding any of those would widen the workflow unnecessarily.
- Required action: Use Pydantic, stdlib `json`/`pathlib`, and existing project
  modules only.

## Recommendation

Proceed with a focused implementation in `kayakgen/search/compare.py`, a Typer
command, and tests. Do not touch the web frontend in this workflow.
