Operator parallelism instruction: use the maximal number of useful sub-agents or parallel workers available for independent investigation, implementation, or verification. Keep scopes disjoint, preserve this assigned Striatum role, and state what sub-agent help was used in the artifact.

Implement the safe-now findings from
`striatum/0040-design-constraint-surfacing/ledger/FINDINGS.md`.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent model/validity metadata, CLI/report output,
desktop UI, web UI, docs, and tests tasks, but keep one agent responsible for
final integration.

Write
`striatum/0040-design-constraint-surfacing/implementation/PATCH_SUMMARY.md`
with files changed, findings addressed, and verification commands/results. Do
not turn advisory warnings into hard failures unless the ledger and accepted RFC
explicitly require it.
