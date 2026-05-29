# Operator report - workflow 0042

Updated: 2026-05-13

> **Note on stale tooling references.** Striatum has since migrated from
> a Python package (`.venv/bin/striatum`) to a Go binary
> (`~/.local/bin/striatum`, built via `make install` from
> `~/git/striatum/`). The `STRIATUM_DAEMON_REQUIRED=0`
> `STRIATUM_TEST_HARNESS=1` env prefix below was a v1.x test-harness mode
> that no longer exists in v2.7.x. Any historical command line below is
> preserved as provenance for the original run; for a current invocation
> see the active RUNBOOKs.

## Current state

- Workflow scaffold created for `0042-design-constraint-surfacing-revision`.
- Scope targets RFC 0031, which supersedes RFC 0029 as the implementation
  target for design-constraint surfacing.
- The workflow uses a `review_remediation` synthesis job before the three
  review lanes so first-pass `needs_revision` verdicts have a declared
  Striatum cycle.
- The workflow preserves the three review lanes: traceability, domain, and
  ops/test.
- Validation passed with
  `STRIATUM_DAEMON_REQUIRED=0 STRIATUM_TEST_HARNESS=1 /home/halbritt/git/kayak-gen/.venv/bin/striatum --repo . workflow validate docs/workflows/0042-design-constraint-surfacing-revision/workflow.json`.
- No runtime product code or root status documents were changed by this
  scaffold.

## Next action

- Start the Striatum run after RFC 0031 is accepted or amended.
