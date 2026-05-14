---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: operator [self-declared: operator-0052-panel-wave1-gemini-4]
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_da2884eeb8c94bca871c8f6c6e98894b
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_high_angle_product_surface_gemini
lease: lease_06e58e49003a45baa54e021f39c8e367
date: 2026-05-14

# Vote — High-Angle Product Surface Decision

## Vote: Option A — Staged Explicit Surfacing

## Decision Sentence

Adopt a staged, explicit, opt-in path for surfacing fixed-trim generated-body v1 high-angle `GZ`: start with an opt-in CLI JSON output, followed by opt-in sweep artifacts and display-only comparison/web views. High-angle results must remain excluded from default sweep objectives, comparison frontiers, desktop live panels, and web slider defaults. Any numeric output must be accompanied by explicit body, load, trim, and provenance warnings, and must never be labeled as a validation, safety, seaworthiness, capsize prediction, solver readiness, or final design fitness claim unless a subsequent admissibility decision explicitly authorizes it.

## Evidence And Citations

### Local Evidence
- `docs/DECISION_LOG.md:40` (D007) has established fixed-trim generated-body v1 as the accepted design for computing the high-angle `GZ` curve, with hull-fixed passive CG, fixed upright trim, per-heel sinkage solve, and sealed-body/flooding warnings.
- `docs/ROADMAP.md:51-53, 269-274` sets the policy that high-angle metrics remain unavailable until generated-body evidence passes. Surfaces must reflect unvalidated hydrostatic comparison curves, avoiding any safety or seaworthiness claims.
- Workflow 0051 implemented the necessary baseline: `evaluate_gz_curve()` checks generated-body gates, handles per-heel failures, and returns computed records containing full provenance metadata (`method="fixed_trim_generated_body_v1"`, `fixture_only=False`, body refs, diagnostic refs, and per-heel metadata).
- The current implementation appropriately keeps high-angle features out of existing default surfaces: `kayakgen stability` only produces initial/equilibrium JSON; sweep summaries exclude high-angle metrics; objective defaults remain `GM0_m`, `displacement_error_kg`, and `mesh_problem_count` (D010); and the web UI strictly marks high-angle output as unavailable.

### External Evidence (accessed 2026-05-14)
- **U.S. Coast Guard Stability Reference Guide**: Treats righting-arm curves as dependent on loading conditions, warning against broad safety claims from initial stability alone.
- **eCFR 46 CFR 28.570 and 174.015**: Tie righting arm criteria to free-trim analysis and downflooding behavior. Kayakgen v1 assumes fixed trim and lacks downflooding models, making it critical to avoid framing its output as fulfilling regulatory style criteria.
- **ISO 12217-3:2022**: Specifically excludes canoes and kayaks from its small-craft stability scope. Consequently, kayakgen v1 cannot claim ISO category assignment or safety guarantees.
- **Maxsurf and Orca3D**: Professional stability documentation confirms the standard of tying large-angle metrics explicitly to the analysis setup (load cases, trim choices, warnings) rather than presenting them as naked scalars.
- **Guillemot Kayaks (Nick Schade)**: Highlights that kayak stability curves rely on assumptions like an immobile paddler, which justifies kayakgen's warnings about passive CG and active paddler modeling.

## Why The Rejected Alternatives Lose

### Option B — Artifact-Only, No Product Surface Yet (Loses)
While holding the safest claim boundary, this option is excessively conservative. Since Workflow 0051 landed the canonical contract that supports per-heel metadata, body refs, and diagnostic states, continuing to hide v1 behind internal APIs prevents users from receiving the JSON contract feedback required for subsequent surface development. Staged, explicitly labeled surfacing is sufficient to mitigate claim risks.

### Option C — Broad Immediate Surfacing Everywhere (Loses)
Surfacing the metric immediately across all defaults conflicts with established tests forbidding high-angle fields in sweep summaries and web render sources. It introduces ranking pressure prior to objective metadata definitions and exposes fixed-trim, sealed-body curves without their necessary context, easily misleading users into interpreting them as safety or capsize guarantees.

### Option D — Wait For Validation Or Free-Trim Successor (Loses)
This is overly restrictive compared to D007's acceptance of fixed-trim generated-body v1. Waiting for physical model test validation or a free-trim successor before presenting any explicitly unvalidated comparison artifacts blocks a working, validated implementation for reasons unrelated to current roadmap boundaries.

## Implementation Gates

- Default `kayakgen stability` and existing default search/comparison workflows (including D010's objectives) must remain unchanged until explicitly triggered.
- Computed generated-kayak output is only permitted when the evaluator returns `status="computed"`, `method="fixed_trim_generated_body_v1"`, `fixture_only=false`, explicit body and diagnostic refs, `summary_semantics="grid_bounded"`, and `result_semantics="unvalidated_hydrostatic_comparison"`.
- CLI high-angle output must be explicit and JSON-centric, emitting detailed warnings instead of pass/fail criteria.
- Sweep surfacing must be opt-in. Default `summary.csv` and candidate artifacts exclude numeric high-angle metrics, limiting output to status and warnings.
- Comparison and Web surfaces must treat v1 as display-only evidence until admissibility rules allow objective promotion.
- Web rendering requires an explicit "Unvalidated hydrostatic comparison" panel detailing assumptions before displaying any plots or tabular data.
- Copy tests and user guides must strictly forbid phrasing related to safety, seaworthiness, capsize prediction, pass/fail, validation, and solver-readiness for v1 output.

## Confidence

**High.** Local D007 policy, Workflow 0051's successful structural changes to `evaluate_gz_curve()`, and external stability references align perfectly behind Option A. Enforcing explicit, provenance-rich artifacts avoids misleading regulatory or safety claims while allowing users to observe valid unvalidated comparisons.
