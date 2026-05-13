# Patch summary - 0011

author: operator
run: run_934bd256c4494cebadb161a0d97d8283
job: implement_findings

## Scope

This implementation round landed the safe, structural slice from the 0011
ledger. It did not choose domain decisions that the ledger classified as human
decisions: CFD watertight/open-surface readiness, bow-positive coordinate
convention, equilibrium sinkage/trim solving, waterline/seat-referenced KG,
canonical resistance calibration data, or default Pareto ranking over raw
resistance.

## Findings addressed

- F-001: RFC 0009 and `kayakgen.search.sweep` now use deterministic
  `candidate_key` identity before `Hull` validation; failed candidates keep
  attempted parameters and validation errors with optional `hull_hash`.
- F-002: RFC 0009 now makes mesh diagnostics optional and dependent on RFC
  0010; sweep records can write mesh diagnostics when the diagnostics layer is
  enabled.
- F-003: Added conservative mesh diagnostics with raw and tolerance-welded edge
  counts, solver-profile schema, nonfinite/degenerate counts, bounding boxes,
  surface area, and readiness capped below `cfd_ready`.
- F-005/F-006/F-007: Added `LoadCase`, `StabilityResult`, and
  design-waterline initial stability with baseline-referenced
  `kg_above_keel_m`; high-angle `GZ` remains explicitly not implemented.
- F-008: Added `ResistanceMetadata` to `ResistanceCurve`; raw curves are marked
  `raw_ittc_michell`, `uncalibrated`, and `comparative_filter`, with warnings
  and quadrature/constants metadata.
- F-009: Added pure Pareto utilities with accepted-use provenance requirements;
  no CLI/UI default ranking over raw resistance was added.
- F-010: Sweep candidate records include evaluator settings, evaluator
  versions, warnings, and optional mesh diagnostics.
- F-011: RFC 0013 now lists RFC 0010 and gates UI/default exploratory
  resistance behavior.
- F-012: Implementation stayed dependency-neutral and added CLI/test coverage
  for touched commands.

## Deferred or human-decision findings

- F-004: Bow-positive coordinate convention remains a human decision.
- F-005: Equilibrium sinkage/trim solving remains a human decision; the current
  stability result is design-waterline-only and carries warnings.
- F-006: Waterline/seat-referenced KG remains a human decision; the safe field
  is baseline/keel-referenced.
- F-009: Default Pareto ranking over exploratory raw resistance remains
  deferred; only opt-in/provenance-aware utilities exist.

## Code changes

- Added RFCs 0009-0013 and updated the RFC index.
- Added `kayakgen/eval/mesh_diagnostics.py`.
- Added `kayakgen/eval/stability.py`.
- Extended `kayakgen/eval/contract.py` with resistance metadata, load cases,
  and stability results.
- Extended `kayakgen/eval/resistance.py` to populate raw-model metadata.
- Added `kayakgen/search/sweep.py` and `kayakgen/search/pareto.py`.
- Replaced the `kayakgen sweep` stub and added `mesh-check` and `stability`
  CLI commands.
- Added focused tests for mesh diagnostics, stability, sweep records, Pareto
  utilities, CLI behavior, and resistance metadata.

## Verification

- `.venv/bin/python -m pytest tests/test_mesh_diagnostics.py tests/test_pareto.py tests/test_stability.py tests/test_resistance.py tests/test_sweep.py tests/test_cli.py -q`
  -> 35 passed, 2 xfailed.
- `.venv/bin/python -m pytest -q` -> 95 passed, 2 xfailed.
- `git diff --check` -> clean.
- `.venv/bin/kayakgen --help` shows `mesh-check`, `stability`, and working
  `sweep`.
- `.venv/bin/ruff check .` could not be run because Ruff is not installed in the
  repo virtual environment.
