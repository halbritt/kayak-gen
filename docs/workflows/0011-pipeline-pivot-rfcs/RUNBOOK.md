# Runbook - workflow 0011

1. Draft RFCs 0009-0013 and update `docs/rfcs/README.md`.
2. Run three parallel reviews:
   - roadmap/traceability,
   - domain/math/mesh,
   - implementation/ops.
3. Consolidate review findings into one ledger.
4. Implement only findings that are safe without domain decisions.
5. Final review gates against the ledger and patch summary.

Implementation guidance:

- Prefer Codex/GPT-5.5 for implementation.
- The implementation agent should use sub-agents where useful for disjoint
  code slices, review, and test diagnosis.
- Do not decide RFC 0004 exact plumb stem/end-cap semantics inside this
  workflow. RFC 0010 may frame the decision, but not silently choose it.
- Keep `OPERATOR_REPORT.md` current at each transition.
