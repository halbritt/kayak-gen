# Runbook - workflow 0033 generated closed-body construction

## Purpose

Define and implement a deterministic generated hull-plus-deck closed body for
closed-volume evaluation. Preserve display STL separation and do not create
CFD readiness evidence.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0033-generated-closed-body-construction/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Keep this report and `OPERATOR_REPORT.md` current before compaction.

