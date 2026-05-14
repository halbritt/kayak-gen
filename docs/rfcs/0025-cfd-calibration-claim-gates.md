# RFC 0025: CFD and Calibration Claim Gates

Status: landed claim-gates
Date: 2026-05-13
Context: revises the wording obligations in RFC 0005, RFC 0012, RFC 0015,
RFC 0017, and RFC 0019 without changing their raw-evaluator or dispatch
contracts.

## Problem

The project now has several numerically precise outputs that are intentionally
not equivalent: analytical resistance from RFC 0005, raw CFD job records from
RFC 0015, candidate source records from RFC 0012, and proposed calibration
fixtures from RFC 0019. Those outputs are useful, but they can be mislabeled as
calibrated, validated, or final design fitness if downstream code only sees a
number.

That would make sweep ranking and UI copy stronger than the evidence supports.

## Goals

- Define explicit claim gates for raw CFD, uncalibrated analytical resistance,
  validation fixtures, calibration fixtures, fitted models, and final design
  fitness.
- Make claim state machine-readable in result metadata and visible in CLI/web
  wording.
- Prevent validation-only data from silently promoting a model to calibrated.
- Preserve useful raw and comparative outputs while keeping their claims narrow.
- Give future workflows a single checklist for when "uncalibrated" warnings may
  be removed.

## Non-Goals

- Selecting a calibration dataset.
- Running or validating a real CFD solver.
- Defining a single hull optimization score.
- Replacing source review, fixture review, or final design testing.

## Proposal

Introduce a small claim taxonomy used consistently by resistance curves, CFD run
records, fixture manifests, reports, CLI output, web UI, and sweep/Pareto
metadata:

| Claim state | Meaning | May be used for |
|---|---|---|
| `raw_unvalidated` | Solver or fixture adapter produced raw records with no accepted validation. | Debugging, provenance, adapter smoke tests. |
| `uncalibrated_comparative` | Analytical resistance is deterministic and sanity checked but has no accepted calibration fixture. | Comparative filtering with warnings. |
| `validation_fixture` | Source-backed measured or deterministic fixture data that can test parser/model behavior but cannot tune the kayak model. | Regression, adapter validation, external comparison. |
| `calibration_fixture_candidate` | A source looks plausible for calibration but has not passed rights, extraction, hull-envelope, and measurement review. | Human review only. |
| `calibration_fixture` | A fixture passed source review and is accepted for fitting a named model within a declared envelope. | Fitting and calibration tests. |
| `calibrated_model` | A named model version was fitted against accepted calibration fixtures and passed acceptance metrics. | Calibrated prediction within its envelope. |
| `validated_design_fitness` | A design decision combines calibrated resistance with other accepted design criteria and explicit validity limits. | Final scoring only after a future RFC accepts that scoring contract. |

Every result record that contains drag, resistance, residual, or design-fitness
numbers should expose:

```python
claim_state: str
accepted_uses: list[str]
calibration_fixture_ids: list[str]
validation_fixture_ids: list[str]
model_version: str | None
fit_status: str | None
validity_envelope: dict[str, object] | None
warnings: list[str]
```

Current RFC 0005 curves remain `uncalibrated_comparative`. Current RFC 0015 CFD
run records remain `raw_unvalidated`. Fixture adapter success does not change
either state. A validation fixture can reduce parser or adapter uncertainty, but
it cannot remove final-prediction or uncalibrated warnings.

Promotion rules:

- Raw CFD may become a validation artifact only when the adapter, command,
  inputs, and outputs are deterministic and source/provenance metadata are
  recorded.
- A validation fixture may become a calibration fixture only after source rights,
  extraction method, measured quantity, hull-class applicability, units,
  uncertainty, and validity envelope are reviewed.
- A model may become calibrated only after fitting code records accepted
  calibration fixture IDs, fitted parameters, metrics, residuals, and the
  envelope where claims apply.
- A final design-fitness score may use calibrated resistance only when another
  RFC defines how resistance is combined with hydrostatics, stability, class
  constraints, and user goals.

## Acceptance Criteria

- Resistance and CFD result metadata cannot omit claim state.
- Current analytical resistance still emits an uncalibrated/comparative claim
  and final-prediction warning.
- Current CFD job records still emit raw/unvalidated semantics even on command
  success.
- Validation fixtures do not change resistance calibration status.
- Calibration fixture promotion requires explicit review metadata, fixture IDs,
  rights status, extraction status, hull envelope, and measured quantity.
- Fitted model metadata records fit status, metrics, fixture IDs, and the
  accepted validity envelope before output may stop saying uncalibrated.
- CLI, web, reports, and sweep metadata use the same claim names or lossless
  equivalents.
- Tests cover at least one negative case for each forbidden overclaim: raw CFD
  as validated, validation fixture as calibration fixture, uncalibrated
  resistance as calibrated, and calibrated resistance as final design fitness.

## Open Questions

- Should claim states live in a shared `kayakgen.eval.claims` module or remain
  per-evaluator metadata until a second calibrated model exists?
- What exact warning strings should be stable API versus human-readable copy?
- Should sweep ranking reject uncalibrated resistance by default, or allow it
  with an explicit exploratory flag?

## Implementation Path

1. Add shared claim constants or an equivalent typed metadata contract.
2. Update resistance and CFD records to expose the contract without changing
   current raw behavior.
3. Add tests for forbidden promotions.
4. Wire CLI/web/report wording to the same metadata fields.
5. Let RFC 0026 and RFC 0027 use these gates for fixture adapter and calibrated
   resistance work.
