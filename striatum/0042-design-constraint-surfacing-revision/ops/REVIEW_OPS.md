# Ops Review

Verdict intent: accept_with_findings

No blocking scaffold issue found. RFC 0031 and workflow 0042 are adequate to start the conservative implementation slice: RFC 0031 narrows RFC 0029, defines the design-validity record fields, compatibility expectations, target surfaces, and acceptance tests (`docs/rfcs/0031-design-constraint-surfacing-revision.md:66`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:102`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:112`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:129`), and workflow 0042 adds the first-pass review-remediation route missing from workflow 0040 (`docs/workflows/0040-design-constraint-surfacing/workflow.json:116`, `docs/workflows/0042-design-constraint-surfacing-revision/workflow.json:51`, `docs/workflows/0042-design-constraint-surfacing-revision/workflow.json:183`).

## Findings

### F-OPS-001 - Medium - Propagation targets must be wired at every serialization boundary

RFC 0031 is clear that `design_validity` is additive JSON and must reach CLI evaluate, web payloads, sweep candidate records, and comparison reports (`docs/rfcs/0031-design-constraint-surfacing-revision.md:114`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:131`). The current code has no such field on `EvaluationResult` (`kayakgen/eval/contract.py:281`), CLI `evaluate` writes only hash/hydrostatics/resistance (`kayakgen/cli/main.py:76`), sweep `CandidateRecord` has no validity slot (`kayakgen/search/sweep.py:95`), sweep candidate evaluation writes no validity data (`kayakgen/search/sweep.py:242`), and comparison summaries preserve only metrics/warnings/provenance (`kayakgen/search/compare.py:30`).

Concrete correction: add one shared design-validity report from the model/evaluator boundary, then propagate it through `EvaluationResult`, CLI `evaluate`, web evaluation payloads, completed sweep candidate records, comparison candidate summaries, and report-level warning counts. Advisory and unsupported findings must not change candidate status, Pareto eligibility, or CLI exit behavior for valid hulls.

### F-OPS-002 - Medium - Additive compatibility needs explicit handling with current strict models

RFC 0031 says unknown future fields must not make older consumers fail and structured metadata should be ignorable (`docs/rfcs/0031-design-constraint-surfacing-revision.md:78`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:108`). Current serialized Pydantic models use `extra="forbid"` on `EvaluationResult`, `CandidateRecord`, `CandidateSummary`, and `ComparisonReport` (`kayakgen/eval/contract.py:284`, `kayakgen/search/sweep.py:98`, `kayakgen/search/compare.py:33`, `kayakgen/search/compare.py:51`).

Concrete correction: keep existing top-level schema compatibility by adding defaulted fields where needed, and make the new design-validity finding/report models tolerant of unknown future optional fields. Add tests proving old records without `design_validity` still load, records with `design_validity` round-trip, and extra future fields inside a finding do not break the new consumer.

### F-OPS-003 - Medium - Web payload and text parity need a canonical implementation target

RFC 0031 requires the web evaluation payload and desktop/web warning text to come from shared codes/messages (`docs/rfcs/0031-design-constraint-surfacing-revision.md:117`, `docs/rfcs/0031-design-constraint-surfacing-revision.md:119`). The web has three plausible surfaces today: compact metrics from `metrics_from_state()` (`kayakgen/ui/web/controllers.py:96`), analysis rows from `analysis_view_model()` (`kayakgen/ui/web/controllers.py:125`), and REST `evaluation_payload()` via `EvaluationResult` (`kayakgen/ui/web/controllers.py:927`). Desktop renders advisory strings separately (`kayakgen/ui/desktop.py:321`), while web mixes advisory and resistance warnings in analysis output (`kayakgen/ui/web/controllers.py:167`) and hardcodes compact resistance warning text (`kayakgen/ui/web/app.py:221`).

Concrete correction: ledger should pin the canonical structured web payload location before implementation. A safe target is `EvaluationResult.design_validity` for REST/CLI JSON, with `metrics_from_state()` and `analysis_view_model()` deriving visible design-warning text from the same report. Add a helper-level parity test that feeds an equivalent hull to desktop/web warning renderers and compares design-validity codes/messages, excluding separate resistance warnings unless explicitly included.

### F-OPS-004 - Low - Selected-class drift needs an explicit source

RFC 0031 requires class drift only when a selected class is known (`docs/rfcs/0031-design-constraint-surfacing-revision.md:91`) and leans toward selected-class-first drift semantics (`docs/rfcs/0031-design-constraint-surfacing-revision.md:157`). Current `Hull` does not store a selected class (`kayakgen/model/hull.py:29`), web state fields do not include one (`kayakgen/ui/web/state.py:18`), and `SweepSpec` only has `base_hull` plus variables/evaluators/limits (`kayakgen/search/sweep.py:79`).

Concrete correction: make selected class an optional input to `evaluate_design_validity(...)`, supplied only by surfaces that actually know it. Do not infer drift from `Hull.name` by default. Add tests for advisory-quiet class defaults and for one explicit selected-class drift case.

## Required Actions

- Implement `kayakgen/model/validity.py` with stable finding codes/messages, required fields, optional future-field tolerance, and a compatibility path that preserves `DesignAdvisory.warnings` (`kayakgen/model/advisory.py:15`).
- Add focused tests for CLI JSON, web payload/text parity, sweep record propagation, comparison report propagation and warning counts, advisory-not-failure behavior, non-neutral reserved-field `unsupported` findings, class defaults, selected-class drift, and `beam_wl_m > beam_oa_m` remaining an enforced model/CLI failure (`kayakgen/model/hull.py:73`).
- Preserve the existing resistance/CFD claim boundaries; RFC 0031 explicitly excludes resistance claim gates, CFD readiness, closed-volume geometry, and solver dispatch changes (`docs/rfcs/0031-design-constraint-surfacing-revision.md:41`).

## Residual Risk

The only process risk is rerun freshness: the runbook says a blocking review cycles back and re-runs that review (`docs/workflows/0042-design-constraint-surfacing-revision/RUNBOOK.md:12`), while the graph routes `review_remediation` to all three first-pass review jobs (`docs/workflows/0042-design-constraint-surfacing-revision/workflow.json:173`). If remediation edits shared RFC/workflow text, operators should ensure sibling review artifacts are not stale before ledger consolidation.

Sub-agent help used: three read-only explorer agents checked CLI/sweep/report propagation, desktop/web/web-payload behavior, and workflow remediation adequacy. No product tests were run; this was a review-only artifact.
