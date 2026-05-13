Read `docs/workflows/0027-closed-volume-geometry-contract/SOURCES.md`,
especially RFC 0004, RFC 0006, RFC 0010, RFC 0015, proposed RFC 0016, and the
queue item for workflow 0027.

Produce `striatum/0027-closed-volume-geometry-contract/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- exact plumb-stem and end-cap deferrals from RFC 0004;
- design-constraint boundaries from RFC 0006 that affect valid generated
  bodies;
- RFC 0010 readiness levels and the `watertight_solid_resistance_v1` profile;
- RFC 0015 dispatch gating and raw/unvalidated status wording;
- which RFC 0016 criteria can land now and which must remain deferred until a
  later high-angle GZ, real CFD, or validation workflow.
