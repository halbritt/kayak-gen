Implement the safe-now findings from
`striatum/0022-generalized-trim-gz-stability/ledger/FINDINGS.md`.

Write `striatum/0022-generalized-trim-gz-stability/implementation/PATCH_SUMMARY.md`
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
- Implement only the accepted stability slice from the findings ledger.
- Suggested splits: load-case model and serialization; trim solver; CLI/sweep
  integration; tests/docs/status.
- Preserve existing default load-case behavior and current
  equilibrium-sinkage callers unless a finding proves a migration is necessary.
- Keep `+x` stern / `-x` bow and trim sign conventions visible in code/docs.
- Add deterministic tests for forward LCG bow-down trim, aft LCG stern-down
  trim, residuals, compatibility normalization, and non-convergence.
- Do not emit high-angle `GZ` values unless the closed-volume decision is
  accepted and implemented with tests.
- Run focused stability/CLI/sweep tests, the full suite, and `git diff --check`.
