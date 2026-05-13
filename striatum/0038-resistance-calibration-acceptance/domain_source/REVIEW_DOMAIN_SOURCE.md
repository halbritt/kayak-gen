Verdict intent: accept

# Domain/Source Review: Resistance Calibration Acceptance

## Sub-agent / Parallel Worker Usage
Parallel workers (via concurrent tool calls) were utilized to independently ingest and cross-reference the RFC corpus (0005, 0012, 0019, 0025, 0027) with the codebase implementations in `kayakgen/eval/resistance.py`, `kayakgen/eval/calibration.py`, and `tests/test_resistance.py`. No external sub-agents were spawned, as the native concurrent execution fully satisfied the disjoint investigation and reading requirements.

## Findings

### 1. Rights, Extraction, and Measured Quantity
The `ResistanceSourceRecord` model explicitly captures `rights_status`, `extraction_status`, `measured_data`, `measured_quantity`, and `measurement_units`. The current default registry accurately documents the rights and extraction limitations that prevent current candidates (e.g., the Edinburgh Pacific Canoe dataset, Gomes 2018) from serving as immediate calibration anchors.

### 2. Hull Envelope and Fixture Promotion
Fixture promotion logic is strictly and programmatically enforced. The `_calibration_fixture_requires_review` validator mandates that any record with an `intended_use` of `"calibration_fixture"` must explicitly furnish a `fixture_id`, `measured_quantity`, `measurement_units`, `hull_envelope`, `uncertainty_notes`, `validity_ranges`, and a `fixture_review_status` of `"accepted"`. This directly satisfies the promotion constraints detailed in RFC 0019 and RFC 0027.

### 3. Validation-Only Behavior and Acceptance Metrics
Validation fixtures and uncalibrated models are rigorously segregated. The test suite (specifically `test_validation_fixture_does_not_promote_resistance_claim`) empirically verifies that declaring a validation fixture does not inappropriately elevate the underlying claim state (`uncalibrated_comparative`) or falsely populate calibration fixture bindings.

### 4. Validity Envelopes and Fitting Metrics
The analytical evaluations correctly emit metadata matching the strict claim taxonomy defined in RFC 0025. `ResistanceMetadata` preserves `claim_state`, `accepted_uses`, `validity_envelope`, and `fit_metrics` attributes. Currently, `resistance_curve` defaults to `UNCALIBRATED_COMPARATIVE` and flags `"uncalibrated_no_validity_envelope"` alongside `"not_final_performance_prediction"`, honestly communicating its uncalibrated bounds.

## Conclusion
The implementation successfully constructs the metadata claim gates, fixture schemas, and verification tests required by the resistance calibration acceptance workflows. It robustly defends the uncalibrated nature of the existing Michell + ITTC models while surfacing the required schema structures to govern the eventual adoption of a canonical calibration dataset.
