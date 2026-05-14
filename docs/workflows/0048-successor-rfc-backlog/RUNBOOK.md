# Workflow 0048 Runbook

Purpose: draft successor RFCs for the remaining UI cleanup findings from
workflow 0047 and the named deferred backlog items around closed-volume/solver
readiness, real CFD adapters, resistance calibration fixtures, and high-angle
`GZ`.

Do not implement runtime behavior in this workflow. This is a docs/RFC
workflow only.

Use Codex for RFC drafting and integration. Ask drafting and integration agents
to use the maximal number of useful sub-agents with disjoint write scopes.

Review lanes:

- Traceability: map each proposed RFC to the final-review finding or backlog
  source that motivates it.
- No-claims/domain: verify no RFC implies calibrated resistance, accepted CFD,
  final prediction, watertight readiness, or real high-angle stability before
  evidence exists.
- Ergonomics/design: verify the UI successor RFCs are user-facing, bounded,
  and not just internal cleanup.
- Ops/test: verify each RFC has testable acceptance criteria and a practical
  implementation path.
