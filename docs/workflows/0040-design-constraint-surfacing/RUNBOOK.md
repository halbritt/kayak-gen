# Runbook - workflow 0040 design constraint surfacing

## Purpose

Implement RFC 0029 so enforced, advisory, and unsupported constraint states are
visible across CLI, desktop, web, sweeps, and reports without hard-locking the
design space.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0040-design-constraint-surfacing/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run the three review lanes before implementation. Keep unsupported shape fields
distinct from invalid inputs and from fully honored geometry controls.
