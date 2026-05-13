author: operator [self-declared: operator-ledger]

# Findings ledger - workflow 0026

Run id: `run_b51d0f3bc0e3409b824f120a59676733`
Job: `findings_ledger`

Gate result: proceed with documentation-only implementation.

## Stats

- Documentation accuracy review: 5 findings, verdict `accept_with_findings`.
- User guide review: 5 findings, verdict `accept_with_findings`.
- Roadmap review: 6 findings, verdict `accept_with_findings`.
- Deduplicated implementation findings: 7.

## Deduplicated findings

### F-001 - Add a practical user guide

Create `docs/USER_GUIDE.md` with quick start, CLI task examples, desktop/web
entry points, mesh packaging, local CFD dispatch status, troubleshooting, and
current limitations.

### F-002 - Correct stale PRD delivery claims

Revise `docs/PRD.md` so delivered/current behavior does not claim watertight
solid generation, full high-angle GZ, calibrated resistance, full web parity,
or real CFD execution.

### F-003 - Reconcile operator report state

Update `OPERATOR_REPORT.md` so it no longer says workflow 0025 is active and
records workflow 0026 as the current docs-roadmap run.

### F-004 - Replace stale deferred queue wording

Update `docs/workflows/0018-deferred-backlog/QUEUE.md` so completed workflows
0019-0025 are history and remaining work starts with 0026/0027 onward.

### F-005 - Draft next proposed RFCs

Add proposed RFCs for the next load-bearing work: closed-volume geometry,
first real CFD adapter, web CFD job routes, resistance calibration fixtures,
and high-angle GZ/secondary stability.

### F-006 - Update RFC index and linking docs

Update `docs/rfcs/README.md` to include the new proposed RFCs and link the
user guide from an appropriate navigation surface. Add a root `README.md` if
that is the clearest user entry point.

### F-007 - Keep all new docs truthful about raw/unvalidated outputs

Any user-facing docs must say resistance is an analytical screening estimate,
CFD dispatch is local job-state plumbing unless a real adapter lands, current
mesh packages are open-surface candidates, and high-angle GZ is unavailable.

## Implementation guidance

Safe now:

- Add `docs/USER_GUIDE.md`.
- Add proposed RFCs 0016-0020 for closed-volume geometry, real CFD adapter, web
  job routes, calibration fixtures, and high-angle GZ.
- Update `docs/rfcs/README.md`, `docs/PRD.md`,
  `docs/workflows/0018-deferred-backlog/QUEUE.md`, `OPERATOR_REPORT.md`, and
  the workflow operator report.
- Optionally add a concise root `README.md` that points users to the guide and
  contributors to `AGENTS.md`.

Do not implement:

- New runtime code.
- Real solver execution, web job routes, calibrated resistance, high-angle GZ,
  closed-volume geometry, or watertight solid generation.
- Acceptance language for proposed RFCs.
