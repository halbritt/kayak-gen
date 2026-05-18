# Role: Reviewer — Traceability

Verify every change made under workflow 0054 traces back to either RFC 0057
or `STAGE_4_DECISIONS.md`. Flag scope creep, undocumented refactors, or
decisions made inside the implementation that should have been operator
choices.

Findings must cite file paths and decision rows. Use `accept_with_findings`
unless the workflow's scope is itself invalid; in that case use
`needs_revision`.
