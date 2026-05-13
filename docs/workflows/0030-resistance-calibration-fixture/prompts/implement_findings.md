Implement the safe ledger result for workflow 0030.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent source, ingestion, fitting/report, tests, and
docs tasks, but keep one agent responsible for final integration. If no dataset
is accepted, do not fabricate fixtures.

Write `striatum/0030-resistance-calibration-fixture/implementation/PATCH_SUMMARY.md`
with findings addressed, files changed, and verification.
