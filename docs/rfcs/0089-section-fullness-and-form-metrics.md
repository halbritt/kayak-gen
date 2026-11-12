# RFC 0089: Section fullness, form metrics and multi-load righting arms

Status: landed stage 1 (section exponent, form metrics, load-case GZ table)
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

- No tumblehome, knuckle or second control on the topside strip. That is
  stage 2.
- No search admission. The new measures are display-only; making them
  objectives or constraints, and exposing the new shape fields as
  default search variables, is stage 2.
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
`form.catch_zone_max_beam_m`, `form.beam_at_reference_m`. All four are
registered `display_only`.

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
- Stage 2 — freer topside and deck controls (tumblehome, carried
  breadth), admission of the new measures as search objectives and
  constraints, default search variables for the new shape fields.

## Domain Modeling

`FormMetrics` is a read model beside `TurningMetrics`. "Section
exponent", "class ratio" and "catch zone" are added to
`UBIQUITOUS_LANGUAGE.md`.
