Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent verification. Keep scopes
disjoint, preserve this assigned Striatum role, and state what sub-agent help
was used in the artifact.

Read RFC 0031, the findings ledger, the implementation patch summary, and the
changed files.

Produce
`striatum/0042-design-constraint-surfacing-revision/final/FINAL_REVIEW.md`.

Verdict must be `accept` or `needs_revision`. Verify that structured
design-validity metadata is additive, existing warning strings remain
compatible, CLI/web/desktop text derives from shared codes/messages, sweeps and
comparison reports preserve metadata without hard-failing advisory findings,
unsupported reserved fields are visible, and tests cover the accepted slice.

If `needs_revision`, name the exact findings that must return to
`implement_findings`. Do not include any byline or any line beginning with
`author:`.
