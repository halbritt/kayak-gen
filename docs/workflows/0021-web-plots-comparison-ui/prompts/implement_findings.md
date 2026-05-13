Implement the safe-now findings from
`striatum/0021-web-plots-comparison-ui/ledger/FINDINGS.md`.

Write `striatum/0021-web-plots-comparison-ui/implementation/PATCH_SUMMARY.md`
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
- Implement the smallest coherent RFC 0008/0013 analysis slice accepted by the
  ledger.
- Suggested splits: web state/controllers; plot/view components; comparison
  fixtures and tests; docs/RFC status.
- Keep plotted units, Pareto axes, warnings, and exploratory resistance labels
  domain-correct.
- Add or strengthen reproducible headless and browser tests for the new views.
- Keep `kayakgen serve` additive and scriptable; avoid changing core hull/eval
  behavior.
- Do not add decorative UI, marketing pages, optimizer behavior, hosted
  deployment claims, or solver dispatch.
- Run focused web/CLI tests, the full suite, and `git diff --check`.
