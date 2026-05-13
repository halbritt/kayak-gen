Implement the safe-now findings from
`striatum/0027-closed-volume-geometry-contract/ledger/FINDINGS.md`.

Write `striatum/0027-closed-volume-geometry-contract/implementation/PATCH_SUMMARY.md`
with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Use the maximal number of useful sub-agents with disjoint write scopes.
  Prefer parallel agents for independent code, test, docs, and review tasks,
  but keep one agent responsible for final integration.
- Implement closed-volume geometry only where the accepted RFC defines the
  contract.
- Suggested splits: geometry/profile models; diagnostics; CLI/package hooks;
  tests; docs/status updates.
- Do not relabel open surfaces as watertight.
- Do not implement high-angle GZ, a real CFD adapter, volume meshing, or
  calibrated/validated resistance or CFD claims.
- Run focused geometry/mesh/CLI tests, the full suite, and `git diff --check`.
