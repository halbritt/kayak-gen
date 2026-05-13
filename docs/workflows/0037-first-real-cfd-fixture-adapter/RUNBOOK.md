# Runbook - workflow 0037 first real CFD fixture adapter

## Purpose

Implement RFC 0026's deterministic fixture/local-command CFD adapter slice. The
workflow must not introduce OpenFOAM, SU2, hosted execution, or validated CFD
claims.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0037-first-real-cfd-fixture-adapter/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run review lanes first, then implement only the ledger-approved adapter slice.

