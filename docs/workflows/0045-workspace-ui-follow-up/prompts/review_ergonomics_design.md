# Ergonomics Design Review Prompt

Review RFC 0034 for expert-workspace ergonomics and interaction design.

Focus on preset interaction, dynamic validity badge behavior, resistance and
mesh card readability, export affordances, keyboard/screen-reader implications,
responsive scan path, and consistency with the landed RFC 0033 theme and UI
language.

Do not edit product code or Striatum state. Write only
`striatum/0045-workspace-ui-follow-up/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`.
Do not add `author:` or byline metadata.

Use the maximal number of useful sub-agents or parallel helpers for independent
interaction/accessibility checks if available.

Include:

- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- use `needs_revision` only for RFC/workflow packet blockers that prevent a
  fair implementation review; route implementation-scope findings through
  `accept_with_findings` for the ledger
- ergonomics/design findings ordered by severity
- accessibility and responsive considerations
- acceptance refinements
- safe implementation recommendation
