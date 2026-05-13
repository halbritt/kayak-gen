author: operator [self-declared: operator-roadmap-review]

# Roadmap review - workflow 0026

Verdict intent: accept_with_findings

## Findings

### R-001 - Post-0025 roadmap should begin with docs reconciliation

Before new runtime work, stale docs and user onboarding need cleanup so users
and future agents do not treat deferred features as landed.

Required action: make workflow 0026 a docs/user-guide/roadmap workflow and mark
it as the active/current item.

### R-002 - Closed-volume geometry is the next load-bearing technical RFC

High-angle GZ, watertight solid readiness, and many solver targets all depend
on a defined closed-volume hull/deck body. This should precede real solver
integration and high-angle stability claims.

Required action: draft RFC 0016 for closed-volume geometry and watertight solid
generation, with workflow 0027 as the first implementation slice.

### R-003 - High-angle GZ should be a separate RFC after volume semantics

RFC 0014 is partial. The next useful stability work should depend on a closed
body rather than smuggling high-angle integration into unrelated mesh work.

Required action: draft a proposed RFC for high-angle GZ/secondary stability or
explicitly tie it as a dependent follow-up after RFC 0016.

### R-004 - Real CFD adapter should follow readiness, not precede it

Workflow 0025 landed only dispatch records. A real OpenFOAM/SU2 adapter needs a
specific mesh readiness target, install/runtime expectations, and raw output
normalization rules.

Required action: draft RFC 0017 for first real CFD adapter and make it depend
on RFC 0016 or an accepted open-surface solver decision.

### R-005 - Web job routes should use the dispatch contract after adapter scope

Web job routes are useful but should not pretend to execute real CFD until the
backend state semantics are agreed. They can expose local unavailable/queued
states earlier if labeled clearly.

Required action: draft RFC 0018 for web CFD job routes/status UI, dependent on
RFC 0015 local dispatch and coordinated with RFC 0017 if real execution is in
scope.

### R-006 - Calibration remains data-gated

The Edinburgh Pacific-canoe source is validation-only. A kayak calibration
fixture still needs source discovery, license review, and ingest design.

Required action: draft RFC 0019 for resistance calibration fixtures and keep
implementation gated on an accepted dataset.
