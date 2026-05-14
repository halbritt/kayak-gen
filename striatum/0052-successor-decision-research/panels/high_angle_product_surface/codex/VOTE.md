---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-004
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_b74d9c32cf634727bcd8c5adde9fdf85
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_high_angle_product_surface_codex
lease: lease_bfd44633478b45cebdcd26827da5843b
date: 2026-05-14

# Vote - High-Angle Product Surface

Vote: Option A - staged explicit surfacing.

## Decision Sentence

Surface fixed-trim generated-body v1 high-angle `GZ` only as an explicit,
opt-in, provenance-rich hydrostatic comparison artifact: CLI JSON first, then
opt-in sweep artifacts, then display-only comparison/web read models, with
desktop kept minimal/supporting and no default objective, live UI, safety,
seaworthiness, capsize, ISO, validation, solver-readiness, or design-fitness
claim unless a later claim/admissibility decision authorizes it.

## Evidence

The research packet's local posture is correct. The roadmap still says
high-angle `GZ`, `GZ_max`, range-of-positive-stability, capsize-range, and
secondary-stability metrics remain unavailable until generated-body evidence
and an accepted heeled-integration model land (`docs/ROADMAP.md:51-53`), and
its Batch G exit criteria keep all CLI/sweep/comparison/desktop/web surfaces
on unavailable results until gates pass (`docs/ROADMAP.md:268-275`). D007
selects fixed-trim generated-body v1 but labels the eventual result as an
unvalidated hydrostatic comparison curve (`docs/DECISION_LOG.md:40`).

Workflow 0051 changed the implementation baseline enough that artifact-only
indefinite deferral is no longer the best next decision. `evaluate_gz_curve()`
now gates synthetic bodies away from real kayak output, rejects missing or
unresolved body refs as unavailable, and runs generated-body v1 only after body
diagnostics pass (`kayakgen/eval/stability.py:629-749`). Computed v1 results
carry `method="fixed_trim_generated_body_v1"`, `fixture_only=False`, body refs,
diagnostic refs, arrays, assumptions, warnings, and per-heel metadata
(`kayakgen/eval/stability.py:1189-1209`). The canonical contract now accepts
that metadata while still forbidding legacy/minimal curves, unknown fields,
unavailable payloads with values, and misaligned arrays
(`kayakgen/eval/contract.py:141-242`).

The product surfaces remain conservative today. The CLI `stability` command
emits only initial or equilibrium stability JSON and has no high-angle flag
(`kayakgen/cli/main.py:276-326`). Sweep records include initial/equilibrium
stability summaries but not high-angle metrics (`kayakgen/search/sweep.py:245-320`),
and tests explicitly forbid `max_gz_m`, `righting_moment_nm`,
`range_positive_stability_deg`, and related fields from sweep summaries
(`tests/test_sweep.py:147-155`). Default comparison objectives are still
`GM0_m`, `displacement_error_kg`, and `mesh_problem_count`
(`kayakgen/search/objectives.py:49-105`). Web copy still says high-angle `GZ`
is unavailable (`kayakgen/ui/web/app.py:240-243`), with tests forbidding
high-angle field names in the current render source
(`tests/test_web_layout.py:304-318`).

Independent external checks support surfacing curves only with analysis setup,
load condition, and warnings. The U.S. Coast Guard stability guide describes
righting-arm curves as loading-condition-specific curves whose area, maximum,
zero crossing, and low-angle shape inform stability, so a naked scalar would be
misleading
(https://www.dco.uscg.mil/Portals/9/DCO%20Documents/5p/CG-5PC/CG-CVC/CVC3/references/Stability_Reference_Guide.pdf).
Current 46 CFR 28.570 uses GM, `GZ`, maximum righting arm, curve area,
positive-arm range, flooding conditions, and free trim as criteria; kayakgen v1
is fixed-trim and must not be described as meeting that regulatory style of
analysis
(https://www.ecfr.gov/current/title-46/chapter-I/subchapter-C/part-28/subpart-E/section-28.570).
Current 46 CFR 174.015 defines righting-arm criteria against the smallest of
maximum righting arm, downflooding angle, or 40 degrees, and defines
downflooding by watertight-closure behavior; kayakgen v1 does not model cockpit
openings or downflooding
(https://www.ecfr.gov/current/title-46/chapter-I/subchapter-S/part-174/subpart-B/section-174.015).
ISO 12217-3:2022 is a small-craft stability/buoyancy standard but its public
abstract excludes canoes and kayaks, so v1 output cannot be framed as assigning
an ISO category or proving kayak safety
(https://www.iso.org/standard/79074.html).
Maxsurf and Orca3D both reinforce the same product pattern: large-angle or
righting-arm analysis is tied to load cases, fixed/free trim choices, criteria,
deck/submerged-geometry assumptions, and reporting context rather than being
just another always-on design metric
(https://maxsurf.net/stability-capability,
https://maxsurf.net/stability/stability-detail,
https://orca3d.com/pages/hydrostatics-stability/1000,
https://orca3d.freshdesk.com/support/solutions/articles/8000097386-multihull-hydrostatics-stability).

## Why Other Options Lose

Option B, artifact-only with no product surface, preserves claims but wastes
the now-typed v1 contract. It also delays user and CI feedback on the exact
JSON shape that future surfaces must consume. The better conservative boundary
is opt-in CLI JSON with provenance and unavailable states, not indefinite
internal-only access.

Option C, broad immediate surfacing everywhere, should be rejected. It would
fight current tests and product copy, create ranking pressure before objective
metadata exists, and make fixed-trim sealed-body values too easy to read as
safety, capsize, or final design guidance.

Option D, waiting for validation, flooding, or free-trim successor work before
any surfacing, is stricter than D007. It is reasonable for safety claims, but
too strict for explicitly unvalidated comparison artifacts after the generated
body and per-heel gates pass.

## Implementation Gates

- Default `kayakgen stability`, default sweeps, default comparison objectives,
  desktop live panels, and web live sliders stay unchanged until explicit
  product-surface work lands.
- Numeric generated-kayak `GZ` output requires `status="computed"`,
  `method="fixed_trim_generated_body_v1"`, `fixture_only=false`, body refs,
  diagnostic refs, `summary_semantics="grid_bounded"`,
  `result_semantics="unvalidated_hydrostatic_comparison"`, aligned per-heel
  metadata, and all requested heel points computed.
- CLI surfacing must be explicit and JSON-first. Stdout should report status,
  output path, body/method/provenance, and warnings rather than presenting
  pass/fail criteria.
- Sweep surfacing must be opt-in. Candidate artifacts may carry full curves;
  summary CSV and frontiers should initially carry only status, method, warning
  count, and artifact refs, not numeric high-angle metrics.
- Comparison/web surfacing must be display-only until an objective/admissibility
  registry entry exists. High-angle metrics cannot become defaults and cannot
  be silently selectable as design-fitness objectives.
- Fixture-only records remain internal/test evidence and cannot satisfy CLI,
  sweep, comparison, desktop, or web generated-kayak output.
- Unavailable and failed records are valid product output: empty arrays,
  `None` summaries, provenance where available, and specific warnings for body
  gate failures, hash/diagnostic mismatch, missing body refs, or non-converged
  heel points.
- Copy and tests must forbid safety, seaworthiness, capsize guarantee, safe
  angle, pass/fail, ISO-category, validation, solver-readiness, final
  prediction, and design-fitness wording.
- User guide and roadmap updates must name every surfaced product surface and
  repeat that v1 is an unvalidated fixed-trim hydrostatic comparison curve with
  sealed-body, flooding/downflooding-not-modeled, cockpit-not-modeled,
  active-paddler-not-modeled, and no-safety/no-seaworthiness warnings.

## Confidence

High. The local policy, current code state, and external stability references
all support the same answer: surface the v1 curve as an explicit comparison
artifact after evidence gates pass, while keeping defaults and ranking
conservative.
