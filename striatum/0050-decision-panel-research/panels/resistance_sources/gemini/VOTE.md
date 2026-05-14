---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---
author: panelist-gemini-pro-3.1-007
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote: Resistance Source Acceptance Decision

Vote: Option A - Conservative Default: Source-Review Packet First, No Fixture Promotion

Decision Sentence:
Adopt a mandatory source-review packet requirement for resistance sources and implement mapping tests before any fixture promotion, keeping all current sources out of calibration fixtures until kayak-envelope measured data passes full review.

Evidence and Citations:
- **RFC 0042 & Roadmap:** The current roadmap (Batch F) and RFC 0042 explicitly narrow resistance calibration work to source review and fixture promotion (`docs/ROADMAP.md:38-40`, `docs/rfcs/0042-resistance-calibration-fixture-successor.md:16-21`, `:54-66`). They forbid premature fitting or declaring calibrated models without an accepted fit workflow.
- **External Dataset Constraints:**
  - *Edinburgh DataShare:* The dataset has open rights (CC BY 4.0), but the test setup (Pacific canoe multihull) falls outside the project's kayak calibration envelope (`docs/design/kayak_hull_design_constraints.md:72-86`).
  - *Gomes et al. / Tzabiras et al.:* These sources measure K1 sprint kayaks (out of envelope) and lack the open data redistribution rights required to publish validation/calibration fixtures.
  - *Sea Kayaker / Kanu.de:* Uses mathematically derived values (Taylor Standard Series) rather than primary experimental measurement. Using model-derived tables would mean tuning our analytical model to another model, not reality.
- **Uncertainty Guidelines:** As per NIST/BIPM JCGM 100:2008 best practices, a formal review packet is essential for identifying source uncertainty and determining whether a lack of numeric uncertainty blocks calibration.

Why rejected alternatives lose:
- *Option B (Edinburgh Validation Fixture After Extraction Schema)* loses because although the dataset is openly licensed, it is outside the required hull envelope. Taking on unit normalization and out-of-envelope validation complexity is safer *after* the structural review packet (Option A) is fully implemented.
- *Option C (K1 Validation Fixture By Permission)* loses due to existing rights constraints. Seeking permission before the review packet infrastructure is in place is premature.
- *Option D (Wait For Kayak-Envelope Calibration Source)* loses because it halts the development of essential ingest and parser/report infrastructure that we can safely exercise using validation-only sources.

Implementation gates and no-claims language:
- **No-Claims Language:** Resistance outputs remain `uncalibrated_comparative`. The model acts strictly as a comparative filter, not a calibrated prediction, design-fitness score, or default optimization objective (`docs/ROADMAP.md`).
- **Implementation Gates:**
  1. Create a source-review packet template encompassing rights, extraction metadata, measured quantity, units, hull/speed envelope, and uncertainty notes.
  2. Implement source-use mapping tests guaranteeing that the five runtime `SourceUse` values (`citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, `calibration_fixture`) remain unmodified and that `rejected` acts strictly as a review outcome.
  3. Validate that validation fixtures include rights/extraction status, and calibration fixtures additionally include the matching hull envelope, uncertainty notes, validity ranges, and accepted review status.
  4. Defer all fitting, uncalibrated-warning removals, and calibrated wording to a future accepted-fit workflow; no source becomes a `calibration_fixture` in this workflow.

Confidence: High
