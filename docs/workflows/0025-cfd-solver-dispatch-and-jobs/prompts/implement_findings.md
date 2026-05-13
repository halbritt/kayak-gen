Implement the safe-now findings from
`striatum/0025-cfd-solver-dispatch-and-jobs/ledger/FINDINGS.md`.

Write `striatum/0025-cfd-solver-dispatch-and-jobs/implementation/PATCH_SUMMARY.md`
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
- Implement the local dispatch contract and unavailable/mock adapter first.
- Suggested splits: job/run models; CLI commands; adapter/failure handling;
  docs/tests.
- Do not integrate a real solver until readiness and installation requirements
  are explicit.
- Do not emit fake solver success or calibrated resistance claims.
- Run focused CFD/CLI tests, the full suite, and `git diff --check`.
