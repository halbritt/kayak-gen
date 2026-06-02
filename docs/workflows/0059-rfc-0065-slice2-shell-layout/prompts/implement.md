# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0065-ui-polish-redesign.md` — §2 and the "Slice 2 observable"
  Acceptance Criteria.
- `docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md` — the
  affirmed Slice 2 decisions (D1–D8); these are your spec.
- `kayakgen/ui/theme.py` (the Slice 1 tokens + `TYPOGRAPHY` roles),
  `kayakgen/ui/web/app.py`, and the Generate-panel modules.
- `tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
  `tests/test_ui_theme.py`.

Implement Slice 2 only. Requirements:

- Stay strictly inside the allowed paths.
- Re-flow the three-region shell, toolbar, four status segments, and Generate
  panel onto the Slice 1 tokens and one typographic hierarchy (D2). Styling is
  token-only (D1): add no new inline dimension/radius/elevation/border/colour
  literal; the widened `tests/test_ui_theme.py` orphan lint must stay green. If a
  genuine token gap appears, add it additively to `theme.py` (both palettes if
  colour-bearing, `CONTRAST_MANIFEST` covered if colour-bearing, lint extended).
- Preserve the region/status contract (D3) and the 1440×900 first-viewport +
  ≤960 px collapse contract (D4); restyle the collapse, do not remove it; keep the
  mobile posture conservative.
- Hook discipline (D5): you MAY rename/move/remove any hook except the region,
  status, and collapse hooks — but reflect EVERY change in `tests/test_web_layout.py`
  (and `tests/test_web_inline_help.py` for inline-help hooks) in this slice. No
  assertion may be left pointing at a removed hook; every new hook gets a positive
  assertion.
- Claim line byte-stable (D6): touch no `CHIP_*` text/class, recolour no chip,
  keep every persistent caption byte-identical, keep the no-go list absent.
- RFC 0032 boundary intact (D7): add no route or claim/readiness/accepted_uses
  literal.
- Docs: `CHANGELOG.md` only; do not touch `USER_GUIDE.md` / `WEB_VERIFICATION.md`;
  do not ratify D047 (D8).
- Add no module-level network or filesystem side effects.

Before editing, split your work into the maximal useful number of disjoint
sub-agent tasks inside the packet write scope (e.g. shell + toolbar + status bar
in `app.py`; the Generate-panel modules; the layout-test reflection). Run
`tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
`tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the full repo suite
(minus the env-gated smoke). Publish the required patch summary artifact with the
exact Striatum front matter and byline, enumerating (a) the files actually
changed, (b) the typographic-role mapping applied per region, (c) the exact list
of `data-testid` / `kg-*` hooks renamed/moved/removed and the corresponding test
edits, (d) any token added additively to `theme.py` and why, and (e) the targeted
test invocation that proved the slice green.
