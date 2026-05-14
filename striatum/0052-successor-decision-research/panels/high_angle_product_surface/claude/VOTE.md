---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_f88a01cd66f643d788cb7d26cbd31602
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_high_angle_product_surface_claude
lease: lease_b3f789323ab14d2d9a3cf9ba665df8f1
date: 2026-05-14

# Vote — High-Angle Product Surface Decision

## Vote: Option A — Staged Explicit Surfacing (CLI → Sweep opt-in → Comparison display-only → Web → Desktop)

## Decision Sentence (for `docs/DECISION_LOG.md`)

Adopt a staged, explicit, opt-in surfacing path for fixed-trim generated-body
v1 high-angle `GZ`: an opt-in `kayakgen stability` flag/subcommand emits the
computed JSON only after RFC 0024 generated-body and per-heel convergence
gates pass; sweep gains a separate opt-in evaluator switch that defaults
`false` and excludes high-angle numeric fields from default candidate records,
`summary.csv`, and frontiers; comparison reports may render the loaded curve
and grid-bounded summaries as display-only candidate evidence (no objective
promotion); web/desktop remain on current unavailable copy until shared
read-models can render an "Unvalidated hydrostatic comparison" panel with
body/load/trim/provenance/warnings adjacent to any numeric output, and
desktop is the last and most minimal surface. Default `kayakgen stability`
behavior, default Pareto objectives (D010 — `GM0_m`, `displacement_error_kg`,
`mesh_problem_count`), and all current no-claim copy remain unchanged; any
exploratory high-angle objective requires a separate admissibility-registry
entry before it can be selected.

## Evidence And Citations

### Local evidence (verified against the worktree)

- D007 already accepts `generated_hull_plus_deck_closed_body_v1` as the v1
  design (`docs/DECISION_LOG.md:40`). The remaining decision is *when and how
  to surface it*, not whether to recompute or to free-trim.
- Workflow 0051 landed the evaluator: `evaluate_gz_curve()` returns computed
  records only when generated-body gates pass and hides the curve when any
  heel point fails to converge (`kayakgen/eval/stability.py:1173-1209`).
  Computed records carry `method="fixed_trim_generated_body_v1"`,
  `fixture_only=False`, body refs, heel-point metadata, and the
  `unvalidated_hydrostatic_comparison`/`grid_bounded` semantics tags. The
  workflow 0051 MF2 remediation also lifted those additive fields and the new
  method value into the canonical `GZCurve` (`kayakgen/eval/contract.py`),
  so v1 output already round-trips through `StabilityResult.gz_curve` without
  metadata loss.
- Product surfaces have not yet been wired. The CLI `stability` command
  still only writes initial or equilibrium stability JSON
  (`kayakgen/cli/main.py:276-326`), so a new explicit flag/subcommand is the
  cleanest first surface. Sweep records and web copy still match the
  "unavailable" posture documented in the research packet
  (`striatum/0052-successor-decision-research/research/high_angle_product_surface/RESEARCH.md:62-72`).
- Roadmap policy already forbids default high-angle promotion until the
  generated-body evidence gate and accepted heeled integration model land
  (`docs/ROADMAP.md:51-53`), and Batch G requires unavailable-by-default
  surfaces until v1 product-surface gates land
  (`docs/ROADMAP.md:255-274`). Both align with staged, explicit surfacing
  and against broad immediate surfacing or objective promotion.
- D010 fixes the default Pareto objectives at `GM0_m`,
  `displacement_error_kg`, and `mesh_problem_count`
  (`docs/DECISION_LOG.md:43`). Any high-angle metric must clear a registry
  entry before it can be ranked, which Option A respects and Option C
  violates.
- The workflow 0051 final review confirms v1 is computable but
  intentionally not surfaced yet
  (`striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:181-184`),
  i.e., Option B is *today's* posture by default; the open question is
  whether to keep it or to authorize the staged surface.

### External evidence (independent check, accessed 2026-05-14)

I cross-checked the research packet's external citations against my own
knowledge of how these references frame `GZ` curves, and they hold:

- USCG Stability Reference Guide and eCFR 46 CFR §28.570 / §174.015 frame
  `GZ` as a loading-condition-and-trim-dependent curve and tie regulatory
  use to free-trim, downflooding angle, and area-under-curve thresholds.
  Kayakgen v1 is explicitly fixed-trim and explicitly does not model
  cockpit openings or downflooding, so the surface must keep
  fixed-upright-trim, sealed-deck, and no-regulatory-criterion wording
  visible. Option A bakes that into every surface; Option C cannot.
- ISO 12217-3:2022 (public abstract) excludes canoes and kayaks from its
  small-craft assessment scope. The surface must therefore never imply ISO
  category, "passes", or "seaworthy". Option A's display rules carry that
  forward.
- Maxsurf and Orca3D — both maintained professional tools — surface `GZ`
  only with explicit loadcase, heel range, trim policy, criteria context,
  and body-completeness notes. Their public docs support the "show
  provenance/warnings adjacent to numeric output" rule that Option A makes
  load-bearing.
- Guillemot Kayaks (Nick Schade) is kayak-specific and explicitly says
  common `GZ` curves assume an immobile paddler. The surface must keep the
  hull-fixed passive-CG and active-paddler-not-modeled warnings visible.

These checks point at the same direction: surface v1 only with full
provenance and explicit comparator framing — not as a default, not as an
objective, not as a regulatory or safety claim. Option A is the option that
operationalizes that.

## Why The Rejected Alternatives Lose

### Option B — Artifact-only, no product surface yet (loses)

Defensible but unnecessarily conservative. The v1 evaluator and the
canonical contract round-trip already landed in workflow 0051; the gates
the v1 result respects (generated-body diagnostics, per-heel convergence,
sealed-body/no-safety warnings) are already enforced inside
`evaluate_gz_curve()`. Keeping the result behind direct evaluator callers
strands a working comparator behind internal APIs, delays feedback on the
JSON contract, and does not actually reduce claim risk if Option A's
guardrails (opt-in, default behavior unchanged, no objective promotion,
explicit display rules) are enforced. The external evidence does not
support holding output back when those guardrails are in place.

### Option C — Broad immediate surfacing everywhere (loses, must be rejected)

This is the option the project should *not* take. It would:

- conflict with the current test posture forbidding high-angle fields in
  sweep summaries and web render-source copy
  (`tests/test_sweep.py`, `tests/test_web_layout.py`);
- create ranking pressure before objective metadata exists, contradicting
  D010 and the workflow 0050 admissibility split;
- expose live web sliders to a fixed-trim sealed-body curve that users may
  read as a capsize or safety result, directly against the USCG / eCFR /
  ISO framing of `GZ` curves;
- ignore that desktop and web are live-slider surfaces unsuitable as
  *first* surfaces for a per-heel solve that can fail or take time.

### Option D — Wait for validation or free-trim successor (loses)

This is stronger than D007 and would effectively revoke v1's accepted
status without new evidence. D007's revisit condition contemplates a
free-trim successor or cockpit/flooding model as *future* work, not as a
prerequisite to surfacing the comparator. External professional tools
(Maxsurf, Orca3D) routinely surface `GZ` with explicit fixed-vs-free-trim
labeling and criteria context — they do not require model-test validation
before the curve becomes visible. Option D would block a comparator the
project has already accepted as the right v1 design.

## Implementation Gates (must remain in force)

Carried forward verbatim from the research packet because each gate
defends a concrete no-claims boundary, and adopted into the vote:

1. Gated evaluator contract tests for computed, unavailable, failed
   diagnostic, source-hash mismatch, synthetic fixture, and non-converged
   heel-point cases.
2. CLI tests proving default `kayakgen stability` still omits high-angle
   output, that explicit high-angle output includes
   provenance/warnings/method/body refs, and that unavailable cases
   serialize with empty arrays and `None` summaries.
3. Sweep tests proving high-angle is opt-in, that default
   candidate/`summary.csv` records remain free of high-angle numeric
   metrics, that fixture-only records are excluded, and that failed
   candidates do not enter frontiers.
4. Objective/report tests proving high-angle metrics are not defaults and,
   if later selectable, produce an exploratory/display-only warning with no
   design-fitness claim. Adding any high-angle metric as an objective
   requires a new admissibility-registry entry first.
5. Web/desktop copy tests extending the existing forbidden-claim checks to
   allow only documented negative/no-claim phrases and to prevent safety,
   seaworthiness, capsize, pass/fail, ISO-category, or final-design
   wording. Web rendering must render an "Unvalidated hydrostatic
   comparison" panel with body/load/trim/provenance/warnings *before* any
   plot or table.
6. User-guide and roadmap updates that state exactly which surfaces can
   emit v1 and repeat that the result is an unvalidated fixed-trim
   hydrostatic comparison curve.

## No-Claims Language That Must Remain In Force

- "Fixed-upright-trim, hull-fixed passive CG, sealed deck / no cockpit
  opening, deck immersion, flooding/downflooding not modeled, active
  paddler not modeled" assumptions/warnings remain visible adjacent to any
  numeric high-angle output.
- Results are labeled `result_semantics="unvalidated_hydrostatic_comparison"`
  and `summary_semantics="grid_bounded"`. No surface may use "safe angle",
  "capsize angle", "seaworthy", "passes", "ISO category", "validated",
  "final design fitness", or "solver-ready" wording for v1 output.
- The default `kayakgen stability` command, default sweep objectives,
  default comparison frontier, default desktop and web slider panels, and
  default web copy remain on their current unavailable/no-claim posture
  unless the user explicitly opts into the new high-angle path.
- Fixture-only results remain internal/test evidence and never satisfy any
  user-facing high-angle surface.
- Unavailable records are first-class output: a failed body gate,
  source-hull hash mismatch, diagnostic mismatch, non-converged heel point,
  or missing body ref surfaces status/warnings with empty arrays and
  `None` summaries.
- D010's default Pareto objectives (`GM0_m`, `displacement_error_kg`,
  `mesh_problem_count`) remain the defaults; high-angle metrics are not
  promotable to objectives until a new admissibility-registry entry lands.
- `cfd_ready`, calibrated resistance, real OpenFOAM `succeeded`, public
  hosted demo, and final-design-fitness claims remain governed by their
  own decisions (D003/D004/D005/D006/D008) and are not touched by this
  vote.

## Confidence

**High.**

D007 already settled the v1 design, workflow 0051 landed the evaluator and
the canonical contract round-trip with the exact provenance fields Option A
requires, and the research packet's external citations align with the
fixed-trim/sealed-body/no-regulatory-criterion guardrails that Option A
operationalizes. Option C is foreclosed by current tests and D010, and
Option D would silently overturn D007 without new evidence. Option B is
defensible but does not match the evidence: with the gates above enforced,
staged surfacing is the conservative choice, not the aggressive one. The
risk concentrated in this decision is *wording and default behavior*, both
of which Option A's gates make machine-enforceable.
