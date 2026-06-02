# Review: Traceability to RFC 0065 Slice 1 decisions
author: reviewer-traceability-claude-opus-4.8-001

## Objective

Verify every workflow 0057 change traces to RFC 0065 §1 ("Visual system:
complete the theme module") and a row of `SLICE_1_DECISIONS.md` (D1–D8). Flag any
scope creep into Slice 2 (layout / information hierarchy), Slice 3 (control or
empty/loading/error state), or Slice 4 (visual-regression harness,
`docs/WEB_VERIFICATION.md` / `docs/USER_GUIDE.md`, DECISION_LOG D047); any
`data-testid` / `kg-*` hook rename or move; any touched `CHIP_*` entry or
persistent caption; any re-typed or removed existing token. Confirm the token
extension is additive and the inline-literal migration is a literal→token
substitution of equal value, not a value change.

## Scope reviewed

Working-tree diff vs `HEAD` (commit `00c8084`):

- `kayakgen/ui/theme.py`  (+86 / −2)
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/generate_frontier_view.py`
- `tests/test_ui_theme.py`
- `CHANGELOG.md`

`git status --porcelain` confirms no other tracked file is modified (only the
above five plus the untracked `striatum/0057-…/` workflow tree).

## Verdict

**accept_with_findings**

Every change traces cleanly to a D1–D8 row; no Slice 2/3/4 scope creep is
present; the extension is additive and the inline-literal migration is
byte-for-byte value-preserving. One non-blocking token-homing observation
(F1) is recorded for the remediation / Slice-2 lane.

## Findings — decision-by-decision traceability

### D1 — Additive token extension only — PASS
`git diff --numstat` on `theme.py` is `86 2`. The only two deleted lines are the
inner `for name, value in TYPOGRAPHY.items()` loop in `css_root_block`, which is
replaced by a loop over `(TYPOGRAPHY, SPACING, DENSITY, RADII, ELEVATION,
BORDERS)` — TYPOGRAPHY emission is preserved, not removed. No existing token map
(`COLORS_LIGHT`, `COLORS_DARK`, `TYPOGRAPHY`, `PLOT_PALETTE`, `CHIP_*`,
`CONTRAST_MANIFEST`) or helper is renamed, removed, or re-typed. All `COLORS_*`
and `CONTRAST_MANIFEST` diff hunks are pure additions.

### D2 — New token families — PASS
All required maps are present in `kayakgen/ui/theme.py`: `SPACING`
(`space-0…space-7`), `DENSITY` (control-height / row-height / table-row-padding
+ migrated component dims), `RADII`, `ELEVATION`, `BORDERS`. The focus-ring token
is present as the `state-focus-ring` colour plus `border-width-focus` /
`state-focus-ring-width` widths. State tokens
(`state-hover|active|disabled-surface|text`) are present.

### D3 — Both palettes resolve — PASS
The seven new colour-bearing tokens (`state-focus-ring`, hover/active/disabled
surface + text) are added to **both** `COLORS_LIGHT` and `COLORS_DARK`.
Dimensionless families (`SPACING`, `DENSITY`, `RADII`, `ELEVATION`, `BORDERS`)
are single palette-independent maps. Asserted green by
`test_new_visual_token_maps_are_additive_and_resolved`.

### D4 — Helpers emit the new tokens — PASS
`css_root_block(dark)` now emits the new dimension/typography maps and (via
`_tokens(dark)`) the per-palette colour tokens. `vuetify_theme_config()` maps
`focus-ring` + the six state surface/text colours and the `focus-ring-width`
variable onto the Vuetify registry. `matplotlib_rc_params()` and
`vtk_background_rgb()` are **not** in the diff — desktop token inheritance is
untouched (D4 / RFC §1 desktop-inheritance clause).

### D5 — Contrast manifest covers the new tokens — PASS
`CONTRAST_MANIFEST` gains `focus.ring.panel` (`state-focus-ring` vs
`surface-panel`, 3.0), `focus.ring.viewport` (vs `surface-viewport-bg`, 3.0),
`state.hover`, `state.active`, and `state.disabled` (3.0). The focus ring is
covered against both required backgrounds.
`test_contrast_manifest_clears_thresholds[light]` and `[dark]` both PASS, so
every pair clears its minimum ratio in both palettes.

### D6 — Orphan-literal lint widened, repo clean — PASS
The scan is widened from colour-only to colour **and** dimension
(`px`/`rem`/`em`), `border-radius` / `box-shadow` / `outline`(-width), and
`focus`(-ring) property literals outside `theme.py`
(`DIMENSION_LITERAL_RE`, `CSS_PROPERTY_NAME_RE`, `FOCUS_PROPERTY_NAME_RE`,
`_css_visual_literal_offenders`). The negative case is included:
`test_visual_literal_lint_fails_on_planted_literal` asserts ≥5 offenders on a
planted file. The clean-tree case
`test_no_orphan_visual_literals_under_kayakgen_ui` PASSes, and an independent
scan confirms every `px/rem/em` literal under `kayakgen/ui/` now lives only in
`theme.py`. The inline migrations are value-preserving (see "Migration
fidelity" below).

### D7 — No layout, behaviour, or claim change — PASS
- **Hooks unmoved.** `app.py` and `generate_frontier_view.py` diffs change only
  `style=` / CSS-string contents; `data-testid` (`share-url-state`,
  `geometry-vtk-view`, `frontier-scatter`) and `kg-*` classes
  (`kg-share-state-probe`, `kg-vtk-frame`, `kg-vtk-viewport`,
  `kg-frontier-section`, `kg-frontier-scatter-svg`, `kg-frontier-point`) are
  byte-stable. No rename/move (Slice 2 boundary intact).
- **Chips / captions byte-stable.** `CHIP_SPECS` / `CHIP_LABELS` /
  `CHIP_CLASSES` and all persistent captions are not in the diff. The
  `_CLAIM_STATE_COLOR_TOKENS` chip-recolour loop in
  `generate_frontier_view.py` is unchanged. No chip recoloured.
- **Boundary intact.** No new REST route, `claim_state`, `Readiness`, or
  `accepted_uses` literal (RFC 0032 boundary). Confirmed in diff and corroborated
  by the claims-lane review.

### D8 — Docs footprint is CHANGELOG only — PASS
Only `CHANGELOG.md` is updated, under `Added`, scoped to the Slice 1 token
foundation and the lint widening, and explicitly disclaiming layout/claim-copy
change. `git diff --name-only HEAD -- docs/USER_GUIDE.md docs/WEB_VERIFICATION.md
docs/DECISION_LOG.md` is empty — protected docs are untouched and DECISION_LOG
row D047 is **not** ratified here (Slice 4 boundary intact).

## Migration fidelity (literal → token, equal value)

Each substitution reconstructs the original CSS string byte-for-byte:

- `app.py` SR probe: `left: -10000px` → `SPACING['screen-reader-offset']`
  (`-10000px`); `width/height: 1px` → `DENSITY['screen-reader-size']` (`1px`).
- `app.py` VTK frame: `height: 520px` → `DENSITY['viewport-height']`;
  `min-height: 480px` → `DENSITY['viewport-min-height']`. Inner view
  `min-height: 480px` → same token; `height/width: 100%` retained as literals
  (`%` is not a linted unit).
- `generate_frontier_view.py`: `gap: 0.75rem` → `SPACING['space-3']`;
  `border: 1px solid` → `BORDERS['border-width-thin'] + " solid"`;
  `border-radius: 4px` → `RADII['radius-sm']`; `max-width: 480px` →
  `DENSITY['frontier-max-width']`; `height: 220px` →
  `DENSITY['frontier-scatter-height']`.

All token values equal the literals they replace (D7 "values **equal** the
literals"). The migrated f-strings interpolate the value out of the literal
segment, so they do not themselves trip the widened lint — confirmed by the
green clean-tree test.

## Scope-creep sweep — NONE FOUND

- Slice 2 (layout / hierarchy / hook rename): none.
- Slice 3 (control or empty/loading/error state): none.
- Slice 4 (harness, `WEB_VERIFICATION.md` / `USER_GUIDE.md`, D047): none.
- Re-typed / removed existing token: none.
- Touched `CHIP_*` / persistent caption / recoloured chip: none.

## Non-blocking finding

**F1 (low / non-blocking) — component-specific dimensions homed in
scale maps.** `DENSITY` (`kayakgen/ui/theme.py`) carries `viewport-height`,
`viewport-min-height`, `frontier-max-width`, `frontier-scatter-height`, and
`screen-reader-size`, and `SPACING` carries `screen-reader-offset`. These are
single-use component dimensions created to host the D6-required inline-literal
migration rather than members of a density/spacing *scale* (D2 lists
control-height / row-height / table-row-padding as DENSITY's intent). This
violates no gate — D2 does not forbid additions, D6 explicitly authorises
migrating these literals into tokens, and the values are preserved — so it is
purely a homing/naming observation for the Slice-2 re-flow lane to revisit if a
cleaner scale is wanted. No action required to land Slice 1.

## Evidence

- `git diff --numstat HEAD -- kayakgen/ui/theme.py` → `86 2`; the two deletions
  are the relocated TYPOGRAPHY loop only.
- `git status --porcelain` → only the five expected files + untracked workflow
  tree.
- `git diff --name-only HEAD -- docs/USER_GUIDE.md docs/WEB_VERIFICATION.md
  docs/DECISION_LOG.md` → empty (protected docs untouched).
- `.venv/bin/python -m pytest tests/test_ui_theme.py -v` → **12 passed**,
  including `test_contrast_manifest_clears_thresholds[light|dark]`,
  `test_new_visual_token_maps_are_additive_and_resolved`,
  `test_new_visual_token_contrast_pairs_are_manifested`,
  `test_no_orphan_visual_literals_under_kayakgen_ui`,
  `test_visual_literal_lint_fails_on_planted_literal`.
- Independent literal scan: every `px/rem/em` literal under `kayakgen/ui/`
  resides only in `theme.py`.
- Byte-for-byte reconstruction of each migrated CSS string (above).
