# Workflow 0018 - Deferred Backlog Structure

## Purpose

This workflow does not start implementation. It turns the remaining known work
into an ordered Striatum-ready queue, drafts missing RFCs, and records where
future implementors should use multi-agent review and implementation splits.

## Operator Instructions

1. Read `AGENTS.md`, `docs/rfcs/README.md`, RFCs 0004, 0006, 0008, 0010, 0011,
   0012, 0013, and the new RFC drafts created by this workflow.
2. Treat existing RFCs as the source of truth where they already cover the work.
3. Create new RFCs only for new load-bearing decisions.
4. Keep the queue ordered by dependency, not by ease.
5. For every implementation workflow, include an implementor prompt that
   encourages the maximal number of useful sub-agents with disjoint write
   scopes.
6. Update `OPERATOR_REPORT.md` before compaction or handoff.

## Non-Goals

- Do not register a Striatum run.
- Do not claim work.
- Do not implement the queued workflows.
- Do not change runtime behavior.
