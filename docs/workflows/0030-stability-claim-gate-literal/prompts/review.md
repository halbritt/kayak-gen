# Task — review the R3 + R7 patch (workflow 0030)

Read the implementer's `PATCH_SUMMARY.md` under
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0030/`, then the diff
on the workflow branch. Verify each item below against the source on
disk and write a single `REVIEW.md` to the same directory.

## Claim-gate fidelity

- `kayakgen/eval/contract.py` — `GZCurve.result_semantics` is a
  Literal containing exactly
  `"unvalidated_hydrostatic_comparison"` and
  `"validated_hydrostatic_comparison"` (plus `| None = None`).
  No third literal was introduced; no other field on `GZCurve`,
  `GeneratedBodyGZCurve`, `StabilityResult`, or `EvaluationResult`
  was modified.
- `kayakgen/eval/stability/high_angle_contracts.py` —
  `AnalyticalClaimLabel` is unchanged; `GeneratedBodyGZCurve` is
  unchanged.
- `contract.py` does NOT import `AnalyticalClaimLabel` from
  `high_angle_contracts` (would be a circular import).

## Constant rollout

- `kayakgen/eval/stability/accepted_fit.py` defines
  `EMPTY_STABILITY_FIT_REGISTRY: tuple["StabilityFitRecord", ...] = ()`
  with a docstring citing D039 and the three call sites; the constant
  appears in `__all__`.
- `kayakgen/eval/stability/evaluator.py`,
  `kayakgen/ui/web/generate_frontier_view.py`, and
  `kayakgen/ui/web/generate_spec_form.py` each import the constant
  and pass it in place of the previous hardcoded `()`.

## Test coverage

- `tests/test_gzcurve_result_semantics_round_trip.py` is present and
  carries the three required assertions:
  1. `GeneratedBodyGZCurve(..., result_semantics=
     "validated_hydrostatic_comparison")` constructs cleanly.
  2. `EvaluationResult.model_validate_json(result.model_dump_json())
     == result` for a `StabilityResult.gz_curve` carrying the
     validated label.
  3. `GZCurve(..., result_semantics="bogus_label")` raises a
     Pydantic `ValidationError`.
- The gating suite passes:
  ```bash
  .venv/bin/pytest \
    tests/test_gzcurve_result_semantics_round_trip.py \
    tests/test_stability.py \
    tests/test_high_angle_stability_evaluator.py \
    tests/test_resolve_analytical_claim_label.py \
    tests/test_stability_accepted_fit.py \
    tests/test_vocabulary_coverage.py \
    tests/test_generate_frontier_view.py \
    -q
  ```

## Scope hygiene

- `CHANGELOG.md` was not modified.
- No audit `FINDINGS.md` was modified.
- The patch did not touch any file outside the
  `write_scope.allowed_paths` declared in `workflow.json`.

## Output

Write `REVIEW.md` with sections matching the four headings above,
each entry checked or noted as a blocker. End with one of:

- `verdict: approve`
- `verdict: needs_revision` (and a numbered list of blockers)

Do NOT modify source, tests, `CHANGELOG.md`, or any audit
`FINDINGS.md`.
