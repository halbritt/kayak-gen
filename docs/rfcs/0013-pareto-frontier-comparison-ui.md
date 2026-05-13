# RFC 0013: Pareto Frontier and Candidate Comparison UI

Status: landed-report-cli
Date: 2026-05-13
Context: builds on RFC 0009 sweep records, RFC 0010 mesh diagnostics, RFC 0011
stability/load cases, RFC 0012 resistance metadata, and RFC 0008 web frontend.

Status note (workflow 0014, 2026-05-13): the comparison report and CLI slice has
landed. Workflow 0017 headless-verified the existing web shell, but web
comparison views remain deferred until RFC 0008 browser acceptance and report
formats stabilize. Default reports exclude raw uncalibrated resistance;
explicitly requested resistance objectives produce exploratory frontiers unless
future calibrated provenance satisfies RFC 0012.

## Problem

The project currently evaluates one hull at a time. The pivot is toward a
generative pipeline, where useful output is a set of candidates and tradeoffs:
drag, displacement, stability, class fit, mesh readiness, and uncertainty.

Those tradeoffs are not scalar. A tool that only picks the lowest drag hull can
discard stability, load fit, or manufacturability.

## Goals

- Compute Pareto frontiers over sweep run records.
- Compare candidates using existing evaluation outputs and explicit warnings.
- Provide machine-readable comparison reports.
- Add a path to web comparison views without blocking on full UI polish.
- Keep uncertainty and partial-model warnings visible.
- Exclude uncalibrated analytical resistance from default Pareto objectives
  until resistance calibration exists.

## Non-Goals

- Optimizer implementation.
- Multi-user design libraries or remote persistence.
- Replacing single-hull editing.
- Hiding invalid candidates unless a user asks for filtered output.

## Proposal

Add comparison utilities over candidate/evaluation records:

- `Objective`: metric path, direction (`min` or `max`), optional label.
- `CandidateSummary`: hull hash, metrics, warnings, artifact paths.
- `ComparisonReport`: selected objectives, Pareto-front hashes, ranked
  candidate summaries.

Initial objectives:

- minimize resistance at target speed only when the resistance result satisfies
  the objective's accepted-use requirement and is calibrated;
- maximize initial `GM0_m`;
- minimize displacement error against load case when available;
- minimize mesh diagnostic problem count when RFC 0010 reports are present;
- keep class/range warnings visible.

Manual/expert reports may still include raw uncalibrated resistance, but those
reports are explicitly non-default and labeled exploratory.

CLI:

```text
kayakgen compare runs/touring-001 --out comparison.json
```

Web follow-up:

- load a comparison report;
- show candidate table;
- show Pareto scatter;
- load a candidate into the existing hull editor.

## Acceptance Criteria

- Pareto utilities pass synthetic dominance tests.
- `kayakgen compare <run-dir>` reads a sweep run and writes a comparison
  report.
- Missing metrics are handled as warnings, not crashes.
- Comparison reports include hull hashes, objective values, warnings, and
  artifact paths.
- A default tiny sweep can be compared deterministically.
- Reports that include raw uncalibrated resistance as an objective are labeled
  `exploratory_frontier`.
- Default reports exclude uncalibrated analytical resistance until RFC 0012 has
  a calibrated result with declared accepted use.
- Web UI acceptance is deferred until RFC 0008 browser acceptance and
  CLI/report formats stabilize.

## Open Questions

- Which objective axes should be defaults?
- Should v1 comparison be web-first, CLI-first, or both?
- Should invalid candidates be visible by default?
- How should model uncertainty be presented in the UI?

## Implementation Path

- Step 1 - Add Pareto and comparison report models.
- Step 2 - Add synthetic dominance tests.
- Step 3 - Add `kayakgen compare` for sweep directories.
- Step 4 - Add web API/view after CLI report format stabilizes.

## Domain Modeling

Candidate comparison is an application/read-model concern over existing hull
and evaluation artifacts. It should not alter hull geometry or evaluator
semantics.
