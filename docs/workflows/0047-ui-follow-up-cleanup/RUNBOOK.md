# Workflow 0047 Runbook

Purpose: turn the UI follow-up findings from workflows 0045 and 0046 into a
small successor RFC, review it across four lanes, and implement only the
ledger-approved cleanup slice.

1. Run `rfc_scope` first. It drafts RFC 0035 from existing final-review
   findings and updates workflow-local notes; it must not implement runtime
   behavior.
2. Run four first-pass reviews in parallel: traceability, no-claims,
   ergonomics/design, and ops/test.
3. Consolidate the findings ledger.
4. Implement the ledger with Codex, using maximal useful sub-agents with
   disjoint write scopes.
5. Run final review before landing.
6. Operator records findings, updates `OPERATOR_REPORT.md`, commits, pushes,
   fast-forwards `main`, and prunes merged branches.
