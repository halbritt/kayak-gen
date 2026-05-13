# Runbook - 0027 closed-volume geometry contract

1. Confirm RFC 0016 is accepted or amended before implementation starts. Treat
   it as proposed planning input during the three review lanes.
2. Run three review lanes before coding:
   - traceability for RFC 0004 exact plumb/end-cap deferrals, RFC 0006 design
     constraint boundaries, RFC 0010 mesh readiness/profile semantics, RFC
     0015 dispatch gating, and RFC 0016 acceptance criteria;
   - domain/geometry for closure policy, deck/hull body semantics, normal
     orientation, manifold checks, signed volume, waterline handling, and
     plumb-stem behavior;
   - ops/test for deterministic artifacts, synthetic valid/open/nonmanifold
     fixtures, CLI behavior, package/profile hooks, and regression coverage.
3. Consolidate findings into a ledger that separates the safe closed-volume
   contract from high-angle GZ, real solver adapters, volume meshing, and
   calibrated/validated physics claims.
4. Implement only the accepted slice: closed-volume data models, closure
   policy metadata, diagnostics, opt-in builder/CLI surfaces, package/profile
   integration, focused tests, and status docs as directed by the ledger.
5. Final review should accept only if current open packages remain honestly
   classified and any new closed-volume profile has tests proving closure and
   manifold behavior.
