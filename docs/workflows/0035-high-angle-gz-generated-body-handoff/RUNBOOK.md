# Runbook - workflow 0035 high-angle GZ generated-body handoff

## Purpose

Implement the RFC 0024 handoff that keeps high-angle `GZ` unavailable until a
generated closed body passes diagnostics. Synthetic fixtures may test math but
must not claim real kayak stability.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Start only after generated closed-body and self-intersection diagnostics are
available. Keep this report and `OPERATOR_REPORT.md` current before
compaction.
