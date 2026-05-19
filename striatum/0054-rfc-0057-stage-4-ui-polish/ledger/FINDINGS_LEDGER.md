---
kind: findings_ledger
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: findings_ledger
authored_by: claude-opus-4-7 (cowboy mode; striatum runner blocked by halbritt/striatum#24)
---

# Workflow 0054 Findings Ledger

## Must-fix (remediation lane)

*(empty)*

No reviewer raised a must-fix finding. Each accepted-with-findings
verdict explicitly scoped its findings as non-blocking.

## Non-blocking successor items

These are recorded for a future workflow or RFC; they are NOT
remediation items in this workflow's cycle.

### NB-1: Per-row Fork buttons in the frontier table

**Origin:** Traceability review.

**Decision row:** STAGE_4_DECISIONS.md D-12 — "one-click 'Fork with new
seed' button on succeeded rows".

**Current state:** A single panel-level Fork button is bound to
`state.generative_job_id`. The `render_fork_button(app, *, job_summary)`
helper exists in `kayakgen/ui/web/generate_fork_button.py` but is not
called from the frontier-view table render loop.

**Successor scope:** Modify `render_frontier_view_section` to call
`render_fork_button` per row when `summary["state"] == "succeeded"`.
Mechanical wiring; no new design surface.

**Why deferred:** The current panel-level button satisfies the
common case (operator selects a job, clicks Fork). The per-row
pattern is a polish item; deferring does not block any decision.

### NB-2: Snapshot-assert literal byte-stability of `_redact_log_text`

**Origin:** Ops/tests review (OQ-1).

**Successor scope:** Add a fixture log captured from a runner-produced
session that contains no `$HOME` / `<jobs_root>` substrings, and assert
`_redact_log_text(snapshot) == snapshot` literally.

**Why deferred:** The existing
`test_generative_job_log_payload_byte_stable_when_no_paths_present`
proves redactor idempotency, which is the spirit of the contract.
Tightening the assertion is a documentation gain, not a correctness
gain.

### NB-3: Direct widget-tree integration tests for the form-builder

**Origin:** Ops/tests review (OQ-2).

**Successor scope:** Drive Trame widgets through the test client
rather than the controller callback layer; assert the rendered DOM
matches the form schema.

**Why deferred:** RFC 0008's browser-acceptance verification is the
upstream gate. Adding widget-tree tests duplicates effort without
catching new regressions in practice.

### NB-4: Constant-ify `REVIEW_TABS` tab values

**Origin:** Ops/tests review (OQ-3).

**Successor scope:** Promote the `"generate"` / `"analysis"` /
`"mesh"` / `"comparison"` / `"cfd"` / `"advisories"` literals into
module-level constants and have the auto-poll listener (and any
future tab-aware code) reference the constant rather than the
string.

**Why deferred:** Touches an RFC 0033-shaped surface; deserves its
own RFC if it goes beyond the auto-poll listener.

## Accepted review concerns (no action)

None — all reviewer findings landed as non-blocking successors or
acceptance evidence.

## Workflow execution note

This ledger was produced cowboy-mode under operator authorisation
because the v1.55.0 `striatum supervise send --packet-id` flow
rejected the IDs returned by `claim-next`, blocking the runner from
dispatching the review packets. Tracking the underlying striatum
gap at <https://github.com/halbritt/striatum/issues/24>. When the
upstream fix lands, this same workflow scaffold
(`docs/workflows/0054-...`) is re-runnable end-to-end on the daemon
for a clean review trail; the reviews above stand as the current
authoritative cowboy-mode record.
