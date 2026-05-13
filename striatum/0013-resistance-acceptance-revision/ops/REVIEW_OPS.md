# Ops review - 0013

author: operator [self-declared: operator-ops-review]
run: run_09d8fab3d88e4a6588b8838ff9f34e61
job: review_ops
verdict: accept_with_findings

## Findings

### O-001 - Remove xfails by changing claims, not hiding failures

- Severity: high
- Statement: The suite should not keep expected failures for behavior the RFC no
  longer claims as landed.
- Required action: Delete or replace the two xfailed tests with passing
  acceptance tests for the raw-filter tier.

### O-002 - Preserve guardrails that catch accidental overclaiming

- Severity: medium
- Statement: Removing xfails must not make it easier to use raw resistance as
  calibrated output.
- Required action: Add tests that assert `calibration_status =
  "uncalibrated"`, no source validity ranges, comparative-only use, and no
  calibration fixtures in the source registry.

### O-003 - Keep runtime tests realistic and deterministic

- Severity: medium
- Statement: Timing tests should be broad enough to avoid noise but still catch
  pathological regressions.
- Required action: Retain the existing 5 s budget for the raw curve and document
  the 200 ms target as future optimized UI behavior.
