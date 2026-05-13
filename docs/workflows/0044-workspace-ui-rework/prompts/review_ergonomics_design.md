Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent ergonomics, accessibility,
responsive-layout, and desktop/web parity checks. Keep scopes disjoint,
preserve this assigned Striatum role, and state what sub-agent help was used
in the artifact.

Read `docs/workflows/0044-workspace-ui-rework/SOURCES.md`, especially RFC
0033, `CLAUDE_DESIGN_UI_REWORK_PROMPT.md`, `kayakgen/ui/web/app.py`,
`kayakgen/ui/web/controllers.py`, `kayakgen/ui/desktop.py`,
`kayakgen/ui/gui_params.py`, and the web/desktop tests.

Produce
`striatum/0044-workspace-ui-rework/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`.

Use this structure: verdict intent, findings, required actions, and residual
risk. Verdict intent is `accept`, `accept_with_findings`, `needs_revision`, or
`reject`.

Focus on whether RFC 0033 and the workflow scaffold give implementers enough
ergonomics guidance for a dense operational tool: first-viewport scan order,
parameter-rail grouping and slider/input affordances, warning triage without
blocking exploration, review-tab order, status-bar click targets, disabled and
unavailable states, keyboard/focus behavior, responsive collapse behavior,
desktop/web conceptual parity, and whether the theme guidance avoids
one-note palettes while preserving contrast.

Use `needs_revision` only for RFC/workflow blockers that must return to
`review_remediation`; use `accept_with_findings` for implementation findings
that can flow to the ledger. Do not invent new backend capabilities, new
claim states, or a custom JavaScript frontend. Do not include any byline or
any line beginning with `author:`.
