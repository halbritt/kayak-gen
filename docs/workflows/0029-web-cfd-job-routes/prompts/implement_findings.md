Implement the safe-now findings from
`striatum/0029-web-cfd-job-routes/ledger/FINDINGS.md`.

Write `striatum/0029-web-cfd-job-routes/implementation/PATCH_SUMMARY.md` with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Implement accepted web CFD job routes and UI states over the existing local
  dispatch contract.
- Use the maximal number of useful sub-agents with disjoint write scopes.
  Prefer parallel agents for independent code, test, docs, and review tasks,
  but keep one agent responsible for final integration.
- Prefer parallel agents for independent API, UI, tests, docs, and review
  tasks, but keep one agent responsible for final integration.
- Reuse existing `CfdJobSpec`, `CfdRunRecord`, solver profile, readiness, and
  local job-store behavior.
- Keep unavailable solver states and failure states visible.
- Do not fake solver success and do not hide unavailable solver states.
- Do not claim raw CFD outputs are calibrated, validated, or final design
  fitness signals.
- Run focused web/CFD tests, optional browser smoke tests when available, the
  full suite when practical, and `git diff --check`.
