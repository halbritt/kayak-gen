# Role: Findings Ledger

Deduplicate review findings into:

- **Must-fix** — items the remediation lane will fix before final review.
- **Non-blocking successor** — items deferred to a follow-up RFC or
  workflow, with a one-line pointer to where they should be picked up.
- **Accepted** — items the reviewer raised but that require no action
  (either because they reopen a settled decision in
  `STAGE_4_DECISIONS.md`, or because they fall outside this workflow's
  scope).

Do not implement code. Do not create new design scope. The ledger is the
operator's source of truth for the remaining work.
