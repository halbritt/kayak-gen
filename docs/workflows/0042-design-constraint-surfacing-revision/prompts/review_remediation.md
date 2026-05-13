Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent scaffold validation, prompt
review, schema review, and blocker remediation. Keep scopes disjoint, preserve
this assigned Striatum role, and state what sub-agent help was used in the
artifact.

Read `docs/workflows/0042-design-constraint-surfacing-revision/SOURCES.md`,
RFC 0031, and the current workflow scaffold.

Produce
`striatum/0042-design-constraint-surfacing-revision/review_remediation/REMEDIATION.md`.

On the first attempt, prepare the review packet: confirm the RFC/workflow scope,
named deferrals, expected review lanes, and no-product-code boundary are clear.
On a revision attempt caused by a first-pass `needs_revision` verdict, read the
blocking review notes and repair only RFC/workflow scaffold issues needed before
that review can run again.

Allowed remediation is limited to RFC 0031, the RFC index, this workflow
scaffold, and changelog wording. Do not implement product code. Do not update
the root `OPERATOR_REPORT.md`. Do not include any byline or any line beginning
with `author:`.
