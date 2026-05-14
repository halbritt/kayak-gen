# Findings Ledger Prompt

Consolidate the RFC 0034 first-pass reviews into one conservative findings
ledger.

Do not implement code. Do not mutate Striatum state. Write only
`striatum/0045-workspace-ui-follow-up/ledger/FINDINGS.md` and, if needed,
the workflow-local operator report. Do not add `author:` or byline metadata.

Use the maximal number of useful sub-agents or parallel helpers for independent
finding extraction if available.

The ledger must include:

- gate verdict: `accept`, `accept_with_findings`, or `needs_revision`
- deduplicated findings with severity and source review references
- safe-now implementation scope
- explicit deferrals
- validation matrix
- risks that require successor RFCs
