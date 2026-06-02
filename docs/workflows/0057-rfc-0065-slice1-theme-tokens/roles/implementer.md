# Role: Implementer (RFC 0065 Slice 1 — theme-token foundation)

Implement Slice 1 of RFC 0065: extend `kayakgen/ui/theme.py` into a complete
visual-token system and make the repo clean against the widened orphan-literal
lint. This is a single coherent slice landing as one commit; there is no other
parallel author track and no integrator.

Deliver, strictly inside the write scope:

- The new token families in `theme.py` — `SPACING`, `DENSITY`, `RADII`,
  `ELEVATION`, `BORDERS`, the focus-ring token, and the state tokens — per
  `SLICE_1_DECISIONS.md` D2/D3, defined in both palettes where colour-bearing.
- `css_root_block` / `vuetify_theme_config` grown to emit them (D4); the
  `matplotlib_rc_params` / `vtk_background_rgb` helpers unchanged in behaviour.
- `CONTRAST_MANIFEST` pairs for the focus ring and state tokens that clear their
  thresholds in both palettes (D5).
- The widened `tests/test_ui_theme.py` orphan scan (D6): it must FAIL on a
  planted dimension/radius literal outside `theme.py` and PASS once you migrate
  the existing inline literals in `kayakgen/ui/web/app.py` and
  `kayakgen/ui/web/generate_frontier_view.py` to the new tokens.
- A `CHANGELOG.md` entry.

Hard invariants (D7): token values equal the literals they replace — no visual
change. Do not rename or move any `data-testid` / `kg-*` hook. Do not touch any
`CHIP_*` text/class or any persistent caption. Do not recolour a chip. Do not add
a REST route or any `claim_state` / `Readiness` / `accepted_uses` literal. Do not
touch `docs/USER_GUIDE.md` or `docs/WEB_VERIFICATION.md` (D8).

Use the maximal useful number of sub-agents for parallel reading/verification,
but keep the final patch inside the packet write scope. Run
`tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the full repo
suite (minus any env-gated smoke) before publishing. Publish the patch summary
with the exact packet byline; enumerate (a) files changed, (b) the lint/contrast
tests added or widened, (c) the targeted test invocation proving the slice green,
and (d) the exact list of inline literals migrated.
