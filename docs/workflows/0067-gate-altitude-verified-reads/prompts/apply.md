# Apply Prompt - workflow 0067

Read DRAFT.md and REVIEW.md. Apply must-fix findings only, inside the original
write scope. Do not reopen deferred G7/G11 work.

Write `docs/workflows/0067-gate-altitude-verified-reads/OPERATOR_REPORT.md`
with landed items, design decisions, verified-read coverage, remaining
path-only surfaces if any, tests/gates, and index DB verification.

Re-run `scripts/full-gate.sh` with heartbeats. Publish
`striatum/0067-gate-altitude-verified-reads/SUMMARY.md` and leave the branch
for operator merge.
