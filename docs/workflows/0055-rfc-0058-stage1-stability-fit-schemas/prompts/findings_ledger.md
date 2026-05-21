# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated findings ledger:

- must-fix findings for the remediation lane;
- non-blocking successor findings (deferred to stage 2/3 of RFC 0058
  or a future workflow);
- explicitly accepted review concerns that require no action.

Do not create new design scope. Cross-check every finding against
`STAGE_1_DECISIONS.md` — a finding that would reopen a settled
decision belongs in the non-blocking successor bucket with a pointer
to the decision row.

Publish the ledger artifact with proper front matter.
