# Implement `resolve_analytical_claim_label` — RFC 0058 stage 2

Read RFC 0058 (section "Analytical-claim upgrade contract"),
`STAGE_2_3_DECISIONS.md` rows D-1 through D-4 and D-20, and the
existing `kayakgen/eval/stability/high_angle_contracts.py`.

Land:

- `resolve_analytical_claim_label(hull, fit_registry) -> Literal[...]`
  in `kayakgen/eval/stability/high_angle_contracts.py`. `hull` is
  typed as a `kayakgen.eval.contract.Hull` (or the closest existing
  protocol — read what evaluator.py already uses). `fit_registry`
  is an `Iterable[StabilityFitRecord]` (import from
  `kayakgen.eval.stability.accepted_fit`).
- Widen `GeneratedBodyGZCurve.result_semantics` to
  `Literal["unvalidated_hydrostatic_comparison", "validated_hydrostatic_comparison"]`,
  keeping `"unvalidated_hydrostatic_comparison"` as the default.
- Export the function from `kayakgen/eval/stability/__init__.py`.

Tests in `tests/test_resolve_analytical_claim_label.py` (new) must
cover:

- empty registry → `unvalidated_hydrostatic_comparison`;
- non-matching `hull_class` → `unvalidated_hydrostatic_comparison`;
- matching `hull_class` but `design_hash` outside envelope →
  `unvalidated_hydrostatic_comparison`;
- one accepted record covering the hull's class + hash →
  `validated_hydrostatic_comparison`;
- one rejected record covering the hull → still `unvalidated_...`;
- two accepted records, one covering one not — still `validated`;
- `GeneratedBodyGZCurve` round-trips with both literals.

Requirements:

- Do not load any registry from disk in this function. Caller passes
  in-memory iterable (decision D-4).
- No new claim-state literal beyond the two above. The forbidden-claim
  scrub list stays untouched.
- Run focused tests + ruff before publishing.

Write scope:
- `kayakgen/eval/stability/high_angle_contracts.py`
- `kayakgen/eval/stability/__init__.py`
- `tests/test_resolve_analytical_claim_label.py`

Publish the required patch summary artifact under
`striatum/0056-.../implementation/claim_label/PATCH_SUMMARY.md`.
