---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-gemini-pro-3.1-006
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

## Vote: Option B - Fixed-Trim Generated-Body V1

### Decision Sentence
Adopt the fixed-trim generated-body model for v1 high-angle stability, using `generated_hull_plus_deck_closed_body_v1` with a `0..90` by 5 degree default grid, hull-fixed CG, and fixed upright trim, requiring explicit longitudinal moment residuals and sealed-deck/flooding warnings.

### Evidence and Citations
- **Bentley Maxsurf Stability manual & 46 CFR 28.570**: External evidence supports distinct fixed-trim versus free-trim modes, demonstrating that a fixed-trim assumption with explicitly reported residuals (or zeroed for free trim) is a standard baseline for comparator curves.
- **Nick Schade / Guillemot Kayaks**: Establishes that kayak stability curves fundamentally rely on CG/CB separation over heel, supporting the hull-fixed passive CG assumption for baseline stability models rather than dynamic or active bracing.
- **PIAS manual**: Justifies the default `0, 5, ..., 90` degree grid, explicitly emphasizing that resolution matters and highlighting the necessity for summaries to clearly report as grid-bounded if not interpolating.
- **Local Context (`docs/ROADMAP.md`, `docs/rfcs/0043-high-angle-gz-successor.md`)**: Reaffirms that generated-body evidence gates (from RFC 0024) and an accepted heeled integration model are prerequisite for high-angle stability availability. Option B aligns with utilizing the existing `generated_hull_plus_deck_closed_body_v1` profile and provides the necessary design gate closures.

### Rejected Alternatives
- **Option A (Conservative Default)**: Rejected because it indefinitely blocks user-facing secondary-stability comparison while the requisite diagnostics and models for a conservative first pass are available and clear.
- **Option C (Free-Trim Per-Heel Model)**: Rejected for v1 due to its significantly higher complexity and convergence risks, which shouldn't block initial real generated-kayak curves. It remains a valid successor (named mode) for future iteration.
- **Option D (Flooding/Downflooding Or Active-Paddler Model)**: Rejected because the current geometry and human model constraints do not support cockpit openings or dynamic responses, necessitating a separate validation RFC.

### Implementation Gates and No-Claims Language
- **Implementation Gates**:
  - `generated_hull_plus_deck_closed_body_v1` must pass closure, volume, and manifold diagnostic checks before heeled integration.
  - Per-heel integration must report sinkage, displacement error, and explicitly unsolved longitudinal moment residuals.
  - Summaries (`max_gz_m`, `range_positive_stability_deg`) must be explicitly labeled as grid-bounded.
  - Failing to clip or converge at any heel point must result in a `non_converged` or `clipping_failed` status for that point.
- **No-Claims Language**:
  - The model must output explicit warnings: `sealed_deck_profile_no_cockpit_opening`, `deck_immersion_assumption`, `flooding_not_modeled`, `downflooding_not_modeled`, and `active_paddler_response_not_modeled`.
  - The results are explicitly `not_seaworthiness_or_safety_claim` and remain unvalidated hydrostatic secondary-stability estimates, not a certified safety rating.

### Confidence
High
