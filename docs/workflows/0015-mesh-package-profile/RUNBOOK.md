# Runbook - 0015 mesh package and solver profile

1. Review RFC 0010, the 0011 findings ledger, current mesh diagnostics, CLI,
   and tests.
2. Run three review lanes:
   - RFC/status and manifest traceability;
   - mesh-domain/profile semantics;
   - implementation, CLI, and test shape.
3. Consolidate findings into a ledger.
4. Implement only the conservative mesh-package/profile slice:
   `kayakgen mesh-package`, a manifest model/writer, first open wetted-surface
   solver profile, and tests that keep watertight `cfd_ready` future.
5. Final review should accept only if default meshes are not falsely promoted
   to watertight readiness and package artifacts are deterministic.
