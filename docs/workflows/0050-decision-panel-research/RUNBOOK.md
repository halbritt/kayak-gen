# Workflow 0050 Runbook

Purpose: resolve the roadmap's open design decisions before starting the next
implementation burn-down.

This is design-only. Do not implement runtime behavior, tests, solver
execution, calibration, watertight-readiness promotion, hosted operation,
desktop rewrite, or optimization/search behavior in this workflow.

For each decision:

1. A research lane gathers local context and current external evidence.
2. A three-lane panel votes independently: Claude, Codex, and Gemini.
3. The integrator records a decision only when at least two panel lanes converge
   on the same answer.
4. If a decision has no majority, the integrator records it as unresolved and
   keeps dependent implementation work blocked.

Decision questions:

- CFD solver path: first external solver target, mesh profile/readiness gate,
  case-template version, parser scope, install/platform notes, and CI strategy.
- Solver-readiness evidence: evidence needed before generated packages can move
  toward solver handoff or `cfd_ready` promotion.
- Resistance source acceptance: measured-source rights, extraction, units,
  envelope, and review metadata required before validation/calibration fixtures.
- Calibrated resistance promotion: fit metrics, validity envelope,
  model-versioning, and wording threshold for calibrated prediction.
- High-angle stability model: heeled integration design gate, body profile,
  heel grid, trim policy, CG convention, clipping, residuals, deck/flooding
  assumptions, and warnings.
- Browser hosting posture: whether to pursue a public hosted demo now and what
  hosted acceptance means.
- Desktop parity strategy: whether desktop parity is still a rewrite target or
  whether the web workspace becomes primary.
- Sweep/search admissibility: reconcile RFC 0009 and decide which metrics are
  admissible for candidate ranking.

After the decisions are accepted by final review, use the recorded decisions
to scaffold and run implementation workflows for all unblocked deferred work
with maximal useful parallelism.
