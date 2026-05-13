# Runbook - 0028 Real CFD solver adapter

1. Review RFC 0015, proposed RFC 0017, RFC 0010 mesh readiness, RFC 0012
   provenance boundaries, workflow 0025's local dispatch result, and workflow
   0027 if the selected solver requires watertight closed-volume input.
2. Run three review lanes before implementation:
   - traceability for RFC 0015 deferrals, accepted RFC 0017 criteria, status
     wording, and the conditional 0027 dependency;
   - domain/CFD for solver setup, boundary conditions, raw/unvalidated result
     wording, speed/fluid inputs, mesh-readiness assumptions, and artifact
     provenance;
   - ops/test for dependency detection, local execution isolation,
     reproducible job directories, failure capture, and solver-free baseline
     tests.
3. Consolidate findings into a ledger that separates the accepted first real
   adapter slice from future solver, web, hosted, watertight, calibration, and
   validation work.
4. Implement only the ledger-approved slice: adapter profile metadata,
   dependency checks, deterministic case generation, command/log capture, raw
   output collection, CLI/status updates, fixture tests, and documentation.
5. Final review should accept only if installed dependencies can execute the
   real adapter path, missing dependencies fail truthfully, and outputs remain
   raw/unvalidated unless a separate calibration RFC has landed.
