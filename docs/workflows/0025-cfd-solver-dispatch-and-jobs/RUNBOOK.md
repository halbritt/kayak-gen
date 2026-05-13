# Runbook - 0025 CFD solver dispatch and jobs

1. Review RFC 0015, RFC 0008 job-stub expectations, RFC 0010 mesh readiness,
   and workflow 0024's `watertight_solid_resistance_v1` profile boundary.
2. Run three review lanes:
   - traceability for RFC acceptance criteria, status wording, and prior
     readiness/profile findings;
   - domain/CFD for raw/unvalidated result semantics, solver profile readiness,
     speed/fluid inputs, and artifact provenance;
   - ops/test for local filesystem queue behavior, failure capture, CLI status,
     deterministic records, and no external solver dependency.
3. Consolidate findings into a ledger separating local dispatch contract work
   from future real solver integration.
4. Implement only the accepted slice: job/run models, local filesystem
   artifacts, CLI prepare/status/run behavior, unavailable/mock adapter states,
   tests, and status docs as directed by the ledger.
5. Final review should accept only if unavailable solver profiles cannot
   produce fake success and all results remain raw/unvalidated.
