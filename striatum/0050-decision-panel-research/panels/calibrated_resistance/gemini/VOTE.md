---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---
author: panelist-gemini-pro-3.1-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Calibrated Resistance Decision Vote

**Vote: Option A** (Conservative Default: Preserve Current No-Promotion Gate)

## Decision Sentence

Preserve the current no-promotion gate for calibrated resistance; keep outputs labeled as uncalibrated comparative filters until RFC 0042 source reviews provide an accepted kayak-envelope calibration fixture and a later workflow defines numeric fit thresholds, validity envelopes, and versioning rules.

## Evidence and Citations

- **Local Constraint Context:** `docs/ROADMAP.md` explicitly limits resistance output to `uncalibrated_comparative` and not a calibrated model or final prediction.
- **Current Source State:** The current registry (`kayakgen/eval/calibration.py`) only has candidate sources and lacks any accepted calibration fixtures. Current K1 and Pacific-canoe sources remain narrow or out-of-envelope.
- **External Evidence - Envelope Validity:** FDA CM&S credibility guidance supports the strict requirement to tie any "calibrated" claim to an explicit validity envelope and context of use, not global claims.
- **External Evidence - Uncertainty and Metadata:** ITTC guidelines (procedures 7.5-02-02-01 and 7.5-02-02-02) highlight the need for comprehensive fixture metadata (scale, dimensions, water properties, etc.) and separating bias from precision. Setting fit thresholds before analyzing source uncertainty is premature.

## Why Rejected Alternatives Lose

- **Option B (Calibrated Prediction Gate, No Design Fitness):** While it is the correct future shape, defining final numeric acceptance thresholds now, before a kayak-envelope source is accepted and its uncertainty is analyzed, is too speculative.
- **Option C (Comparative Calibration For Ranking Only):** Using rank metrics to claim a model is "calibrated" does not neatly map to the `final_prediction` claim and risks users misinterpreting comparative ranking as absolute force prediction. It would require complex, specific new UI copy.
- **Option D (Validated Design Fitness):** Conflating calibrated resistance with broader design fitness ignores the need for separate hydrostatics, real high-angle stability, and design constraints, bypassing the requirement for a separate focused RFC.

## Implementation Gates and No-Claims Language

The following implementation gates and no-claims language must remain strictly in force:
- Resistance output is explicitly an `uncalibrated_comparative` analytical screening filter. It is not a calibrated model, final prediction, design-fitness score, or default optimization objective.
- No calibrated wording may appear unless `claim_allows_calibrated_prediction` passes, which requires a non-empty `model_version`, non-empty calibration fixture IDs, fit metrics, a non-null validity envelope, and no uncalibrated warning codes.
- Out of envelope must remain a hard wording gate triggering uncalibrated/out-of-envelope warnings and falling back to raw comparative output.
- `claim_allows_final_design_fitness` remains unsatisfied and distinct.
- RFC 0042-style source-review packets must be completed before any fixture row is ingested or promoted.

## Confidence

High
