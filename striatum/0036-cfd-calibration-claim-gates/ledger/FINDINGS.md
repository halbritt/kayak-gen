author: operator [self-declared: operator-0036-ledger]

# Findings ledger - workflow 0036 CFD calibration claim gates

run: run_38b1b70956eb48eabbf39449375579ed
job: findings_ledger
date: 2026-05-13
gate_result: accept_with_findings

## Scope

This ledger consolidates the traceability, domain/source, and ops reviews for
RFC 0025. The accepted implementation slice is limited to claim-state metadata,
promotion gates, visible warnings, and negative tests over the existing raw
resistance and local CFD dispatch surfaces.

This ledger does not authorize real solver success, validated CFD drag,
accepted calibration fixtures, calibrated resistance models, or final
design-fitness scoring.

## Stats

- Review artifacts read: 3
- Raw review findings: 11
- Deduplicated accepted findings: 6
- Safe-now implementation areas: claim metadata, report gating, source/fixture
  state vocabulary, CLI/web wording, forbidden-promotion tests
- Deferred areas: real solver validation, calibration datasets, fitted models,
  validity envelopes for calibrated prediction, final design-fitness scoring

## Accepted Findings

### F-001 - Result records lack the shared RFC 0025 claim contract

- Severity: high
- Review sources: T-001, DS-001, DS-002, O-001
- Affected files: `kayakgen/eval/contract.py`,
  `kayakgen/eval/resistance.py`, `kayakgen/eval/cfd/jobs.py`,
  `tests/test_resistance.py`, `tests/test_cfd_jobs.py`

Current resistance metadata uses legacy fields such as `calibration_status`,
`accepted_use`, optional provenance fields, and warning strings. Current CFD
records use `result_semantics = "raw_unvalidated"`. Those fields are truthful
for today's raw outputs, but they are not the shared RFC 0025 contract:
`claim_state`, `accepted_uses`, fixture ID lists, model version, fit status,
validity envelope, and warnings.

Required action:

- Add a shared claim metadata model, constants, or lossless equivalent used by
  resistance and CFD result records.
- Populate current analytical resistance as
  `claim_state = "uncalibrated_comparative"` with comparative-filter accepted
  use and final-prediction/no-validity-envelope warnings.
- Populate current CFD job, run, profile, and raw adapter records as
  `claim_state = "raw_unvalidated"` with no calibrated or validated accepted
  uses.
- Preserve compatibility fields such as `calibration_status`, `accepted_use`,
  and `result_semantics` only as aliases or legacy fields; they must not be the
  only source of truth.
- Add JSON round-trip and omission tests proving claim state cannot be absent
  from result records that carry drag, resistance, residual, or design-fitness
  numbers.

### F-002 - Report provenance can trust self-declared final-prediction fields

- Severity: high
- Review sources: O-002, DS-004
- Affected files: `kayakgen/search/compare.py`, `tests/test_compare.py`

Comparison reports currently accept `Rt_N_last` provenance when legacy
metadata is not `uncalibrated` and includes `final_prediction` in accepted use.
That can be forged before a model has accepted calibration fixture IDs, fit
status, model version, metrics, or a validity envelope.

Required action:

- Gate accepted report provenance on the full claim contract.
- A resistance metric may be accepted as calibrated prediction only when the
  record carries `claim_state = "calibrated_model"`, nonempty accepted
  calibration fixture IDs, model version, passed fit status or fit metrics, and
  an applicable validity envelope.
- Keep default Pareto/report behavior from treating raw comparative resistance
  as accepted final prediction.
- Add negative tests for forged legacy metadata, missing fixture IDs, missing
  fit evidence, missing validity envelope, and any attempt to treat calibrated
  resistance as final design fitness.

### F-003 - Source and fixture states cannot safely model validation fixtures

- Severity: medium
- Review sources: DS-003, O-003
- Affected files: `kayakgen/eval/calibration.py`,
  `tests/test_resistance.py`

The registry is conservative today and has no default calibration fixture.
However, the state vocabulary jumps from `validation_candidate` to
`calibration_fixture` and can represent a calibration fixture without the
fixture-review fields RFC 0019 and RFC 0025 require.

Required action:

- Extend the vocabulary to distinguish `validation_fixture` and
  `calibration_fixture_candidate` from accepted `calibration_fixture`, or split
  source candidate records from fixture manifests.
- Require fixture review metadata before any record can become a calibration
  fixture: fixture ID, rights status, extraction status, measured quantity and
  units, hull envelope, uncertainty or measurement notes, and validity ranges.
- Add negative tests proving validation-only records cannot remove
  uncalibrated resistance warnings and cannot become calibration fixtures by
  changing a single enum field.

### F-004 - Web compact metrics show resistance numbers without claim wording

- Severity: medium
- Review sources: T-002, O-004
- Affected files: `kayakgen/ui/web/controllers.py`,
  `kayakgen/ui/web/app.py`, `tests/test_web.py`

The analysis view shows resistance as a raw comparative filter and surfaces
warnings. The compact live metrics path returns and renders `Rv_N`, `Rw_N`, and
`Rt_N` without resistance claim metadata or warning text.

Required action:

- Carry resistance claim state and warning strings through `metrics_from_state`
  whenever at-speed resistance values are returned.
- Render a compact visible warning near the at-speed resistance lines, for
  example that resistance is a raw comparative filter and not final prediction.
- Add a headless web test that fails when compact metrics include resistance
  values without claim wording.

### F-005 - CLI evaluate writes resistance metadata without stdout claim wording

- Severity: low
- Review source: T-003
- Affected files: `kayakgen/cli/main.py`, CLI tests

`kayakgen evaluate` writes resistance metadata to JSON by default, but stdout
only reports the output path. The CFD commands already print raw/unvalidated
wording, so the resistance CLI surface is less explicit than the CFD surface.

Required action:

- When `kayakgen evaluate` includes resistance, print a compact warning such as
  `Resistance is uncalibrated/comparative only; see metadata`.
- Do not print that warning when `--skip-resistance` is used.
- Add CLI coverage for both paths.

### F-006 - Forbidden-promotion tests are incomplete

- Severity: medium
- Review sources: DS-004, O-001, O-002, O-003
- Affected files: `tests/test_resistance.py`, `tests/test_cfd_jobs.py`,
  `tests/test_compare.py`, `tests/test_web.py`

Existing tests cover today's honest raw warnings, unavailable CFD state, and
default source registry conservatism. They do not cover the complete RFC 0025
matrix of forbidden promotions.

Required action:

- Add focused negative tests for raw CFD as validated, validation fixture as
  calibration fixture, uncalibrated resistance as calibrated, and calibrated
  resistance as final design fitness.
- Tie those tests to the shared claim contract rather than to loose legacy
  strings alone.
- Keep the tests small and local to the surfaces being gated.

## No-Action Findings

- User guide, changelog, RFC index, and existing source registry wording do not
  currently overclaim calibrated resistance, validated CFD, real solver success,
  or final design fitness.
- Existing unavailable and mock-failure CFD profiles should remain raw and
  unvalidated; the safe slice should not add a real success path.
- Current analytical resistance remains useful as an exploratory comparative
  filter and should not be removed while claim gates are added.

## Safe-Now Implementation Scope

Implementers may:

- add shared claim-state constants or metadata models;
- attach claim metadata to existing resistance and CFD records;
- keep backward-compatible aliases for existing JSON consumers;
- harden comparison/report acceptance rules around the full claim contract;
- extend source/fixture state validation without adding real fixtures;
- add CLI and web warning text for currently displayed raw numbers;
- add unit and headless web tests for the forbidden-promotion cases.

Implementers must not:

- add calibrated model output;
- promote any current source to calibration fixture;
- treat validation fixtures as calibration fixtures;
- add a real solver success claim or validated CFD drag;
- add final design-fitness scoring;
- remove uncalibrated or final-prediction warnings from current resistance
  output.

## Deferred Items

- Selecting or checking in calibration datasets.
- Defining calibrated resistance fit metrics, model versions, and accepted
  validity envelopes.
- Running or validating OpenFOAM, SU2, hosted workers, or any other real CFD
  solver.
- Promoting raw CFD to validated drag.
- Defining final design-fitness scoring that combines resistance,
  hydrostatics, stability, constraints, and user goals.
- Replacing the raw analytical resistance model with an optimized or calibrated
  predictor.

## Implementation Guidance

Start with F-001 because the other gates need one canonical claim shape. Then
land F-002 and F-003 so future calibrated or fixture work cannot bypass the
claim gates. F-004 and F-005 are small visible-warning patches that can land in
the same implementation slice once claim metadata is available. F-006 should
land with the relevant gates rather than as broad fixture or solver work.
