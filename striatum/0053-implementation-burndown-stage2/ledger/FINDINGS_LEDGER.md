---
schema_version: "striatum.findings_ledger.v1"
artifact_kind: "findings_ledger"
summary_count: 0
---

author: operator [self-declared: operator-0053-findings-ledger-repair]
schema_version: striatum.findings_ledger.v1
kind: findings_ledger
logical_name: findings_ledger
date: 2026-05-14

# Findings Ledger - Workflow 0053 Stage 2

## Ledger Verdict

`accept_with_must_fix_findings`

The three review artifacts originally reduced to one must-fix remediation item. The traceability and claims reviews are accepting with no actionable findings. The compatibility concern was later explicitly waived by operator direction, so the ledger no longer carries an open remediation item.

## Must-Fix Remediation Items

None.

### MF1 - `SweepRunRecord` is not backward-compatible with pre-`pending_count` `run.json` files

**Source finding:** Ops/tests review O1
(`striatum/0053-implementation-burndown-stage2/reviews/ops_tests/REVIEW.md`).

**Severity:** high.

**Affected paths:** `kayakgen/search/sweep.py`, `kayakgen/search/compare.py`,
`kayakgen/ui/web/controllers.py`, `kayakgen/cli/main.py`.

**Deduplicated issue:** `SweepRunRecord` now requires `pending_count`, but
`load_sweep_run()` still deserializes existing `run.json` files with
`SweepRunRecord.model_validate_json(...)` and no compatibility fallback. Older
sweep artifacts created before this change no longer load through the compare
CLI or web controller paths.

**Required remediation:** Make `pending_count` backward-compatible, either by
defaulting it and deriving the value when absent or by adding a load-time
compatibility shim in `load_sweep_run()` / the sweep model validator so older
`run.json` files continue to deserialize cleanly. Keep `pending_count` in new
serialized output.

**Disposition:** Waived by operator direction on 2026-05-15. No remediation
requested.

**Boundary to preserve:** Do not reopen any solver, hosting, or calibration
scope. This is a serialization compatibility fix only.

## Non-Blocking Successor Items

None were published in the three review artifacts for this run.

## Accepted Reviews With No Action

- Traceability review: accept, no actionable findings.
- Claims review: accept, no actionable findings.

## Deduplication Notes

- The ops/tests finding is superseded by operator direction.
- No separate successor item was introduced for the accepted reviews.
