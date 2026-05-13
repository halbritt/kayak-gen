# Runbook - workflow 0030 resistance calibration fixture

## Purpose

Review and implement the safe slice for RFC 0019. The workflow must either
land a rights-cleared calibration or validation fixture, or record why the work
remains blocked. It must not fabricate data or describe current resistance as
calibrated.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0030-resistance-calibration-fixture/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Start only after the operator confirms the branch. Keep this report and
`OPERATOR_REPORT.md` current before compaction.
