# Traceability Review Prompt

Review RFC 0034 against RFC 0033, the workflow 0044 final review, and existing
code/tests.

Do not edit product code or Striatum state. Write only
`striatum/0045-workspace-ui-follow-up/traceability/REVIEW_TRACEABILITY.md`.
Do not add `author:` or byline metadata.

Use the maximal number of useful sub-agents or parallel helpers for independent
traceability checks if available.

Include:

- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- use `needs_revision` only for RFC/workflow packet blockers that prevent a
  fair implementation review; route implementation-scope findings through
  `accept_with_findings` for the ledger
- findings ordered by severity
- acceptance criteria coverage
- missing or overbroad scope
- suggested safe implementation slice
