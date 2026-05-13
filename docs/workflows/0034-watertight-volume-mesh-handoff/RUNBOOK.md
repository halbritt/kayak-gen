# Runbook - workflow 0034 watertight volume mesh handoff

## Purpose

Implement the RFC 0023 handoff from a passing generated closed body to a
watertight volume-mesh package that can honestly claim `cfd_ready` for
`watertight_solid_resistance_v1`.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0034-watertight-volume-mesh-handoff/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Start only after generated closed-body and self-intersection diagnostics are
available. Keep this report and `OPERATOR_REPORT.md` current before
compaction.
