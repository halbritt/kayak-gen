# Implementation review - 0012

author: operator [self-declared: operator-implementation-review]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: review_implementation
verdict: accept_with_findings

## Summary

The existing raw resistance metadata already implements much of the safe
fallback. The smallest useful patch is to make calibration/provenance fields
explicit, centralize raw warnings, rename Wigley language to verification, and
add citation-only source records.

## Findings

### I-001 - Add calibration/provenance fields without changing raw behavior

- Severity: high
- Files: `kayakgen/eval/contract.py`, `kayakgen/eval/resistance.py`,
  `tests/test_resistance.py`
- Required action: Add optional metadata fields such as calibration name,
  version, validity ranges, source citation, source license, and extraction
  method. Defaults must preserve current raw behavior.

### I-002 - Do not add numeric calibration without a source gate

- Severity: blocker
- Required action: Keep `resistance_curve()` raw by default. If a future source
  is accepted, add calibration as an explicit wrapper, not an implicit change to
  current evaluator output.

### I-003 - Add a source registry/read model

- Severity: medium
- Required action: Add a small structured registry for citation-only and
  validation candidate sources. It should be clear that no source is accepted
  for calibration yet.

### I-004 - Preserve RFC 0005 xfails

- Severity: medium
- Required action: Keep the two RFC 0005 expected failures until either a
  genuine calibrated implementation satisfies them or RFC 0005 is revised.

## Gate recommendation

Proceed with a safe fallback implementation: provenance/source registry plus
metadata tightening. Do not proceed to resistance closure as a calibration
success; proceed instead to a no-calibration RFC update and explicit next
workflow decision.
