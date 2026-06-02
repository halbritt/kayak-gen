# Review Prompt

Read the workflow runbook, the changed files, the implementer patch summary,
`SLICE_0_DECISIONS.md`, the RFC 0065 Slice 0 line + §5, and the project rules.

Review for your role's concern. Findings must be actionable and grounded in file
paths or artifacts. Use `accept_with_findings` for fixable issues; use
`needs_revision` only when the scope is invalid, unsafe, or impossible to
remediate this run.

Slice-0 checks against your role:

- Capture at all three viewports with the 3D region masked out of the diff.
- Compare is advisory in Slice 0 (not a hard gate; the gate is Slice 4); missing
  Playwright/Chromium is a SKIP.
- Committed baselines are of the current shell; `--update-visual-baselines`
  regenerates them; the `visual_baselines/README.md` records canonical env + regen.
- No `kayakgen/ui/` source / layout / hook / claim change; `USER_GUIDE.md` /
  `WEB_VERIFICATION.md` untouched; D047 not ratified here.
- Behavioural browser-acceptance checks and the rest of the suite stay green.

Flag any env-fragility likely to false-positive the next slice's diff and
recommend a tolerance/canonical-env path. Publish the finding artifact + verdict.
