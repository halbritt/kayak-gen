---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept_with_findings
---

author: reviewer-traceability-claude-opus-4.8-001

# Workflow 0059 Traceability Review — RFC 0065 Slice 2 (Shell Layout)

## Scope

Verified that every working-tree change on branch
`striatum/0059-rfc-0065-slice2-shell-layout` traces to RFC 0065 §2
("Information hierarchy across the shell") and a row of
`docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md`
(D1–D8), and that no change crosses into a Slice 1, Slice 3, or Slice 4
boundary. Diffed against `HEAD`:

- `kayakgen/ui/theme.py` (+1 line)
- `kayakgen/ui/web/app.py` (the `WORKSPACE_SHELL_CSS` block + Generate panel re-flow)
- `kayakgen/ui/web/generate_fork_button.py`, `generate_frontier_view.py` (one class each)
- `tests/test_ui_theme.py`, `tests/test_web_layout.py`
- `CHANGELOG.md`

Cross-checked the implementer summary
(`striatum/0059-…/implementation/PATCH_SUMMARY.md`), re-ran the focused
suite (`tests/test_ui_theme.py tests/test_web_layout.py
tests/test_web_inline_help.py` → **54 passed**), and resolved every
`var(--token)` reference in the new CSS against `theme.py`.

## Decision-by-decision traceability

| Decision | Verdict | Concrete evidence |
| --- | --- | --- |
| **D1 — token-only styling, no new orphan literals** | ✓ | Every dimension/radius/elevation/border/colour value in `WORKSPACE_SHELL_CSS` is a `var(--token)`; all 37 referenced token keys resolve in `theme.py`. The one new token `DENSITY["collapse-breakpoint"] = "960px"` (`theme.py:192`) is **additive** (no existing token re-typed/removed), non-colour (no `CONTRAST_MANIFEST`/dual-palette obligation), and the lint is extended (`test_ui_theme.py:175`). The media-query `960px` enters **only** via runtime `% theme.DENSITY["collapse-breakpoint"]` substitution, so the AST-based orphan lint sees `%s`, never a literal — `test_no_orphan_visual_literals_under_kayakgen_ui` stays green (54/54). |
| **D2 — one typographic hierarchy** | ✓ (see F1 caveat) | All six roles (`type-display/-heading/-label/-body/-caption/-metric`) are applied across rail, geometry/metrics, review cards/tables, toolbar, status bar, and Generate build/watch/pick surfaces. All 55 `.kg-*` selectors in the stylesheet map to a class actually rendered somewhere under `kayakgen/ui/` (0 orphan selectors). Enforced positively by the new `test_shell_and_generate_sections_share_typography_and_token_density`. |
| **D3 — region + status-bar contract preserved** | ✓ | `LAYOUT_TEST_IDS` still `region-params/-geometry/-review` (`app.py:228`); `STATUS_SEGMENTS` still `package/readiness/resistance/cfd` (`app.py:201`); `workspace-status-bar` testid (`app.py:2297`) and per-segment `data-testid="status-{key}"` + tab routing via `_focus_review_tab` (`app.py:2305-2314`) untouched by the diff. |
| **D4 — first-viewport + collapse contract** | ✓ | `REGION_CLASSES` retain all collapse hooks (`app.py:234-241`); the single `@media (max-width: 960px)` block **restyles** (radius/margin/wrap) the four collapse hooks `kg-collapse-under-960`, `kg-geometry-accordion-under-960`, `kg-review-body-under-960`, `kg-status-wrap-under-960` rather than removing them (`app.py:475-484`). No new breakpoint introduced and no new mobile-editing affordance — posture stays conservative. |
| **D5 — hook discipline (renames reflected same slice)** | ✓ with findings | No D3/D4 hook renamed/removed. New layout hooks `kg-generate-build` / `kg-generate-watch` get positive source assertions (`test_web_layout.py:189-190`). Two new hooks under-covered — see **F2** (`kg-generate-pick-action`) and **F3** (`kg-generate-pick`). No orphaned assertion left pointing at a removed hook. |
| **D6 — claim line byte-stable** | ✓ | No `CHIP_SPECS`/`CHIP_LABELS`/`CHIP_CLASSES` or persistent-caption constant appears in the diff (corroborated by the claims review). Chip selectors (`kg-chip`, `kg-claim-chip`, `kg-readiness-chip`, `kg-validity-badge`, `kg-class-preset-chip`) receive **only** `border-radius` + `font: var(--type-caption)` — no `background`/`color`, so no chip is recoloured into the success palette. No RFC 0033 §8 no-go literal added. |
| **D7 — RFC 0032 boundary intact** | ✓ | Added-line scan finds no new `claim_state` / `Readiness(` / `accepted_uses` literal and no `.route(`/`add_url_rule`; `controllers.py` is untouched. The `kg-readiness-chip` / `kg-mesh-readiness-card` selectors are pre-existing presentation hooks, not new `Readiness` state literals. |
| **D8 — docs footprint is CHANGELOG only** | ✓ | Working tree touches only `CHANGELOG.md`, code, and tests. `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, `docs/DECISION_LOG.md`, and the harness are unchanged; DECISION_LOG **D047** is not ratified here. (`OPERATOR_REPORT.md` not yet filled — a later-role obligation, not a Slice-2 source change.) |

## Findings (non-blocking; remediable)

### F1 — New `:focus-visible` control focus-state rules cross the Slice 3 boundary

`kayakgen/ui/web/app.py:467-473` adds a net-new `:focus-visible` outline
block for `.kg-status-segment`, `.kg-toolbar-action`,
`.kg-variable-remove-btn`, and the Generate variable-table `select`/`input`:

```css
.kg-status-segment:focus-visible, .kg-toolbar-action:focus-visible, … {
  outline: var(--state-focus-ring-width) var(--border-style-solid) var(--state-focus-ring);
  outline-offset: var(--border-width-focus);
}
```

The token usage is clean (all Slice 1 tokens), but applying a **control
focus state** is on the Slice 2 out-of-scope list — *"Control
hover/focus/active/disabled states … (Slice 3)"* — and none of D1–D8
authorise it. There is genuine tension: the SLICE_2 preamble lists
`focus-ring`/`state` among the token *vocabulary* Slice 2 builds on, but
the out-of-scope list defers the *application of control interaction
states* to Slice 3. **Recommendation:** remediation lane either removes
the `:focus-visible` group (defer to Slice 3) or obtains explicit operator
ratification to keep it as a Slice-2 accessibility baseline. Flagging so
the call is deliberate rather than silent.

### F2 — New hook `kg-generate-pick-action` is unstyled and unasserted (D5)

`kayakgen/ui/web/generate_fork_button.py:66` adds
`kg-generate-pick-action` to the fork button, but the class has **no**
`.kg-generate-pick-action` rule in `WORKSPACE_SHELL_CSS` and **no**
assertion in `tests/test_web_layout.py` or `test_web_inline_help.py`. D5
requires a positive assertion for every new hook. As shipped it is a
dangling hook (neither styled nor tested). **Recommendation:** add a
positive assertion, or remove the unused class.

### F3 — New hook `kg-generate-pick` lacks an element-binding assertion (D5)

`kayakgen/ui/web/generate_frontier_view.py:650` adds `kg-generate-pick`
to `kg-frontier-section`. The test asserts the `.kg-generate-pick`
*selector* exists in the stylesheet (`test_web_layout.py:172`) but — unlike
`kg-generate-build`/`-watch`, which assert the `with
html_widgets.Div(classes="…")` source binding — there is no assertion that
the frontier element actually carries the class. **Recommendation:** add a
source/element-binding assertion for symmetry, so the hook is anchored to
its render site, not just to the CSS.

## Out-of-scope items confirmed absent

- **Slice 1:** no existing `theme.py` token renamed, removed, or re-typed; the only edit is the additive `collapse-breakpoint` density token.
- **Slice 3:** no empty/loading/error-state surface added; the only state-token applications are F1 (`:focus-visible`, flagged) and a static `kg-resistance-row-target` row tint (`var(--state-focus-row)`, a persistent orientation highlight on the raw comparative table — not an interaction state and not a success-palette recolour).
- **Slice 4:** no Playwright/a11y harness, no `WEB_VERIFICATION.md`/`USER_GUIDE.md` edit, no D047 ratification.

## Verdict

`accept_with_findings`. Every shipped change traces to RFC 0065 §2 and a
D1–D8 row; the token-only contract, the typographic hierarchy, the
region/status hooks, and the first-viewport + ≤960 px collapse contract
all hold, and the orphan lint stays green. The three findings are
remediable by the remediation lane and do not invalidate the workflow
scope: **F1** is the only one with scope weight (a deliberate keep-or-defer
decision on the new control focus-state), and **F2/F3** are mechanical D5
hook-coverage gaps.
