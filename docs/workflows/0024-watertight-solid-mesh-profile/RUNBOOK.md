# Runbook - 0024 watertight solid mesh profile

1. Review RFC 0010, RFC 0015, workflow 0015 results, current mesh diagnostics,
   and mesh package behavior.
2. Run three review lanes:
   - traceability for accepted mesh-package criteria, open deferrals, and
     status wording;
   - domain/geometry for hull/deck closure, end caps, normals, waterline
     boundary semantics, and manifold expectations;
   - ops/test for deterministic packages, CLI behavior, synthetic invalid
     meshes, and downstream solver profile hooks.
3. Consolidate findings into a ledger that separates safe-now readiness work
   from future geometry/volume-meshing work.
4. Implement only the accepted slice. A safe outcome may be a named
   watertight-required profile that remains blocked by current open geometry,
   plus diagnostics/tests/docs proving current packages are not mislabeled.
5. Final review should accept only if no open surface is relabeled as
   watertight or `cfd_ready`, tests pass, and RFC/status docs match what
   actually landed.
