author: reviewer-ops-tests-codex-gpt-5.5-001
kind: finding
logical_name: review
verdict: accept_with_findings

# Review Findings: Ops and Tests

I reviewed workflow `0055-rfc-0058-stage1-stability-fit-schemas` for test determinism, schema round-trip coverage, validator branch coverage, promotion-packet refusal coverage, and operational risk.

## Findings

- **F1 - FixtureRef is missing the pinned schema version required by the Stage 1 review contract.** `docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/prompts/review.md` says every record in the Stage 1 surface must use `ConfigDict(extra="forbid")` and pinned `schema_version: Literal["1"]`. `FixtureRef` has `extra="forbid"` but no `schema_version` field in `kayakgen/eval/stability/accepted_fit.py:32`. `tests/test_stability_accepted_fit.py:100` only asserts schema versions for `StabilityFitRecord`, `HullFamilyScope`, `StabilityFitMetrics`, and `ReviewerSignature`, so the omission is not caught. Add `schema_version: Literal["1"] = "1"` to `FixtureRef` and assert it in the round-trip test.

- **F2 - Threshold branch tests do not cover every default threshold independently.** The role objective asks for validator coverage of every threshold. `tests/test_stability_accepted_fit.py:113` covers only `rmse_m > 0.005` under `strict=True`; the `strict=False` test at `tests/test_stability_accepted_fit.py:121` sets all four bad metrics but only proves the bypass path. Add strict-mode negative cases for `mape_fraction > 0.05`, `max_error_m > 0.01`, and `coverage_fraction < 0.9`, ideally parametrized over metric name/value/expected token.

- **F3 - Promotion-packet review-verdict refusal is only sampled for one verdict field.** The role objective asks for every promotion-packet refusal path. `tests/test_stability_accepted_fit.py:153` exercises `hull_identity_review="deferred"` but does not independently cover `rights_review`, `calibration_drift_review`, `hysteresis_review`, or `free_equilibrium_review`. The implementation currently checks all verdicts through a tuple, but the test suite would not catch a future omission of one field from that tuple. Add a parametrized test over all five review verdict fields.

## Verification

- `.venv/bin/ruff check .` passed.
- Focused schema and scan run passed: `.venv/bin/pytest tests/test_stability_accepted_fit.py tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui tests/test_import_boundaries.py tests/test_services_boundaries.py` -> `109 passed`.
- Full suite passed: `.venv/bin/pytest` -> `1057 passed, 4 skipped`. The skips are the existing opt-in OpenFOAM-v2512 smoke/stage tests.

## Verdict

`accept_with_findings`. The implementation is operationally green and preserves the no-claims boundary, but the schema/version and branch-coverage gaps above should be remediated before treating the Stage 1 contract as fully pinned.
