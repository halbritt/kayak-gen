# Domain review - 0014 comparison reports

author: operator [self-declared: operator-domain-review]
run: run_98b5ec4a7a31461bbdc78bbc00179aad
job: review_domain
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### D-001 - Default comparison objectives must be provenance-safe

- Severity: high
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`,
  future comparison report code
- Statement: RFC 0013 allows resistance only when the result satisfies an
  accepted-use requirement and is calibrated. Workflow 0013 established that
  current resistance is raw and uncalibrated.
- Required action: Build default objectives from currently safe metrics only,
  such as `GM0_m` when present, and exclude resistance from default Pareto
  computation.

### D-002 - Raw resistance needs explicit exploratory labeling if exposed

- Severity: high
- File(s): `kayakgen/search/pareto.py`, future comparison report code
- Statement: `CandidateRecord.summary` can contain `Rt_N_last` when sweep
  resistance is enabled, but that summary only carries raw comparative-filter
  metadata. Using it in a frontier without a report-level label would overstate
  the result.
- Required action: If implementation exposes raw resistance as a user-requested
  objective, set report kind/status to `exploratory_frontier` and add warnings
  to every affected candidate/report.

### D-003 - Missing metrics should annotate candidates, not remove them

- Severity: high
- File(s): future comparison report code, `kayakgen/search/pareto.py`
- Statement: The existing Pareto utility correctly treats missing metrics as
  non-dominating, but a report must also keep the warning visible for every
  candidate summary, including candidates not on the frontier.
- Required action: Candidate summaries should preserve source warnings and add
  objective-specific warnings such as missing metric or unsupported objective.

### D-004 - Failed and skipped sweep candidates remain reportable

- Severity: medium
- File(s): `kayakgen/search/sweep.py`, future comparison report code
- Statement: Sweep records intentionally persist failed and skipped candidates.
  Comparison reports should not silently drop them from the report, even if only
  complete candidates can participate in Pareto computation.
- Required action: Include failed/skipped records in `candidate_summaries` with
  status, warnings/error, artifacts, and no objective values where unavailable.

## Recommendation

Proceed. The existing `Objective`, `CandidatePoint`, and `pareto_front`
utilities are a suitable base, but the report layer must enforce safe defaults,
warning propagation, and explicit exploratory labeling.
