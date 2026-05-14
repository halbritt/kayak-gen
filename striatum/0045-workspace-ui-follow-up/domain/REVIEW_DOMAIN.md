---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Domain Review

## Verdict Intent

`accept_with_findings`

## Domain Findings (ordered by severity)

### P0 - Wiring of Forbidden-Claim Language and Chips

The core domain safety relies on explicitly presenting no-claim language and status chips in the UI. While RFC 0034 focuses on wiring existing read models, it is critical to ensure that all instances where these claims could be implicitly made are explicitly negated or clarified. This includes:

- **Resistance Card:** Verify the persistent caption "Raw comparative filter; not final prediction." and the chip `uncalibrated_comparative` are correctly rendered alongside every `Rt` value, as specified in RFC 0033 §4 and confirmed in the Workflow 0044 Final Review F3.
- **Stability Sub-tab:** Confirm the exact block heading "High-angle GZ unavailable" is present and that no numeric `GZ_max` or `heel_angle_max_deg` values are rendered, per RFC 0033 §4.
- **Mesh Tab:** Ensure that the bare word `cfd_ready` only appears in the allowed explanatory negation "not watertight cfd_ready" when current generated packages do not satisfy watertight-solid readiness, as per RFC 0033 §4.
- **CFD Tab:** Verify both persistent banners ("Local filesystem CFD jobs on this server only; no hosted worker is running." and "Raw solver artifact only; not calibrated or validated.") are correctly displayed. Also, confirm that forbidden terms like `hosted`, `cloud`, `worker queue`, `OpenFOAM`, or `SU2` do not appear outside the no-hosted-worker notice, per RFC 0033 §4.

### P1 - Export Menu Clarity for Mesh Package

RFC 0034 proposes extending the export menu to include "Mesh package…". It is crucial that this action does *not* imply web-side mesh authoring or hosted storage. The UX should clearly communicate that this wraps existing server-local `kayakgen mesh-package` semantics, or if not yet implemented, should be explicitly disabled or marked as unavailable with an honest message. This aligns with the non-goal of "No new REST route shape unless an existing local route already exposes the data safely."

## No-Claims Copy Risks

The RFC 0033 §8 "Forbidden-claim guard" and the Workflow 0044 Final Review F6 list specific strings that must not appear in the UI without explicit negation. RFC 0034 explicitly expands regression tests to cover this. The risk lies in any new UI wiring accidentally introducing these terms or implicitly suggesting capabilities that do not exist (e.g., hosted workers, calibrated drag) through context or proximity. The current approach of using explicit negation and dedicated chips mitigates this risk significantly, but vigilance is required during implementation review to prevent subtle reintroductions.

## Safe-Now vs. Deferred Work

RFC 0034 is explicitly scoped to wire in dynamic UI elements from existing read models, adhering to the "no-new-backend-capability" boundary established by RFC 0033. All non-goals and explicit deferrals listed in RFC 0033 and RFC 0034 (e.g., hosted CFD workers, calibrated drag, final prediction, high-angle GZ visualization, watertight `cfd_ready` promotion, multi-variant 2D overlay, Pareto plot widget) remain deferred. The focus is on truthful presentation of *current* capabilities.

## Concrete Source References

- `docs/rfcs/0033-workspace-ui-rework.md` (specifically sections 4, 5, 8, and Non-Goals)
- `docs/rfcs/0034-workspace-ui-follow-up.md` (specifically Goals, Non-Goals, and Acceptance Criteria)
- `striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` (specifically F1-F6 and Residual Risk)
- `docs/design/kayak_hull_design_constraints.md` (for the underlying domain context of stability, resistance, etc.)

## Notes on Commands/Checks Run

This review was conducted as the Gemini lane fallback due to a quota limit for Gemini Pro 3.1. The analysis relied on careful reading and synthesis of the provided documentation, specifically focusing on explicit statements of scope, goals, non-goals, and acceptance criteria related to domain claims and truthful language. No shell commands were run as part of this domain review to verify code content, as that is typically part of an implementation review or ops review. The focus was purely on the RFC and workflow packet's textual content and its implications for domain safety.
