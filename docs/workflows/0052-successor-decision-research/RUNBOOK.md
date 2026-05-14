# Workflow 0052 Runbook

Purpose: resolve the remaining post-0051 design choices before the next
implementation burn-down.

This is design-only. Do not implement runtime behavior, tests, solver
execution, calibration, watertight-readiness promotion, hosted operation,
desktop rewrite, or optimization/search behavior in this workflow.

For each decision:

1. A dedicated research lane gathers local context and current external
   evidence, producing one cited research artifact for that decision before
   any panel lane votes.
2. A three-lane panel votes independently: Claude, Codex, and Gemini.
3. The integrator records a decision only when at least two panel lanes converge
   on the same answer.
4. If a decision has no majority, the integrator records it as unresolved and
   keeps dependent implementation work blocked.

Decision questions:

- Volume-mesh production path: what, if anything, should follow the 0051
  readiness report toward production volume-mesh evidence.
- OpenFOAM success gate: what exact evidence and optional installed-solver
  smoke scope are required before the `openfoam-v2512-interfoam-local` adapter
  can ever return `succeeded`.
- Resistance source candidate: which source, if any, should receive the first
  full source-review packet for validation or calibration fixture promotion.
- High-angle product surface: when and how fixed-trim generated-body v1 `GZ`
  output may be surfaced on CLI, sweep, comparison, desktop, or web surfaces.
- Public demo operations: whether a narrow public browser demo can proceed now
  without additional human/operator owner and budget evidence.
- Sweep next delta: which remaining RFC 0009/search delta should be scheduled
  next: `pending` state, sweep-side STL artifacts, optimizer/search, or more
  metadata/claim hardening.

After the decisions are accepted by final review, use the recorded decisions
to scaffold and run implementation workflows for all unblocked deferred work
with maximal useful parallelism.
