# Task - consolidate the three reviews

Read:

- `striatum/0010-rfc-completion-review-remediation/claude/REVIEW_TRACEABILITY.md`
- `striatum/0010-rfc-completion-review-remediation/gemini/REVIEW_ARCH_DOMAIN.md`
- `striatum/0010-rfc-completion-review-remediation/codex-review/REVIEW_INTERFACE_OPS.md`

Write:

`striatum/0010-rfc-completion-review-remediation/ledger/FINDINGS.md`

Use this structure:

```markdown
# Findings ledger - 0010

Date: <YYYY-MM-DD>
Review inputs: traceability, arch/domain, interface/ops

## Stats

- Source findings: N
- Deduplicated findings: M
- By severity: blocker N / major N / minor N / nit N
- Actionable now: N
- Needs human decision: N

## Findings

### F-001 - <short title>
- Source: F-TRACE-001, F-OPS-003
- Severity: blocker | major | minor | nit
- Classification: actionable-now | docs-only | process-only | needs-human-decision | defer-follow-up
- RFC(s): 000N
- File(s): <paths and lines>
- Statement: <merged 2-4 sentence finding>
- Suggested remediation: <specific action for implementation>
- Dissent or nuance: <only when needed>
```

Rules:

1. Merge duplicate findings with the same root cause.
2. Keep severity from the most severe credible source unless you explain the
   downgrade.
3. The implementation job must fix every `actionable-now` blocker and major
   finding.
4. Do not turn human/process questions into code work. Classify them clearly.
