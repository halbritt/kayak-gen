---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14

# High-Angle Stability Model Research

## Decision Question

Which high-angle `GZ` model should kayak-gen accept before it emits real generated-kayak secondary-stability curves: body profile, heel grid, trim policy, CG convention, waterline clipping, residuals, convergence warnings, deck/flooding assumptions, and user-facing warnings?

## Local Project Constraints

The current product boundary is explicit: high-angle `GZ`, `GZ_max`, range-of-positive-stability, capsize-range, and secondary-stability metrics are unavailable for real generated kayaks until both a generated-body evidence gate and an accepted heeled integration model land (`docs/ROADMAP.md:51-53`). The high-angle stability track is `blocked`, and the required next work is a design gate covering accepted body profile, heel grid, trim policy, CG convention, waterline clipping, residuals, convergence warnings, and deck/flooding assumptions (`docs/ROADMAP.md:71`, `docs/ROADMAP.md:191-207`).

The PRD and user guide say the same thing from the user-facing side. Hydrostatics and upright trim exist, but high-angle stability is not currently available because real heeled integration over generated closed-body evidence has not landed (`docs/PRD.md:37-40`). The `kayakgen stability` command writes initial stability and upright equilibrium results; high-angle curves and secondary-stability peak metrics remain unavailable, with fixture-only synthetic math kept out of real kayak claims (`docs/USER_GUIDE.md:113-143`).

RFC 0043 is the current successor and should frame the decision. It says RFC 0024's unavailable boundary remains in force, and a future workflow may implement generated-body high-angle `GZ` only after model choices are recorded and tested: generated-body profile, heel grid, heel transform/sign convention, trim policy, displacement solve, CG convention, waterline clipping, and deck/flooding assumptions (`docs/rfcs/0043-high-angle-gz-successor.md:70-93`). Until then, the evaluator must not fill `gz_m`, righting moments, or summary metrics with placeholders or fixture-derived values (`docs/rfcs/0043-high-angle-gz-successor.md:95-100`).

The body evidence gate is already narrow. RFC 0024 requires a generated kayak closed body with passing closure, positive signed volume, zero blocking boundary/nonmanifold edges, no blocking self-intersections, matching source hull hash/coordinates/units/tolerances, and a stability-compatible closure policy before real kayak `GZ` can be emitted (`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:44-65`). Synthetic bodies are only internal fixtures and must stay `fixture_only` (`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:62-65`). RFC 0022 defines the current generated closed-body profile, `generated_hull_plus_deck_closed_body_v1`, as a full hull-plus-deck body derived from the parametric hull, with cap surfaces, join strips, waterline metadata, source hash, policy, and diagnostics; display STLs remain separate and not authoritative (`docs/rfcs/0022-generated-closed-body-construction.md:46-60`, `docs/rfcs/0022-generated-closed-body-construction.md:110-127`).

The current code matches that boundary. `kayakgen/eval/stability.py` says high-angle GZ returns an RFC 0024 result envelope but real kayak curves remain unavailable until a generated closed body passes diagnostics and a later heeled-volume solver lands (`kayakgen/eval/stability.py:1-8`). The current default heel grid is `0, 5, ..., 90` degrees, while real-GZ assumptions are explicitly unresolved for CG model, trim policy, and deck/flooding (`kayakgen/eval/stability.py:38-44`). Even when a generated body passes diagnostics, the evaluator still returns unavailable with `high_angle_gz_generated_body_solver_not_implemented` (`kayakgen/eval/stability.py:617-641`). The `GZCurve` contract rejects legacy unproven curves and requires availability, body provenance, grid, arrays, summaries, assumptions, and warnings to be coherent (`kayakgen/eval/contract.py:109-165`).

The local design constraints still describe the desired domain output: primary stability via `GM0`, secondary stability via the high-angle `GZ` curve, a 0-90 degree full curve, and kayak secondary-stability peaks typically in the 25-40 degree range (`docs/design/kayak_hull_design_constraints.md:21-48`). That is a target for future hydrostatics, not current product capability.

## External Evidence

External sources were accessed on 2026-05-14.

| Source | Claim supported |
| --- | --- |
| [Nick Schade / Guillemot Kayaks, Kayak Stability](https://guillemot-kayaks.com/kayak-stability) | Kayak stability curves are righting-arm curves built from CG/CB separation over heel; the example convention fixes the paddler bolt upright in the seat with no active correction and highlights CG height as material. This supports a clear fixed-CG assumption and a visible warning that active bracing/body motion is out of model. |
| [Bentley Maxsurf Stability manual, Analysis menu](https://maxsurf.net/stability/Bentley/Maxsurf%20Stability%20Manual.htm) | Large-angle stability tools expose heel-angle ranges, loadcase displacement/VCG/LCG, fixed trim or free trim modes, and water-on-deck/damage options. This supports making trim policy and flooding/deck assumptions explicit choices rather than hidden defaults. |
| [46 CFR 28.570, Intact stability criteria](https://www.law.cornell.edu/cfr/text/46/28.570) | Regulatory intact-stability calculations use righting arms, areas under the curve, downflooding angle, and, in one method, free trim until trimming moment is zero at each heel. This supports recording downflooding/flooding assumptions and distinguishing fixed-trim comparator curves from free-trim equilibrium curves. |
| [IMO 2008 Intact Stability Code page](https://www.imo.org/en/OurWork/Safety/Pages/IntactStability-Default.aspx) | IMO frames intact stability around righting lever criteria and weather/wave/flooding limitations. It is not kayak-specific, but it reinforces that `GZ` values need criteria context and cannot be reworded as seaworthiness or safety claims. |
| [PIAS manual, Calculation of GZ curves](https://www.sarc.nl/images/manuals/pias/htmlEN/stab.html) | Stability software warns that heel-angle resolution should be sufficient where curves have high curvature, and that large heel-angle ranges are needed for asymmetric cases. This supports a default grid plus caller-supplied grids, with summaries labeled grid-bounded or interpolation-bounded. |
| [DELFTship manual, Stability](https://www.delftship.net/manuals/professional/introduction/stability/) | Stability outputs include righting-arm curves and downflooding/deck-edge submersion curves. This supports user-facing warnings when deck immersion or flooding is not modeled. |
| [VTK Cutter class documentation](https://vtk.org/doc/nightly/html/classvtkCutter.html) | Cutting data with a plane is a standard geometric operation for extracting intersections, with sorted contour values and a specified cut function. This supports treating the heeled waterplane intersection as an explicit geometric operation. |
| [VTK FillHolesFilter documentation](https://vtk.org/doc/release/4.0/html/classvtkFillHolesFilter.html) | Filling open mesh boundaries is topology-sensitive and can fail or create overlap for nonmanifold/open surfaces. This supports the local rule that waterline clipping/capping must depend on closed-body diagnostics and emit failures rather than silently fabricating a volume. |
| [Trimesh base documentation](https://trimesh.org/trimesh.base.html) | Trimesh exposes `is_watertight`, `is_volume`, volume, center of mass, and mass properties on mesh bodies, with volume meaningful for watertight volume meshes. This supports the need for closed, oriented body evidence before volume/centroid integration. |

## Model Choices To Decide

### Accepted Body Profile

The conservative local fit is `generated_hull_plus_deck_closed_body_v1`, but only as a stability evidence body after RFC 0024 gates pass. It is already a generated kayak body, not a display STL and not a CFD package. Using it avoids creating a second body concept before the existing one is exhausted.

The risk is that a full hull-plus-deck closed body represents a sealed boat. Kayaks may have cockpit openings and flooding/downflooding behavior that the current hull model does not represent. If this profile is chosen for v1, results must say `sealed_deck_profile_no_cockpit_opening`, `deck_immersion_assumption`, and `flooding_not_modeled` when relevant. A future stability-specific hull-only or cockpit-cut profile remains a viable successor, but it would need a new body profile and tests.

### Heel Grid

The current local default, `0, 5, ..., 90` degrees, is defensible as the comparison grid for the first generated-kayak model. It covers the kayak design target in `docs/design` and includes the likely max-GZ region. The result should echo the requested grid exactly, accept a strictly increasing caller-supplied grid, and not infer dense-curve precision from a coarse grid.

For summaries, `max_gz_m` and `heel_at_max_gz_deg` may be grid-derived. `range_positive_stability_deg` should be `grid_bounded` by default; interpolation between sign-changing points should be a named mode or a separate field because PIAS-style evidence warns that angle resolution matters where curves bend sharply.

### Trim Policy

External evidence supports both fixed-trim and free-trim modes. The eCFR/free-trim criterion is stronger for regulatory-style equilibrium, but it is a larger numerical problem. The conservative first generated-kayak comparator should hold the upright trim solution fixed and solve only sinkage/displacement at each heel point. It must report the unsolved longitudinal moment residual so users know it is a fixed-trim curve.

A free-trim-per-heel mode should remain a named successor or optional mode, not silently replace the fixed-trim curve. If implemented, it should solve both displacement and longitudinal moment at each heel, record final trim angle, residuals, iteration counts, and warnings per heel point, and expose the higher failure rate as part of the result contract.

### CG Convention

The first model should use hull-fixed CG for hull, paddler, and cargo components: the load case moves with the kayak as it heels, and the paddler is modeled as passive/bolt-upright relative to the boat. This aligns with the project-local RFC 0011 adoption of the Schade explainer and keeps active bracing/body lean out of scope.

The output should record component masses, LCG, KG, and the reference conversion used. If compact load cases expand to centered components or default KG, warnings should say so. World-fixed or actively shifting paddler CG is a different human-response model and should not be mixed into v1.

### Waterline Clipping And Volume Integration

At each heel point, the algorithm should transform the accepted body by heel and fixed/upright trim, then solve a waterplane offset for target displacement. The submerged portion is the part below the world waterplane. The clipping operation must produce a closed capped submerged body before volume and CB are accepted; if clipping/capping fails, the heel point is failed, not heuristic-filled.

The result should distinguish body-level diagnostics from per-heel clipping diagnostics. Passing `generated_hull_plus_deck_closed_body_v1` diagnostics is necessary but not sufficient: each heeled waterline cut can still fail due to topology, tangency, numerical tolerance, deck immersion, or cap ambiguity.

### Residuals And Convergence Warnings

Each heel point needs a status record even if the first `GZCurve` model keeps arrays additive:

- `heel_deg`;
- `status`: `computed`, `non_converged`, `clipping_failed`, `skipped`, or `unsupported`;
- `sinkage_m` / waterplane offset;
- `trim_angle_deg` and `trim_policy`;
- `displaced_volume_m3`, `displaced_mass_kg`, `load_mass_kg`;
- `displacement_error_kg` and relative displacement error;
- `load_cg_world_m`, `buoyancy_cb_world_m`, and derived `gz_m`;
- `righting_moment_nm`;
- `longitudinal_moment_error_kg_m` for fixed trim, or solved moment residual for free trim;
- tolerance names/values, iteration count, and max iterations;
- per-point warnings.

The top-level curve should carry `status = unavailable` if no real generated-kayak values are allowed. Once computed results are allowed, a missing or failed heel point should either make summaries `None` or mark summaries as partial/grid-bounded. The UI and comparison reports should not rank a partial curve as final secondary stability unless the decision explicitly accepts that behavior.

### Deck/Flooding And User-Facing Warnings

The first model should not model cockpit openings, paddler body volume, flooded compartments, water on deck, or progressive downflooding. It should report a sealed generated body assumption and surface warnings when heel waterline/deck geometry enters a zone where the model's sealed-body assumption matters. At minimum:

- `sealed_deck_profile_no_cockpit_opening`;
- `deck_immersion_assumption`;
- `flooding_not_modeled`;
- `downflooding_not_modeled`;
- `active_paddler_response_not_modeled`;
- `not_seaworthiness_or_safety_claim`.

Unavailable states should remain prominent: `generated_closed_body_not_available`, `heeled_integration_model_not_available`, `heel_point_non_converged`, `waterline_clipping_failed`, `fixture_only_body_not_user_facing`, and more specific diagnostic-derived reasons.

## Viable Options

### Option A - Conservative Default: Keep Real GZ Unavailable

Preserve the current RFC 0024/0043 behavior. Add only the design decision and maybe fixture-only math tests. This is lowest risk and exactly matches the roadmap until the model details are accepted. It does not satisfy the desire for real secondary-stability comparison, but it avoids premature numeric claims.

Acceptance: no generated-kayak `gz_m`, righting moments, or summaries; fixture outputs stay `fixture_only`; docs and UI continue to show unavailable.

### Option B - Fixed-Trim Generated-Body V1

Use `generated_hull_plus_deck_closed_body_v1` after diagnostics pass; default grid `0..90` by 5 degrees; hull-fixed CG; fixed upright trim; per-heel sinkage solve; closed waterline clipping/capping; grid-bounded summaries; sealed-deck/flooding warnings. This is the smallest real generated-kayak model that fits existing project state.

Acceptance: every point has displacement residual and clipping status; longitudinal moment residual is reported but not solved; summaries derive only from computed points; user surfaces label the model as fixed-trim, sealed-body, unvalidated hydrostatic secondary-stability output.

### Option C - Free-Trim Per-Heel Model

Use the same body and grid gate, but solve both sinkage and trim independently at each heel point. This better matches recognized intact-stability equilibrium practice, but it increases implementation complexity and non-convergence cases. It also raises the bar for residuals, bracketing, and per-point warnings.

Acceptance: every point reports solved trim angle, mass residual, longitudinal moment residual, iteration count, and convergence status. This should be a named mode, not an invisible default change.

### Option D - Flooding/Downflooding Or Active-Paddler Model

Add cockpit openings, water-on-deck/flooding progression, paddler body volume, or active CG response. External stability tools and regulations treat flooding/downflooding as important, but kayak-gen does not have the geometry or human model for it today.

Acceptance: defer. This requires new geometry/profile fields and a separate validation or assumptions RFC.

## Recommendation

The evidence supports Option A as the default project posture until the panel accepts a model decision. If the panel wants to unlock first real generated-kayak curves, choose Option B as the v1 model.

Option B is narrow enough to implement against existing RFC 0022/0024 gates, but honest enough to expose the big assumptions: fixed trim, hull-fixed passive CG, sealed full hull-plus-deck body, no flooding/downflooding, no active paddler response, no validation, and no safety/seaworthiness claim. Option C should be the named successor when the project is ready to solve trim per heel.

## Risks And Unknowns

- `generated_hull_plus_deck_closed_body_v1` may overstate reserve buoyancy at high heel because it has no cockpit opening or flooding model.
- Fixed trim is a comparison curve, not a full per-heel equilibrium curve; the unsolved longitudinal moment residual may be material for asymmetric load cases.
- A 5-degree grid can miss narrow peaks or sign crossings; summaries need grid-bounded wording unless interpolation is explicitly accepted.
- Waterline clipping can fail even for a closed body if the cut creates ambiguous caps, tangencies, or numerical near-contacts.
- Existing `GZCurve` has no per-heel status field; adding one should be additive before real curves are user-facing.
- No measured kayak stability validation source has been accepted. The first implementation remains a geometry-based hydrostatic model, not validated safety or design-fitness output.

## Implementation Gates Before Any Work

- Record the selected body profile: `generated_hull_plus_deck_closed_body_v1` v1 or a new stability-specific profile.
- Decide fixed-trim v1 versus free-trim v1; if fixed trim is selected, require longitudinal moment residual reporting.
- Freeze default heel grid and summary semantics: grid-bounded versus interpolated.
- Add per-heel status/residual metadata to `GZCurve` before any partial curve can reach CLI, sweep, comparison, desktop, or web surfaces.
- Define exact waterline clipping/capping diagnostics and failure warnings.
- Define deck/flooding warning triggers for the sealed generated body.
- Keep unavailable results and `None` summaries for any gate failure.
- Update docs only after the accepted model and tests land; do not reword output as safety, seaworthiness, final prediction, or design fitness.

## Sub-Agent Help

No spawned sub-agents were used. I used parallel read-only local inspections and external source research.
