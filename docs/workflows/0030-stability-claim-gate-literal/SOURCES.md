# Sources for workflow 0030

## Source audit

- `docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md` — batches
  R3 and R7. R3 explicitly defers to "a follow-up striatum workflow
  ('0030-stability-claim-gate-literal' or similar)"; R7 bundles into
  R3 as a low-severity neighbor in the same module.
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
  — finding `AUD-P-001` (high) on the Literal mismatch and
  `AUD-P-002` (low) on the hardcoded empty-tuple call sites.

## Files in scope

### Source under change

- `kayakgen/eval/contract.py:175` — `GZCurve.result_semantics` Literal
  widening.
- `kayakgen/eval/stability/accepted_fit.py` — new
  `EMPTY_STABILITY_FIT_REGISTRY` constant + `__all__` export.
- `kayakgen/eval/stability/evaluator.py:385` — replace `fit_registry=()`.
- `kayakgen/ui/web/generate_frontier_view.py:558` — replace
  `fit_registry=()`.
- `kayakgen/ui/web/generate_spec_form.py:832` — replace `registry=()`.

### Tests under change

- `tests/test_gzcurve_result_semantics_round_trip.py` (new) — pins the
  validated-label round-trip and the unknown-label rejection.

### Context (read but not modified)

- `docs/rfcs/0058-stability-calibration-acceptance.md` — defines the
  two-element `AnalyticalClaimLabel` Literal.
- `docs/DECISION_LOG.md` — D039 documents the byte-stable empty-registry
  default and the stage-4 graduation point.
- `kayakgen/eval/stability/high_angle_contracts.py` — owns
  `AnalyticalClaimLabel` and `GeneratedBodyGZCurve`; the inlined
  Literal in `contract.py` must stay in lock-step.
- `tests/test_stability.py`,
  `tests/test_high_angle_stability_evaluator.py`,
  `tests/test_resolve_analytical_claim_label.py`,
  `tests/test_stability_accepted_fit.py`,
  `tests/test_vocabulary_coverage.py`,
  `tests/test_generate_frontier_view.py` — gating suite.

## Forbidden surfaces (parent agent owns)

- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
- `docs/audits/2026-05-22-code-doc-audit/docs-decision-drift/FINDINGS.md`
- `docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`
- Anything outside the allowlist in `workflow.json` `write_scope`.

## Where workflow artifacts land

`docs/audits/2026-05-22-code-doc-audit/follow-ups/0030/`:

```
PATCH_SUMMARY.md   # implementer
REVIEW.md          # reviewer
```
