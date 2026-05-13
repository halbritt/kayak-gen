author: operator [self-declared: operator-traceability-review]

# Traceability review - equilibrium stability

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0011 step 5 is not represented in code

RFC 0011 records a post-run decision that stability should support both
design-waterline diagnostics and equilibrium-solved mode, but
`kayakgen.eval.stability` still only exposes `evaluate_initial_stability()` with
warnings `design_waterline_initial_stability_only` and
`equilibrium_sinkage_trim_not_solved`.

Required action: add an equilibrium entry point or mode and keep the existing
design-waterline evaluator/API available.

### T-002 - StabilityResult cannot encode equilibrium provenance

`StabilityResult.method` is limited to `design_waterline_initial`, and the model
does not expose equilibrium draft, trim, convergence tolerance, iteration count,
or convergence/failure status.

Required action: extend the result contract so callers can distinguish
design-waterline diagnostics from equilibrium outputs without parsing warning
strings.

### T-003 - CLI has no equilibrium mode

`kayakgen stability` always writes design-waterline initial stability. RFC 0011
needs a user-facing way to request the equilibrium pass while preserving the
current diagnostic default.

Required action: add explicit CLI mode selection or an `--equilibrium` flag,
with output JSON proving the chosen method.

### T-004 - RFC status and index will become stale after the patch

RFC 0011 is still `proposed` even though steps 1-4 have landed and this workflow
is intended to land the equilibrium slice.

Required action: update RFC 0011 and the RFC index to describe the exact landed
slice, without claiming high-angle `GZ` or full trim if it remains deferred.

### T-005 - High-angle GZ must remain explicitly not implemented

The acceptance criteria require GZ calls to fail clearly until heeled-volume
semantics are decided. Nothing in this workflow should convert the reserved
`GZCurve` surface into a fake curve.

Required action: retain the current `GZNotImplementedError` behavior and keep
tests for it.
