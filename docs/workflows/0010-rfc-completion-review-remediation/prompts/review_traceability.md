# Task - RFC traceability review

Read `docs/workflows/0010-rfc-completion-review-remediation/SOURCES.md` and
all RFCs 0002 through 0008. Write:

`striatum/0010-rfc-completion-review-remediation/claude/REVIEW_TRACEABILITY.md`

Use this structure:

```markdown
# RFC traceability review - 0010

Date: <YYYY-MM-DD>
Reviewer: claude
Verdict intent: accept | accept_with_findings | needs_revision | reject

## Summary

<One concise paragraph.>

## RFC acceptance matrix

| RFC | Criterion | Status | Evidence | Gap |
|---|---|---|---|---|
| 0002 | <criterion> | pass / partial / fail / deferred | <path:line or command> | <short gap> |

## Findings

### F-TRACE-001 - <short title>
- Severity: blocker | major | minor | nit
- RFC: 000N, section or criterion
- File(s): <paths and lines>
- What you found: <2-4 sentences>
- Suggested remediation: <specific fix or doc update>
- Evidence: <commands, paths, or reasoning>
```

Rules:

1. Include every non-template RFC currently indexed through RFC 0008.
2. A missing acceptance criterion is at least `major` if the RFC is marked
   proposed but implementation work appears to have landed.
3. Mark stale or contradictory RFC text separately from code defects.
4. Do not trust prior workflow summaries. Inspect the current repo.
