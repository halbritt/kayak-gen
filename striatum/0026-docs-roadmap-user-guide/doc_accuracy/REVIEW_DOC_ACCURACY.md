author: operator [self-declared: operator-doc-accuracy-review]

# Documentation accuracy review - workflow 0026

Verdict intent: accept_with_findings

## Findings

### A-001 - PRD overstates delivered geometry and stability behavior

`docs/PRD.md` still describes triangulating a watertight mesh and computing a
full 0-90 degree GZ curve as product behavior. Current RFC status says current
packages are open surfaces, watertight solid geometry is deferred, and
high-angle GZ remains unavailable until a closed-volume body model exists.

Required action: update PRD language to distinguish current behavior from
future roadmap scope. Keep watertight solid geometry and high-angle GZ in the
roadmap, not in the delivered capability list.

### A-002 - Root operator report is stale after workflows 0025 and Striatum refresh

`OPERATOR_REPORT.md` still says workflow 0025 is active and contains old
verification baseline numbers. That conflicts with `main`, which has workflow
0025 landed and Striatum bundles refreshed.

Required action: rewrite the active-state section to say no workflow is active
until 0026, then update it as 0026 progresses.

### A-003 - Deferred queue presents completed workflows as future work

`docs/workflows/0018-deferred-backlog/QUEUE.md` still lists workflows 0019-0025
as queued even though they are complete. This obscures what remains after
workflow 0025.

Required action: convert the queue to show completed history separately from
next queued workflows starting at 0026/0027.

### A-004 - No user-facing guide exists

The repo has `AGENTS.md` for contributors and RFCs for design intent, but no
single user guide for installing, creating a hull, exporting STL, evaluating,
running sweeps, packaging meshes, or using the local CFD status contract.

Required action: add `docs/USER_GUIDE.md` and link it from the RFC index or a
root `README.md`.

### A-005 - Any new docs must preserve raw/unvalidated claims

RFC 0005, 0012, and 0015 all separate analytical raw filters, validation-only
source metadata, and local CFD status records from calibrated/validated
hydrodynamic claims.

Required action: user docs must explicitly label resistance as an analytical
screening estimate and CFD dispatch as local job-state plumbing, not a real CFD
solver or validated result.
