# Workflow 0046 Runbook

Purpose: fix the reported slider-label visibility problem without broad UI
redesign or backend scope expansion.

1. Run the three first-pass reviews in parallel: traceability, ergonomics and
   design, and ops/test.
2. Consolidate a narrow implementation ledger.
3. Implement the ledger with Codex, using maximal useful sub-agents with
   disjoint write scopes.
4. Run a final review before landing.
5. Operator records findings, updates `OPERATOR_REPORT.md`, commits, pushes,
   fast-forwards `main`, and prunes merged branches.
