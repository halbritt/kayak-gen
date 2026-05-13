# Traceability review - 0014 comparison reports

author: operator [self-declared: operator-traceability-review]
run: run_98b5ec4a7a31461bbdc78bbc00179aad
job: review_traceability
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### T-001 - RFC 0013 CLI acceptance is unimplemented

- Severity: high
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  `kayakgen/cli/main.py`
- Statement: RFC 0013 requires `kayakgen compare <run-dir>` to read a sweep run
  and write a comparison report, but no such command exists.
- Required action: Implement `kayakgen compare <run-dir> --out <file>` and
  cover it with CLI tests.

### T-002 - Report model names in RFC 0013 are not present in code

- Severity: high
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  `kayakgen/search/pareto.py`
- Statement: RFC 0013 names `CandidateSummary` and `ComparisonReport`, but the
  code currently has only `Objective`, `CandidatePoint`, and pure Pareto
  functions.
- Required action: Add report models that preserve hull hash, objective values,
  warnings, status, and artifact paths.

### T-003 - Default objective policy is only tested at the utility level

- Severity: high
- File(s): `tests/test_pareto.py`, future comparison tests
- Statement: Existing tests prove `accepted_use_required` works for synthetic
  points, but no report/CLI test proves default reports exclude raw
  uncalibrated resistance from sweep outputs.
- Required action: Add a sweep-backed comparison test where resistance-enabled
  candidates still produce a default report without resistance objectives.

### T-004 - RFC/readme status should change after the report slice lands

- Severity: medium
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  `docs/rfcs/README.md`
- Statement: RFC 0013 is currently `proposed`. If this workflow lands the
  CLI/report slice but defers web UI, status should say so explicitly.
- Required action: Update RFC 0013 and the RFC index to `partial` or
  `landed-report-cli`, with web UI still deferred.

## Recommendation

Proceed with implementation. The RFC acceptance can be satisfied as a
CLI/report slice without doing web UI work.
