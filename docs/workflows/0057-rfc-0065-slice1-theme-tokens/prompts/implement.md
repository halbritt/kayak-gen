# Implementation Prompt

Read the packet objective, write scope, context docs, and:

- `docs/rfcs/0065-ui-polish-redesign.md` — §1 and the "Slice 1 observable"
  Acceptance Criteria.
- `docs/workflows/0057-rfc-0065-slice1-theme-tokens/SLICE_1_DECISIONS.md` — the
  affirmed Slice 1 decisions (D1–D8); these are your spec.
- `kayakgen/ui/theme.py`, `tests/test_ui_theme.py`, and the inline dimension
  literals in `kayakgen/ui/web/app.py` and
  `kayakgen/ui/web/generate_frontier_view.py`.

Implement Slice 1 only. Requirements:

- Stay strictly inside the allowed paths.
- Additive token extension (D1): rename, remove, or re-type no existing token.
- Add `SPACING` / `DENSITY` / `RADII` / `ELEVATION` / `BORDERS`, the focus-ring
  token, and the state tokens (D2); colour-bearing tokens resolve in both
  palettes, dimensionless tokens are single maps (D3).
- Grow `css_root_block` and `vuetify_theme_config` to emit them (D4); leave the
  `matplotlib_rc_params` / `vtk_background_rgb` behaviour unchanged.
- Extend `CONTRAST_MANIFEST` for the focus ring + state tokens, clearing
  thresholds in both palettes (D5).
- Widen the orphan-literal lint (D6) so a raw dimension / radius / shadow / focus
  literal outside `theme.py` under `kayakgen/ui/` fails; migrate the existing
  inline literals so the clean tree passes. The lint must fail on a planted
  literal — include that negative case in the test.
- No layout / behaviour / claim change (D7): token values equal the literals they
  replace; rename or move no hook; touch no `CHIP_*` entry or caption; recolour
  no chip; add no route or claim/readiness literal.
- Docs: `CHANGELOG.md` only; do not touch `USER_GUIDE.md` / `WEB_VERIFICATION.md`
  (D8).
- Add no module-level network or filesystem side effects.

Before editing, split your work into the maximal useful number of disjoint
sub-agent tasks inside the packet write scope. Run `tests/test_ui_theme.py`, the
desktop rendered-bbox tests, and the full repo suite (minus the env-gated smoke).
Publish the required patch summary artifact with the exact Striatum front matter
and byline, enumerating (a) the files actually changed, (b) the lint/contrast
tests added or widened, (c) the targeted test invocation that proved the slice
green, and (d) the exact list of inline literals migrated.
