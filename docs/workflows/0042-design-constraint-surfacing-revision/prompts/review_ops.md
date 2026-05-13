Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent investigation and cross-checking.
Keep scopes disjoint, preserve this assigned Striatum role, and state what
sub-agent help was used in the artifact.

Read `docs/workflows/0042-design-constraint-surfacing-revision/SOURCES.md`,
especially RFC 0031, workflow 0040, the sweep/compare code, CLI evaluation
surface, desktop/web helpers, and tests.

Produce
`striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md`.

Use this structure: verdict intent, findings, required actions, and residual
risk. Verdict intent is `accept`, `accept_with_findings`, `needs_revision`, or
`reject`.

Focus on additive JSON compatibility, preserving existing string warnings,
CLI/web/desktop parity, sweep/report propagation, tests for shared warning
codes/messages, and making sure advisory findings do not become hard failures.
Use `needs_revision` only for scaffold blockers that must return to
`review_remediation`; use `accept_with_findings` for implementation findings
that can flow to the ledger.

Do not include any byline or any line beginning with `author:`.
