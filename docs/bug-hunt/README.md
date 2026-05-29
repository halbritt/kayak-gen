# Bug Hunt

A self-paced, model-driven bug-hunt loop over the kayak-gen
codebase. Distinct from the three-lane `code_doc_audit` workflow
(RFC 0059) — that audit reads each surface once per cycle for
drift; this loop reads each surface for **runtime bugs** —
race conditions, validator gaps, off-by-one math, missing
error paths, dead code, security issues, claim-state leaks
the audit lanes didn't catch.

## How it runs

The loop is driven by `/loop` in dynamic (self-paced) mode. Each
tick:

1. Reads `COVERAGE.md` to pick a surface not searched recently
   (and not still in the cool-down window).
2. Dispatches an `Explore` subagent with a bug-pattern brief
   focused on that surface.
3. Appends any actionable findings to `LEDGER.md` with a stable
   `BUG-NNN` id.
4. Updates `COVERAGE.md` (surface marked searched, with
   timestamp and lookback).
5. Decides next-tick delay via `ScheduleWakeup`. Stops when
   either: (a) the coverage table shows every surface has been
   searched in the last hour with no new findings, or (b) the
   operator explicitly stops the loop, or (c) three consecutive
   ticks find nothing actionable.

## Files

| File | Purpose |
|---|---|
| `LEDGER.md` | Append-only list of bugs found (or null findings recorded as positive baseline). |
| `COVERAGE.md` | Surface inventory + last-touched timestamp + lookback. |
| `README.md` | This file. |

## Severity vocabulary

Same as the audit findings (RFC 0059 §3):

- **critical**: data loss, silent corruption, claim-state lie
  surfaced to operators.
- **high**: incorrect computation under a documented input
  range; missing validator on a public schema; security gap.
- **medium**: incorrect under a rare-but-real input; missing
  error path; integration bug between two modules.
- **low**: cosmetic correctness gap; missing test for a known
  invariant; harmless dead code.
- **info**: null finding — surface searched, nothing actionable.

## Closing a finding

When a bug is fixed, flip the LEDGER entry's `status: open` →
`status: closed by <commit-sha>` (or `closed by <workflow-id>`
for striatum-mediated fixes). The LEDGER is append-only for
new entries but the existing rows' `status` field can be
flipped centrally per the audit precedent.

For a fix that touches `kayakgen/` source: route through
striatum per `feedback_striatum_required` — same discipline as
the audit follow-up workflows.
