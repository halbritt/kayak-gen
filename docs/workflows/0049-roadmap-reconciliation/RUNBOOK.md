# Workflow 0049 Runbook

Purpose: produce a current roadmap for all outstanding RFCs, deferred items,
and backlog work without implementing runtime behavior.

This workflow exists because the RFC index is current, while the older deferred
queue is intentionally historical and no longer captures successor RFCs 0036
through 0043. Treat both as sources, reconcile conflicts explicitly, and make
`docs/ROADMAP.md` the contributor-facing summary.

Use Codex for roadmap authoring and integration. Ask authoring and integration
agents to use the maximal number of useful sub-agents with disjoint write
scopes.

Review lanes:

- Backlog completeness: verify every outstanding RFC, partial RFC, deferred
  item, successor RFC, stale queue item, and final-review follow-up is either
  placed on the roadmap or explicitly marked completed/background/superseded.
- No-claims/domain: verify the roadmap does not imply calibrated resistance,
  real CFD acceptance, watertight `cfd_ready`, final design fitness, or
  high-angle stability before evidence exists.
- Roadmap sequencing/ops: verify dependencies, ready-now work, blocked work,
  workflow batching, docs/changelog/report updates, and validation commands are
  practical.

Do not edit runtime code in this workflow.
