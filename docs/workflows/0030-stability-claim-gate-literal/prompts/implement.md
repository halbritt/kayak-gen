# Task — implement R3 + R7 (workflow 0030)

You close audit findings `AUD-P-001` (high) and `AUD-P-002` (low) per
[`docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md`](../../../audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md)
batches R3 and R7.

Read in order:

1. `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
   entries `AUD-P-001` and `AUD-P-002`.
2. The two REMEDIATION_PLAN.md sections above.
3. `kayakgen/eval/contract.py` (full file).
4. `kayakgen/eval/stability/high_angle_contracts.py` (full file) —
   confirms that the canonical `AnalyticalClaimLabel = Literal[
   "unvalidated_hydrostatic_comparison",
   "validated_hydrostatic_comparison"]` lives here.
5. `kayakgen/eval/stability/accepted_fit.py`.
6. The three call sites: `kayakgen/eval/stability/evaluator.py`,
   `kayakgen/ui/web/generate_frontier_view.py`,
   `kayakgen/ui/web/generate_spec_form.py`.
7. `tests/test_stability.py` (the existing
   `EvaluationResult.model_validate_json(result.model_dump_json())`
   round-trip patterns and the `_skipped_heel_metadata` helper shape).

## Patch — AUD-P-001 (R3)

In `kayakgen/eval/contract.py`, replace

```python
result_semantics: Literal["unvalidated_hydrostatic_comparison"] | None = None
```

with the inlined two-element Literal:

```python
result_semantics: Literal[
    "unvalidated_hydrostatic_comparison",
    "validated_hydrostatic_comparison",
] | None = None
```

Do NOT import `AnalyticalClaimLabel` from
`kayakgen/eval/stability/high_angle_contracts.py` — that module
already imports from `contract.py`, so the import would be circular.
Inline the two literals and accept the duplication.

Create `tests/test_gzcurve_result_semantics_round_trip.py` with:

- A construction test on `GeneratedBodyGZCurve(status="unavailable",
  method="fixed_trim_generated_body_v1", fixture_only=False,
  body_ref=..., body_type="generated_hull_plus_deck_closed_body",
  heel_grid_deg=[0.0, 5.0], heel_point_metadata=[<two skipped
  GZHeelPointMetadata entries>],
  result_semantics="validated_hydrostatic_comparison")` and asserts
  it constructs without raising.
- A round-trip test that wraps the curve in `StabilityResult` (via
  `GZCurve.model_validate(curve.model_dump())` to drop the subclass
  identity, as `tests/test_stability.py` does) and an
  `EvaluationResult` with real `hydrostatics`, then asserts
  `EvaluationResult.model_validate_json(eval_result.model_dump_json())
  == eval_result`.
- A negative test that `GZCurve(status="unavailable",
  result_semantics="bogus_label")` raises a Pydantic
  `ValidationError`.

## Patch — AUD-P-002 (R7)

In `kayakgen/eval/stability/accepted_fit.py`, after the existing
imports / before the `Literal` aliases, add:

```python
EMPTY_STABILITY_FIT_REGISTRY: tuple["StabilityFitRecord", ...] = ()
"""Default empty fit registry for RFC 0058 stage-2/3 call sites.

Per D039 (`docs/DECISION_LOG.md`), defaults stay byte-stable with an empty
registry until stage 4 promotes the first measured-stability fixture
(blocked on D007 / D014). Three call sites consume this constant:
``kayakgen/eval/stability/evaluator.py``,
``kayakgen/ui/web/generate_frontier_view.py``,
``kayakgen/ui/web/generate_spec_form.py``. Replacing the constant with a
loaded registry is the stage-4 graduation point.
"""
```

Add `EMPTY_STABILITY_FIT_REGISTRY` to `__all__`.

Replace the three call sites:

- `kayakgen/eval/stability/evaluator.py:385` —
  `resolve_analytical_claim_label(hull, fit_registry=())` →
  `resolve_analytical_claim_label(hull, fit_registry=EMPTY_STABILITY_FIT_REGISTRY)`.
  Import the constant at the top of the file.
- `kayakgen/ui/web/generate_frontier_view.py:558` —
  `fit_registry=()` → `fit_registry=EMPTY_STABILITY_FIT_REGISTRY`.
  Import the constant.
- `kayakgen/ui/web/generate_spec_form.py:832` —
  `cfd_in_loop_evaluator_status(registry=(), hull_scope=scope)` →
  `cfd_in_loop_evaluator_status(registry=EMPTY_STABILITY_FIT_REGISTRY,
  hull_scope=scope)`. Import the constant.

## Verify

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

All must pass.

## Publish

Write `PATCH_SUMMARY.md` to
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0030/` with:

- One-line summary keyed to `AUD-P-001` and `AUD-P-002`.
- Bulleted list of files touched with file:line ranges.
- Verification command and pass counts per test file.
- Explicit confirmation: "did not touch `CHANGELOG.md` or any audit
  `FINDINGS.md`".

## Out of scope

- `CHANGELOG.md`.
- `docs/audits/2026-05-22-code-doc-audit/*/FINDINGS.md`.
- Any file outside the `write_scope.allowed_paths` in
  `workflow.json`.
- Promoting any fixture; introducing any third claim-label literal;
  altering the empty-registry default.
