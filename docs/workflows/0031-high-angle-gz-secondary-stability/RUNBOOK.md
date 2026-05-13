# Runbook - workflow 0031 high-angle GZ and secondary stability

## Purpose

Implement high-angle `GZ` only after closed-volume geometry is accepted and
available. Unsupported hulls must return explicit unavailable status rather
than placeholder curves.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0031-high-angle-gz-secondary-stability/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Start only after workflow 0027 has landed. Keep this report and
`OPERATOR_REPORT.md` current before compaction.
