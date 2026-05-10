# Task — gate the remediation plan

Read:

- `striatum/0009-multi-lane-review/ledger/FINDINGS.md`
- `striatum/0009-multi-lane-review/synthesis/REMEDIATION.md`

Write `striatum/0009-multi-lane-review/final/FINAL_REVIEW.md`.

Structure:

```markdown
# Final review — 0009 multi-lane review

Date: <YYYY-MM-DD>
Verdict: accepted | needs_revision

## Coverage check

For every blocker / major finding in the ledger, confirm it is either
addressed by a P-row in the remediation plan, or explicitly placed in
`Deferred / rejected` with an acceptable reason.

| Finding | Severity | Plan status | Comment |
|---|---|---|---|
| F-001 | blocker | P-002 | OK |
| F-005 | major   | deferred | Reason cited; agree |
| ... | | | |

## Verdict notes

If `needs_revision`: list specific gaps the synthesizer must close in
the next iteration. Be concrete — reference finding IDs, not "you
missed something".

If `accepted`: optional commendation or note for the operator.
```

Rules:

1. **Do not raise new findings.** Your job is gating, not extending
   the review. If you spot a fresh issue mid-gate, queue it for a
   follow-on review run by noting it in `Verdict notes` under a
   "For a follow-on run" subheading. Do not block the current run on
   it.
2. **A single uncovered blocker triggers `needs_revision`.** Major
   findings can be deferred with reason; blockers cannot.
3. **One cycle maximum.** If after one revision the synthesis still
   misses a blocker, return `needs_revision` and stop. The operator
   takes it from there (the workflow's `cycles[].max_iterations` is 1).
