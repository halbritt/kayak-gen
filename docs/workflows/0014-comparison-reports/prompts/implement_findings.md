Implement the safe-now findings from
`striatum/0014-comparison-reports/ledger/FINDINGS.md`.

Write `striatum/0014-comparison-reports/implementation/PATCH_SUMMARY.md` with:

- author line: `author: operator [self-declared: operator-implementer]`
- files changed
- findings addressed
- verification commands and results

Implementation constraints:

- Prefer Codex for implementation.
- Use sub-agents maximally where useful for bounded, parallel, disjoint work.
- Keep comparison/report code inside `kayakgen/search/` unless the ledger
  justifies another package boundary.
- Add or update `kayakgen compare <run-dir> --out <file>`.
- Use current sweep run outputs; do not invent a new run format unless the
  ledger identifies an unavoidable gap.
- Default objectives must exclude raw uncalibrated resistance.
- Any raw-resistance comparison must be explicitly labeled exploratory and only
  included when requested.
- Do not implement web UI work.
- Do not add pandas, scipy, YAML, database, or web-test dependencies.
- Run focused tests, the full test suite, and `git diff --check`.
