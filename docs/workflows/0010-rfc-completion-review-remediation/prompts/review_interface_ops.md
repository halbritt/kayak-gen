# Task - interface, packaging, and operations review

Read `docs/workflows/0010-rfc-completion-review-remediation/SOURCES.md`,
RFCs 0002, 0003, 0007, and 0008. Write:

`striatum/0010-rfc-completion-review-remediation/codex-review/REVIEW_INTERFACE_OPS.md`

Use this structure:

```markdown
# Interface and operations review - 0010

Date: <YYYY-MM-DD>
Reviewer: codex
Verdict intent: accept | accept_with_findings | needs_revision | reject

## Summary

<One concise paragraph.>

## Commands run

```text
<command> -> <result>
```

## Findings

### F-OPS-001 - <short title>
- Severity: blocker | major | minor | nit
- RFC: 000N, section or criterion
- File(s): <paths and lines>
- What you found: <2-4 sentences>
- Suggested remediation: <specific fix or test>
- Evidence: <commands, paths, or output excerpts>
```

Specific checks:

1. Desktop GUI and station-view behavior promised by RFCs 0002 and 0003.
2. CLI entry points and package extras promised by RFC 0007.
3. Trame web state, controllers, REST shape, and Docker behavior promised by
   RFC 0008.
4. Whether `pytest` can run in the current environment. If not, capture the
   first actionable failure.
5. Whether workflow artifacts and current repo state honestly reflect the work
   completed.

Prefer reproducible command evidence for broken-state claims.
