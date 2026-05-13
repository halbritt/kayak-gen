# Runbook - 0016 equilibrium stability

1. Review RFC 0011, the current hydrostatics/stability implementation, load
   case contract, CLI, and tests.
2. Run three review lanes:
   - RFC/status and acceptance traceability;
   - hydrostatic equilibrium/domain semantics;
   - implementation, CLI, and test shape.
3. Consolidate findings into a ledger that separates safe-now equilibrium work
   from future high-angle or CFD-backed stability work.
4. Implement only the conservative equilibrium slice: load-case equilibrium
   evaluation with convergence tolerances, explicit design-waterline diagnostic
   preservation, CLI/test coverage, and RFC status updates.
5. Final review should accept only if equilibrium results are honest about
   sinkage/trim support, high-angle GZ remains deferred, and tests pass.
