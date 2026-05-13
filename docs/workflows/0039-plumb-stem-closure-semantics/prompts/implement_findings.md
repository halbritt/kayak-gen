Implement the safe-now findings from
`striatum/0039-plumb-stem-closure-semantics/ledger/FINDINGS.md`.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent model/schema, geometry/cap construction,
diagnostics/readiness, CLI/docs, and tests tasks, but keep one agent responsible
for final integration.

Write
`striatum/0039-plumb-stem-closure-semantics/implementation/PATCH_SUMMARY.md`
with files changed, findings addressed, and verification commands/results. Do
not promote open inspection surfaces to closed-volume or watertight-solid
readiness unless diagnostics prove that state.
