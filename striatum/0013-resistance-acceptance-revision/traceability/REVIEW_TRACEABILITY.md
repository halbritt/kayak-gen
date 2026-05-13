# Traceability review - 0013

author: operator [self-declared: operator-traceability-review]
run: run_09d8fab3d88e4a6588b8838ff9f34e61
job: review_traceability
verdict: accept_with_findings

## Findings

### T-001 - RFC 0005 still carries retired acceptance criteria

- Severity: high
- Statement: RFC 0005 still lists low-Froude wave/viscous and 200 ms full-curve
  criteria even though workflow 0012 established that the current model is raw,
  uncalibrated, and comparative-only.
- Required action: Split current accepted behavior from future calibrated or
  optimized behavior. Mark the raw filter as landed and move stronger criteria
  to future RFC 0012/optimization work.

### T-002 - Expected failures now encode obsolete claims

- Severity: high
- Statement: The two RFC 0005 xfails are no longer useful pending tests if the
  project has decided not to claim calibrated low-Froude or 200 ms full-curve
  behavior.
- Required action: Replace them with passing tests that assert warnings,
  uncalibrated metadata, and the realistic raw-filter budget.

### T-003 - RFC index should explain the split

- Severity: medium
- Statement: The index still describes RFC 0005 as partial without stating that
  the raw comparative tier is the accepted landed slice and calibration remains
  RFC 0012 work.
- Required action: Update the index wording.
