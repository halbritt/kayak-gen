# Runbook - workflow 0039 plumb-stem closure semantics

## Purpose

Implement RFC 0028 so exact plumb end caps, asymmetric rake, coordinate/sign
conventions, and generated closed-body dependency boundaries are explicit and
tested.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0039-plumb-stem-closure-semantics/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run the three review lanes before implementation. Keep open inspection surfaces
and generated closed-body readiness labels distinct.
