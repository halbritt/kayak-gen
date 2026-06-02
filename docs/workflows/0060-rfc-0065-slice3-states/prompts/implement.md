# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0065-ui-polish-redesign.md` — §3 and the "Slice 3 observable"
  Acceptance Criteria.
- `docs/workflows/0060-rfc-0065-slice3-states/SLICE_3_DECISIONS.md` — the affirmed
  Slice 3 decisions (D1–D8); these are your spec.
- `docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md` and its
  findings ledger — the Slice 2 layout contract you preserve, and **ledger S1**
  (reintroduce uniform focus styling in Slice 3) which authorises your D1 pass.
- `kayakgen/ui/theme.py` (Slice 1 state + focus-ring tokens),
  `kayakgen/ui/web/app.py`, and the Generate-panel modules.
- `tests/test_web_layout.py` (layout hooks + the forbidden-copy scan to extend),
  `tests/test_web_inline_help.py`, `tests/test_ui_theme.py`.

Implement Slice 3 only. Requirements:

- Stay strictly inside the allowed paths.
- Uniform control states (D1) from Slice 1 tokens across every button/select/
  slider/toggle/tab — including reintroducing the focus-ring/`:focus-visible`
  treatment uniformly (deferred out of Slice 2).
- Honestly-disabled controls stay disabled with byte-identical copy (D2):
  watertight-solid, disabled `EXPORT_MENU_ROWS` (keep `aria-disabled`), Cm
  reserved-preset, `generative_submit_disabled` + blocking-reason copy.
- Explicit, consistent empty/loading/error states with stable, tested
  `data-testid` hooks for the Generate jobs table, frontier scatter, Comparison,
  Mesh, CFD (both banners intact), and Share-URL / invalid-hull (D3). State copy
  is unchanged.
- Copy byte-stable (D4): no `CHIP_*` change, no chip recoloured, every persistent
  caption byte-identical; no failed/empty state reads as a successful claim.
- Hook discipline + token-only styling (D5): reflect every hook change in
  `tests/test_web_layout.py` + `tests/test_web_inline_help.py`; add no new inline
  literal (orphan lint green); any new `theme.py` token is additive. Preserve the
  Slice 2 region/status/collapse/first-viewport contract.
- Extend the forbidden-copy / no-go scan in `tests/test_web_layout.py` to every
  new rendered string (state messages, ARIA labels, tooltips) (D6).
- RFC 0032 boundary intact (D7): add no route or claim/readiness/accepted_uses
  literal.
- Docs: `CHANGELOG.md` only; do not touch `USER_GUIDE.md` / `WEB_VERIFICATION.md`;
  do not ratify D047 (D8).
- Loading-state tests must be deterministic — no real timers / `time.sleep`.

Before editing, split your work into the maximal useful number of disjoint
sub-agent tasks inside the packet write scope (control states; the jobs-table /
frontier states; the comparison/mesh/cfd/share-url states; the test reflection +
forbidden-copy extension). Run `tests/test_web_layout.py`,
`tests/test_web_inline_help.py`, `tests/test_ui_theme.py`, the desktop
rendered-bbox tests, and the full repo suite (minus the env-gated smoke; the known
NB-2 services-import-boundary failure is pre-existing and out of scope). Publish
the required patch summary artifact with the exact Striatum front matter and
byline, enumerating (a) files changed, (b) the control-state token mapping, (c)
the per-panel empty/loading/error hooks added and their test assertions, (d) the
forbidden-copy strings added to the scan, (e) any token added additively to
`theme.py`, and (f) the targeted test invocation proving the slice green.
