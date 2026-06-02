# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated findings ledger:

- must-fix findings for the remediation lane;
- non-blocking successor findings (deferred to a later RFC 0065 slice or a
  follow-up workflow), each with an explicit pointer;
- explicitly accepted review concerns that require no action.

Do not create new design scope or implement code. Cross-check every finding
against `SLICE_1_DECISIONS.md` — a finding that would reopen a settled decision
belongs in the non-blocking successor bucket with an explicit pointer to the row
it would override.

Publish the ledger artifact.
