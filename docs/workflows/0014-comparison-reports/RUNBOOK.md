# Runbook - 0014 comparison reports

1. Review RFC 0009 sweep records, RFC 0013 comparison reports, the 0011
   findings ledger, and the completed 0013 resistance-acceptance gate.
2. Run three review lanes:
   - RFC/status and acceptance traceability;
   - Pareto/objective domain semantics;
   - implementation, CLI, and test cleanup.
3. Consolidate findings into a ledger.
4. Implement only the conservative report/CLI slice:
   `kayakgen compare`, comparison report models, deterministic tests, and
   default objectives that exclude uncalibrated resistance.
5. Final review should accept only if the CLI/report contract is truthful,
   missing metrics are warnings rather than crashes, and raw resistance is never
   used as a default Pareto objective.
