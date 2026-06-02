# Review Prompt

Read the workflow runbook, the changed files, the implementer patch summary,
`SLICE_3_DECISIONS.md`, RFC 0065 §3, and the project's no-claims rules.

Review for your role's concern. Findings must be actionable and grounded in file
paths or artifacts. Use `accept_with_findings` for issues the remediation lane
can fix. Use `needs_revision` only when the workflow scope is invalid, unsafe, or
impossible to remediate in the current run.

Slice-3-specific checks to verify against your role:

- Control states (default/hover/focus/active/disabled) derive from Slice 1 tokens
  and apply uniformly across buttons/selects/sliders/toggles/tabs (D1).
- Honestly-disabled controls stay disabled and keep byte-identical copy
  (watertight-solid, disabled `EXPORT_MENU_ROWS` + `aria-disabled`, Cm
  reserved-preset, `generative_submit_disabled` + blocking-reason copy) (D2).
- Each panel renders an explicit, consistent empty/loading/error state with a
  stable, tested `data-testid` hook (D3); state copy is byte-stable (D4) and no
  failed/empty state reads as a successful/validated claim.
- Styling is token-only (orphan lint green); any new `theme.py` token is additive;
  every hook change is reflected in `tests/test_web_layout.py` +
  `tests/test_web_inline_help.py`; the Slice 2 region/status/collapse/first-viewport
  contract holds (D5).
- The forbidden-copy / no-go scan in `tests/test_web_layout.py` was extended to
  every new rendered string and stays green (D6).
- No new route/claim-state/readiness literal; `CHIP_*` + captions byte-stable;
  the §8 no-go list absent (D4, D7).
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` untouched; D047 not ratified
  (D8). The known NB-2 services-import-boundary failure is out of scope.

Publish the required finding artifact and verdict.
