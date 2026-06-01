author: reviewer-codex-gpt-5.5-003

# Design Review: Measured Stability Claim-Gate Threat Model

## Verdict

Changes requested. The direction is sound only if the implementation treats
`MeasuredStabilityFixture` validation as schema validation, not promotion, and
keeps analytical high-angle GZ claim promotion behind a separate accepted
comparison/fit gate. As framed, the stage-4 goal can be read as "accepted
fixture exists -> measured-or-better claim_state", which is the principal
overclaim risk.

## Trust Boundaries

- Raw rig data and reduction code -> `MeasuredStabilityFixture` JSON.
- Fixture schema validation -> operator promotion review.
- Accepted fixture -> analytical GZ comparison or calibration workflow.
- Claim metadata -> CLI, sweep, comparison, web, and search interpretation.

The main attack surface is editable JSON carrying self-attested path refs,
summary bounds, and `intended_use="measured_stability_fixture"`. The second
attack surface is generic claim metadata whose literals were designed around
resistance/CFD and do not carry evaluator kind or measured quantity.

## Findings

### P1: "Accepted fixture exists" is insufficient to flip analytical GZ claim state

`SOURCES.md` says the stage-4 goal is to flip high-angle GZ claim_state once an
accepted `measured_stability_fixture` exists
(`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md:7`).
That conflicts with RFC 0056's explicit gate: an accepted measured fixture is
necessary but not sufficient; the label changes only after a fitting workflow is
accepted and the analytical evaluator passes that workflow on the same hull
family (`docs/rfcs/0056-strain-gauged-gz-rig.md:69`,
`docs/rfcs/0056-strain-gauged-gz-rig.md:208`). RFC 0043 also requires the
generated-body evidence to match the evaluated hull before real GZ can be
emitted (`docs/rfcs/0043-high-angle-gz-successor.md:136`).

Threat path: a future claim resolver loads one promoted fixture, sees
`is_promoted() == True`, and changes analytical `GZCurve` metadata from
`unvalidated_hydrostatic_comparison` to measured/calibrated wording without an
accepted stability fit record, residuals, validity envelope, same-hull binding,
or generated-body gate check.

Required mitigation: make the stage-4 claim resolver require a separate
accepted measured-stability comparison/fit record that binds fixture id,
measured quantity `gz_m`, analytical model version, generated-body diagnostic
ref, source hull hash, load/configuration, metrics, residuals, and validity
envelope. Until that record exists, keep analytical GZ semantics unchanged and
surface the fixture only as validation evidence available for comparison.

### P1: Fixture schema validation can be mistaken for promotion acceptance

`MeasuredStabilityFixture` documents that the aggregate does not promote
fixtures and that promotion requires a separate operator review
(`kayakgen/eval/stability/measured_fixture.py:235`). However, the same model
also exposes `is_promoted()` as a plain check of
`intended_use == "measured_stability_fixture"`
(`kayakgen/eval/stability/measured_fixture.py:320`). If the new acceptance path
uses `validate_measured_stability_fixture_path(...).is_promoted()` as its gate,
then the promoter is the submitted JSON itself.

Concrete leakage paths in the current schema:

- `FreeEquilibriumTrace.smoothness_failures` may be non-empty while
  `intended_use="measured_stability_fixture"` still passes
  (`kayakgen/eval/stability/measured_fixture.py:172`,
  `kayakgen/eval/stability/measured_fixture.py:294`).
- Calibration and hysteresis are accepted from manifest summary fields; the
  validator does not resolve the trace paths or recompute drift/hysteresis from
  raw runs (`kayakgen/eval/stability/measured_fixture.py:120`,
  `kayakgen/eval/stability/measured_fixture.py:191`).
- `rights` must be present, but `redistribution_authorized=False` is not a
  promotion blocker (`kayakgen/eval/calibration/rights.py:29`,
  `kayakgen/eval/stability/measured_fixture.py:249`).
- `non_promotion_reasons` and `warnings` are allowed on a promoted fixture
  without rejection (`kayakgen/eval/stability/measured_fixture.py:265`).

Required mitigation: introduce a measured-stability acceptance record separate
from the fixture manifest. That acceptance record should be the only object that
can make a fixture usable as accepted evidence. It must reject non-empty
smoothness failures, unresolved calibration/raw-run refs, failed checksum
bindings, rights that do not permit the intended checked-in/derived use, and any
promotion blockers or blocking warnings.

### P1: Self-attested measurement-error summaries can hide drift or fixture misuse

RFC 0056 requires accepted fixtures to carry dead-weight calibration sweeps,
hysteresis evidence, and free-equilibrium evidence
(`docs/rfcs/0056-strain-gauged-gz-rig.md:167`,
`docs/rfcs/0056-strain-gauged-gz-rig.md:174`,
`docs/rfcs/0056-strain-gauged-gz-rig.md:184`). The current schema enforces the
presence of summary objects but not the evidence chain behind them. A malformed
or over-optimistic fixture can report identical pre/post arms, observed
hysteresis below the bound, and three smooth-looking trim/heave points while
raw DAQ traces are absent, stale, or from another run.

Required mitigation: `accept-measured-stability` should resolve all path refs
relative to a fixture root, require content hashes for raw runs, calibration
traces, reduction code, and geometry manifest, and recompute or independently
verify drift, hysteresis, free-equilibrium smoothness, valid heel coverage, and
`GZ_max` from those artifacts. The accepted artifact should record the computed
values, not just copy the submitted manifest values.

### P1: Hull/load binding is not strong enough to prevent fixture reuse across hulls

RFC 0043 requires source hull hash, coordinate system, units, closure policy,
and diagnostic refs to match the evaluated hull
(`docs/rfcs/0043-high-angle-gz-successor.md:144`). RFC 0056 says a fixture for
one physical hull does not validate generated bodies for other hulls
(`docs/rfcs/0056-strain-gauged-gz-rig.md:208`). The fixture schema records a
64-character `scan_hash`, `geometry_manifest_ref`, loading, and configuration,
but there is no acceptance boundary tying those to the analytical hull/body
evidence. `scan_hash` is length-checked only, not hex-checked
(`kayakgen/eval/stability/measured_fixture.py:81`).

Threat path: an accepted sea-kayak fixture is reused for another generated
hull, or a sealed-deck unloaded fixture is used to justify a flooded/loaded
analytical curve, because the claim resolver only checks hull class or fixture
id presence.

Required mitigation: claim-state resolution must compare fixture identity
against the evaluated analytical record: physical scan hash or geometry
manifest hash, analytical `source_hull_hash`, body diagnostic ref, load case,
configuration, units, and valid heel range. Mismatches should leave the
analytical result in unvalidated comparison semantics with an explicit warning.

### P2: Generic claim metadata can cross-wire resistance acceptance into stability

`ClaimMetadata` has `claim_state`, fixture id lists, model version, fit status,
metrics, and envelope, but no evaluator kind or measured quantity
(`kayakgen/eval/claims.py:88`). `claim_allows_calibrated_prediction()` is
documented as a resistance helper and accepts any record with
`claim_state="calibrated_model"`, `accepted_uses` containing
`final_prediction`, non-empty calibration fixture ids, `accepted_fit`, metrics,
and envelope (`kayakgen/eval/claims.py:195`). That shape is necessary for RFC
0027 resistance, but it is not enough to prove a stability claim.

Threat path: a resistance accepted fit, or a stability record copied into the
same generic fields, satisfies a generic calibrated-prediction check and leaks
into GZ wording or search admissibility. RFC 0027 explicitly says validation
fixtures or metrics alone must not satisfy calibrated prediction
(`docs/rfcs/0027-resistance-calibration-acceptance.md:97`).

Required mitigation: add a measured-stability-specific helper in the shared
claims module that still reuses the existing grammar but also requires
evaluator kind `stability_high_angle_gz`, measured quantity `gz_m`, accepted
measured-stability fixture ids, and a stability comparison/fit acceptance
record. The existing resistance helper should not be reused directly for GZ.

## Acceptance Conditions For This Workflow

- `accept-measured-stability` writes an immutable acceptance artifact separate
  from the fixture manifest.
- A submitted fixture's `intended_use` never promotes itself.
- Accepted evidence is hash-bound and recomputed or independently verified from
  raw traces/reduction artifacts.
- Analytical GZ claim semantics remain `unvalidated_hydrostatic_comparison`
  unless both RFC 0043 generated-body gates and a later accepted stability
  comparison/fit workflow pass.
- Tests cover direct JSON self-promotion, smoothness failures, missing raw
  traces, rights refusal, hull/load mismatch, resistance-fit cross-wiring, and
  validation-candidate misuse.
