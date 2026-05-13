Implement the safe-now findings from
`striatum/0020-browser-acceptance-demo/ledger/FINDINGS.md`.

Write `striatum/0020-browser-acceptance-demo/implementation/PATCH_SUMMARY.md`
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
- Add or strengthen reproducible headless web tests where browser tooling is
  unavailable.
- Add demo/deployment documentation if missing.
- Keep `kayakgen serve` additive and scriptable; avoid changing core hull/eval
  behavior.
- Do not add heavy browser/Lighthouse dependencies unless already installed and
  usable or the ledger proves a small reproducible dependency slice.
- Do not claim Playwright, Lighthouse, or a hosted demo unless that exact check
  or deployment exists.
- Run focused web/CLI tests, the full suite, and `git diff --check`.
