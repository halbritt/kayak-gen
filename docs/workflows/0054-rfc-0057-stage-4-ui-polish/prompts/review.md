# Review Prompt

Read the workflow runbook, changed files, implementation patch summaries,
`STAGE_4_DECISIONS.md`, RFC 0057, and the project's no-claims rules.

Review for your role's concern. Findings must be actionable and grounded in
file paths or artifacts. Use `accept_with_findings` for issues the
remediation lane can fix. Use `needs_revision` only when the workflow scope
is invalid, unsafe, or impossible to remediate in the current run.

Stage-4 specific review concerns to verify against your role:

- Form-builder respects the live admissibility filter (display-only metrics
  never appear in the objective picklist; claim-admissibility refusals
  surface inline).
- 2D scatter + sortable table sync stays inside the existing forbidden-copy
  scrub set. Color coding does not introduce new claim-state literals.
- Auto-poll cadence is cancellable and does not duplicate manual refreshes.
- `kayakgen serve` default flip from in-process to subprocess is documented
  and the `--jobs-in-process` opt-in works.
- Log redaction strips `$HOME` and the resolved `jobs_root` prefix without
  changing behavior for redaction-free payloads.
- Fork-with-seed reuses `manager.start` rather than introducing a new
  manager class; the source job's claim state and read-model semantics
  are unchanged.

Publish the required finding artifact and verdict.
