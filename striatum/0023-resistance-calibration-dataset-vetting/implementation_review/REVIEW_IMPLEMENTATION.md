# Implementation review - resistance dataset vetting

author: operator [self-declared: operator-implementation-review]
run: run_6ca2095f019345e199943d5f46f0676f
job: review_implementation
date: 2026-05-13
verdict: accept_with_findings

## Scope

Reviewed the source inventory, RFC 0012, current resistance source registry,
and tests for the smallest safe implementation after this dataset-vetting pass.

## Findings

### I1 - Safe code change is a registry record plus tests

Add the Edinburgh DataShare dataset to `default_resistance_source_registry()`
as `intended_use="validation_candidate"`, with `measured_data=True`,
`rights_status` reflecting CC BY 4.0, and warnings that it is not a sea-kayak
calibration source. This is compatible with the existing `ResistanceSourceRecord`
model and should require no schema expansion.

Tests should assert:

- the Edinburgh source ID is present;
- it is not a `calibration_fixture`;
- it has measured data and CC BY 4.0 provenance;
- all default sources still avoid `calibration_fixture`.

Classification: actionable now.

### I2 - RFC/status docs need a precise partial outcome

RFC 0012 should record the new source as an open measured validation candidate
and explicitly state that it does not make current curves calibrated. The RFC
README can remain `proposed` for RFC 0012 because calibrated prediction is
still blocked.

Classification: actionable now.

### I3 - Do not add numeric fixture ingestion in this workflow

The workbook can be inspected and downloaded, but a checked-in numeric fixture
requires attribution and extraction metadata that the codebase does not yet
model. Adding rows opportunistically would create a second provenance problem.
If useful, a future RFC should define a validation fixture schema.

Classification: defer.

## Recommendation

Implement the registry/test/RFC update only. Do not change
`ResistanceMetadata.calibration_status`, `accepted_use`, comparison behavior,
or sweep scoring.
