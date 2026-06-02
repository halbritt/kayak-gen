# Review Prompt

Read the workflow runbook, the changed files, the implementer patch summary,
`SLICE_1_DECISIONS.md`, RFC 0065 §1, and the project's no-claims rules.

Review for your role's concern. Findings must be actionable and grounded in file
paths or artifacts. Use `accept_with_findings` for issues the remediation lane
can fix. Use `needs_revision` only when the workflow scope is invalid, unsafe, or
impossible to remediate in the current run.

Slice-1-specific checks to verify against your role:

- The token extension is additive; no existing token is renamed, removed, or
  re-typed.
- New colour-bearing tokens resolve in both palettes; `CONTRAST_MANIFEST` covers
  the focus ring + state tokens and clears thresholds in both.
- The widened orphan-literal lint fails on a planted literal and passes on the
  clean tree; the inline dimension literals were migrated to tokens of equal
  value, not deleted with their effect.
- No layout / hook / claim change: hooks unmoved; `CHIP_*` and captions
  byte-stable; no chip recoloured; no new route / claim-state / readiness literal.
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` are untouched; DECISION_LOG
  D047 is not ratified here.

Publish the required finding artifact and verdict.
