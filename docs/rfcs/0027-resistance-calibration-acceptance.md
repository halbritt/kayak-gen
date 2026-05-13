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

The three stage labels are normative groupings over the existing source-state
vocabulary, not a second serialized taxonomy. The implementation source state
remains `kayakgen/eval/calibration.py::SourceUse` with these five literal
values:

| RFC 0027 stage label | Existing `SourceUse` values | Required behavior |
|---|---|---|
| `candidate_source` | `citation_only`, `validation_candidate`, `calibration_fixture_candidate` | Records are usable for citation or review queues only. They do not provide validation evidence, calibration fixture IDs, or calibrated-model evidence. Current registry records stay in this grouping unless a later review explicitly promotes them. |
| `validation_fixture` | `validation_fixture` | Data may exercise parsers, reports, adapter behavior, and holdout metrics. It cannot fit the default model, change resistance output to `calibrated_model`, or remove uncalibrated warnings. |
| `calibration_fixture` | `calibration_fixture` | Data passed source and fixture review and may be used to fit a named model within a declared envelope. Promotion requires explicit fixture metadata and review status; loading rows is insufficient. |

Do not add a `candidate_source` literal or any parallel source-state enum. UI,
report, or documentation surfaces may display the three stage labels only as
derived groupings from `SourceUse`.

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

RFC 0027 inherits RFC 0025's claim gates. Specifically, it inherits the model
promotion rule that a model may become calibrated only after fitting code
records accepted calibration fixture IDs, fitted parameters, metrics,
residuals, and the envelope where claims apply. The shared implementation gate
for calibrated resistance prediction is
`kayakgen/eval/claims.py::claim_allows_calibrated_prediction`; RFC 0027 work
must extend and harden that helper rather than creating a resistance-specific
parallel helper. For resistance fit records, the canonical passing status is
`accepted_fit`. Legacy migration aliases, validation fixtures, or non-empty
metrics alone must not satisfy the calibrated-prediction gate.

The RFC 0025 forbidden-overclaim rules also remain in force: raw CFD must not
be treated as validated, a validation fixture must not be treated as a
calibration fixture, uncalibrated resistance must not be treated as calibrated,
and calibrated resistance must not be treated as final design fitness.

Resistance output may stop saying `uncalibrated` only when:

- selected curve metadata satisfies `claim_allows_calibrated_prediction`;
- at least one accepted `calibration_fixture` is referenced by ID;
- a named model version has an `accepted_fit`;
- fit metrics and residuals are persisted and tests assert the acceptance
  thresholds;
- the evaluated hull/speed lies inside the accepted validity envelope;
- output still warns when outside the envelope or when falling back to the raw
  model.

## Acceptance Criteria

- Fixture records keep the existing five `SourceUse` values and may group them
  under `candidate_source`, `validation_fixture`, and `calibration_fixture`
  only through the normative mapping table above.
- No current default registry record becomes a validation fixture or calibration
  fixture from this vocabulary reconciliation alone.
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
  metadata satisfies `claim_allows_calibrated_prediction`.

## Open Questions

- Which metric thresholds are appropriate for the first kayak-class fixture?
- Should the first calibrated model fit ITTC form factor, Michell wave scale, or
  a speed-dependent residual correction?
- Should fixture rows store dimensional force, nondimensional coefficients, or
  both?
- Should calibration models be opt-in by version or become default inside their
  validity envelope after final review?

## Implementation Path

1. Reconcile fixture stage wording with the existing `SourceUse` literals and
   keep current registry records as candidates or citation-only records.
2. Add fit-record schema and serialization.
3. Extend `claim_allows_calibrated_prediction` so RFC 0027 calibrated
   prediction requires `accepted_fit` and complete accepted-fit evidence.
4. Implement candidate fitting without changing default output claims.
5. Add acceptance metrics and negative tests for overclaiming.
6. Switch selected calibrated model output only after a final review accepts the
   fit and envelope.
