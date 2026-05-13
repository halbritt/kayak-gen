Implement the safe-now findings from
`striatum/0028-real-cfd-solver-adapter/ledger/FINDINGS.md`.

Write
`striatum/0028-real-cfd-solver-adapter/implementation/PATCH_SUMMARY.md` with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Implement the first accepted real CFD adapter slice.
- Use the maximal number of useful sub-agents with disjoint write scopes. Prefer parallel agents for independent code, test, docs, and review tasks, but keep one agent responsible for final integration.
- Require RFC 0017 to be accepted or amended before implementation begins.
- Depend on workflow 0027 if the selected solver requires watertight solid
  input.
- Suggested splits: adapter profile/dependency checks; deterministic case
  generation; command/log capture and collection; CLI/status/docs; fixture and
  optional integration tests.
- Preserve RFC 0015 job/run/profile compatibility.
- Missing solver binaries must produce `unavailable`.
- Bad commands or missing output files must produce `failed` with `error_kind`
  and useful error text.
- Do not normalize raw outputs into calibrated physical claims unless a
  separate validation/calibration RFC has landed.
- Run focused CFD/CLI tests, the full suite when feasible, and
  `git diff --check`.
