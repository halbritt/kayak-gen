# Findings ledger - 0014

author: operator [self-declared: operator-ledger]
run: run_98b5ec4a7a31461bbdc78bbc00179aad
job: findings_ledger
date: 2026-05-13

## Gate result

Proceed with a focused comparison-report implementation. The safe slice is a
dependency-free `kayakgen compare` CLI and report layer over existing sweep
records. Default objectives must exclude raw uncalibrated resistance. Failed,
skipped, incomplete, and missing-metric candidates remain visible with warnings
instead of crashing or being silently dropped.

## Stats

- Source findings: 15
- Deduplicated findings: 7
- By severity: high 5 / medium 2
- Actionable now: 7

## Findings

### F-001 - Comparison CLI is missing

- Sources: T-001, O-002
- Severity: high
- Classification: actionable-now
- File(s): `kayakgen/cli/main.py`, `tests/test_cli.py`
- Statement: RFC 0013 requires `kayakgen compare <run-dir> --out <file>`, but
  the command does not exist.
- Required remediation: Add a Typer `compare` command that reads the sweep run
  directory, writes the requested report, and returns non-zero for missing or
  invalid run inputs.

### F-002 - Comparison report models and writer are absent

- Sources: T-002, O-001
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/search/compare.py`
- Statement: The code has pure Pareto utilities but no `CandidateSummary`,
  `ComparisonReport`, run loader, or report writer.
- Required remediation: Add Pydantic models and a report builder that maps
  `SweepRunRecord` candidates to summaries with hull hash, status, metrics,
  objective values, warnings, errors, and artifact paths.

### F-003 - Default objectives must exclude uncalibrated resistance

- Sources: T-003, T-004, D-001, D-002
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/search/compare.py`, `tests/test_compare.py`
- Statement: Current resistance is raw, uncalibrated, and comparative-only.
  Default comparison reports must not use it as a Pareto objective.
- Required remediation: Define default objectives over currently safe metrics
  only. If raw resistance is exposed as an explicit option, label the report
  `exploratory_frontier` and require accepted-use/calibration provenance before
  treating the metric as an accepted objective.

### F-004 - Missing metrics need report-level warnings

- Sources: T-003, D-003
- Severity: high
- Classification: actionable-now
- File(s): new `kayakgen/search/compare.py`, `tests/test_compare.py`
- Statement: Existing Pareto utilities annotate missing metrics only on
  `CandidatePoint` copies. The report layer must preserve those warnings for
  every candidate summary, not only the final front.
- Required remediation: Add warnings for missing objective metrics,
  unsupported objectives, and unavailable reports. Preserve existing candidate
  warnings.

### F-005 - Failed and skipped candidates must stay visible

- Sources: D-004
- Severity: medium
- Classification: actionable-now
- File(s): new `kayakgen/search/compare.py`, `tests/test_compare.py`
- Statement: Sweep records intentionally persist failed and skipped candidates,
  but only complete candidates should participate in Pareto computation.
- Required remediation: Include failed/skipped records in candidate summaries
  with status, warnings/error, artifacts, and no objective values where
  unavailable.

### F-006 - Sweep summary CSV should include parameter traceability

- Sources: supplemental traceability T-005
- Severity: medium
- Classification: actionable-now
- File(s): `kayakgen/search/sweep.py`, `tests/test_sweep.py`
- Statement: RFC 0009 says `summary.csv` includes varied parameters, but the
  current CSV omits parameter columns even though record JSON has them.
- Required remediation: Add deterministic `param_<name>` columns to
  `summary.csv`, or explicitly make `run.json` the comparison source of truth
  and update documentation. Prefer adding the CSV columns because it is small
  and directly satisfies RFC 0009.

### F-007 - RFC status should reflect the landed report/CLI slice

- Sources: T-004
- Severity: high
- Classification: actionable-now
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  `docs/rfcs/README.md`
- Statement: RFC 0013 is currently `proposed`. If this workflow lands the
  report/CLI slice, status should not imply that web UI work has landed.
- Required remediation: Mark RFC 0013 as landed for report/CLI only, and keep
  web UI acceptance deferred.

## Implementation guidance

Safe now:

- Add `kayakgen/search/compare.py` with `CandidateSummary`,
  `ComparisonReport`, default objective selection, run loading, report
  building, and report writing.
- Add `kayakgen compare <run-dir> --out <file>` to the Typer CLI.
- Add deterministic tests over tiny sweep fixtures and CLI output.
- Add `param_<name>` columns to sweep `summary.csv`.
- Update RFC 0013 and the RFC index status/note.
- Keep implementation dependency-free.

Do not implement:

- Web comparison UI.
- Optimizer or ranking score.
- Default Pareto resistance objective from raw uncalibrated resistance.
- Calibration, validity-envelope, or external dataset work.
- New pandas/scipy/YAML/database dependencies.
