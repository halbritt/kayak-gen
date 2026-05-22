# Role: Reviewer (workflow 0030)

You review the implementer's patch for the two findings closed by this
workflow: `AUD-P-001` (high — `GZCurve.result_semantics` Literal
widening) and `AUD-P-002` (low — `EMPTY_STABILITY_FIT_REGISTRY`
constant rollout).

You write a single `REVIEW.md` to
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0030/`. You do NOT
modify source, tests, `CHANGELOG.md`, or any audit `FINDINGS.md`.

## Required checks

- `kayakgen/eval/contract.py` `GZCurve.result_semantics` is a Literal
  with exactly the two members
  `"unvalidated_hydrostatic_comparison"` and
  `"validated_hydrostatic_comparison"` (plus `| None`). No third
  literal was introduced.
- The Literal is inlined — `contract.py` does not import
  `AnalyticalClaimLabel` from `high_angle_contracts` (that would
  recreate a circular import).
- `tests/test_gzcurve_result_semantics_round_trip.py` includes (a) a
  construction test for the validated label on
  `GeneratedBodyGZCurve`, (b) a round-trip test that asserts
  `EvaluationResult.model_validate_json(result.model_dump_json())
  == result` for a `StabilityResult.gz_curve` carrying the validated
  label, and (c) a negative test that the parent `GZCurve` rejects
  an unknown label.
- `kayakgen/eval/stability/accepted_fit.py` exports
  `EMPTY_STABILITY_FIT_REGISTRY` from `__all__` and the docstring
  cites D039 plus the three call sites.
- Each of the three call sites (`evaluator.py`,
  `generate_frontier_view.py`, `generate_spec_form.py`) imports and
  uses the new constant in place of the hardcoded empty tuple.
- The full gating suite from `RUNBOOK.md` passes; numbers are
  included in `PATCH_SUMMARY.md`.
- The patch did not touch `CHANGELOG.md` or any audit
  `FINDINGS.md`.

## Verdict

End your `REVIEW.md` with either `verdict: approve` or
`verdict: needs_revision` and a one-paragraph rationale. List any
blocking issues explicitly.
