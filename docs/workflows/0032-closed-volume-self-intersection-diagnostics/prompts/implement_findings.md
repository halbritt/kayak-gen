Implement the safe ledger result for workflow 0032.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent diagnostic model, geometry algorithm, tests,
docs, and CLI/serialization tasks, but keep one agent responsible for final
integration. Do not construct generated hull-plus-deck closed bodies here, and
do not promote any body to `cfd_ready`.

Write
`striatum/0032-closed-volume-self-intersection-diagnostics/implementation/PATCH_SUMMARY.md`
with findings addressed, files changed, and verification.

