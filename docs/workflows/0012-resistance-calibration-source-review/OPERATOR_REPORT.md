# Operator report - workflow 0012

Updated: 2026-05-13

## Current state

- User asked to queue the next workflow and, if it succeeds, continue through
  the remaining pipeline backlog.
- Starting from clean `main` at `7222d5b`.
- Primary gate: resistance calibration source review for RFC 0012.
- Follow-on queue is recorded in `QUEUE.md` and should only advance after the
  active workflow's final review accepts or explicitly accepts with bounded
  findings.

## Queue

1. Resistance calibration source review and provenance gate.
2. RFC 0005/0012 resistance closure or revision based on the gate.
3. RFC 0013 comparison report/CLI with calibrated-resistance-aware defaults.
4. RFC 0010 mesh package and first open-wetted-surface solver profile.
5. RFC 0011 sinkage/trim equilibrium stability mode.
6. RFC 0008 web verification and deployment follow-up.

## Findings recorded

- No workflow findings yet.

## Next action

- Validate and start the 0012 Striatum run.
