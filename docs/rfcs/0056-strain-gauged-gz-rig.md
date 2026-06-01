# RFC 0056: Strain-Gauged Moment-Arm Rig for Measured High-Angle GZ

Status: landed schemas + stage-4 acceptance pipeline (MeasuredStabilityFixture schema + the registry gate-chain that consumes it via RFC 0043 stage 4); first promotion of a real measured fixture still gated on D007/D014 rig data
Date: 2026-05-16; schema landing 2026-05-19
Context: extends the calibration-fixture family (RFC 0019, RFC 0027,
RFC 0042) into measured *stability* data, and supplies the validation
input that RFC 0043's analytical high-angle `GZ` evaluator currently
lacks. Parallel to RFC 0054, which lands the ingest schema for the
discrete inclining-by-known-weight protocol (`IncliningTestRun` —
one `(heel_deg, applied_moment_nm)` row per measurement); this RFC
scopes the continuous strain-gauged-arm protocol as a distinct data
kind that produces a dense `(θ, GZ)` trace in a single sweep.
Grounded in `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md`
which concluded that public measured high-angle GZ datasets for
in-envelope kayaks do not exist, and that the realistic path is to
produce them. The rig design lives at
`docs/research/STRAIN_GAUGED_GZ_RIG_DESIGN_2026-05-16.md`.

## Problem

Decision log gates D007 and D014 require measured high-angle `GZ` data
on in-envelope kayak hulls before the analytical evaluator
(`unvalidated_hydrostatic_comparison`, RFC 0043) can be upgraded to a
calibrated or validated claim. The findings memo confirmed no public
dataset satisfies that requirement, and ranked three measurement
protocols by cost. Protocol 1 — inclining-by-known-weight — yields only
a handful of discrete `(M, θ)` points and becomes unsafe past the angle
of maximum GZ, exactly where the evaluator's claims about secondary
stability live.

Replacing the fixed weight with a strain-gauged moment arm produces a
continuous `F(θ)` trace that resolves `GZ_max`, the angle of vanishing
stability `φ_v`, and the area under positive `GZ` in a single sweep.
The project has no fixture kind for the resulting data and no acceptance
gates that say what it takes to promote a raw rig run to a citable
`measured_stability_fixture`. Without those, a future rig output could
be checked in as authored stability "truth" without provenance,
calibration trace, free-equilibrium evidence, or hull identity — the
same failure mode RFC 0019 closed for resistance data.

## Goals

- Define `measured_stability_fixture` as a sibling data kind to
  `calibration_fixture` and `validation_fixture`, with parallel
  provenance discipline (rights, source, extraction, hull identity,
  envelope).
- Specify the fixture manifest and per-row schema for measured
  `(θ, GZ)` data produced by a strain-gauged moment-arm rig.
- Define acceptance gates that promote a raw rig run to
  `measured_stability_fixture`, including dead-weight calibration
  records, hysteresis bounds, free-equilibrium evidence, and hull
  identity.
- Preserve every RFC 0043 claim gate: a measured fixture for a
  physical hull does not by itself authorize an analytical `GZCurve`
  on the generated body to claim calibration.
- Keep raw rig output, intermediate reductions, and accepted fixtures
  distinguishable, so future fitting work cannot accidentally tune
  against unaccepted data.

## Non-Goals

- This RFC does not stand up the rig, fund tank time, or pick a
  hull to test first. The rig design memo handles the physical
  layout.
- This RFC does not implement calibration fitting against measured
  stability data. Fitting is a later RFC with its own acceptance
  gates, parallel to the resistance-calibration acceptance work in
  RFC 0027.
- This RFC does not upgrade RFC 0043's
  `result_semantics="unvalidated_hydrostatic_comparison"` label.
  That label changes only when an accepted measured fixture exists
  *and* a fitting workflow has been accepted *and* the analytical
  evaluator passes that workflow on the same hull family.
- This RFC does not model dynamic capsize, bracing, waves, surf,
  flooding, or paddler control. Those are out of scope for both the
  rig and the fixture.
- This RFC does not promote any existing dataset.
  `CALIBRATION_DATA_FINDINGS_2026-05-16.md` enumerated the public
  data; none of it qualifies.

## Dependencies

- RFC 0011 for load-case mass and KG conventions the rig must
  record per run.
- RFC 0014 for the `GZCurve` boundary the fixture schema mirrors.
- RFC 0019 for the original calibration-fixture format and the
  "provenance-before-promotion" precedent.
- RFC 0024 for the generated-body handoff that any analytical/measured
  comparison binds against.
- RFC 0027 for the `SourceUse` acceptance pattern that gates fixture
  promotion.
- RFC 0042 for the current resistance source-review and
  fixture-promotion workflow whose shape this RFC mirrors for
  stability.
- RFC 0043 for the claim gates that still apply to any analytical
  `GZCurve`, with or without measured data.
- RFC 0054 for the `IncliningTestRun` schema (discrete fixed-weight
  protocol) and the `AcceptedFitRecord` schema. This RFC's continuous
  trace is the sweep-rate analog of the discrete inclining row, and
  the `AcceptedFitRecord` flow defined there applies once a measured
  stability fixture is bound to an analytical comparison.

## Proposal

### New fixture kind

Introduce `measured_stability_fixture` as an `intended_use` value
alongside the existing `calibration_fixture` and `validation_fixture`
values from RFC 0019. A `measured_stability_fixture` carries measured
`(θ, GZ)` data for a specific physical hull configuration; it is not
interchangeable with the resistance fixture kinds.

### Fixture manifest

A new directory under
`data/stability/fixtures/<fixture_id>/manifest.json` with a parallel
shape to RFC 0019:

```python
MeasuredStabilityFixture(
    fixture_id: str,
    title: str,
    source_citation: str,
    source_url: str,
    rights_status: str,
    extraction_method: str,
    hull_class: str,
    hull_identity: HullIdentityRef,
    configuration: Literal["sealed_deck", "flooded_cockpit"],
    loading: LoadingConfiguration,
    measured_quantity: Literal["gz_m"],
    heel_units: Literal["deg"],
    arm_units: Literal["m"],
    valid_heel_range_deg: tuple[float, float],
    rig_design_ref: str,
    geometry_manifest_ref: str,
    calibration_trace_ref: str,
    intended_use: Literal[
        "measured_stability_fixture",
        "validation_candidate",
    ],
    warnings: list[str],
)
```

Per-row records carry `theta_deg`, `gz_m`, and standard deviation across
sweeps. Each fixture also carries a `runs/` subdirectory with raw DAQ
traces and reduction code provenance so downstream consumers can
re-derive the binned curve without trusting the manifest alone.

### Hull identity

`HullIdentityRef` records a 3D scan hash of the tested hull plus
manufacturer/model strings. Manufacturer model name alone is
insufficient: production-tolerance variation between two units of the
same model can be larger than the rig's measurement uncertainty.

### Loading configuration

`LoadingConfiguration` records displacement, paddler ballast position
and mass, sealed-deck or flooded-cockpit state, and any added ballast.
These pin the CG convention so the measured curve can be compared to
RFC 0043's load-case-aware analytical evaluator.

### Calibration trace

Every accepted fixture carries pre-run and post-run dead-weight
calibration sweeps in `calibration_trace_ref`. The acceptance gate
rejects fixtures where pre/post drift exceeds the declared bound, or
where the calibration sweep is missing.

### Free-equilibrium evidence

The fixture must record trim and heave traces over the sweep.
Acceptance requires that they vary smoothly with `θ` and do not show
clamping or oscillation patterns characteristic of rig restraint. If
trim or heave are constrained intentionally, the constraint must be
declared and the fixture is `intended_use: validation_candidate`, not
`measured_stability_fixture` — it cannot be cited as free-hydrostatic
truth.

### Hysteresis bound

Forward and reverse sweeps must agree within an accepted bound (default
3 % of `GZ_max`) at each binned `θ`. Larger hysteresis flags the run
as too fast, too tight, or rig-bound; the run is preserved as raw data
but not promoted.

### Promotion review

Promotion of a rig run to `measured_stability_fixture` requires a
review note answering:

- whether rights permit checked-in derived data and the raw DAQ
  traces;
- whether `hull_identity.hull_class` overlaps the project design
  envelope;
- whether the rig design used matches the cited
  `STRAIN_GAUGED_GZ_RIG_DESIGN_*.md` revision;
- whether the calibration trace drift, hysteresis, and
  free-equilibrium evidence are within bounds;
- whether the analytical evaluator may compare against this fixture
  (validation) or may also tune against it (calibration); the default
  is validation-only.

### Relationship to RFC 0043

An accepted `measured_stability_fixture` is *necessary but not
sufficient* to upgrade an analytical `GZCurve` claim. RFC 0043's gates
on the generated body — closure, diagnostics, source hull hash,
heeled-integration model availability — all still apply. The measured
fixture validates the *analytical pipeline for that hull family*; it
does not retroactively validate generated bodies for hulls not tested.

## Acceptance Criteria

- This RFC lands as documentation only, with no runtime behavior
  change.
- Fixture manifest schema is added under `data/stability/fixtures/`
  with validators that enforce: `intended_use` enumeration,
  `HullIdentityRef` presence, calibration trace presence, free-
  equilibrium trace presence, and hysteresis bound declaration.
- The source registry distinguishes `measured_stability_fixture`,
  `validation_candidate`, and rejected rig runs, parallel to the
  resistance fixture states.
- No fixture is promoted by this RFC. D007 and D014 remain open.
- RFC 0043's `result_semantics="unvalidated_hydrostatic_comparison"`
  remains the only legal label for analytical `GZCurve` outputs
  until a separate fitting/validation RFC accepts both the fixture
  and the analytical comparison.
- Documentation explains why a `measured_stability_fixture` for one
  physical hull does not authorize a calibration claim for the
  generated body of any other hull.

## Open Questions

- Should `measured_stability_fixture` carry an explicit "configurations
  tested" matrix (sealed-deck × loaded vs unloaded, etc.) on the same
  hull, or should each configuration be its own fixture? The design
  memo recommends one fixture per (hull, configuration) pair; this RFC
  defers final choice to first ingest.
- What hull-class taxonomy should `hull_class` use? Reuse the
  resistance fixture taxonomy from RFC 0019, or define a stability-
  specific one (sea kayak, sprint K1, surfski, recreational, SOT)?
  Reusing is simpler; a stability-specific split is more honest about
  envelope.
- Should the fitting acceptance RFC (the successor) live as 0050.x
  or as a separate top-level RFC, parallel to RFC 0027 succeeding
  RFC 0019?
- Should rig output for hulls *outside* the envelope (e.g. canoes,
  surf-skis at the edge of the sea-kayak envelope) be storable as
  `validation_candidate` for cross-envelope sanity checks, or
  rejected at ingest? Recommended: storable, never promotable.
- What hysteresis bound is correct? 3 % of `GZ_max` is a starting
  number from the design memo's error budget; first pilot run should
  set the production value.
- Should the rig design memo's revision hash be carried on the
  fixture, so a fixture taken under v1 of the rig is distinguishable
  from a fixture taken under a future v2?

## Implementation Path

1. Accept this RFC as the scope boundary for measured-stability data
   ingest.
2. Add the `MeasuredStabilityFixture` manifest schema and validators
   under `data/stability/fixtures/` with no fixtures present.
3. Extend the source registry to enumerate the new fixture state and
   the rejected-rig-run state.
4. Land a pilot rig run on a single in-envelope hull as
   `validation_candidate`, with full raw traces, calibration sweeps,
   free-equilibrium evidence, and hull-scan hash. Do not promote.
5. Run a source-review packet on the pilot fixture to set production
   values for hysteresis bound, drift bound, and free-equilibrium
   thresholds.
6. Promote the first pilot to `measured_stability_fixture` only after
   the review packet accepts both the rig run and the bounds.
7. Open a separate RFC for the analytical-comparison fitting
   workflow. That RFC, not this one, owns any change to RFC 0043's
   `result_semantics` label.

## Domain Modeling

`MeasuredStabilityFixture` is evaluator reference data and provenance,
following the same pattern as `ResistanceCalibrationFixture` from
RFC 0019. It is not a hull-domain entity; it constrains how
`GZCurve` read models may claim validation or calibration. The
`HullIdentityRef` value object binds a fixture to a physical hull
instance and is reusable by any future measured-fixture kind.

The rig itself is **not** a domain entity. It is a measurement
process whose only durable artifacts are the fixture manifest, raw
traces, reduction code provenance, and calibration sweeps. Reusing
the rig across runs does not create a long-lived domain object; the
artifact graph is what persists.
