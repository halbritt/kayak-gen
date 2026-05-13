# Runbook - 0029 web CFD job routes

This workflow implements the accepted web CFD job-route slice after RFC 0018
is accepted or amended. It must expose the existing RFC 0015 local dispatch
contract through the web frontend without claiming real solver availability,
hosted execution, or validated physics.

1. Review RFC 0008, RFC 0015, proposed RFC 0018, and the queue entry for
   workflow 0029.
2. Run three review lanes before implementation:
   - traceability for RFC acceptance criteria, route shape, UI state coverage,
     and explicit deferrals;
   - browser/domain for browser wording, artifact visibility, solver state
     truthfulness, and raw/unvalidated CFD boundaries;
   - ops/test for route errors, local job-store access, artifact serving
     boundaries, browser/headless coverage, and reproducible tests.
3. Consolidate review results into a ledger that separates safe local web-route
   work from hosted workers, real solver adapters, authentication, and
   validated CFD claims.
4. Implement only the ledger-approved slice over existing `CfdJobSpec`,
   `CfdRunRecord`, solver profiles, mesh package readiness gates, and local job
   artifacts.
5. Final review should accept only if unavailable, failed, queued/running, and
   raw-output states are visible and cannot be mistaken for validated CFD
   success.
