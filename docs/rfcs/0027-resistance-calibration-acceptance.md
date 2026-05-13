# RFC 0027: Resistance Calibration Acceptance

Status: proposed
Date: 2026-05-13
Context: revises RFC 0019 where useful and uses RFC 0025 claim gates to define
when resistance output may stop saying uncalibrated.

## Problem

RFC 0019 defines calibration fixtures, but acceptance still needs sharper rules
for promotion, fitting, metrics, and output wording. A project can have useful
candidate data and validation fixtures while still having no calibrated
resistance model. The implementation needs an explicit line between "loaded a
fixture" and "fit passed acceptance."

## Goals

- Define promotion from source candidate to validation fixture to calibration
  fixture.
- Define fitting status and metrics for a named calibrated resistance model.
- Keep validation fixtures useful without letting them remove uncalibrated
  warnings.
- State exactly when resistance output may stop saying uncalibrated.
- Preserve RFC 0005 raw ITTC/Michell output as an exploratory comparative tier.

## Non-Goals

- Selecting the first sea-kayak calibration dataset.
- Claiming CFD or tow-tank validation where no accepted source exists.
- Defining final Pareto or design-fitness scoring.
- Requiring every user to run fitting code during ordinary resistance
  evaluation.

## Proposal

Revise RFC 0019 into a three-stage acceptance model.

Stage 1, candidate source:

- rights and citation are known enough to discuss;
- data may be incomplete, out of envelope, model-derived, or not yet extracted;
- current output remains `uncalibrated_comparative`.

Stage 2, validation fixture:

- rights permit checked-in derived data or manifest-only validation;
- extraction method, units, rows, and uncertainty assumptions are recorded;
- fixture can test parsers, reports, or model behavior;
- fixture is not accepted for fitting the default kayak calibration.

Stage 3, calibration fixture:

- source review accepts rights, measured quantity, hull class, displacement,
  speed/Froude range, L/B range, extraction method, and applicability;
- fixture has a stable ID and version;
- rows are machine-readable and unit-normalized;
- review states which parameters may be fitted and which metrics gate success.

Add fitting metadata:

```python
ResistanceFitRecord(
    model_version: str,
    fit_status: Literal["not_fit", "candidate_fit", "accepted_fit", "rejected_fit"],
    calibration_fixture_ids: list[str],
    validation_fixture_ids: list[str],
    fitted_parameters: dict[str, float],
    metrics: dict[str, float],
    residuals_ref: str,
    validity_envelope: dict[str, object],
    warnings: list[str],
)
```

Initial accepted metrics should include at least:

- force RMSE and mean absolute percentage error over the fitted speed range;
- bias by low/mid/high Froude bands when enough rows exist;
- monotonicity and non-negative resistance checks;
- holdout or validation-fixture error if a validation fixture is declared.

Resistance output may stop saying `uncalibrated` only when:

- at least one `calibration_fixture` is accepted;
- a named model version has an `accepted_fit`;
- fit metrics and residuals are persisted and tests assert the acceptance
  thresholds;
- the evaluated hull/speed lies inside the accepted validity envelope;
- output still warns when outside the envelope or when falling back to the raw
  model.

## Acceptance Criteria

- Fixture records distinguish `candidate_source`, `validation_fixture`, and
  `calibration_fixture`.
- Promotion to calibration fixture requires review metadata and cannot happen
  by loading rows alone.
- Fit records distinguish `not_fit`, `candidate_fit`, `accepted_fit`, and
  `rejected_fit`.
- The default resistance evaluator remains uncalibrated until a selected model
  version has an accepted fit.
- Validation fixtures can appear in metrics without being listed as calibration
  fixture IDs.
- Tests cover rejected promotion, validation-only fixture behavior, accepted
  fit metadata, out-of-envelope warnings, and raw fallback wording.
- CLI/web/report output may use calibrated wording only when the selected curve
  metadata satisfies the accepted-fit gate.

## Open Questions

- Which metric thresholds are appropriate for the first kayak-class fixture?
- Should the first calibrated model fit ITTC form factor, Michell wave scale, or
  a speed-dependent residual correction?
- Should fixture rows store dimensional force, nondimensional coefficients, or
  both?
- Should calibration models be opt-in by version or become default inside their
  validity envelope after final review?

## Implementation Path

1. Add fixture promotion status and review metadata.
2. Add fit-record schema and serialization.
3. Implement candidate fitting without changing default output claims.
4. Add acceptance metrics and negative tests for overclaiming.
5. Switch selected calibrated model output only after a final review accepts the
   fit and envelope.

