author: reviewer-traceability-claude-opus-4.8-001

# Review — Traceability to RFC 0065 Slice 0 decisions

**Verdict:** `accept_with_findings`

Scope is valid. Every workflow-0058 change traces to RFC 0065's "Slice 0 —
Pre-redesign baseline" line and a row of `SLICE_0_DECISIONS.md` (S0-D1…S0-D6).
No scope creep into Slice 2/3/4 was found. The captured baseline is of the
**current** (pre-redesign) shell and the live 3D region is masked. Findings
below are advisory/forward-looking; none invalidates the slice.

## Changeset under review

```
M CHANGELOG.md                       (+8)   docs footprint  → S0-D6
M tests/conftest.py                  (+6)   --update-visual-baselines → S0-D3
M tests/test_web_browser.py          (+215) capture/mask/compare → S0-D1,D2,D4
?? tests/visual_baselines/1440x900.png       committed baseline → S0-D3
?? tests/visual_baselines/1024x768.png       committed baseline → S0-D3
?? tests/visual_baselines/960x720.png        committed baseline → S0-D3
?? tests/visual_baselines/README.md          canonical env + regen → S0-D3,D6
```

`git diff main…HEAD --name-only -- kayakgen/` and the working-tree diff are both
**empty for `kayakgen/`** — no source touched. `docs/USER_GUIDE.md` and
`docs/WEB_VERIFICATION.md` untouched; `docs/DECISION_LOG.md` untouched (D047 not
ratified here). Suite collects cleanly: `4 tests collected` (3 parametrized
visual + the existing `test_kayakgen_serve_browser_acceptance`).

## Decision traceability (S0-D1 … S0-D6)

| Decision | Requirement | Evidence | Status |
|---|---|---|---|
| **S0-D1** | Capture in browser-acceptance profile at 1440×900 / 1024×768 / ≤960px after settle | `test_web_browser.py:627` `@pytest.mark.browser_acceptance` + `VISUAL_VIEWPORTS` (1440×900, 1024×768, 960×720); `_capture_masked_workspace_png` reuses `_wait_for_workspace_shell` + `_assert_nonblank_3d` settle | ✅ (see F1) |
| **S0-D2** | Mask `geometry-vtk-view` / `.kg-vtk-viewport`; liveness asserted separately | `_mask_vtk_viewport` overlays `[data-testid='geometry-vtk-view'], .kg-vtk-viewport` with solid `#f3f4f6`; `_assert_nonblank_3d` still asserts liveness pre-mask | ✅ |
| **S0-D3** | Committed in-repo PNGs + README (canonical env + regen) | 3 PNGs under `tests/visual_baselines/`; `README.md` records host/Python/Playwright/Chromium/date + `--update-visual-baselines` regen; `conftest.py` adds the flag | ✅ |
| **S0-D4** | Advisory compare; SKIP on missing tooling; HARD gate deferred to Slice 4 | `_compare_visual_png` writes actual/diff PNGs; every mismatch / missing-baseline / missing-Pillow / missing-Playwright / missing-Chromium path is `pytest.skip` — no `fail`/pixel-`assert` | ✅ |
| **S0-D5** | No `kayakgen/ui/` source, hook rename, chip/caption/claim change | No `kayakgen/` diff; existing `geometry-vtk-view`/`kg-vtk-viewport` only **read**, not renamed; baseline is current shell | ✅ (see F2) |
| **S0-D6** | Docs footprint = CHANGELOG + new README only; D047 not ratified | CHANGELOG "### Added" Slice 0 entry; `visual_baselines/README.md` new; USER_GUIDE/WEB_VERIFICATION/DECISION_LOG untouched | ✅ |

## Scope-creep checklist (all clear)

- `kayakgen/ui/` source change → **none**.
- Information-hierarchy reflow (Slice 2) → **none** (no source).
- Control / empty-loading-error state work (Slice 3) → **none**.
- HARD-FAILURE visual-regression gate → **none**; compare is advisory-skip only.
- a11y / focus-order / contrast / Lighthouse checks (Slice 4) → **none added**;
  the pre-existing `_assert_parameter_slider_accessibility` is unchanged.
- `WEB_VERIFICATION.md` / `USER_GUIDE.md` edits → **none**.
- `data-testid` / `kg-*` rename → **none** (see F2 for an additive test-only literal).
- `CHIP_*` / caption touched → **none**.
- New claim-state / readiness literal → **none**; the new test only asserts on
  existing rendered text ("kayakgen", "Length (m)", "Metrics", "Hydrostatics").

## Baseline-of-current-shell + 3D-mask confirmation

- **Current shell:** the committed PNGs render the present pre-redesign layout —
  Parameters rail, Geometry pane, Metrics, Hydrostatics/Stability/Resistance
  review column, top action bar, bottom status strip. No appearance change.
- **3D masked:** the Geometry/`VtkRemoteView` region is a flat `#f3f4f6` fill in
  all three PNGs; the live frame never enters the comparison. Liveness stays
  covered by `_assert_nonblank_3d` (run before masking). S0-D2 satisfied.

## Findings

### F1 — Advisory: the 1024×768 and 960×720 baselines are pixel-identical (under-serves S0-D1's third viewport)

The two narrow baselines are **byte-decoded pixel-identical** (`ImageChops`
diff bbox = `None`) and both render at **1050×1829**, not their nominal
viewport widths. Only `1440×900.png` (1440×1299) is visually distinct.

Root cause (two compounding factors, both expected for this slice):
1. No responsive `@media` / breakpoint collapse exists in source yet — the
   `kg-collapse-under-960` / `kg-*-under-960` classes in
   `kayakgen/ui/web/app.py:235-251` are currently **inert markers** (grep finds
   no `@media` rule anywhere in `kayakgen/`); the responsive reflow is Slice 2.
2. `page.screenshot(full_page=True, …)` in `_capture_masked_workspace_png`
   captures the shell's intrinsic ~1050px content width, so the 960px and
   1024px viewport settings collapse to the same render.

Net: this satisfies S0-D1 **literally** (three viewport buckets of the current
shell are captured and committed) and violates no scope rule, but the "≤960px
collapsed" bucket does **not** exercise a distinct collapsed/mobile layout, and
in Slice 2/3 the 960 and 1024 diffs will move together — the collapsed-layout
diff will not be independently reviewable, which is the stated purpose of
capturing three viewports.

**Recommendation (Slice 2 / Slice 4, not a blocker now):** when the responsive
collapse lands, re-baseline the narrow buckets; consider capturing the narrow
viewports with `full_page=False` (viewport-clipped) so the viewport width
actually governs the render, or assert the three baselines are pairwise distinct
so a future redundancy is caught. This is the env/efficacy fragility the review
prompt asks to flag for the next slice's diff.

### F2 — Informational: additive test-only `kg-*` / `data-testid` literals (no violation)

`_mask_vtk_viewport` injects an overlay element carrying
`class="kg-visual-mask"` and `data-testid="visual-vtk-mask"`. These are **not**
renames of source hooks and are **not** written into `kayakgen/ui/` — they are
created at runtime via `page.evaluate`, removed at the top of each mask call,
and never persisted. Grep confirms neither literal exists anywhere under
`kayakgen/`, so there is no collision with a real hook. Traces to S0-D2
(masking) and is harmless; logged only for traceability completeness.

### F3 — Low: `full_page` + `position: fixed` mask is robust today but viewport-dependent

The mask is a `position: fixed` overlay positioned from the VTK region's
`getBoundingClientRect()`. It lands correctly in the committed PNGs (the
Geometry region is cleanly filled). The forward risk: if a Slice 2/3 reflow
pushes the VTK region below the fold, a `full_page` capture combined with a
viewport-fixed overlay could misalign and leak live frame pixels into the diff.
No action this slice; revisit mask placement when the reflow lands.

## Disposition

`accept_with_findings`. Scope is valid and fully traceable to S0-D1…S0-D6 with
no creep; baseline is the current shell with the 3D region masked. F1 is the
actionable forward-looking item (redundant narrow baselines / `full_page`
overflow) to address when the Slice 2 responsive collapse lands; F2/F3 are
informational.
