# RFC 0065 Slice 1 — Theme/Visual-System Foundation: Affirmed Decisions

These are the RFC-derived, operator-affirmed decisions that Slice 1 implements.
They are the authoritative spec for the implementer and the yardstick for every
reviewer. Source: `docs/rfcs/0065-ui-polish-redesign.md` §1 ("Visual system:
complete the theme module") and the "Slice 1 observable" Acceptance Criteria.

Slice 1 is **additive and presentation-only**. It extends the token vocabulary;
it changes no layout, no behaviour, and no claim copy. Each decision below is a
hard gate.

## D1 — Additive token extension only

`kayakgen/ui/theme.py` gains new named token maps **without renaming, removing,
or re-typing** any existing token (`COLORS_LIGHT`, `COLORS_DARK`, `TYPOGRAPHY`,
`PLOT_PALETTE`, `CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES`,
`CONTRAST_MANIFEST`, and the existing helpers). The module stays the single
public surface.

## D2 — New token families

Add, as named Python maps emitted as CSS variables:

- `SPACING` — a spacing scale on one consistent step (e.g. a 4 px base,
  `space-0 … space-7`) for panel padding, gaps, and inset rhythm.
- `DENSITY` — control-height, row-height, and table-row-padding tokens so the
  desktop-dense layout and the ≤960 px collapse share one definition.
- `RADII`, `ELEVATION`, `BORDERS` — corner-radius, shadow/elevation, and
  border-width/edge tokens for cards, chips, selects, and the metrics strip.
- A **focus-ring token**: a `--state-focus-ring` colour plus a ring width.
- **State tokens**: named hover / active / disabled surface and text tokens.

## D3 — Both palettes resolve

Every new **colour-bearing** token (focus-ring colour; state hover/active/
disabled surface + text) is defined in **both** `COLORS_LIGHT` and
`COLORS_DARK`. Dimensionless tokens (spacing, radius, density, border width,
elevation, ring width) are palette-independent single maps. No new token may be
defined in only one palette.

## D4 — Helpers emit the new tokens

- `css_root_block(dark=False)` emits the new CSS variables (palette-independent
  dimension tokens once; colour tokens per palette).
- `vuetify_theme_config()` maps the new state/focus tokens onto the Vuetify 3
  theme registry.
- `matplotlib_rc_params()` and `vtk_background_rgb(dark=False)` keep their
  current behaviour (desktop token inheritance is unchanged); the desktop
  rendered-bbox tests stay green as the proof.

## D5 — Contrast manifest covers the new tokens

`CONTRAST_MANIFEST` gains pairs so the focus ring is visible against
`surface-panel` and `surface-viewport-bg`, and the state surface/text tokens
clear their minimum ratios — in **both** palettes. Every pair passes
`tests/test_ui_theme.py::test_contrast_manifest_clears_thresholds`.

## D6 — Orphan-literal lint widened, and the repo made clean against it

The RFC 0033 §6 invariant widens from "colour literals" to "colour **and**
spacing / radius / elevation / border / focus literals". Extend the
`tests/test_ui_theme.py` orphan scan so a raw dimension literal (`px` / `rem` /
`em`), a `border-radius` / `box-shadow` / `outline`(-width) literal, or a
focus-ring literal **outside `theme.py`** under `kayakgen/ui/` fails the test.
The handful of existing inline dimension literals (today in
`kayakgen/ui/web/app.py` and `kayakgen/ui/web/generate_frontier_view.py`) are
migrated to the new tokens so the widened lint passes. The lint must demonstrably
fail on a planted literal (include the negative case in the test).

## D7 — No layout, behaviour, or claim change

Token values **equal** the literals they replace; the rendered shell is visually
unchanged. No `data-testid` / `kg-*` hook is renamed or moved (that is Slice 2).
`CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` and every persistent caption are
byte-identical. No chip is recoloured. No new REST route, `claim_state`,
`Readiness`, or `accepted_uses` literal (RFC 0032 boundary intact). The RFC 0033
§8 no-go list stays absent from rendered output.

## D8 — Docs footprint is CHANGELOG only

Slice 1 updates `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md` only.
`docs/USER_GUIDE.md` and `docs/WEB_VERIFICATION.md` are **not** touched (their
updates belong to Slice 4, which lands the harness those docs would describe).
DECISION_LOG row **D047** is **not** ratified here (Slice 4).

## Out of scope (later slices)

Shell layout & information hierarchy (Slice 2); control + empty/loading/error
states (Slice 3); the Playwright/Chromium visual-regression + a11y harness and
the D047 baseline procedure (Slice 4); desktop visual polish (Slice 5, deferred,
operator-gated per D009 / D021).
