# Sources — Workflow 0059 (RFC 0065 Slice 2)

- `docs/rfcs/0065-ui-polish-redesign.md` — authoritative spec. Slice 2 = §2
  ("Information hierarchy across the shell") + the "Slice 2 observable"
  Acceptance Criteria.
- `docs/rfcs/README.md` — RFC index entry 0065.
- `docs/rfcs/0033-workspace-ui-rework.md` — the three-region shell, the
  first-viewport contract, the §8 no-go claim list.
- `docs/DECISION_LOG.md` — D047 (committed-baseline visual-regression strategy;
  ratified at Slice 4, **not** here).
- `docs/WEB_VERIFICATION.md` — the `data-testid` hook contract is internal, not a
  public API (read-only context; not modified by Slice 2).
- `kayakgen/ui/theme.py` — the Slice 1 token vocabulary Slice 2 consumes
  (`SPACING` / `DENSITY` / `RADII` / `ELEVATION` / `BORDERS` / focus-ring / state)
  and the `TYPOGRAPHY` roles.
- `kayakgen/ui/web/app.py` — the three-region shell, toolbar, four status
  segments (`STATUS_SEGMENTS`: package / readiness / resistance / cfd),
  `LAYOUT_TEST_IDS`, `REGION_CLASSES`, and the Review tabs.
- `kayakgen/ui/web/generate_spec_form.py`, `generate_frontier_view.py`,
  `generate_fork_button.py`, `generate_state_listener.py` — the Generate panel.
- `tests/test_web_layout.py` — the layout/hook contract that must reflect every
  hook rename/move; `tests/test_web_inline_help.py` — inline-help hooks;
  `tests/test_ui_theme.py` — the widened orphan-literal lint that keeps styling
  token-only.
- `docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md` — the
  affirmed Slice 2 decisions (D1–D8).
- `docs/workflows/0057-rfc-0065-slice1-theme-tokens/` — the landed Slice 1
  (token foundation Slice 2 builds on).
