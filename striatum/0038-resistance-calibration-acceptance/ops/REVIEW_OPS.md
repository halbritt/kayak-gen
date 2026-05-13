# Ops/Test Review: Resistance Calibration Acceptance

Verdict intent: accept_with_findings

## Scope

Assigned workflow: `0038-resistance-calibration-acceptance`

Assigned role: `reviewer_ops`

Required artifact path: `striatum/0038-resistance-calibration-acceptance/ops/REVIEW_OPS.md`

I read `AGENTS.md` first, then the assigned workflow files:

- `docs/workflows/0038-resistance-calibration-acceptance/SOURCES.md`
- `docs/workflows/0038-resistance-calibration-acceptance/roles/reviewer_ops.md`
- `docs/workflows/0038-resistance-calibration-acceptance/prompts/review_ops.md`

This review focuses on schemas, serialization, fit records, metrics, negative promotion tests, out-of-envelope warnings, raw fallback behavior, and reproducible test fixtures.

## Sub-agent Help Used

I used four independent read-only sub-agents, keeping scopes disjoint:

- Spec pass: extracted acceptance expectations from RFCs 0005, 0012, 0019, 0025, and 0027.
- Evaluator/schema pass: inspected `kayakgen/eval/resistance.py` and `kayakgen/eval/calibration.py`.
- CLI/test pass: inspected `kayakgen/cli/main.py` and `tests/test_resistance.py`.
- Fixture/reproducibility pass: searched for calibration fixtures, fit records, goldens, residual artifacts, and claim-gate tests.

I also performed a direct local review pass and ran focused tests. No project code was edited, `striatum` was not called, and `OPERATOR_REPORT.md` was not updated.

## Findings

### O-001: Calibrated-prediction gate allows rejected or candidate fits when metrics are present

Severity: high

`claim_allows_calibrated_prediction()` accepts a record if `fit_status` is in the legacy passing set or if `fit_metrics` is merely non-empty: `kayakgen/eval/claims.py:139-153`.

That is too permissive for RFC 0027. A record with `claim_state="calibrated_model"`, `accepted_uses=["final_prediction"]`, fixture IDs, model version, validity envelope, `fit_status="rejected_fit"`, and any metrics currently passes the gate. I verified this directly in the local environment.

RFC 0027 requires fit records to distinguish `not_fit`, `candidate_fit`, `accepted_fit`, and `rejected_fit`, and only an accepted fit should permit calibrated wording: `docs/rfcs/0027-resistance-calibration-acceptance.md:59-90`.

Recommended follow-up: make `accepted_fit` the canonical passing status, reject `candidate_fit` and `rejected_fit` even with metrics, and add negative tests for candidate/rejected fit records with populated metrics.

### O-002: RFC 0027 fit-record schema is not implemented yet

Severity: medium

`ResistanceFitRecord` exists only in RFC text: `docs/rfcs/0027-resistance-calibration-acceptance.md:61-72`.

Live metadata exposes loose fields instead: `fit_status: str | None`, `fit_metrics: dict[str, float]`, and `validity_envelope`: `kayakgen/eval/contract.py:31-34`; `kayakgen/eval/claims.py:56-59`.

The current code keeps default resistance output honest by setting fit fields empty/null in `resistance_curve()`: `kayakgen/eval/resistance.py:165-189`. It does not yet provide serialization for fitted parameters, residual references, canonical status literals, accepted metrics, or persisted residual artifacts.

Recommended follow-up: add a typed fit-record model or typed metadata subset before enabling any calibrated-model selection.

### O-003: Calibration fixture validation accepts weak source evidence

Severity: medium

`ResistanceSourceRecord` enforces extra metadata only when `intended_use == "calibration_fixture"`: `kayakgen/eval/calibration.py:46-67`.

That validator requires fixture ID, measured quantity, units, hull envelope, uncertainty notes, validity ranges, and accepted review status. However, it does not require `measured_data=True`, non-empty `rights_status`, or non-empty `extraction_status`. I verified that a `calibration_fixture` with `measured_data=False`, empty rights, and empty extraction status validates if the optional review fields are present.

RFC 0019 and RFC 0027 require explicit rights, extraction metadata, measured quantity, hull applicability, and review metadata before fixture acceptance: `docs/rfcs/0019-resistance-calibration-fixtures.md:80-90`; `docs/rfcs/0027-resistance-calibration-acceptance.md:51-58`.

Recommended follow-up: strengthen fixture validation and add negative tests for model-derived data, empty rights, and empty extraction metadata.

### O-004: Validation fixtures have no required fixture metadata

Severity: medium

`SourceUse` includes `validation_fixture`: `kayakgen/eval/calibration.py:13-19`, but the validator returns immediately for anything other than `calibration_fixture`: `kayakgen/eval/calibration.py:46-49`.

That means a validation fixture can be declared without fixture ID, measured quantity, units, envelope, uncertainty notes, or review status. RFC 0019 expects validation fixtures to remain distinct from calibration fixtures, but still to have machine-readable rows and metadata sufficient for reproducible validation: `docs/rfcs/0019-resistance-calibration-fixtures.md:66-87`.

Recommended follow-up: define minimum metadata for `validation_fixture` records, distinct from the stricter calibration fixture gate.

### O-005: Out-of-envelope warning and raw-fallback behavior are not implemented

Severity: medium

The current raw evaluator always emits uncalibrated comparative metadata and warnings: `kayakgen/eval/resistance.py:165-189`. That is correct for the default path.

There is no selected calibrated model path, no envelope-membership check, no out-of-envelope warning, and no fallback-to-raw branch. The current claim helper only checks that `validity_envelope` is present, not whether the evaluated hull or speed is inside it: `kayakgen/eval/claims.py:151`.

The CLI also has no calibration selection or raw-fallback surface. `evaluate` only supports `--skip-resistance` and otherwise calls `resistance_curve(hull)`: `kayakgen/cli/main.py:65-83`.

Recommended follow-up: when calibrated selection is added, route CLI/report wording through the claim gate and explicit envelope checks, with tests for in-envelope calibrated output, out-of-envelope warning, and raw fallback wording.

### O-006: Negative promotion tests cover raw defaults, but not the full RFC 0027 matrix

Severity: medium

Existing tests cover useful baseline behavior:

- raw resistance metadata remains uncalibrated: `tests/test_resistance.py:123-145`
- metadata serialization round-trips raw claim fields: `tests/test_resistance.py:173-189`
- default registry has no calibration fixtures: `tests/test_resistance.py:201-223`
- calibration fixture promotion without review metadata is rejected: `tests/test_resistance.py:250-255`
- comparison tests reject incomplete calibrated claim contracts: `tests/test_compare.py:264-301`
- calibrated resistance is not final design fitness: `tests/test_compare.py:304-330`

Missing RFC 0027 coverage remains:

- rejected/candidate fit with metrics must not pass
- `accepted_fit` metadata positive serialization
- validation-only fixture participating in metrics without becoming calibration input
- out-of-envelope warning behavior
- raw fallback wording
- fixture row loading, units, monotonic speed ordering, declared validity ranges, and residual references

The current `test_validation_fixture_does_not_promote_resistance_claim()` creates a validation fixture but does not pass it into a fit, metadata builder, registry, evaluator, or claim gate: `tests/test_resistance.py:225-247`.

## Compliant Areas

Default resistance output does not overclaim. `resistance_curve()` emits:

- `claim_state="uncalibrated_comparative"`
- `model_family="raw_ittc_michell"`
- `calibration_status="uncalibrated"`
- empty calibration and validation fixture IDs
- no model version, fit status, or validity envelope
- comparative-only warnings including `not_final_performance_prediction` and `uncalibrated_no_validity_envelope`

See `kayakgen/eval/resistance.py:165-189`.

The source registry also remains conservative. It records candidate and validation-candidate sources but no default calibration fixtures: `kayakgen/eval/calibration.py:70-165`.

## Verification

Focused tests were run with bytecode and pytest cache disabled:

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_resistance.py tests/test_compare.py tests/test_cli.py -p no:cacheprovider`

Result: `45 passed in 8.69s`.

I also directly exercised the claim helper and source-record validation paths to verify O-001 and O-003.

## Verdict Rationale

The current implementation can proceed as an uncalibrated raw comparative evaluator, and the workflow can advance with these findings recorded. The default output is conservative and tested.

The main acceptance work still owed is not cosmetic: typed fit records, stricter fixture validation, rejected-fit gates, envelope checks, raw fallback wording, and reproducible fixture/residual artifacts must land before any calibrated resistance claim or calibrated CLI/report wording is accepted.