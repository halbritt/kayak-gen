# Runbook - workflow 0038 resistance calibration acceptance

## Purpose

Implement RFC 0027's promotion and accepted-fit gates. The workflow must keep
current resistance output uncalibrated unless accepted calibration fixtures,
fit records, metrics, and validity envelopes satisfy the RFC.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0038-resistance-calibration-acceptance/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run review lanes before implementation and do not fabricate fixtures or accepted
fits.

