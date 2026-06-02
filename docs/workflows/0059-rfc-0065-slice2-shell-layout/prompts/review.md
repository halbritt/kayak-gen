# Review Prompt

Read the workflow runbook, the changed files, the implementer patch summary,
`SLICE_2_DECISIONS.md`, RFC 0065 §2, and the project's no-claims rules.

Review for your role's concern. Findings must be actionable and grounded in file
paths or artifacts. Use `accept_with_findings` for issues the remediation lane
can fix. Use `needs_revision` only when the workflow scope is invalid, unsafe, or
impossible to remediate in the current run.

Slice-2-specific checks to verify against your role:

- Styling is token-only — no new inline dimension/radius/elevation/border/colour
  literal; the widened orphan-literal lint stays green (D1). Any new `theme.py`
  token is additive and both-palette/contrast-covered.
- The `TYPOGRAPHY` roles are applied consistently across regions; heading weight
  signals importance the same way everywhere (D2).
- The region (`region-params`/`-geometry`/`-review`) and status (the four
  `status-*` segments + `workspace-status-bar`) hooks survive (D3); the 1440×900
  first-viewport contract and the ≤960 px collapse hooks hold and the collapse is
  restyled, not removed; mobile posture stays conservative (D4).
- EVERY renamed/moved/removed `data-testid` / `kg-*` hook is reflected in
  `tests/test_web_layout.py` (and `tests/test_web_inline_help.py` where relevant);
  no orphaned assertion, a positive assertion for each new hook (D5).
- Claim line byte-stable: `CHIP_*` and every persistent caption unchanged; no chip
  recoloured; no new route/claim-state/readiness literal; the §8 no-go list absent
  (D6, D7).
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` untouched; DECISION_LOG D047
  not ratified here (D8).

Publish the required finding artifact and verdict.
