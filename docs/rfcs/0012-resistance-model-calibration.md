# RFC 0012: Resistance Model Calibration

Status: proposed
Date: 2026-05-13
Context: RFC 0005 is partial. The current ITTC estimator is usable, while the
Michell implementation is documented as an exploratory fast-filter signal.

## Problem

Resistance output currently looks numerically precise, but workflow 0010 made
clear that RFC 0005 acceptance is not landed. The analytical model needs
metadata, validity warnings, calibration provenance, and a way to separate raw
model output from calibrated design-score output.

Without that separation, sweeps and future Pareto ranking can optimize a signal
that is presented as stronger than it is.

## Human Decisions Recorded 2026-05-13

- Prefer published kayak/canoe resistance data as the first calibration source,
  if a usable and licensable dataset can be found.
- Initial candidates to vet are Sea Kayaker-derived resistance tables and
  peer-reviewed kayak passive-drag data such as Gomes et al. (2017). The former
  is broad and sea-kayak-specific but appears to mix historically published
  review data with model-derived values; the latter is experimental but narrow
  to a sprint K1 kayak and simulated paddler weights.
- Until the dataset is selected and checked into an explicit data/provenance
  format, analytical output stays `uncalibrated`.
- Workflow 0012 reviewed the initial candidate set and did not accept any
  source as canonical calibration data. Sea Kayaker-derived tables remain
  citation-only/model-to-model context. Gomes and Tzabiras sprint-K1 studies are
  validation candidates, not general sea-kayak calibration anchors.

## Goals

- Make resistance provenance explicit in every curve.
- Preserve raw ITTC/Michell output for comparative filtering.
- Define a calibration data format and metadata contract.
- Surface validity warnings by Froude range, hull slenderness, and calibration
  status.
- Provide a path to retire the RFC 0005 expected-failure tests honestly.

## Non-Goals

- RANS, OpenFOAM, panel-method integration, or seakeeping.
- Claiming final performance prediction accuracy.
- Claiming a canonical dataset before source, license, hull coverage, and
  extraction quality are reviewed.
- Replacing sweep/Pareto decisions with a single score.

## Proposal

Extend resistance output with metadata:

- model family (`raw_ittc_michell`, future `calibrated_kayak_v1`);
- calibration name;
- calibration status;
- calibration version;
- source citation, source license, and extraction method;
- Froude and slenderness validity ranges;
- quadrature settings;
- accepted use (`comparative_filter`, `final_prediction`);
- warnings.

Add a future `ResistanceCalibration` model:

```python
name: str
valid_fn_min: float
valid_fn_max: float
valid_l_b_min: float
valid_l_b_max: float
form_factor_k: float
wave_scale: float
source_notes: str
```

The first implementation should add metadata and warnings without pretending a
canonical calibration dataset has been chosen.

Add a `ResistanceSourceRecord` registry for candidate sources. A source record
has `source_id`, `title`, `url`, `source_type`, `intended_use`,
`measured_data`, `hull_class`, `rights_status`, `extraction_status`, `notes`,
and `warnings`. The initial registry includes only `citation_only` and
`validation_candidate` records; it has no `calibration_fixture` records.

Current raw curves should use `model_family = "raw_ittc_michell"`,
`calibration_status = "uncalibrated"`, `accepted_use =
["comparative_filter"]`, and warnings containing both a final-prediction
disclaimer and `uncalibrated_no_validity_envelope` until humans choose raw
validity ranges. The Wigley parabolic hull case is a verification fixture for
the numerical implementation, not a kayak calibration dataset.

## Acceptance Criteria

- `ResistanceCurve` declares whether it is raw or calibrated.
- Current curves say they are accepted for comparative filtering only.
- Current curves leave calibration/provenance fields unset rather than implying
  a source-backed calibration.
- The default source registry contains candidate records but no calibration
  fixture records.
- Quadrature settings and physical constants are recorded.
- Curves include warnings when outside declared validity ranges.
- Until raw validity ranges are selected, curves include an explicit
  no-validity-envelope warning.
- Existing RFC 0005 xfails remain until real acceptance criteria are met or the
  RFC is revised.
- Tests cover metadata serialization and warning behavior.

## Open Questions

- Can the project obtain explicit permission or an open measured dataset for
  checked-in calibration fixtures?
- Should calibration tune total resistance only, or viscous form factor and wave
  component separately?
- Is the original 200 ms curve budget still real acceptance, or should it be
  relaxed for calibrated curves?

## Implementation Path

- Step 1 - Add resistance metadata fields.
- Step 2 - Populate raw model metadata in `resistance_curve`.
- Step 3 - Add validity warning helpers.
- Step 4 - Add tests while preserving existing raw APIs.
- Step 5 - Add candidate source registry.
- Step 6 - Add calibrated wrapper only after a dataset passes source review.

## Domain Modeling

Resistance calibration is evaluator metadata around an analytical model. It is a
read-model concern, not a new hull-domain concept.
