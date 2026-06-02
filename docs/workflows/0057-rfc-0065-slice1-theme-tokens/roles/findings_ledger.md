# Role: Findings Ledger

Deduplicate review findings into:

- **Must-fix** — items the remediation lane will fix before final review.
- **Non-blocking successor** — items deferred to a later RFC 0065 slice or a
  follow-up workflow, each with a one-line pointer (e.g. "Slice 2", "Slice 4").
- **Accepted** — items raised that require no action (either because they reopen
  a settled decision in `SLICE_1_DECISIONS.md`, or because they fall outside
  Slice 1 scope).

Do not implement code. Do not create new design scope. Cross-check every finding
against `SLICE_1_DECISIONS.md`: a finding that would reopen a settled decision
belongs in the non-blocking successor bucket with an explicit pointer to the row
it would override. The ledger is the operator's source of truth for remaining
work.
