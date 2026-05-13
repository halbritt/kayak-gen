# Task - implement findings from the ledger

Read:

- `striatum/0010-rfc-completion-review-remediation/ledger/FINDINGS.md`
- The relevant RFCs and files cited by the ledger.

Fix every `actionable-now` blocker and major finding. Also fix minor/nit
findings when they are on the same path and low risk. Prefer Codex for this
implementation round; this job is already bound to the Codex lane.

Write:

`striatum/0010-rfc-completion-review-remediation/implementation/PATCH_SUMMARY.md`

Use this structure:

```markdown
# Patch summary - 0010

Date: <YYYY-MM-DD>
Implementer: codex

## Findings addressed

| Finding | Action | Files changed | Tests |
|---|---|---|---|
| F-001 | <summary> | <paths> | <commands> |

## Findings not addressed

| Finding | Reason | Required next step |
|---|---|---|

## Tests run

```text
<command> -> <result>
```

## Residual risk

<Short list or paragraph.>
```

Rules:

1. Stay inside the workflow write scope. Do not write `.striatum/`, `.codex/`,
   or `.claude/`.
2. Do not rewrite broad architecture unless the ledger identifies that as the
   root cause.
3. If a finding requires a human decision, document it under "Findings not
   addressed" and do not guess.
4. Run the most relevant tests you can. If the full suite cannot run, capture
   the first actionable failure and run focused tests after fixes.
