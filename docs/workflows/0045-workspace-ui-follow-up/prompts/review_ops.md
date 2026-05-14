# Ops/Test Review Prompt

Review RFC 0034 for implementation feasibility, package boundaries, browser
behavior, reproducibility, and test strategy.

Do not edit product code or Striatum state. Write only
`striatum/0045-workspace-ui-follow-up/ops/REVIEW_OPS.md`. Do not add `author:`
or byline metadata.

Use the maximal number of useful sub-agents or parallel helpers for independent
test/export/package-boundary checks if available.

Include:

- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- use `needs_revision` only for RFC/workflow packet blockers that prevent a
  fair implementation review; route implementation-scope findings through
  `accept_with_findings` for the ledger
- ops/test findings ordered by severity
- test matrix and browser acceptance recommendations
- export safety concerns
- implementation sequencing
