# Runbook - workflow 0042 design constraint surfacing revision

## Purpose

Implement RFC 0031 as the conservative successor to RFC 0029. The run should
land additive design-validity metadata, preserve existing advisory behavior,
and disclose unsupported reserved shape fields without changing product
geometry.

## Review and revision route

The workflow starts with `review_remediation`, which prepares the first review
packet. If any first-pass review returns `needs_revision`, Striatum cycles that
review back through `review_remediation` once before re-running the review.

After all three review lanes accept or accept with findings, the run proceeds
through `findings_ledger`, `implement_findings`, and `final_review`. A final
review `needs_revision` cycles once back to `implement_findings`.

## Commands

```bash
WF=docs/workflows/0042-design-constraint-surfacing-revision/workflow.json

striatum --repo . workflow validate "$WF" --json

striatum --repo . run prepare --workflow "$WF" --json
```

Keep implementation conservative. Do not implement rocker, deadrise,
chine-radius, flare, full LCB redistribution, optimizer scoring, CFD readiness,
or resistance calibration.
