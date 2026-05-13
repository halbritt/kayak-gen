Implement the safe-now findings from
`striatum/0017-web-verification/ledger/FINDINGS.md`.

Write `striatum/0017-web-verification/implementation/PATCH_SUMMARY.md`
with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Use sub-agents where useful for bounded, parallel, disjoint work.
- Add or strengthen reproducible headless web tests where browser tooling is
  unavailable.
- Add demo/deployment documentation if missing.
- Keep `kayakgen serve` additive and scriptable; avoid changing core hull/eval
  behavior.
- Do not add heavy browser/Lighthouse dependencies unless already installed and
  usable.
- Run focused web/CLI tests, the full suite, and `git diff --check`.
