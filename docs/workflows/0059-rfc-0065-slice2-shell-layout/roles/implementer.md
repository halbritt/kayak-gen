# Role: Implementer (RFC 0065 Slice 2 — shell layout & information hierarchy)

Implement Slice 2 of RFC 0065: re-flow the three-region web shell, the toolbar,
the four status-bar segments, and the Generate panel onto the Slice 1 theme
tokens and one typographic hierarchy. This is a single coherent slice landing as
one commit; there is no other parallel author track and no integrator.

Deliver, strictly inside the write scope:

- The shell (`region-params` / `region-geometry` / `region-review`), the toolbar,
  the four status segments (package / readiness / resistance / cfd), and the
  Generate panel (build / watch / pick) re-flowed onto the Slice 1 tokens
  (`SPACING` / `DENSITY` / `RADII` / `ELEVATION` / `BORDERS` / focus-ring / state)
  with consistent section rhythm and card/strip density (D1).
- One typographic hierarchy: the `TYPOGRAPHY` roles (`type-display` /
  `type-heading` / `type-label` / `type-body` / `type-caption` / `type-metric`)
  applied consistently so heading weight signals section importance the same way
  in every panel (D2).
- The region/status contract preserved (D3); the 1440×900 first-viewport and
  ≤960 px collapse contract preserved and restyled, not removed (D4); conservative
  mobile posture.
- Every renamed/moved/removed `data-testid` / `kg-*` hook reflected in
  `tests/test_web_layout.py` (+ `tests/test_web_inline_help.py` for inline-help
  hooks) in this slice (D5).
- A `CHANGELOG.md` entry.

Hard invariants: styling is token-only — add no new inline dimension/radius/
elevation/border/colour literal; the widened orphan lint stays green; any new
`theme.py` token is additive (D1). Claim line byte-stable: touch no `CHIP_*`
text/class, recolour no chip, keep every persistent caption byte-identical, keep
the RFC 0033 §8 no-go list absent (D6). Add no REST route or `claim_state` /
`Readiness` / `accepted_uses` literal (D7). Do not touch `docs/USER_GUIDE.md` or
`docs/WEB_VERIFICATION.md`; do not ratify D047 (D8).

Use the maximal useful number of sub-agents for disjoint reading/verification and
disjoint edit regions, but keep the final patch inside the packet write scope. Run
`tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
`tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the full repo suite
(minus any env-gated smoke) before publishing. Publish the patch summary with the
exact packet byline; enumerate (a) files changed, (b) the typographic-role mapping
per region, (c) the exact list of hooks renamed/moved/removed and the matching
test edits, (d) any token added additively to `theme.py` and why, and (e) the
targeted test invocation proving the slice green.
