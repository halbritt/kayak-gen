# Findings Ledger Prompt — workflow 0056

Read all three review artifacts plus the final-review prompt's
acceptance criteria preview (in `final_review.md`). Produce a
deduplicated findings ledger:

- must-fix findings for the remediation lane (and **only** those
  that block stage 2 + 3 acceptance against
  `STAGE_2_3_DECISIONS.md`);
- non-blocking successor findings (deferred to a future workflow
  or a successor RFC);
- explicitly accepted review concerns that require no action.

Do not create new design scope. Cross-check every finding against
`STAGE_2_3_DECISIONS.md` — a finding that would reopen a settled
decision belongs in the non-blocking successor bucket with a
pointer to the decision row.

A reviewer's `accept_with_findings` verdict on a non-blocking
finding does not become a must-fix item; it becomes a successor
item.

Publish the ledger artifact with proper `striatum.findings_ledger.v1`
front matter.
