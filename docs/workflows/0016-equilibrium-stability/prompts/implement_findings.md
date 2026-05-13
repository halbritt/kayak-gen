Implement the safe-now findings from
`striatum/0016-equilibrium-stability/ledger/FINDINGS.md`.

Write `striatum/0016-equilibrium-stability/implementation/PATCH_SUMMARY.md`
with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Use sub-agents where useful for bounded, parallel, disjoint work.
- Preserve the existing design-waterline initial stability API.
- Add an equilibrium mode with explicit convergence tolerance reporting.
- Normalize KG references consistently under the equilibrium draft.
- Be explicit and conservative about trim support with the current load-case
  contract.
- Do not implement high-angle GZ curves, CFD/dynamic stability, or new
  dependencies.
- Run focused tests, the full suite, and `git diff --check`.
