# Runbook - workflow 0032 closed-volume self-intersection diagnostics

## Purpose

Define and implement conservative self-intersection diagnostics for closed
volume bodies. Keep the result as closed-volume diagnostic evidence only; do
not create or imply CFD readiness.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0032-closed-volume-self-intersection-diagnostics/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Keep this report and `OPERATOR_REPORT.md` current before compaction.

