Implement the safe-now findings from
`striatum/0019-legacy-rfc-partial-closure/ledger/FINDINGS.md`.

Write `striatum/0019-legacy-rfc-partial-closure/implementation/PATCH_SUMMARY.md`
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
- Preserve current public geometry defaults unless the ledger identifies a
  concrete regression.
- Keep open-surface mesh readiness and watertight/solid readiness distinct.
- Be explicit and conservative about exact plumb-stem/end-cap support.
- Do not add new dependencies.
- Run focused tests, the full suite, and `git diff --check`.
