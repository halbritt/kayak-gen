# Role: Implementer (RFC 0065 Slice 3 — control + empty/loading/error states)

Implement Slice 3 of RFC 0065: make control interaction states and per-panel
empty/loading/error states uniform and explicit. This is a single coherent slice
landing as one commit; there is no other parallel author track and no integrator.

Deliver, strictly inside the write scope:

- Uniform default/hover/focus/active/disabled treatment for every button, select,
  slider, toggle, and tab, sourced from the Slice 1 state + focus-ring tokens —
  including reintroducing the focus-ring/`:focus-visible` treatment uniformly
  (deferred out of Slice 2 per workflow 0059 ledger S1) (D1).
- Honestly-disabled controls kept disabled with byte-identical copy: the
  watertight-solid readiness option, the disabled `EXPORT_MENU_ROWS` rows (keep
  `aria-disabled`), the Cm reserved-preset, and `generative_submit_disabled` +
  blocking-reason copy (D2).
- Explicit, consistent empty/loading/error states with stable, tested
  `data-testid` hooks for the Generate jobs table (empty/running/failed via
  `GenerativeJobError.kind`/cancelled/resumable), the Pareto frontier scatter
  (loading/empty/rendered), Comparison (no-report vs present), Mesh
  (`mesh-no-package-chip` vs `mesh-live-readiness-chip`), CFD (no-job vs status,
  both banners intact), and the Share-URL (`share-url-state`) + invalid-hull
  banners (D3). State copy unchanged.
- Every hook change reflected in `tests/test_web_layout.py` +
  `tests/test_web_inline_help.py`; the forbidden-copy scan extended to every new
  rendered string (D5, D6).
- A `CHANGELOG.md` entry.

Hard invariants: styling is token-only (no new inline literal; orphan lint green;
any new `theme.py` token additive). Copy byte-stable (D4): no `CHIP_*` change, no
chip recoloured, every persistent caption byte-identical, no failed/empty state
reading as a successful claim. Preserve the Slice 2 region/status/collapse/
first-viewport contract. Add no REST route or `claim_state` / `Readiness` /
`accepted_uses` literal (D7). Do not touch `docs/USER_GUIDE.md` or
`docs/WEB_VERIFICATION.md`; do not ratify D047 (D8). Loading-state tests must be
deterministic (no real timers / sleeps).

Use the maximal useful number of sub-agents for disjoint edit regions, but keep
the final patch inside the packet write scope. Run `tests/test_web_layout.py`,
`tests/test_web_inline_help.py`, `tests/test_ui_theme.py`, the desktop
rendered-bbox tests, and the full repo suite (minus the env-gated smoke; NB-2 is
pre-existing/out of scope). Publish the patch summary with the exact packet byline;
enumerate (a) files changed, (b) the control-state token mapping, (c) the per-panel
state hooks + their test assertions, (d) the forbidden-copy strings added, (e) any
additive `theme.py` token, and (f) the targeted test invocation proving the slice
green.
