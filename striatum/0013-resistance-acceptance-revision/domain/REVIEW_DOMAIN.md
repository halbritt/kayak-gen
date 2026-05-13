# Domain review - 0013

author: operator [self-declared: operator-domain-review]
run: run_09d8fab3d88e4a6588b8838ff9f34e61
job: review_domain
verdict: accept_with_findings

## Findings

### D-001 - Low-Froude wave-ratio claim is not defensible for raw output

- Severity: high
- Statement: The current Michell implementation is verified qualitatively and
  against Wigley, but it is not calibrated for absolute component ratios on the
  generated kayak hull at very low Froude numbers.
- Required action: Remove the low-Froude component-ratio acceptance criterion
  from the landed raw-filter tier. Keep warnings that absolute component
  interpretation is not final-prediction behavior.

### D-002 - Runtime budget needs tier semantics

- Severity: high
- Statement: A 200 ms full-curve budget may be a future UI/surrogate target, but
  the current raw Michell curve is an offline/snapshot evaluator.
- Required action: Use the existing realistic raw-filter budget in tests and
  reserve any 200 ms requirement for a future optimized/surrogate evaluator.

### D-003 - Current defensible domain claim is comparative filtering

- Severity: medium
- Statement: The implemented resistance model can support qualitative sweep
  filtering when metadata warnings are honored.
- Required action: Acceptance should focus on finite nonnegative output,
  monotonic viscous behavior, paddler-envelope sanity, Wigley verification,
  metadata warnings, and source/provenance transparency.
