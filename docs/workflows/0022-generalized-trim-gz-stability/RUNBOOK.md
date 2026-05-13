# Runbook - 0022 generalized trim and GZ stability

1. Review RFC 0011's equilibrium-sinkage deferrals and RFC 0014's proposed
   generalized trim/high-angle stability contract.
2. Run three review lanes:
   - traceability for RFC acceptance criteria, status wording, and prior
     stability deferrals;
   - domain for longitudinal coordinates, load moments, trim sign convention,
     fixed-paddler-CG assumptions, and high-angle volume semantics;
   - ops/test for JSON compatibility, CLI output, sweep/evaluation records,
     numerical tolerances, and non-convergence behavior.
3. Consolidate findings into a ledger that separates the safe trim-equilibrium
   slice from any future high-angle `GZCurve` volume decision.
4. Implement only the accepted slice: longitudinal load components,
   compatibility normalization, trim equilibrium result fields, CLI/sweep
   serialization, tests, and status docs as directed by the ledger.
5. Final review should accept only if forward/aft load positions produce the
   expected trim direction, residuals and non-convergence are explicit, and
   unsupported high-angle GZ remains unavailable rather than synthetic.
