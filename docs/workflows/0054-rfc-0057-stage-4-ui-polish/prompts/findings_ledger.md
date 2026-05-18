# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated findings ledger:

- must-fix findings for the remediation lane;
- non-blocking successor findings (deferred to a follow-up RFC or workflow);
- explicitly accepted review concerns that require no action.

Do not create new design scope or implement code. Cross-check every finding
against `STAGE_4_DECISIONS.md` — a finding that would reopen a settled
decision belongs in the non-blocking successor bucket with an explicit
pointer to the decision row it would override.

Publish the ledger artifact.
