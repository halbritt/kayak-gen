author: implementer-codex-gpt-5.5-004

# Patch Summary

- Added `resolve_analytical_claim_label(hull, fit_registry)` in
  `kayakgen/eval/stability/high_angle_contracts.py`.
- Kept the empty-registry and non-covering defaults at
  `unvalidated_hydrostatic_comparison`.
- Upgraded only accepted `StabilityFitRecord` entries whose
  `hull_family_scope.hull_class` matches the hull and whose envelope contains
  the hull design hash.
- Widened `GeneratedBodyGZCurve.result_semantics` to allow
  `validated_hydrostatic_comparison` while preserving the unvalidated default.
- Re-exported the resolver from `kayakgen.eval.stability`.
- Added focused resolver and round-trip tests in
  `tests/test_resolve_analytical_claim_label.py`.

# Verification

- `.venv/bin/pytest tests/test_resolve_analytical_claim_label.py`
- `.venv/bin/ruff check kayakgen/eval/stability/high_angle_contracts.py kayakgen/eval/stability/__init__.py tests/test_resolve_analytical_claim_label.py`
