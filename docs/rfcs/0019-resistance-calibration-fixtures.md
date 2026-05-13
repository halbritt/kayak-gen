# RFC 0019: Resistance Calibration Fixtures

Status: proposed
Date: 2026-05-13
Context: builds on RFC 0012 resistance provenance and the workflow 0023 source
review that accepted an open Pacific-canoe dataset only as a validation
candidate, not a kayak calibration anchor.

## Problem

Resistance curves now carry metadata and warn that current analytical output is
uncalibrated. The project still lacks checked-in calibration fixtures with
source rights, extraction provenance, hull applicability, and regression
expectations.

Without fixture rules, future calibration work can become an undocumented
spreadsheet exercise or silently tune models against data outside the kayak
design envelope.

## Goals

- Define the fixture format for measured or source-backed resistance data.
- Require source license, extraction method, hull class, and validity envelope.
- Keep validation fixtures distinct from calibration fixtures.
- Provide a review path for accepting the first `calibrated_kayak_v1` dataset.
- Preserve raw analytical output until a fixture is accepted.

## Non-Goals

- Choosing a canonical calibration dataset in this RFC.
- Claiming the current resistance model is calibrated.
- Replacing CFD, tow-tank validation, or on-water testing.
- Checking in data with unclear rights.
- Optimizing hulls to a single resistance score.

## Dependencies

- RFC 0012 for resistance metadata, source registry, and warning behavior.
- RFC 0005 for the analytical resistance estimator being calibrated.
- A source-review decision for any dataset promoted from candidate to fixture.

## Proposal

Add a fixture schema under a future data directory, for example
`data/resistance/fixtures/<fixture_id>/manifest.json`:

```python
ResistanceCalibrationFixture(
    fixture_id: str,
    title: str,
    source_citation: str,
    source_url: str,
    rights_status: str,
    extraction_method: str,
    hull_class: str,
    measured_quantity: str,
    speed_units: str,
    force_units: str,
    valid_fn_range: tuple[float, float],
    valid_l_b_range: tuple[float, float],
    intended_use: Literal["calibration_fixture", "validation_fixture"],
    warnings: list[str],
)
```

Each fixture contains machine-readable rows of speed, resistance, displacement,
trim/sinkage assumptions if known, and uncertainty when available. Raw source
images or PDFs are not required unless rights allow them; extracted rows must
record who extracted them, when, and how.

Promotion from candidate to calibration fixture requires a small review note
answering:

- whether rights permit checked-in derived data;
- whether the hull class overlaps the project design envelope;
- whether resistance values are measured rather than model-derived;
- what model parameters may be tuned against the fixture;
- what should remain validation-only.

## Acceptance Criteria

- Fixture schema and manifest validation exist.
- The source registry can distinguish candidate, validation fixture, and
  calibration fixture records.
- No fixture can be accepted without explicit rights and extraction metadata.
- Regression tests load fixtures and verify units, monotonic speed ordering,
  and declared validity ranges.
- Current resistance output remains `uncalibrated` until at least one
  calibration fixture is accepted by source review.
- Documentation explains why validation fixtures do not imply calibration.

## Open Questions

- Can the project obtain a licensable measured sea-kayak resistance dataset?
- Should the Edinburgh Pacific-canoe dataset become a validation fixture even
  though it is outside the sea-kayak design envelope?
- Should fixtures store dimensional hull geometry, nondimensional coefficients,
  or both?
- What error metric should gate calibration: force residuals, coefficient
  residuals, rank correlation, or speed-weighted aggregate error?

## Implementation Path

- Step 1 - Add fixture manifest schema and validation tests.
- Step 2 - Extend the source registry with fixture states and review metadata.
- Step 3 - Add one validation fixture only if rights and extraction metadata are
  clear.
- Step 4 - Add calibration fitting code only after a kayak-class fixture is
  accepted.
- Step 5 - Update resistance output status from `uncalibrated` only when a
  calibrated model version is explicitly selected.

## Domain Modeling

Resistance calibration fixtures are evaluator reference data and provenance
records. They are not hull-domain entities; they constrain how resistance read
models may claim calibration.
