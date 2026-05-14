# Review Remediation Prompt

Prepare the RFC 0034 review packet, or remediate first-pass review-blocking
scope/scaffold issues if this is a revision cycle.

Read the required context docs, especially RFC 0034, RFC 0033, and the workflow
0044 final review. Keep changes inside the declared write scope. Do not edit
runtime product code. Do not mutate Striatum state. Do not add `author:` or
byline metadata.

Use the maximal number of useful sub-agents or parallel helpers for independent
source/RFC/workflow/doc checks if your environment supports them.

Write `striatum/0045-workspace-ui-follow-up/review_remediation/REMEDIATION.md`
with:

- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- any remediation performed
- any reviewer-facing caveats
- validation commands run
