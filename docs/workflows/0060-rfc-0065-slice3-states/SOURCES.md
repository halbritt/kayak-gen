# Sources — Workflow 0060 (RFC 0065 Slice 3)

- `docs/rfcs/0065-ui-polish-redesign.md` — authoritative spec. Slice 3 = §3
  ("Control states and empty / loading / error states") + the "Slice 3
  observable" Acceptance Criteria.
- `docs/rfcs/README.md` — RFC index entry 0065.
- `docs/rfcs/0033-workspace-ui-rework.md` — §2 Share-URL/invalid-hull banners,
  §8 no-go claim list.
- `docs/DECISION_LOG.md` — D047 (committed-baseline visual-regression strategy;
  ratified at Slice 4, **not** here).
- `docs/WEB_VERIFICATION.md` — internal `data-testid` hook contract (read-only;
  not modified by Slice 3).
- `docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md` and its
  findings ledger — Slice 2 layout contract Slice 3 builds on; **ledger S1**
  ("reintroduce uniform focus styling in Slice 3") is the authority for Slice 3's
  D1 control focus-state pass.
- `kayakgen/ui/theme.py` — Slice 1 state + focus-ring tokens Slice 3 consumes.
- `kayakgen/ui/web/app.py` — control surfaces, `EXPORT_MENU_ROWS` (disabled rows),
  `watertight-solid` copy, `generative_submit_disabled`, and the state hooks
  (`mesh-no-package-chip`, `mesh-live-readiness-chip`, `comparison-*-block`,
  `share-url-state`).
- `kayakgen/ui/web/generate_spec_form.py`, `generate_frontier_view.py`,
  `generate_state_listener.py` — the Generate jobs table and frontier scatter
  states (empty / loading / failed via `GenerativeJobError.kind` / cancelled /
  resumable).
- `tests/test_web_layout.py` — the layout/hook contract AND the forbidden-copy /
  no-go scan to extend; `tests/test_web_inline_help.py` — inline-help hooks;
  `tests/test_ui_theme.py` — the widened orphan-literal lint.
- `docs/workflows/0060-rfc-0065-slice3-states/SLICE_3_DECISIONS.md` — the affirmed
  Slice 3 decisions (D1–D8).
