# RFC 0042: Resistance Calibration Fixture Successor

Status: proposed
Date: 2026-05-14
Context: successor to RFC 0019 after RFC 0025 claim gates and RFC 0027
acceptance gates landed. Current resistance output remains raw ITTC/Michell
comparative screening. The Edinburgh Pacific-canoe source remains an open
measured validation candidate only, not a kayak calibration fixture.
Disposition of predecessor: RFC 0042 narrows RFC 0019 into the current
source-review and fixture-promotion successor. RFC 0027 remains the landed
acceptance gate for `SourceUse`, fit records, and calibrated-prediction
wording.

## Problem

RFC 0019 described the fixture format broadly, and RFC 0027 landed the claim
gates that prevent validation-only data from becoming calibrated resistance.
What remains is narrower: the project needs a source-review and fixture-ingest
successor that can accept or reject concrete measured resistance sources without
inventing fixture data, changing default resistance claims, or treating adapter
fixtures as hydrodynamic evidence.

The current backlog item still says "Resistance Calibration Fixture", but the
first useful successor is not a calibrated model. It is an evidence packet and
promotion workflow that can answer, for each candidate source, whether it is:

- citation-only context;
- a validation candidate or validation fixture;
- a calibration fixture candidate;
- an accepted calibration fixture for a later fitting workflow; or
- rejected for rights, extraction, measurement, or envelope reasons.

Until that boundary exists, calibration work risks either stalling on informal
source notes or overcorrecting by checking in rows that the project has no
right to use or no basis to apply to kayak-scale hulls.

## Goals

- Narrow RFC 0019 into an implementable successor focused on source review,
  provenance, and fixture promotion.
- Keep RFC 0027's existing `SourceUse` values and calibrated-prediction gate as
  the authority for claim wording.
- Define the minimum evidence packet required before any measured source can
  become a calibration fixture.
- Allow useful validation fixtures without letting them remove uncalibrated
  warnings.
- Keep the current raw ITTC/Michell evaluator and fixture-local-command CFD
  adapter outputs explicitly uncalibrated or raw/unvalidated.
- Make negative outcomes first-class: a source review may conclude
  validation-only, citation-only, or rejected.
- Land this scope as documentation/RFC work only; runtime implementation
  belongs to a later accepted workflow.

## Non-Goals

- Selecting or naming the first accepted kayak calibration fixture.
- Checking in measured rows, digitized tables, source PDFs, or derived data in
  this RFC.
- Claiming any current source is licensed, in-envelope, or accepted for
  calibration beyond the statuses already recorded in earlier RFCs.
- Fitting a calibrated resistance model or changing default evaluator output.
- Defining final prediction, final design fitness, Pareto default scoring, or
  optimization weights.
- Treating CFD fixture-adapter output as measured hydrodynamic data.
- Making capsize, high-angle stability, seaworthiness, or secondary-stability
  claims.

## Dependencies

- RFC 0005 for the raw analytical ITTC/Michell resistance estimator.
- RFC 0012 for resistance metadata and the source registry.
- RFC 0019 for the broad fixture schema this RFC narrows.
- RFC 0025 for shared claim gates and forbidden overclaims.
- RFC 0026 for the raw/unvalidated fixture-local-command adapter boundary.
- RFC 0027 for source-stage mapping, fit records, and calibrated-prediction
  acceptance gates.

## Proposal

Treat the next resistance calibration fixture workflow as a source-review and
fixture-promotion slice, not as model calibration. The successor should add a
small review packet for candidate measured resistance sources and a fixture
promotion record that is separate from both raw resistance curves and CFD run
records.

### Source Review Packet

Each candidate source considered for fixture promotion must have a review packet
with at least:

- stable source ID and human citation;
- source URL, DOI, archive reference, or other durable locator when available;
- rights and license statement for original material and derived rows;
- source type, such as tow-tank measurement, passive-drag experiment, on-water
  measurement, model-derived table, or secondary citation;
- measured quantity and units, with explicit distinction between measured force
  and model-derived resistance;
- hull description, class, dimensions, displacement or load state, and any
  available lines/offsets or coefficients;
- speed range and, when enough geometry is known, Froude range;
- trim, sinkage, appendage, paddler, and water-property assumptions when known;
- extraction method, extractor identity, date, tooling, and uncertainty notes;
- review verdict and reasons.

The source-use verdicts are:

- `citation_only`;
- `validation_candidate`;
- `validation_fixture`;
- `calibration_fixture_candidate`;
- `calibration_fixture`.

These source-use verdicts must map losslessly onto the existing RFC 0027
`SourceUse` values. Do not create a second runtime taxonomy unless a later
implementation RFC proves the existing enum cannot represent the state.
The explicit RFC 0027 mapping is:

| Review verdict | RFC 0027 stage label | Runtime `SourceUse` value |
| --- | --- | --- |
| `citation_only` | `candidate_source` | `citation_only` |
| `validation_candidate` | `candidate_source` | `validation_candidate` |
| `calibration_fixture_candidate` | `candidate_source` | `calibration_fixture_candidate` |
| `validation_fixture` | `validation_fixture` | `validation_fixture` |
| `calibration_fixture` | `calibration_fixture` | `calibration_fixture` |

A review may also end in:

- `rejected`.

`rejected` is a terminal review outcome, not a fixture source-use value. It
must not be used to create a runtime fixture record that can participate in
validation, fitting, or claim gates, and it must not be added as a runtime
`SourceUse` enum member.

### Promotion Rules

A source may become a validation fixture when rights, units, extraction, and
rows are adequate for parser, reporting, or holdout checks, even if the hull
class is outside the kayak calibration envelope.

A source may become a calibration fixture only when review explicitly accepts:

- rights for checked-in or reproducibly derived machine-readable data;
- measured resistance or drag data rather than purely model-derived values;
- hull applicability to the kayak design envelope under review;
- displacement, load, and speed/Froude ranges;
- extraction method and uncertainty treatment;
- row schema and unit normalization;
- intended fit parameters or explicit statement that fitting is deferred.

Loading rows, passing parser tests, or producing plausible residuals is not
promotion. Promotion requires a review verdict that names the fixture ID,
version, accepted use, validity envelope, and reasons.

### Fixture Record Shape

The successor should keep the RFC 0019 fixture idea but split source review from
row data. A future implementation may serialize a fixture manifest in a shape
like:

```python
ResistanceFixtureManifest(
    fixture_id: str,
    version: str,
    source_id: str,
    title: str,
    source_use: SourceUse,
    review_verdict: str,
    rights_status: str,
    source_type: str,
    measured_quantity: str,
    speed_units: str,
    resistance_units: str,
    hull_class: str,
    hull_dimensions: dict[str, float | str | None],
    displacement_or_load: dict[str, float | str | None],
    valid_fn_range: tuple[float, float] | None,
    valid_speed_range_mps: tuple[float, float] | None,
    extraction_method: str,
    uncertainty_notes: list[str],
    accepted_fit_parameters: list[str],
    warnings: list[str],
)
```

This RFC does not require that exact Python type or path. It records the
minimum information the later implementation must preserve.

### Claim Boundaries

Current resistance curves remain `uncalibrated_comparative`. Current CFD job
and fixture-local-command records remain `raw_unvalidated`. Validation fixtures
may appear in reports, holdout metrics, or parser tests, but they must not be
listed as calibration fixture IDs for an accepted fit.

Resistance output may stop saying uncalibrated only under RFC 0027's calibrated
prediction gate: a selected named model version has `accepted_fit`, accepted
calibration fixture IDs, persisted fit metrics and residuals, and an envelope
that contains the evaluated hull and speed.

## Acceptance Criteria

- A source-review packet format is documented with rights, extraction,
  measurement, hull-envelope, units, uncertainty, and verdict fields.
- Source-use verdicts map to RFC 0027's existing `SourceUse` vocabulary without
  silently promoting current registry records, while rejected reviews stay out
  of fixture and fit records.
- Later implementation tests assert the five existing RFC 0027 `SourceUse`
  values are preserved and that `rejected` review outcomes serialize only as
  review records, not runtime fixture source-use values.
- No current source is promoted to `validation_fixture` or
  `calibration_fixture` by this RFC alone.
- Validation fixtures remain usable only for validation, parser, report, or
  holdout behavior and cannot remove uncalibrated warnings.
- Calibration fixture promotion requires explicit review metadata and cannot be
  inferred from row loading, parser success, or residual metrics.
- CFD fixture-adapter results remain excluded from measured-source calibration
  fixtures.
- Documentation and tests for any later implementation preserve the forbidden
  overclaims from RFC 0025 and RFC 0027.

## Open Questions

- What specific candidate source should receive the first full review packet?
- Can the project obtain a licensable, measured sea-kayak or close
  kayak-envelope resistance dataset with enough geometry and load metadata?
- Should the Edinburgh Pacific-canoe source remain a validation candidate or be
  promoted only to a validation fixture after row extraction and rights review?
- How much hull geometry is enough for calibration applicability: dimensions
  and coefficients, offsets, generated approximation, or full lines plan?
- Should uncertainty be required numerically for calibration fixtures, or may
  some sources carry qualitative extraction uncertainty with stricter metrics?
- Which fit parameters are acceptable for the first calibrated model: ITTC form
  factor, Michell wave scale, component scales, or a residual correction?

## Implementation Path

1. Add a source-review packet template and fixture-promotion checklist.
2. Apply the template to one candidate source without promoting it unless the
   review evidence is complete.
3. Add manifest validation and source-use mapping tests.
4. Add validation-fixture ingest only if rights and extraction metadata are
   sufficient.
5. Add calibration-fixture ingest only after source review accepts a
   kayak-envelope measured source.
6. Defer fitting and any calibrated-output wording to a separate accepted-fit
   workflow under RFC 0027.

## Domain Modeling

Resistance calibration fixtures are evaluator reference data with provenance
and claim metadata. They are not hull-domain entities, not CFD solver outputs,
and not design-fitness decisions. The aggregate boundary remains the source and
fixture review record that constrains what resistance read models may claim.
