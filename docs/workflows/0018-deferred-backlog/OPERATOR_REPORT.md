# Operator report - workflow 0018

Updated: 2026-05-13

## Current state

- User asked to structure the remaining project work into sensible workflows,
  draft RFCs where needed, and ensure future implementation prompts encourage
  maximal useful sub-agent use.
- No Striatum run was registered, prepared, started, or claimed.
- `main` was clean before this planning/scaffolding pass.

## Work completed

- Added RFC 0014 draft for generalized trim and high-angle `GZ` stability.
- Added RFC 0015 draft for CFD solver dispatch and job artifacts.
- Added workflow 0018 scaffolding with `RUNBOOK.md`, `SOURCES.md`,
  `QUEUE.md`, and this report.
- Structured the remaining backlog into proposed workflows 0019-0025:
  legacy RFC partial closure, browser acceptance/demo, web plots/comparison UI,
  generalized trim/GZ stability, resistance calibration dataset vetting,
  watertight solid mesh profile, and CFD solver dispatch/jobs.
- Included a three-lane review pattern for each queued workflow.
- Included Codex-preferred implementation prompts that instruct implementors to
  use the maximal number of useful sub-agents with disjoint write scopes.
- Updated `docs/rfcs/README.md` to index RFCs 0014 and 0015 and link to the
  deferred-work queue.
- `striatum doctor` initially found three stale bundle problems after the local
  Striatum install moved to `1.31.0`: `claude_code` skills, `codex` skills, and
  the `codex` plugin bundle.
- Refreshed the `claude_code` and `codex` skill bundles plus the `codex`
  plugin bundle. A follow-up `striatum doctor` returned zero problems.

## Findings recorded

- Existing RFCs already cover browser acceptance, web analysis UI, resistance
  calibration, mesh profile readiness, and legacy plumb-bow/design-constraint
  partials.
- New RFCs are needed for generalized trim/high-angle stability and solver
  dispatch because those decisions are cross-cutting and were intentionally
  deferred by RFCs 0010 and 0011.

## Next action

- Amend the local commit with bundle refresh metadata, then push `main`.
