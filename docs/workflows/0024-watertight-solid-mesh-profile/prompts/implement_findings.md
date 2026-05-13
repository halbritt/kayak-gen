Implement the safe-now findings from
`striatum/0024-watertight-solid-mesh-profile/ledger/FINDINGS.md`.

Write `striatum/0024-watertight-solid-mesh-profile/implementation/PATCH_SUMMARY.md`
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
- Implement a named watertight solid mesh readiness profile only where the
  geometry contract is explicit.
- Suggested splits: geometry/profile design; diagnostics/package writer; CLI
  and manifest tests; docs/RFC status.
- Do not relabel open surfaces as watertight.
- Preserve current open wetted-surface package behavior and tests.
- Run focused mesh diagnostics/package/CLI tests, the full suite, and
  `git diff --check`.
