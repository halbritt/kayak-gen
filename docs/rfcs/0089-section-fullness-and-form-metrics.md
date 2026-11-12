# RFC 0089: Section fullness, form metrics and multi-load righting arms

Status: landed stages 1 and 2 (section exponent, form metrics, load-case GZ table; tumblehome, sheer plan, deck crown, search admission)
Date: 2026-11-11
Context: RFC 0048 (`distribution_v2`), RFC 0088 (topsides), RFC 0043
(high-angle GZ), RFC 0053 (turning metrics), RFC 0049/0068 (identity);
D075; `kayakgen/model/distribution_v2.py`, `kayakgen/model/geometry.py`,
`kayakgen/eval/form_metrics.py`, `kayakgen/eval/high_angle_gz.py`,
`kayakgen/search/sweep.py`.

## Problem

The owner's fast-tourer study compared generated hulls with a
scan-reconstructed production kayak at equal length and nearly equal
waterline beam. The production hull had about a quarter more calculated
righting arm at 20 degrees for the same paddle clearance, and it became
stiffer as load came off where the generated hull became more tender.
Changing the deck did not close the gap: moving the sheer from 50% to
90% of the freeboard moved the 30 degree righting arm by 2 mm.

Section cuts showed why. Five centimetres below the waterline the
production hull is 42 cm wide and the generated hull 35 cm. The `round`
family is a fixed parabola, `z = -draft * (1 - (y / b)^2)`, with an area
coefficient of 2/3. No field changes it, so the design space could not
express a firm bilge, and every comparison charged that limit to the
candidate.

The study also took three measures by hand on every candidate, outside
the tool: the race-class length-to-beam ratio, the overall beam where
the paddle enters, and righting arms at more than one load. A hand
measure is not reproducible, is not recorded with the candidate, and
cannot be used by a search.

## Goals

- A `round` v2 section can be made fuller or finer than the parabola,
  constant or varying along the length.
- The class ratio and the catch-zone beam are computed by the tool from
  the same sections every other surface uses.
- One hull can be given several named loads and return a righting-arm
  block for each.
- Existing hulls, sweep specs, candidate records and evaluation results
  keep their geometry, serialized bytes and identities.

## Non-Goals

- Stage 1 had no tumblehome and no search admission; stage 2 (below)
  adds both.
- No fullness control for the other five section families.
- No physical validation of any value. The class ratio is the geometric
  ratio at a stated draft; a race organiser's tape measure can differ
  by several percent. GZ claim states are unchanged.
- No dotted-path variables in the deterministic sweep. Active search
  (RFC 0063) already reaches nested fields.

## Proposal

### Section exponent

`DistributionV2Spec` gains optional `section_exponent`, a scalar or a
`LongitudinalDistribution`, range [1.5, 8]. The `round` arc becomes

    z = -draft * (1 - (y / half_breadth) ** section_exponent)

before the deadrise and rocker terms, which are unchanged. The area
coefficient of that arc is `m / (m + 1)`: 0.60 at 1.5, 0.667 at 2,
0.80 at 4, 0.889 at 8. Unset means 2 and takes the previous code path,
so the arc is bit-identical. Section points keep the breadth spacing of
the exponent-2 arc for every exponent, so a full section does not crowd
its points into the bilge.

Setting the field with any family other than `round` is refused; a
silently ignored shape field would report a hull that was not built.
Out-of-range and non-finite values are refused at 201 stations.

The field is omitted from serialized output while unset, like
`topsides`. Records written before it existed keep their bytes and
both hashes. Setting it, even to 2.0, changes both.

The waterline breadth does not change with the exponent. Displacement,
wetted surface, centre of buoyancy and so GM do; a designer who changes
the exponent re-solves draft for the load, as with any other change of
volume.

### Form metrics

`kayakgen.eval.form_metrics.evaluate_form_metrics(hull, ...)` returns a
`FormMetrics` block. Like turning metrics it reads only the hull
geometry.

- **Class ratio.** A plane is set `class_ratio_draft_m` above the lowest
  keel point (default 0.1016 m, the 4 in the Sound Rowers kayak classes
  assume). Waterline beam is the widest crossing of that plane by the
  lower or upper ring at any station; waterline length is the span of
  stations with a crossing, with the end stations interpolated. The
  ratio is `None` when there is no crossing.
- **Catch zone.** The reference station is the centroid of the
  design-waterline section areas unless supplied; it stands in for the
  seat. `catch_zone_max_beam_m` is the largest overall beam of hull and
  deck between `near` and `far` metres forward of it (default 0.6 to
  1.2). The beam at the reference station and the overall maximum are
  reported beside it.

The bow is at `-x`, as everywhere in v2 geometry.

`EvaluationResult.form_metrics` carries the block and is omitted from
serialized output while unset. `kayakgen evaluate --form-metrics
[--class-ratio-draft-m D]` attaches it. A sweep computes it with
`evaluators.form_metrics` and writes four summary columns:
`form.class_length_beam_ratio`, `form.class_waterline_beam_m`,
`form.catch_zone_max_beam_m`, `form.beam_at_reference_m`. Stage 1
registered them `display_only`; stage 2 changes that.

### Load-case GZ table

`build_load_case_gz_table(hull, load_cases, heel_grid_deg=...)` returns
one unchanged `build_high_angle_gz_block` result per named `LoadCase`.
Names must be unique and non-blank. Every assumption and warning of the
single-load block applies to each entry.

A sweep runs it with `evaluators.high_angle_gz_load_cases`, a list of
load-case records. Each candidate writes `load_case_gz.json` (artifact
kind `load_case_gz_artifact`, checked by candidate reuse) and summary
keys `load_case_gz.<name>.gz_m_at_<angle>deg`. Those keys are not
registered, so they stay out of `summary.csv`.

### Byte stability of options

The four new `EvaluatorOptions` fields are omitted from serialized
output while they hold their defaults. `SweepSpec.spec_hash()`,
candidate keys and `evaluator_settings` of existing specs and records
do not move.

## Acceptance Criteria

- Unset exponent: no key in serialized output, identity unchanged,
  section arrays bit-identical to the explicit value 2.0.
- Set exponent: the arc follows the stated power law to 1e-12; the
  polygon area coefficient is within 1% of `m / (m + 1)`; waterline
  breadth is unchanged; upright displacement agrees with direct section
  integration within 0.2%; a distribution is honoured station by
  station; the closed body with topsides stays closed and GZ runs.
- Out-of-range, non-finite and wrong-family exponents are refused.
- Class beam and length agree with an independent section measurement;
  topsides are read when the class plane is above the design waterline;
  the catch zone is forward of the reference and clips at the bow with
  a note; a draft beyond the body reports no ratio; bad inputs are
  refused.
- The load-case table equals the single-load blocks, entry by entry.
- Default options, results and sweeps serialize as before; a sweep with
  the options set writes the block, the artifact, the summary keys and
  the CSV columns.
- Tests: `tests/test_rfc0089_section_form.py`.

## Open Questions

- Whether the reference station should become a hull field (seat
  position) instead of a derived centroid.
- Which race rule variants beyond a fixed-draft length-to-beam ratio
  are worth a named preset.

## Implementation Path

- Stage 1 — section exponent, form metrics, load-case table, sweep and
  CLI surfaces, tests, docs. Landed.
- Stage 2 — tumblehome, sheer plan, deck crown exponent, shaft
  clearance beam, class beam fraction, search admission. Landed; see
  "Stage 2" below.

## Stage 2

Stage 1's first use showed that section fullness trades stability
between loads and does not close the gap to the scan-reconstructed
hull. What remains is above the waterline: that hull carries about 4 cm
more breadth near the top of its deck, and a paddler needs the sheer
narrow only where the blade enters. Stage 2 adds the controls for both
and lets a search use the stage 1 measures.

### Tumblehome

`sheer_beam_ratio` may now be as low as 0.6 (was 1). Below 1 the sheer
is narrower than the waterline. The topside strip keeps its quadratic
Bezier form, but its control point reaches only
`sqrt(0.01 * b * (b - sheer_half_breadth))` along the breadth, so the
strip turns inward tightly and bulges past the waterline edge by about
1% of the half-breadth at most. Ratios of 1 and above take the RFC 0088
path unchanged. The ring keeps its point count and anchors; the lower
ring, upright hydrostatics and design-waterline resistance are
unchanged. `DistributionV2Geometry.sheer_z_at(x)` gives the sheer
height, and the offsets export uses it where the sheer is inside the
waterline, since the widest-point rule cannot find such a sheer.

A ratio that RFC 0088 refused (0.6 to 1) is now accepted. No stored
record can contain one, so no identity moves.

### Sheer plan

A first draft of this stage narrowed the sheer with a local dip in the
ratio (a "catch cutout"). It worked numerically and drew a hull that
looked pinched: the sheer narrowed at the catch and widened again
forward of it. No fair hull does that, and a penalty on unfairness
would have left the search to rediscover fairness by trial. The dip
was removed before landing. The sheer is instead drawn as its own
outline, fair by construction.

`TopsidesSpec.sheer_plan` is an optional `SheerPlan` with four scalars:
`max_half_breadth_m`, `max_position_xi`, `forward_exponent` and
`aft_exponent` (each exponent 1.2 to 4). The sheer half-breadth is

    max_half_breadth_m * (1 - u ** n)

with `u` running from 0 at `max_position_xi` to 1 at the bow (using
`forward_exponent`) or at the stern (using `aft_exponent`). Each side
is monotone and curves one way only, so the outline has no pinch,
hollow or flat. A lower exponent gives a finer, straighter end; moving
the widest point aft narrows the sheer where the paddle enters.

With a plan, `sheer_beam_ratio` must be left at 1; giving both is
refused. The plan must stay within [0.6, 1.5] times the waterline
half-breadth for `|xi| <= 0.9`, checked on the whole spec because the
topsides record does not know the waterline. Closer to the pointed
ends, where both breadths go to zero, the sheer is held within that
range of the local waterline. One outline can therefore be inside the
waterline forward (tumblehome) and outside it aft (flare).
`DistributionV2Geometry.is_tumblehome_at(x)` reports which.

Scalars are used, not a distribution, so active search (RFC 0063
dotted keys) can vary each one.

### Deck crown exponent

`TopsidesSpec.deck_crown_exponent`, scalar or distribution in [2, 12],
replaces the built-in arch exponent between sheer and crown
(`4 + 6 * bow_flare` forward, 4 aft). A larger value keeps the deck
high out to the sheer, so more volume immerses at large heel. Unset
keeps the built-in value.

`sheer_plan` and `deck_crown_exponent` are omitted from serialized output
while unset, so a topsides record written under RFC 0088 keeps its
bytes and both hashes.

### Form metrics

- `catch_zone_max_upper_beam_m`: the largest breadth in the catch zone
  counting only the body at or above `catch_upper_height_m` over the
  design waterline (default 0.10 m). This is what a paddle shaft clears.
  The stage 1 overall beam cannot fall below the waterline beam, so it
  gives no credit to tumblehome; this one does.
- `class_beam_length_fraction`: class waterline beam over overall
  length. The USCA Sea Kayak class requires at least 0.085 at 4 in with
  an overall length of 18 ft or less.

### Search admission

- The six `form.*` metrics move from `display_only` to
  `explicit_exploratory`. A search may rank on them only with
  `objectives_explicit_exploratory`, which marks the run exploratory.
  They are exact for the generated sections and are not a validated
  fitness.
- `load_case_gz.*` keys are refused as objectives in every mode, with
  the RFC 0043 display-only token. They are the same unvalidated
  hydrostatic comparison as the single-load GZ mirrors.
- Any summary key may bound a search as a constraint, as before. A
  righting-arm floor per load and a class-ratio ceiling are therefore
  expressible; a candidate that misses one is `constraint_failed`.

### Stage 2 acceptance

- Topsides records without the new fields serialize as before.
- Tumblehome: sheer at `ratio * b` and the stated height; ring shape
  and anchors preserved; no section wider than 1.011 `b`; closed bodies
  for all six families with a sheer plan and crown together;
  upright hydrostatics unchanged; righting arm at 20 and 30 degrees
  orders tumblehome < wall-sided < flared; offsets report the sheer
  height.
- Sheer plan: widest at the stated station and breadth, zero at both
  ends, monotone and single-curvature each side; a lower forward
  exponent is narrower everywhere forward and unchanged aft; geometry
  puts the sheer on the plan at every station; one plan gives
  tumblehome forward and flare aft; upright hydrostatics unchanged; a
  finer forward plan lowers the upper catch beam.
- Deck crown: 4.0 reproduces the built-in arch aft; a larger value
  raises the deck everywhere and adds closed-body volume.
- Out-of-range ratio, plan and crown values, a plan given with a ratio,
  and a plan outside the waterline range are refused.
- Form metrics are objectives only under the exploratory opt-in;
  `load_case_gz.*` never; a search over the plan's forward exponent and
  the crown exponent runs, honours a righting-arm floor, and rejects every candidate when
  the floor is unreachable.
- Tests: `tests/test_rfc0089_stage2_deck.py`.

### Still open after stage 2

- No knuckle or chine in the topside strip, and no topsides for lofted
  geometry.
- Fairness is guaranteed for the sheer plan only. A ratio given as a
  key-point distribution can still draw an unfair sheer, and nothing
  measures fairness of the sheer in profile or of the deck surface.
- With a fair outline the first candidates only matched the reference
  hull's paddle clearance. A recessed deck (a lower sheer and flatter
  crown at the catch) is the remaining route and is expressible with
  the existing `sheer_height_frac` and `deck_crown_exponent`
  distributions, but those are not scalar and so not searchable.
- No default search variables in class presets for the new fields.
- A cockpit, coaming or deck recess is not modelled, so foot and knee
  room under a narrowed deck is not checked.

## Domain Modeling

`FormMetrics` is a read model beside `TurningMetrics`. `SheerPlan` is a
value object owned by `TopsidesSpec`. "Section exponent", "class
ratio", "catch zone", "tumblehome" and "sheer plan" are added to
`UBIQUITOUS_LANGUAGE.md`.
