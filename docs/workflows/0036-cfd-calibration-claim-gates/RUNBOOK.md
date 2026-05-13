# Runbook - workflow 0036 CFD calibration claim gates

## Purpose

Implement RFC 0025 claim gates so raw CFD, uncalibrated analytical resistance,
validation fixtures, calibration fixtures, fitted models, and final design
fitness cannot be mislabeled.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0036-cfd-calibration-claim-gates/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run the three review lanes before implementation. Keep the implementation slice
limited to accepted ledger findings and keep raw/unvalidated behavior visible.

