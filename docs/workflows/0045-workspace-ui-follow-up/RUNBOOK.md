# Runbook

1. Validate the workflow:

   ```bash
   STRIATUM_DAEMON_REQUIRED=0 STRIATUM_TEST_HARNESS=1 \
     .venv/bin/striatum --repo . workflow validate \
     docs/workflows/0045-workspace-ui-follow-up/workflow.json
   ```

2. Prepare/start the run from `main`.
3. Launch first-pass review lanes in parallel.
4. Publish only curated artifacts without falsified bylines.
5. Use the findings ledger to gate Codex implementation.
6. Require final review before fast-forwarding `main`.
