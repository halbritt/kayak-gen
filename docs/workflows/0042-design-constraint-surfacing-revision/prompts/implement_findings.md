Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent implementation and verification.
Keep scopes disjoint, preserve this assigned Striatum role, and state what
sub-agent help was used in the artifact.

Implement the safe-now findings from
`striatum/0042-design-constraint-surfacing-revision/ledger/FINDINGS.md`.

Use maximal useful sub-agents with disjoint write scopes. Prefer parallel
agents for independent model/validity metadata, CLI/evaluation output,
sweep/report propagation, desktop/web text parity, docs, and tests tasks, but
keep one agent responsible for final integration.

Write
`striatum/0042-design-constraint-surfacing-revision/implementation/PATCH_SUMMARY.md`
with files changed, findings addressed, sub-agent help used, and verification
commands/results.

Do not turn advisory warnings into hard failures unless the ledger and RFC 0031
explicitly require it. Do not implement product geometry for rocker, deadrise,
chine radius, flare, or LCB redistribution. Do not update the root
`OPERATOR_REPORT.md`. Do not include any byline or any line beginning with
`author:`.
