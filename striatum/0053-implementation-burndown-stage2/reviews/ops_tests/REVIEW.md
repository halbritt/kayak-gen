---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: operator [self-declared: operator-0053-review-ops-repair]
schema_version: striatum.finding.v1
kind: finding
logical_name: review
session: sess_a28e3c85d4d241d49ec2a07ad13c7c08
date: 2026-05-14

# Ops And Tests Review - Workflow 0053 Stage 2

## Verdict

`accept_with_findings`

The stage-two patch set is testable and the focused gates for the changed
sweep, comparison, stability, CLI, and web slices passed in this worktree.
I found one compatibility regression that should be remediated before the new
`pending` sweep state is treated as fully landed.

## Validation

- `.venv/bin/python -m pytest -q tests/test_sweep.py tests/test_compare.py tests/test_cli.py -k 'pending or resume or compare or sweep_runs_json_spec'`
  - `31 passed, 23 deselected`
- Direct model check of an old-format sweep record without `pending_count`
  fails validation as expected from the current schema.

## Findings

### O1 - `SweepRunRecord` is no longer backward-compatible with existing `run.json` files

**Severity:** high

**Where:** `kayakgen/search/sweep.py:125-136`, `kayakgen/search/compare.py:105-111`,
`kayakgen/ui/web/controllers.py:1315-1318` (load path), `kayakgen/cli/main.py:388-391`.

`SweepRunRecord` now requires `pending_count`, and `load_sweep_run()` still
deserializes `run.json` with `SweepRunRecord.model_validate_json(...)` without
any fallback. I verified that an older sweep record with the previous shape
(`candidate_count`, `completed_count`, `failed_count`, `skipped_count`, and
`candidates`, but no `pending_count`) raises a `ValidationError`.

That makes every existing run directory created before this change unreadable
through the comparison CLI and web controller code paths that load `run.json`
directly. It is an API/operational compatibility break, not just a test gap:
historical sweep artifacts become inaccessible even though the new behavior is
meant to be additive.

**Suggested remediation:** make `pending_count` backward-compatible by giving
it a default and deriving it from candidate statuses when absent, or add a
load-time compatibility shim in `load_sweep_run()` / the sweep model validator
so older `run.json` files continue to deserialize cleanly. Keep the new field
in serialized output for fresh runs.

## Non-Findings

- The focused sweep, comparison, CLI, stability, and web regressions added in
  this packet are coherent and the targeted tests I ran passed.
- I did not see a determinism regression in the new pending-resume behavior.
- The `pending` comparison handling keeps pending candidates visible but out of
  the Pareto front, which matches the workflow intent.
