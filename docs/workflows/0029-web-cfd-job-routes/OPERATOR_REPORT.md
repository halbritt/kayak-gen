# Operator report - workflow 0029

Updated: 2026-05-13

## Current state

- Queue item 0029 is `0029-web-cfd-job-routes`.
- Scope targets RFC 0008, RFC 0015, and proposed RFC 0018.
- Workflow purpose: expose CFD job preparation, status, and artifact inspection
  in the web frontend over the existing local dispatch contract without
  implying solver success or validated physics.
- Scaffold created with three required review lanes before implementation:
  traceability, browser/domain, and ops/test.
- Implementation lane is Codex-preferred and preserves the exact
  maximal-subagents instruction from `docs/workflows/0018-deferred-backlog/QUEUE.md`.
- This scaffold does not edit shared docs or runtime code.

## Next action

- Validate the workflow JSON.
- Start the Striatum run after RFC 0018 is accepted or amended.
