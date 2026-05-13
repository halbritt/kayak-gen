# Runbook - workflow 0010

This workflow creates an RFC completion audit followed by a Codex remediation
round. It is intended for a repo that may be partially broken.

## Shape

1. Three review jobs run in parallel:
   - `review_traceability` on the Claude lane.
   - `review_arch_domain` on the Gemini lane.
   - `review_interface_ops` on the Codex lane.
2. `findings_ledger` merges the reviews into one normalized ledger.
3. `implement_findings` runs on the Codex lane and fixes actionable findings.
4. `final_review` gates the patch. A `needs_revision` verdict sends the run
   back to Codex implementation once.

## Operator notes

Prepare and start this only when you are ready for agents to mutate the repo.
The implementation job is intentionally broad enough to edit package code,
tests, docs, packaging, and compatibility shims, but it cannot write
`.striatum/`, `.codex/`, or `.claude/`.

The branch is `confirm` mode with suggested name
`striatum/0010-rfc-completion-review-remediation`.
