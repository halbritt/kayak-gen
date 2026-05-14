---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-002
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_e03f35fb8eb6476381f8557258f29612
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_research_high_angle_product_surface
lease: lease_303e45f950e446979c73b49afd55af0f
date: 2026-05-14

# Research - High-Angle Product Surface Decision

## Decision Question

When and how may fixed-trim generated-body v1 high-angle `GZ` output be surfaced
on CLI, sweep, comparison, desktop, or web while preserving the project's
unvalidated, no-safety, and no-seaworthiness boundaries?

## Short Answer

The conservative, evidence-supported answer is staged, explicit, and
comparison-only: expose v1 first as an opt-in CLI JSON artifact after the
generated-body and per-heel gates pass; then allow opt-in sweep artifacts and
display-only comparison/web views; keep default sweep objectives, comparison
frontiers, desktop live panels, and web slider defaults on the current
unavailable/read-only posture until a later claim/admissibility gate explicitly
permits more.

Numeric `GZ` values should never be the default stability answer, never be a
default objective, never be shown without body/load/trim/provenance/warnings,
and never be labeled as safety, seaworthiness, capsize prediction, final design
fitness, validation, or solver readiness.

## Local Constraints

The project already has the controlling policy:

- `docs/ROADMAP.md:51-53` says high-angle `GZ`, `GZ_max`,
  range-of-positive-stability, capsize-range, and secondary-stability metrics
  remain unavailable until a generated-body evidence gate and accepted heeled
  integration model land.
- `docs/DECISION_LOG.md:40` accepted fixed-trim generated-body v1:
  `generated_hull_plus_deck_closed_body_v1`, default 0-90 degrees by 5 degrees,
  hull-fixed passive CG, fixed upright trim, per-heel sinkage solve,
  clipping/capping diagnostics, grid-bounded summaries, and sealed-body /
  flooding warnings.
- `docs/ROADMAP.md:269-274` makes the product boundary explicit: until gates
  pass, all surfaces must show unavailable results; after v1 lands, results are
  unvalidated hydrostatic comparison curves, not safety, seaworthiness,
  capsize, design-fitness, or solver-readiness claims.
- Workflow 0051 changed the technical baseline: `evaluate_gz_curve()` now has
  generated-body v1 plumbing and returns computed values only after
  generated-body gates pass (`kayakgen/eval/stability.py:629-745`); it hides
  the curve if any heel point fails (`kayakgen/eval/stability.py:1173-1184`);
  and computed records carry `method="fixed_trim_generated_body_v1"`,
  `fixture_only=False`, body refs, full arrays, assumptions, warnings, and
  per-heel metadata (`kayakgen/eval/stability.py:1189-1209`).
- Product surfaces have not been wired yet. `kayakgen stability` still writes
  only initial/equilibrium stability JSON (`kayakgen/cli/main.py:277-326`).
  Sweep calls only initial or equilibrium stability and records only
  conservative stability summary fields (`kayakgen/search/sweep.py:245-320`).
  The current objective registry defaults remain `GM0_m`,
  `displacement_error_kg`, and `mesh_problem_count`
  (`kayakgen/search/objectives.py:49-87`). Web copy still says high-angle `GZ`
  is unavailable (`kayakgen/ui/web/app.py:240-243`), and tests still forbid
  high-angle fields in sweep summaries and web render-source copy
  (`tests/test_sweep.py:147-154`, `tests/test_web_layout.py:304-313`).

## External Evidence

Access date for all external sources: 2026-05-14.

- The U.S. Coast Guard stability guide frames a righting-arm curve as a
  loading-condition-specific plot of righting arm versus heel; it derives
  area-under-curve, zero crossing, maximum righting arm, and low-angle shape
  from that curve, while also warning that initial stability does not prove
  overall stability. This supports showing `GZ` only with load-case context and
  no broad safety claim. Source:
  https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/CG-5PC/CG-CVC/CVC3/references/Stability_Reference_Guide.pdf
  (opened lines 126-167).
- Current eCFR 46 CFR 28.570 uses GM, `GZ`, maximum righting arm, curve area,
  positive-righting-arm range, and flooding/free-surface conditions as formal
  vessel criteria; it also states that righting arm for that rule is calculated
  with the vessel free to trim until trimming moment is zero. That is directly
  relevant because kayakgen v1 is fixed-trim, so it must not be described as
  satisfying regulatory/free-trim criteria. Source:
  https://www.ecfr.gov/current/title-46/chapter-I/subchapter-C/part-28/subpart-E/section-28.570
  (opened lines 203-227).
- Current eCFR 46 CFR 174.015 defines stability criteria by area under the
  righting-arm curve up to the smallest of maximum righting arm, downflooding
  angle, or 40 degrees, and defines downflooding by openings that do not close
  watertight automatically. Kayakgen v1 explicitly does not model cockpit
  openings or downflooding, so product copy must avoid capsize/downflooding
  interpretations. Source:
  https://www.ecfr.gov/current/title-46/chapter-I/subchapter-S/part-174/subpart-B/section-174.015
  (opened lines 202-209).
- ISO 12217-3:2022 is a small-craft stability and buoyancy assessment standard
  for boats under 6 m, but its public abstract excludes canoes and kayaks. This
  supports the boundary that kayakgen cannot present v1 output as assigning an
  ISO small-craft design category or proving kayak safety. Source:
  https://www.iso.org/standard/79074.html (opened lines 144-160).
- Maxsurf's maintained stability documentation says large-angle analysis is
  based on a loadcase, heel range, fixed or free trim, damage/water-on-deck
  options, and criteria; it can tabulate/graph `GZ` and calculate criteria from
  the curve. This is useful product evidence: professional tools surface `GZ`
  with explicit analysis setup and criteria context, not as a naked scalar.
  Sources: https://maxsurf.net/stability-capability (opened lines 77-84,
  104-109) and https://maxsurf.net/stability/stability-detail (opened lines
  246-269, 288-303, 716-746).
- Orca3D's public documentation lists righting arm and trim angle versus heel
  as output at specified displacement/CG conditions, and separately says deck
  geometry is needed when deck immersion occurs in a righting-arm calculation.
  Its criteria examples also tell users to verify criteria files themselves.
  These support body-completeness warnings and explicit verification status.
  Sources: https://orca3d.com/pages/hydrostatics-stability/1000 (opened lines
  110-135), https://orca3d.freshdesk.com/support/solutions/articles/8000097386-multihull-hydrostatics-stability
  (opened lines 26-33), and
  https://orca3d.com/pages/example-stability-criteria (opened lines 115-121).
- Nick Schade's kayak-specific explainer describes a kayak stability curve as
  horizontal CG-CB distance over heel angle, tied to righting moment. It also
  states that the common curve assumes an immobile paddler and that CG height,
  paddler weight, and paddler skill materially affect interpretation. This is
  non-normative product/domain context, but it supports keeping kayakgen's
  hull-fixed passive-CG and active-paddler-not-modeled warnings visible.
  Source: https://guillemot-kayaks.com/kayak-stability (opened lines 72-85,
  107-128, 131-135).

## Viable Options

### Option A - Staged Explicit Surfacing (Conservative Default)

Surface computed v1 output only when the existing evaluator returns:

- `status="computed"`;
- `method="fixed_trim_generated_body_v1"`;
- `fixture_only=false`;
- generated-body `body_ref`, `body_type`, and `body_diagnostic_ref`;
- `summary_semantics="grid_bounded"`;
- `result_semantics="unvalidated_hydrostatic_comparison"`;
- all requested heel points computed with aligned `heel_point_metadata`;
- assumptions/warnings including fixed upright trim, hull-fixed passive CG,
  sealed deck/no cockpit opening, deck immersion, flooding/downflooding not
  modeled, active paddler response not modeled, and no safety/seaworthiness
  claim.

Recommended surface order:

1. **CLI first.** Add an explicit flag or subcommand for high-angle output,
   with default `kayakgen stability` unchanged. The JSON may include full
   `gz_curve`; stdout should report only status, output path, body ref, method,
   and warnings. The command must never imply pass/fail criteria, ISO category,
   safety, seaworthiness, or capsize prediction.
2. **Sweep second, opt-in only.** Add a separate high-angle evaluator switch
   defaulting false. Per-candidate evaluation JSON may carry the full
   `stability.gz_curve`; candidate records and `summary.csv` should initially
   carry only status, method, warning count, and artifact reference. Numeric
   high-angle summaries should wait for objective/display metadata so they
   cannot silently become ranking inputs.
3. **Comparison third, display-only.** Comparison reports may show loaded v1
   curves and grid-bounded summaries as candidate evidence, but not default
   objectives. If a later workflow wants explicit exploratory high-angle
   objectives, it should add objective metadata first and mark reports
   exploratory. Until then, `max_gz_m`, `heel_at_max_gz_deg`,
   `range_positive_stability_deg`, `area_under_positive_gz_m_deg`, and
   `righting_moment_nm` remain display/read-model fields only.
4. **Web after report/read-model stability.** Keep live slider analysis on
   primary stability unless a computed v1 record is loaded or explicitly
   requested through a gated backend path. Web should render an "Unvalidated
   hydrostatic comparison" panel with body/load/trim assumptions and warnings
   before any plot or table. With no computed record, the current unavailable
   copy remains correct.
5. **Desktop last or minimal.** The desktop GUI is a supported local surface,
   not the primary UI composition target. It can keep the current no-claim
   status or add only the same read-only status/summary as web after shared
   read models exist. It should not be the first product surface for high-angle
   graphs.

This option gives users the real artifact they need for inspection while
keeping defaults, ranking, UI copy, and optimizer posture conservative.

### Option B - Artifact-Only, No Product Surface Yet

Keep v1 available only to direct evaluator callers and tests. CLI, sweep,
comparison, desktop, and web continue to show unavailable high-angle results.

This is safest for claims, but it strands the newly landed v1 evaluator behind
internal APIs and delays feedback on the actual JSON contract. It is defensible
if reviewers believe the generated-body solver still lacks enough numerical
review, but it is more conservative than the external evidence requires.

### Option C - Broad Immediate Surfacing Everywhere

Wire computed v1 into CLI, sweep summaries, comparison metrics, web plots, and
desktop panels at once.

This should be rejected. It conflicts with the current test posture that keeps
high-angle fields out of sweep summaries and web render copy, creates ranking
pressure before objective metadata exists, and risks users reading a fixed-trim
sealed-body curve as a safety or capsize result.

### Option D - Wait For Validation Or Free-Trim Successor

Do not surface any real generated-kayak high-angle values until measured kayak
validation, cockpit/flooding modeling, or a free-trim per-heel model lands.

This is stronger than the existing D007 decision. It is appropriate only if
the project decides that unvalidated comparison curves are too easy to misuse
even with explicit warnings. It preserves safety boundaries but blocks the
accepted v1 comparator from becoming product-observable.

## Product Surface Rules

The following rules should apply no matter which implementation path is chosen:

- Default behavior remains unchanged unless the user explicitly asks for
  high-angle output.
- Fixture-only results remain internal/test evidence and never satisfy CLI,
  sweep, comparison, desktop, or web generated-kayak output.
- Unavailable records are first-class product output. A failed body gate,
  source-hull hash mismatch, diagnostic mismatch, non-converged heel point, or
  missing body ref should surface status/warnings with empty arrays and `None`
  summaries.
- Use "grid-bounded last positive `GZ` angle" or the raw field name in JSON;
  avoid UI labels that read as a capsize guarantee. Do not use "safe angle",
  "capsize angle", "seaworthy", "passes", or "ISO category".
- Show load case, KG/CG convention, trim policy, heel grid, body ref,
  diagnostic ref, method, result semantics, and warnings adjacent to numeric
  output.
- Treat `righting_moment_nm` and area-under-positive-`GZ` as hydrostatic
  comparison quantities only. They are not wave, surf, bracing, rolling,
  flooding, re-entry, or active-paddler models.
- Comparison and search defaults remain governed by D010: `GM0_m`,
  `displacement_error_kg`, and `mesh_problem_count` stay the default
  objectives. High-angle metrics require a new registry/admissibility entry
  before they can be selected as objectives, and should be display-only in the
  first product slice.

## Risks And Unknowns

- **Fixed-trim mismatch.** Regulatory examples often require or support
  free-trim calculations; eCFR 46 CFR 28.570 explicitly requires free trim for
  that rule. Kayakgen v1 is useful as a comparator, but fixed-trim wording must
  be visible wherever values appear.
- **Sealed full-deck body can mislead.** The model does not include cockpit
  openings, downflooding, flooded compartments, paddler body volume, or water on
  deck. External tools and regulations treat those conditions as meaningful.
- **Ranking pressure.** Once numeric fields exist in sweep/compare artifacts,
  future users or optimizers may treat them as objectives unless metadata
  blocks that path.
- **Summary naming.** `range_positive_stability_deg` is a valid internal field,
  but product labels should avoid making it sound like an actual capsize or
  recovery guarantee.
- **Latency and UX.** Web/desktop live sliders are not the right first surface
  if generated-body creation and per-heel clipping are slower or failure-prone.
  Start with explicit artifact generation and loaded-report display.
- **Validation gap.** No measured kayak stability source has been accepted.
  Warnings cannot turn the curve into a validated prediction.

## Implementation Gates

Before any product surface shows numeric generated-kayak `GZ`, require:

1. Gated evaluator contract tests for computed, unavailable, failed diagnostic,
   source-hash mismatch, synthetic fixture, and non-converged heel-point cases.
2. CLI tests proving default `kayakgen stability` still omits high-angle output,
   explicit high-angle output includes provenance/warnings, and unavailable
   cases serialize with empty arrays and `None` summaries.
3. Sweep tests proving high-angle is opt-in, default summaries remain free of
   high-angle numeric metrics, fixture-only records are excluded, and failed
   candidates do not enter frontiers.
4. Objective/report tests proving high-angle metrics are not defaults and, if
   later selectable, produce an exploratory/display-only warning with no
   design-fitness claim.
5. Web/desktop copy tests extending the existing forbidden-claim checks to
   allow only documented negative/no-claim phrases and to prevent safety,
   seaworthiness, capsize, pass/fail, ISO-category, or final-design wording.
6. User-guide and roadmap updates that state exactly which surfaces can emit v1
   and repeat that the result is an unvalidated fixed-trim hydrostatic
   comparison curve.

## Recommendation

Adopt Option A.

The evidence supports surfacing v1 as a real, opt-in hydrostatic comparison
artifact once body diagnostics and per-heel convergence pass. It does not
support default ranking, pass/fail criteria, regulatory interpretation,
seaworthiness wording, capsize language, or live UI promotion. The safest next
decision is therefore: CLI JSON first; sweep artifacts second; comparison and
web display-only after shared metadata exists; desktop minimal/supporting; no
objective promotion until a separate admissibility registry entry and tests
make the claim state machine-enforceable.
