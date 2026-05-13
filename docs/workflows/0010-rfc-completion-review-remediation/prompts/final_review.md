# Task - final remediation gate

Read:

- `striatum/0010-rfc-completion-review-remediation/ledger/FINDINGS.md`
- `striatum/0010-rfc-completion-review-remediation/implementation/PATCH_SUMMARY.md`
- The current git diff.

Write:

`striatum/0010-rfc-completion-review-remediation/final/FINAL_REVIEW.md`

Use this structure:

```markdown
# Final review - 0010

Date: <YYYY-MM-DD>
Verdict: accepted | needs_revision | reject

## Coverage check

| Finding | Required action | Status | Evidence |
|---|---|---|---|
| F-001 | fix / escalate / defer | pass / fail / partial | <path, test, or rationale> |

## Test review

<Commands from patch summary, whether they are sufficient, and any gaps.>

## Verdict notes

<Concrete notes. For needs_revision, name exact findings that must go back to Codex.>
```

Rules:

1. Gate only against the ledger and patch summary. Do not introduce unrelated
   new scope.
2. Any unresolved `actionable-now` blocker is `needs_revision` or `reject`.
3. Any unresolved `actionable-now` major finding is `needs_revision` unless the
   implementer documented a defensible escalation.
4. The workflow allows one revision cycle back to `implement_findings`.
