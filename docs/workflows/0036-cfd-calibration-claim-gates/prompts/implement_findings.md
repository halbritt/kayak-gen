Implement the safe-now findings from
`striatum/0036-cfd-calibration-claim-gates/ledger/FINDINGS.md`.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent evaluator, CFD metadata, CLI/web wording, tests,
and docs tasks, but keep one agent responsible for final integration.

Write
`striatum/0036-cfd-calibration-claim-gates/implementation/PATCH_SUMMARY.md`
with files changed, findings addressed, and verification commands/results.
Do not claim calibration, validation, or final design fitness unless the ledger
and accepted RFC explicitly allow it.

