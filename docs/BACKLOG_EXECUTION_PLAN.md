# Backlog Execution Plan

This document is the operator-facing execution order for the current backlog.
It is derived from `docs/ROADMAP.md` and the accepted RFC posture. It does not
replace the roadmap; it turns it into a practical run sequence.

## Operating Rules

- Keep every batch inside the current no-claims boundaries.
- Use Striatum workflows for implementation, review, ledgering, remediation,
  and final review.
- Prefer the smallest safe slice that can land cleanly.
- Keep `OPERATOR_REPORT.md`, `CHANGELOG.md`, `docs/ROADMAP.md`, and
  `docs/rfcs/README.md` synchronized after each landing.
- Do not reopen settled decisions unless a later accepted RFC says otherwise.

## Execution Order

### 1. Docs, Status, And Claim Hygiene

Purpose: keep the repo’s planning and user-facing text aligned with the actual
landed state.

Work items:
- correct stale RFC statuses and labels
- reconcile roadmap text after each workflow landing
- keep user guide examples and limitations current
- append changelog entries for product-visible changes
- update operator reports for active workflows

Exit criteria:
- docs match current behavior
- no stale RFC labels are left as implementation authority

### 2. UI Cleanup Successors

Purpose: finish the narrow UI follow-ups without opening new backend scope.

Work items:
- Trame same-seed listener proof or removal
- export-row schema consolidation
- disabled export copy polish
- web snapshot and CFD alias schema unification

Execution notes:
- bundle adjacent cleanup items when they share the same review surface
- keep desktop parity out of scope unless a later RFC explicitly requests it

Exit criteria:
- visible copy and schema behavior are consistent
- no backend capability changes are introduced

### 3. Browser Hosting And Parity

Purpose: keep browser-facing work honest and limited to the accepted hosted-demo
posture.

Work items:
- narrow hosted-demo operation using the documented serve/Docker path
- browser acceptance and smoke checks
- compact plot/dashboard parity where needed
- any remaining web workspace parity gaps

Execution notes:
- treat full public hosting as blocked until the recorded evidence exists
- do not imply hosted CFD, production SLA, or desktop parity rewrite

Exit criteria:
- browser work stays local or narrowly hosted as approved
- the docs clearly distinguish demo posture from production hosting

### 4. Geometry Evidence And Solver Readiness

Purpose: build the evidence spine needed before any real solver promotion.

Work items:
- generated-body hardening
- `snappyHexMesh` evidence harness
- deterministic dictionary and patch metadata capture
- `checkMesh` and artifact checksum recording
- dispatch rejection tests for missing evidence

Execution notes:
- keep meshing as evidence, not solver success
- do not promote ordinary generated packages to `cfd_ready`

Exit criteria:
- the harness produces reproducible evidence artifacts
- solver readiness remains gated on the accepted evidence spine

### 5. Real CFD Adapter

Purpose: advance the first external solver path only after the evidence gates
are satisfied.

Work items:
- OpenFOAM-v2512 local adapter work
- force.dat parser correctness
- deterministic smoke coverage
- raw-unvalidated output handling

Execution notes:
- keep `succeeded` blocked until the mesh/evidence gates are met
- do not claim validation, calibration, or design fitness

Exit criteria:
- adapter behavior is deterministic and raw/unvalidated
- any success path is still evidence-bound

### 6. Resistance Evidence And Calibration

Purpose: separate source review from calibration promotion.

Work items:
- review and classify resistance source packets
- keep validation-only packets clearly labeled
- promote calibration only after rights, extraction, uncertainty, and fit
  evidence are accepted

Execution notes:
- the first full source-review packet is validation-only
- calibration remains a later workflow with a stricter gate

Exit criteria:
- source-review results are traceable
- calibration is not implied until its acceptance gate is explicit

### 7. High-Angle Stability Surfacing

Purpose: surface high-angle `GZ` data incrementally without overclaiming.

Work items:
- CLI JSON surfacing first
- opt-in sweep artifacts next
- display-only comparison and web read models after that
- minimal desktop support last

Execution notes:
- keep real kayak stability claims unavailable until the generated-body
  evidence model and heeled integration gate exist
- preserve conservative defaults and objectives

Exit criteria:
- the staged surfacing path is explicit and opt-in
- user-facing claims remain bounded

### 8. Sweeps, Comparison, And Search

Purpose: finish the sweep lifecycle and comparison behavior before broader
optimizer work.

Work items:
- `pending` lifecycle support
- resume preservation
- visible-but-frontier-ineligible comparison rows
- sweep-side STL artifacts
- objective metadata
- later optimizer/search work

Execution notes:
- keep `pending` additive and visible
- do not start optimizer/search expansion until lifecycle and provenance are
  settled

Exit criteria:
- sweep runs can represent partial progress honestly
- comparison output matches the lifecycle rules

## Suggested Implementation Cadence

1. Land one batch at a time unless two batches are explicitly independent.
2. Run review lanes in parallel whenever write scopes do not overlap.
3. Deduplicate findings into a ledger before remediation.
4. Close each workflow with final review and a changelog/doc sync.
5. Recheck the roadmap after each landing and mark completed work as history.

## What Not To Do

- Do not reopen full desktop parity as a default goal.
- Do not claim hosted CFD or production hosting without the recorded evidence.
- Do not promote calibration or solver success ahead of their gates.
- Do not let stale queue items outrank the current roadmap and RFC index.
