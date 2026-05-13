# Operator report - workflow 0020

Updated: 2026-05-13

## Current state

- User asked to proceed through the structured workflows and keep this report
  updated before each workflow step.
- Workflow 0019 accepted and `main` was fast-forwarded/pushed through
  `d126e3b`.
- Queue item 0020 is `0020-browser-acceptance-demo`: real-browser or equivalent
  smoke coverage, Lighthouse checks only where practical, and truthful
  demo/deployment documentation for RFC 0008.
- Workflow 0017 landed headless web verification and `docs/WEB_VERIFICATION.md`
  but explicitly left browser automation, Lighthouse, and hosted demo acceptance
  open.
- This workflow is being scaffolded from clean `main`.
- Scaffold validation passed:
  `striatum --repo . workflow validate docs/workflows/0020-browser-acceptance-demo/workflow.json`.
- Whitespace validation passed: `git diff --check`.

## Findings recorded

- None yet. Findings will be recorded after the three review lanes and ledger.

## Next action

- Commit and push the workflow 0020 scaffold, then prepare and start the
  Striatum run.
