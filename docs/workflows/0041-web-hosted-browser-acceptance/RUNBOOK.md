# Runbook - workflow 0041 web hosted browser acceptance

## Purpose

Implement RFC 0030 so hosted-demo, real-browser, console-clean, Lighthouse,
plot/dashboard parity, and web CFD route dependency acceptance are explicit.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0041-web-hosted-browser-acceptance/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

Run the three review lanes before implementation. Keep real-browser acceptance
separate from headless web checks and keep unavailable CFD routes explicit.
