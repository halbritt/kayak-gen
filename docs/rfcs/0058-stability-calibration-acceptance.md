# RFC 0058: Stability Calibration Acceptance and CFD-In-Loop Graduation

Status: proposed
Date: 2026-05-19
Context: RFC 0056 lands the `MeasuredStabilityFixture` schema + validators
for the strain-gauged moment-arm rig data ingest, but no acceptance gate
yet says "this fixture validates this analytical pipeline" or "this
analytical pipeline may now claim calibration against this hull family."
RFC 0027 is the resistance-side parallel; this RFC supplies the
stability-side parallel and is the final gate that lets the CFD-in-loop
evaluator in the Generate panel (RFC 0057 stage 4 / D-4) graduate from
opt-in to first-class.

## Problem

Today's pipeline has three pieces with no connection:

1. RFC 0043's analytical high-angle `GZ` evaluator emits
   `result_semantics="unvalidated_hydrostatic_comparison"` on every
   output. The label is correct — there is no measured comparison
   anywhere in the project that says the analytical curve agrees with
   reality on any kayak family.
2. RFC 0056's `MeasuredStabilityFixture` schema admits a strain-gauged
   rig run and records the per-row `(θ, GZ)` data plus the calibration
   and free-equilibrium evidence the run depended on. But no gate says
   "this fixture is sufficient to upgrade RFC 0043's label" — the RFC
   explicitly defers that.
3. RFC 0057 stage 4 ships a CFD-in-loop opt-in row in the Generate
   panel. The acknowledgement copy is unambiguous: "I accept evaluation
   may take orders of magnitude longer." But the evaluator is gated on
   RFC 0046's three-mechanism opt-in *plus* an analytical-comparison
   discipline that doesn't exist — there's no contract for when
   CFD-in-loop output may stop carrying `raw_unvalidated`.

The missing piece in all three is an **accepted-fit record for
stability** parallel to RFC 0027's resistance side. Without it, a
future operator with a real measured fixture has no path to graduate
any analytical or CFD output beyond the existing labels.

## Goals

- Define promotion from `validation_candidate` to
  `measured_stability_fixture` (RFC 0056 already encodes the data
  shape; this RFC owns the review packet that accepts the promotion).
- Define a `StabilityFitRecord` aggregate that binds:
  - the accepted `measured_stability_fixture`(s);
  - the analytical pipeline (RFC 0043 evaluator version, hull-family
    scope, valid heel range);
  - the fit metrics (RMSE / MAPE / max-error on `(θ, GZ)` pairs);
  - the acceptance verdict and reviewer signature.
- Define the analytical-claim upgrade contract: when a hull's
  `record_hash`/`design_hash` falls within an accepted
  `StabilityFitRecord`'s envelope, RFC 0043's analytical `GZCurve`
  output may carry `result_semantics="validated_hydrostatic_comparison"`
  instead of `unvalidated_hydrostatic_comparison`.
- Define the CFD-in-loop graduation contract: when an accepted
  `StabilityFitRecord` exists AND the CFD adapter has its own
  RFC 0041/0046 succeeded path against a fixture in the same envelope,
  the CFD-in-loop evaluator in the Generate panel may be promoted from
  opt-in row to first-class evaluator toggle.

## Non-Goals

- Promoting any specific fixture or fit. This RFC is the gate
  definition; the first concrete promotion happens in a later
  workflow once a real measured dataset arrives.
- Defining safety, seaworthiness, capsize, or design-fitness claims.
  The graduated label remains `validated_hydrostatic_comparison`, not
  "safe" or "seaworthy".
- Changing the existing `unvalidated_hydrostatic_comparison` default —
  the upgrade is opt-in and gated on the fit record being present.
- Selecting the rig hardware, the first hull family, or the
  experimental schedule. RFC 0056's design memo handles the physical
  side; this RFC handles the acceptance discipline.

## Dependencies

- RFC 0014 — the `GZCurve` boundary the analytical evaluator produces.
- RFC 0019 — the resistance-side fixture provenance precedent.
- RFC 0024 — the generated-body GZ handoff envelope.
- RFC 0027 — the resistance-side acceptance pattern this RFC mirrors.
- RFC 0041 / RFC 0046 — the real CFD adapter and three-mechanism
  opt-in that govern whether `succeeded` is admissible.
- RFC 0043 — the analytical high-angle `GZ` evaluator whose label
  this RFC upgrades.
- RFC 0049 — the `Hull.{record,design}_hash()` identity vocabulary
  used to bind a fit record to a hull family.
- RFC 0054 — the resistance-side accepted-fit record (`AcceptedFitRecord`)
  whose validator pattern this RFC reuses.
- RFC 0056 — the `MeasuredStabilityFixture` schema this RFC accepts
  for promotion and binds into fit records.
- RFC 0057 — the Generate panel where the graduated CFD-in-loop
  evaluator surfaces as a first-class toggle.

## Proposal

### Stage labels (normative grouping over RFC 0056's `MeasuredStabilityUse`)

A three-stage acceptance model mirroring RFC 0027:

| Stage label | RFC 0056 `MeasuredStabilityUse` values | Required behavior |
| --- | --- | --- |
| `candidate_run` | `validation_candidate`, `rejected` | Records are usable for citation or future review only. They do not provide validation evidence, fit fixture IDs, or analytical-comparison evidence. RFC 0043's label stays `unvalidated_hydrostatic_comparison`. |
| `measured_stability_fixture` | `measured_stability_fixture` (constrained-trace caps blocked at validation_candidate per RFC 0056) | Data may exercise the analytical pipeline as a holdout. It cannot promote any analytical claim or change RFC 0043's label without an accepted `StabilityFitRecord` that cites it. |
| `accepted_stability_fit` | Not stored in `MeasuredStabilityUse`; lives in `StabilityFitRecord.acceptance_verdict == "accepted"` | The analytical evaluator may claim `validated_hydrostatic_comparison` against hulls whose `record_hash` falls within the fit's declared envelope. Untouched hull families remain `unvalidated_hydrostatic_comparison`. |

Do not add a `candidate_run` literal or a parallel `MeasuredStabilityUse`
enum. UI, report, or documentation surfaces may display the three stage
labels only as derived projections of the underlying RFC 0056 vocabulary
plus the presence/absence of an accepted `StabilityFitRecord`.

### `StabilityFitRecord` aggregate

A new Pydantic aggregate under
`kayakgen/eval/stability/accepted_fit.py`:

```python
StabilityFitRecord(
    schema_version: Literal["1"],
    fit_id: str,
    analytical_evaluator_version: str,   # RFC 0043 version pin
    hull_family_scope: HullFamilyScope,  # design-hash envelope + class
    valid_heel_range_deg: tuple[float, float],
    fixtures: list[FixtureRef],          # one or more measured_stability_fixture
    fit_metrics: StabilityFitMetrics,    # RMSE / MAPE / max_error_m / coverage
    acceptance_verdict: Literal["accepted", "rejected"],
    rejection_reasons: list[str],        # empty when accepted
    reviewer_signature: ReviewerSignature,
    accepted_at: datetime | None,
    notes: list[str],
)
```

Field constraints (all validated at Pydantic time):

- `fit_id` is unique across all records in the project's fit registry.
- `analytical_evaluator_version` must match the runtime version of the
  RFC 0043 evaluator when the comparison was run.
- `fixtures` must be non-empty and every cited fixture must have
  `intended_use == "measured_stability_fixture"`. Validators resolve
  the fixture refs on disk (`MeasuredStabilityFixture` round-trip).
- `fit_metrics` must satisfy declared per-metric thresholds:
  - `rmse_m` ≤ `0.005 m` (default; per RFC 0056's pilot-run tightening
    contract this may revise to the actual rig uncertainty floor).
  - `mape_fraction` ≤ `0.05` (default).
  - `max_error_m` ≤ `0.01 m` (default).
  - `coverage_fraction` ≥ `0.9` (default; fraction of fixture rows
    that fall inside the analytical evaluator's converged subdomain).
- `acceptance_verdict == "accepted"` requires `accepted_at` to be set
  and `rejection_reasons` to be empty.

### Analytical-claim upgrade contract

`kayakgen/eval/stability/high_angle_contracts.py` gains a function
`resolve_analytical_claim_label(hull, fit_registry) -> Literal[...]`
that returns:

- `"unvalidated_hydrostatic_comparison"` when no accepted
  `StabilityFitRecord` covers the hull's `design_hash`/`hull_class`.
- `"validated_hydrostatic_comparison"` when an accepted record's
  `hull_family_scope` includes the hull AND the requested heel range
  is within the fit's `valid_heel_range_deg`.

The result is recorded on the `GZCurve` payload's `result_semantics`
field. **No** record promotes to safety, seaworthiness, calibrated, or
final-prediction claims — those remain forbidden.

### CFD-in-loop graduation contract

`kayakgen/services/generative_jobs.py` gains a helper
`cfd_in_loop_evaluator_status(*, registry, hull_scope) -> Literal[
"opt_in_only", "first_class"]` that returns:

- `"opt_in_only"` (the default; current state) — RFC 0057 stage 4's
  CFD-in-loop opt-in row stays the only path. The form gates on the
  explicit acknowledgement.
- `"first_class"` only when:
  1. an accepted `StabilityFitRecord` covers the spec's `base_hull`
     scope (analytical pipeline is validated for that family);
  2. RFC 0041/0046's CFD adapter has its own accepted-fit record
     (this RFC defers that record to a parallel resistance-side
     successor of RFC 0027 + a CFD-vs-measured comparison);
  3. the operator has not explicitly opted out via a persistent
     setting.

In `first_class` mode the form-builder's evaluators block surfaces the
CFD-in-loop toggle without the explicit acknowledgement copy (the
acknowledgement is implicit in the graduated label).

### Promotion-review packet

A new `StabilityFixturePromotionPacket` aggregate parallels
RFC 0042's `ResistanceSourceReviewPacket`:

```python
StabilityFixturePromotionPacket(
    schema_version: Literal["1"],
    fixture_ref: str,           # path to the MeasuredStabilityFixture manifest
    rights_review: RightsReviewVerdict,
    hull_identity_review: HullIdentityReviewVerdict,
    rig_design_match: bool,     # cited RFC 0056 design memo matches the
                                # revision used
    calibration_drift_review: CalibrationDriftReviewVerdict,
    hysteresis_review: HysteresisReviewVerdict,
    free_equilibrium_review: FreeEquilibriumReviewVerdict,
    promotion_target: Literal[
        "measured_stability_fixture",
        "validation_candidate",  # keep at candidate
        "rejected",
    ],
    rejection_reasons: list[str],
    reviewer_signature: ReviewerSignature,
)
```

Validators enforce:

- `promotion_target == "measured_stability_fixture"` requires every
  review verdict to be `"accepted"` and `rejection_reasons` to be
  empty.
- A packet that promotes a fixture whose `FreeEquilibriumTrace` has
  `constrained_trim` or `constrained_heave` is refused at validate
  time (mirrors RFC 0056's own constraint).

### CLI surface

New `kayakgen stability` subcommands (sibling to `kayakgen calibration`):

- `kayakgen stability ingest-rig-run <manifest> --out <dir>` — ingest a
  rig run as a `MeasuredStabilityFixture` (default
  `intended_use="validation_candidate"`); writes the canonical manifest
  under `data/stability/fixtures/<fixture_id>/manifest.json`.
- `kayakgen stability promote-fixture <fixture_id> --packet <path>` —
  read a promotion packet and update the fixture's `intended_use`. Refuses
  any packet that fails its own validation.
- `kayakgen stability accept-fit <fit_record> --packet <path>` — accept
  a `StabilityFitRecord` given a review packet; writes the immutable
  record to `data/stability/fits/<fit_id>.json`. Refuses to overwrite
  an existing record under the same `fit_id`.
- `kayakgen stability residual-plot <fit_record>` — render an SVG of
  the analytical vs measured `(θ, GZ)` curves and their residuals,
  using the same vendored renderer pattern as RFC 0054's
  resistance-side plot.

### Read-model wiring

The Generate panel's frontier-view module reads
`resolve_analytical_claim_label(hull, fit_registry)` to colour the
scatter points: validated points use the existing
`theme.kg-state-validated` token; unvalidated points use the existing
`theme.kg-state-raw` token. No new tokens, no new claim-state literal.

The Generate panel's form-builder evaluators block calls
`cfd_in_loop_evaluator_status(...)` on the current `base_hull` to
decide whether to render the explicit acknowledgement checkbox; in
`first_class` mode the checkbox is hidden and the evaluator toggle
appears alongside hydrostatics / stability / mesh-diagnostics.

## Acceptance Criteria

- `StabilityFitRecord`, `HullFamilyScope`,
  `StabilityFixturePromotionPacket`, `StabilityFitMetrics`,
  `ReviewerSignature` Pydantic records exist under
  `kayakgen/eval/stability/accepted_fit.py` with byte-stable canonical
  JSON and `schema_version="1"`.
- `resolve_analytical_claim_label(hull, fit_registry)` is implemented and
  returns `unvalidated_hydrostatic_comparison` by default; only an
  accepted fit covering the hull's `design_hash`/`hull_class` upgrades
  to `validated_hydrostatic_comparison`.
- `cfd_in_loop_evaluator_status(...)` is implemented; default behavior
  is `opt_in_only` until at least one accepted `StabilityFitRecord`
  exists AND an accepted RFC 0041/0046 CFD-vs-measured fit record
  exists in the same envelope.
- New `kayakgen stability` sub-app with the four subcommands above.
- No fixture is promoted by this RFC. The first concrete promotion
  happens in a later workflow once a real measured dataset arrives.
- RFC 0043's default `result_semantics="unvalidated_hydrostatic_comparison"`
  remains the only legal label for analytical `GZCurve` outputs until
  an accepted `StabilityFitRecord` exists for the hull family.
- All existing forbidden-claim scrub-list tokens remain enforced; no
  new safety / seaworthiness / final-prediction / design-fitness
  wording is introduced.
- `docs/USER_GUIDE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/DDD.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`, and
  `docs/DECISION_LOG.md` (new row Dnnn) are updated in the same
  landing.

## Open Questions

- What metric thresholds are correct? The defaults (`rmse_m ≤ 0.005`,
  `mape ≤ 0.05`, `max_error_m ≤ 0.01`, `coverage ≥ 0.9`) are placeholders
  derived from RFC 0056's pilot-run error budget. The first concrete
  fit record should set production values.
- Should the analytical-evaluator version pin be a single string or a
  structured `EvaluatorVersion(record_hash, evaluator_id)` pair? A
  single string is simpler; structured is more discoverable when
  multiple evaluators land. Recommended: single string for now,
  promote to structured when a second evaluator lands.
- Should `cfd_in_loop_evaluator_status` honor the persistent setting
  from RFC 0046's three-mechanism opt-in, or does graduation override
  the operator's persistent choice? Recommended: persistent setting
  wins. Graduation only changes the *default*; the operator can still
  opt out per session.
- Should `StabilityFitRecord` carry a notion of "expires_at" so a
  fit that drifts from later measurements can age out? Probably yes,
  but defer to a successor RFC once the first record is real.
- Should the CFD-in-loop graduation also require a separate
  `CfdInLoopFitRecord` (different from the analytical-stability one),
  or is the analytical fit enough? The current proposal requires both.
  This is conservative but adds another schema; the alternative
  (analytical fit alone) is simpler but lets CFD-in-loop graduate on
  evidence about an unrelated pipeline. Recommended: keep both.

## Implementation Path

Stage 1 — schemas:

1. Land `StabilityFitRecord`, `HullFamilyScope`,
   `StabilityFitMetrics`, `ReviewerSignature`, and
   `StabilityFixturePromotionPacket` Pydantic records.
2. Land the validators (metric thresholds, scope coverage check,
   fixture-ref resolution).
3. Round-trip tests for every record.

Stage 2 — contracts:

4. Land `resolve_analytical_claim_label(hull, fit_registry)` and wire
   it into RFC 0043's `result_semantics` resolution.
5. Land `cfd_in_loop_evaluator_status(...)` and wire it into the
   form-builder's evaluators-block render.
6. Default behavior byte-stable: with no accepted fit records, both
   functions return their pre-existing values.

Stage 3 — CLI + read-model:

7. Land the four `kayakgen stability` subcommands.
8. Wire the frontier-view colour mapping through the new label.
9. Update the user guide and ROADMAP.

Stage 4 — first promotion (separate workflow, not in this RFC):

10. A future workflow ingests an actual rig run, lands the first
    `StabilityFixturePromotionPacket`, runs the analytical pipeline,
    and writes the first `StabilityFitRecord`. That workflow is gated
    on physical data acquisition (D007/D014) and operator review.

## Domain Modeling

`StabilityFitRecord` is *evaluator reference data and provenance*,
not a hull-domain entity. It governs what the analytical evaluator's
`GZCurve` may claim. The `HullFamilyScope` value object binds a fit
to a family (by `class` + `design_hash` envelope) and is reusable by
any future fit-record kind.

The promotion-review process is *not* a domain entity. It is a
review packet whose only durable artifact is a verdict record on
disk. Re-running the review (e.g. with new evidence) creates a new
packet; the prior one stays as audit history but the fit registry
binds to the latest accepted packet.

Bound state:
- `MeasuredStabilityFixture.intended_use ∈ {validation_candidate, measured_stability_fixture, rejected}`
- `StabilityFitRecord.acceptance_verdict ∈ {accepted, rejected}`
- `resolve_analytical_claim_label` is a pure function of (hull, fit_registry).
- `cfd_in_loop_evaluator_status` is a pure function of (hull_scope, fit_registry, optional persistent setting).

No part of this RFC's surface persists hidden state. The fit registry
and fixture registry are filesystem-backed; every transition is
recorded as a separate review-packet artifact.
