# Runbook - workflow 0043 web hosted browser acceptance revision

## Purpose

Create the revised successor path for RFC 0032 after the blocked 0041
web-hosted-browser-acceptance run. The workflow keeps the same three first-pass
review lanes, then ledger, Codex implementation, and final review. It adds an
explicit review revision anchor so a first-pass browser `needs_revision`
verdict routes to remediation and re-review instead of an unplanned human
checkpoint.

## Commands

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0043-web-hosted-browser-acceptance-revision/workflow.json

striatum --repo "$TARGET" workflow validate "$WF" --json

striatum --repo "$TARGET" run prepare --workflow "$WF" --json
```

## Execution Notes

1. Run `review_revision_anchor` first. It carries forward the 0041 blocker
   context and creates the source artifact that feeds all three first-pass
   reviews.
2. Run the three review lanes in parallel: traceability, browser acceptance,
   and ops/tests.
3. If any first-pass review records `needs_revision`, the declared cycle routes
   back to `review_revision_anchor` once and then re-runs that review attempt.
4. After accepting review verdicts, run the ledger, then Codex implementation,
   then final review.
5. If final review records `needs_revision`, the workflow cycles back to Codex
   implementation once.

The implementation slice should stay conservative: local browser acceptance and
hosted-demo documentation, with no real CFD, hosted worker, custom JavaScript
frontend, or full dashboard-parity implementation unless the ledger explicitly
accepts that expansion.
