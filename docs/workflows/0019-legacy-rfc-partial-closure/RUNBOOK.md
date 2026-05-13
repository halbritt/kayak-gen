# Runbook - 0019 legacy RFC partial closure

1. Review RFC 0004, RFC 0006, the current model/geometry/classes/UI
   implementation, and the tests that already cover plumb bow and class
   presets.
2. Run three review lanes:
   - RFC/status and acceptance traceability;
   - domain semantics for coordinate conventions, plumb stems, class ranges,
     and advisory warnings;
   - implementation, CLI/web/desktop propagation, and test shape.
3. Consolidate findings into a ledger that separates safe-now closure work from
   follow-up design decisions such as exact end-cap/watertight-solid semantics
   and asymmetric bow/stern rake.
4. Implement only the accepted safe slice. Prefer status/documentation and
   targeted tests when behavior is already present; avoid geometry churn unless
   the ledger identifies a concrete regression.
5. Final review should accept only if RFC 0004/0006 status wording is truthful,
   no open-surface mesh is mislabeled as watertight, and focused/full tests pass.
