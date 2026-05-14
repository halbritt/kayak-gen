---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: operator [self-declared: operator-0047-review-ergonomics]

# Review — Ergonomics And Design (Workflow 0047 UI Follow-Up Cleanup)

## Verdict Intent

`accept_with_findings`

Proposed RFC 0035 reads as the narrowest correct successor to workflow 0045
and workflow 0046 final reviews. Every proposal in §Proposal traces to a
concrete, pre-existing maintenance or semantic finding (`F1`-`F5` in
`striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md` and `M1`-`M3`
in `striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md`).
The seven items collectively *clarify* the existing UI rather than
re-laying it out, and none expands a capability claim, read-model
contract, or theme token surface. Compactness, predictability, and
RFC 0033/0034 visible-copy guarantees survive the proposed scope.

Findings below are ergonomic refinements that the implementation lane
should respect when the ledger is drafted. None blocks the RFC; each
points at a small user-visible detail where the literal text of RFC 0035
could produce a slightly worse experience than the current shipped UI if
implemented naively.

## Surface Reproduction (read from current code)

Slider rail, web (`kayakgen/ui/web/app.py:201-210,975-993`):

- `PARAMETER_RAIL_CSS` prepends `theme.css_root_block()` *and* a single
  scoped rule `.kg-param-slider .v-slider__label { font: var(--type-label);
  color: var(--text-secondary); white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; }`. The `:root` block is also injected by the
  Vuetify theme path on every page render (last definition wins, identical
  values).
- Each row is built as `html_widgets.Div(raw_attrs=_param_row_raw_attrs(key,
  label), classes="kg-param-slider kg-param-{key} mt-3")` wrapping a
  `v3.VSlider(label=label, thumb_label=True, density="compact", …)`. The
  wrapper carries `role="group"` and `aria-label="<canonical label>"`
  (`app.py:246-254`); the slider inside re-renders the same canonical
  label as `.v-slider__label`.

Slider rail, desktop (`kayakgen/ui/desktop.py:47-49,221-250`):

- `_SLIDER_SUPPORTS_LABEL_LOCATION` introspects `widgets.Slider.__init__`
  once at import. When `True`, slider rows pass `label_location="bottom"`
  and rely on Matplotlib's built-in placement. When `False`, the rows
  fall back to `s.label.set_position((0.5, -0.52))` + center/top alignment.
  Both branches set label and value text to 7.5 pt.

Preset surfaces, web (`kayakgen/ui/web/app.py:925-934,962-974`):

- Two `class_preset`-bound controls coexist: a `v3.VSelect` in the
  toolbar (`kg-class-preset-select`) and a `v3.VRadioGroup` of `VRadio`
  rows in the drawer (`kg-class-preset-radio`). Both list
  `CLASS_PRESET_OPTIONS` and both flip the same state key.
- The active class preset is the only input to
  `validity_badge_from_state` (`controllers.py:128-141`). Desktop's
  `_classify` (`desktop.py:384-398`) instead scans every class envelope
  before falling back to L/B_wl strings.
- Hull-parameter listener (`app.py:711-727`) flips `class_preset` to
  `custom` whenever a `HULL_STATE_FIELDS` value moves outside the seed.
  `target_speed_kt` is wired through `_on_view_param_change`
  (`app.py:729-731`) so the rail stays on its current preset when the
  view speed changes. Non-canonical hull fields (deck_height_m, Cm,
  deck_flatness, center_box_ratio, bow_rake, stern_rake) are inside
  `HULL_STATE_FIELDS`, so editing them flips the rail to `custom`
  even though their bounds were never narrowed by the active preset.
- The `_state_matches_preset_seed` branch (`app.py:715-718,476-484`)
  matches exact float equality of every canonical hull field to the
  preset seed; in normal listener flow the listener fires only after the
  user just changed one of those values, so the branch is reached only
  if the user moved a slider back to the exact seed value within `1e-9`.

Export menu (`kayakgen/ui/web/app.py:104-138,1062-1106`):

- `EXPORT_MENU_ROWS` declares five entries with `key`, `label`,
  `status`, and `description` fields and is exposed both as the read
  model contract (`tests/test_web_layout.py:147-163`) and as
  `self.state.export_menu_rows` (`app.py:353`).
- `_render_export_menu` hand-rolls a `VMenu` with five `VListItem` rows.
  Titles match `EXPORT_MENU_ROWS[*].label`. Subtitles diverge for the
  three enabled rows: the inline subtitles drop the word "Download" and
  the trailing period, e.g. inline `"Current open hull inspection
  surface"` vs `EXPORT_MENU_ROWS[0]["description"]` `"Download the
  current open hull inspection surface."`. The two unavailable rows
  match.

## Findings (Severity-Ordered)

### E1 — Medium: All-class validity-badge detection is the right ergonomic call, but the desktop short strings must not leak

RFC 0035 §Proposal 1 moves the web badge toward the desktop classifier so
a custom-flagged hull that happens to satisfy a known class envelope is
reported as `In <class> envelope` rather than `Custom (L/B_wl=X.X)`. This
is ergonomically correct: the badge is the rail's anchor for "did my
changes leave the class envelope?", and today a user who lands inside
the touring envelope while the selector still reads `custom` sees a
"Custom" badge that contradicts their actual position.

Caveat: `desktop._classify` (`kayakgen/ui/desktop.py:384-398`) returns
slightly longer strings — `f"Custom — sub-touring (L/B_wl={l_over_bwl:.1f})"`
and `f"Custom — beyond elite (L/B_wl={l_over_bwl:.1f})"` with the
numeric tail attached. The accepted web vocabulary (RFC 0033 / RFC 0034)
is exactly `Custom — sub-touring`, `Custom — beyond elite`, and
`Custom (L/B_wl=X.X)`. The implementation must reuse the existing
controller branching that produces those three exact strings; it must
not import desktop's longer variants.

How to apply: in `validity_badge_from_state`, classify the hull against
all entries in `CLASSES` first (using the same envelope test
`_hull_in_kayak_class` already used); only if no class matches, drop to
today's L/B_wl branch (`controllers.py:135-141`). Keep the four accepted
strings byte-for-byte. Confirm `tests/test_web_read_models.py` exact-badge
assertions stay green.

Source: `kayakgen/ui/web/controllers.py:128-141`;
`kayakgen/ui/desktop.py:384-398`; RFC 0033 §Acceptance badge vocabulary;
RFC 0035 §Acceptance Criteria item 1.

### E2 — Medium: `_render_export_menu` consolidation must preserve the visible subtitle copy users already see

RFC 0035 §Proposal 4 says to render the export menu from
`EXPORT_MENU_ROWS` so labels and disabled flags cannot drift. The labels
already match, but the `description` field of `EXPORT_MENU_ROWS` does
not match the current inline `subtitle` text for the three enabled
rows:

| key            | shipped `subtitle`                              | `EXPORT_MENU_ROWS[*].description`                                             |
| -------------- | ----------------------------------------------- | ------------------------------------------------------------------------------ |
| `hull_stl`     | `Current open hull inspection surface`          | `Download the current open hull inspection surface.`                          |
| `deck_stl`     | `Current open deck inspection surface`          | `Download the current open deck inspection surface.`                          |
| `hydro_json`   | `Current local evaluation data`                 | `Download current local evaluation data as JSON.`                              |
| `stability_json` | `Use kayakgen stability for current initial-stability JSON.` | (matches)                                                                      |
| `mesh_package` | `Mesh package authoring is not enabled in the browser; use kayakgen mesh-package.` | (matches)                                                                      |

The literal "render from EXPORT_MENU_ROWS" approach would change the
visible subtitle copy on the three enabled rows. That is a small
ergonomic regression: today's clipped subtitles fit a 360-px-wide
drawer better than the "Download …" variants, and they read as state
("Current local evaluation data") rather than as imperatives
("Download current local evaluation data as JSON.").

How to apply: the ledger must pick one canonical wording. Two options
keep the cleanup ergonomically neutral:

1. **Adopt the shipped subtitles into `EXPORT_MENU_ROWS`** — rename
   the field `subtitle`, drop "Download …" prefixes, and have
   `_render_export_menu` iterate the data. Test surface widens slightly
   (the read-model test must lock the shorter strings), but visible
   copy is identical to today.
2. **Adopt the "Download …" wording into the menu** — accept the
   subtitle change as part of the cleanup and explicitly mention it in
   `CHANGELOG.md`.

Either is acceptable; option 1 is the smaller user-visible delta. Do
not silently inherit option 2 by iterating today's
`EXPORT_MENU_ROWS[*]["description"]` field unchanged.

Source: `kayakgen/ui/web/app.py:104-138,1062-1106`; RFC 0035
§Acceptance Criteria item 3.

### E3 — Low: The disabled "Mesh package..." ellipsis convention reads as "opens a dialog" — review whether the label is still honest

Per the UX convention adopted by Vuetify and most desktop frameworks,
trailing `...` on a menu item signals "selecting this opens a dialog
for further input." On the current menu, `Mesh package...` is *disabled*
with subtitle "Mesh package authoring is not enabled in the browser; use
kayakgen mesh-package." A user reading only the label may assume the
greyed-out state is temporary and that clicking would have opened a
dialog. The subtitle clarifies, but the label is the first signal.

How to apply: while the ledger is renaming subtitle text per E2,
consider also normalizing the label to `Mesh package` (no ellipsis) or
`Mesh package (CLI only)`. RFC 0033's accepted vocabulary calls the
profile `open-wetted-surface` and uses "unavailable" rather than a
dialog metaphor (`EXPORT_MENU_ROWS[4]["status"] == "unavailable"`), so a
non-ellipsis label is consistent with the rest of the contract. This is
optional and not required for the cleanup to land.

Source: `kayakgen/ui/web/app.py:131,1098`.

### E4 — Low: The `role="group"` slider wrapper accessibility model needs a confirmed pattern, not just one visible-text assertion

RFC 0035 §Proposal 6 asks the review to "Confirm the wrapper
`role="group"` and `aria-label` structure produces one clear accessible
name per slider row and still preserves the canonical visible label."
Per `_param_row_raw_attrs` (`app.py:246-254`) the wrapper Div carries
`role="group"` plus `aria-label="<canonical label>"`, and the inner
VSlider re-renders the same string as `.v-slider__label` and exposes it
as the slider's accessible name via Vuetify's default labelling. There
are now three potential accessible-name surfaces in a single row:

1. wrapper `aria-label` (group),
2. inner slider `aria-label` (Vuetify `label=label` → slider role
   accessible name),
3. visible `.v-slider__label` (rendered text).

The "one clear accessible name per slider row" property is only
*indirectly* tested today: `tests/test_web_browser.py` asserts that the
canonical label appears as `aria-label` somewhere in the row subtree
(any of the three surfaces is acceptable for that assertion). If a
screen reader announces "group Length (m), slider Length (m), 4.5 of
6.5", the verbosity is a small ergonomic regression versus the
single-line announcement most users expect ("Length (m) slider, 4.5 of
6.5").

How to apply: have the implementation lane decide whether the wrapper
*needs* `role="group"`. For a single form control inside the wrapper,
ARIA prefers either no role + no `aria-label` (let the slider's own
`aria-label` carry the name) or `role="presentation"` (purely
structural). If the wrapper exists only so the scoped CSS selector
(`.kg-param-slider`) has a stable container, dropping `role="group"`
and keeping the class hooks gives the same visual outcome with a
cleaner accessibility tree. Whichever way the ledger decides, add a
focused test for the chosen rule — assert the wrapper has the role you
intend, count the `aria-label` occurrences in the subtree, and lock
the canonical visible-label text. The current test surface only locks
the visible text, not the role/aria-label cardinality.

Source: `kayakgen/ui/web/app.py:246-254,975-993`;
`striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md` M2.

### E5 — Low: Drop the duplicated `:root` token block in `PARAMETER_RAIL_CSS`

RFC 0035 §Proposal 6 asks the review to confirm the duplicate `:root`
token emission can go. Confirming: `theme.css_root_block()` is already
injected by the Vuetify theme path on every web page render and there
is no observable styling case in which `PARAMETER_RAIL_CSS`'s
prepended `:root` block adds a usable variable that is not already
defined upstream. Removing the prepend leaves the single scoped rule:

```css
.kg-param-slider .v-slider__label {
  font: var(--type-label);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

This is the simplest correct form and is what
`tests/test_web_layout.py:92-103` would still pass against (the test
asserts `var(--type-label)` and `var(--text-secondary)` *usage*; the
`--type-label`/`--text-secondary`/`--surface-rail` *definitions* in the
existing test are already covered by `theme.css_root_block()`'s own
test in `tests/test_ui_theme.py` and could move there if not already).

How to apply: rewrite `PARAMETER_RAIL_CSS` to just the scoped rule.
Update `tests/test_web_layout.py:101-103` so it asserts the token
*usages* in `PARAMETER_RAIL_CSS` but asserts the token *definitions*
through `theme.css_root_block()` (`tests/test_ui_theme.py` already
exercises that surface). No new tokens, no new selectors.

Source: `kayakgen/ui/web/app.py:201-210`;
`kayakgen/ui/theme.py:373-382`;
`striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md` M3.

### E6 — Low: Preset edit model — give the rail a one-sentence user-facing rule, and keep the dual selector in sync

RFC 0035 §Proposal 2 keeps the existing semantics: presets seed and
narrow only the five canonical hull sliders; edits to other hull
sliders flip to `custom`; target-speed edits never flip the preset.
This is internally consistent but is two rules deep (canonical-vs-not
*and* hull-vs-view) and is not documented in the user guide today.

The non-canonical hull sliders (`deck_height_m`, `Cm`, `deck_flatness`,
`center_box_ratio`, `bow_rake`, `stern_rake`) still keep global
`SLIDER_DEFS` bounds when a preset is active. From the user's point of
view, the rail looks like: five sliders that visibly narrowed when I
picked a class, six sliders that did not, and one slider (target
speed) that is purely a view. Editing any of the first eleven flips to
`custom`. Editing the twelfth does not. The current rail gives no
visual signal of which group a given slider belongs to.

How to apply: do not add a visual badge to non-canonical sliders —
that would expand RFC 0035's scope. Add one user-guide sentence (the
RFC already calls for this in §Acceptance Criteria item 2): "Class
presets narrow the five principal hull sliders (length, beam OA, beam
WL, draft, prismatic). Editing any other parameter rail slider returns
the class to Custom; editing target speed does not." The toolbar
`VSelect` and drawer `VRadioGroup` are both bound to `class_preset`
and are kept in sync by Vuetify's two-way binding; that behavior is
already correct and is out of scope for this cleanup. Worth noting only
that the user guide sentence should not imply there is only one preset
selector — the user can use either.

Source: `kayakgen/ui/web/app.py:445-451,711-727,925-934,962-974`;
RFC 0035 §Acceptance Criteria item 2;
`striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md` F3.

### E7 — Low: `_state_matches_preset_seed` removal is the cleaner ergonomic outcome; if retained, the user-visible behavior must not move

RFC 0035 §Proposal 3 allows removal of the
`_state_matches_preset_seed` branch (`app.py:476-484,714-718`) if the
review confirms no observable interaction depends on it. From a user's
point of view the branch is invisible: in the only path that reaches
it (move a hull slider back to within `1e-9` of the seed), the user
sees the same preset name and the same narrowed bounds either way.
The narrowed-bounds restoration the branch performs is identical to
what `_apply_class_preset` already does when the preset is selected,
and the listener has not yet flipped the preset to custom at that
point.

How to apply: prefer removal. If retained for any reason, lock the
behavior with a focused test that drives the exact event sequence
(set a preset, move a slider, move it back to within `1e-9` of the
seed, assert the preset stays non-custom and the bounds are still
narrowed). Either outcome is ergonomically equivalent; removal reduces
maintenance surface.

Source: `kayakgen/ui/web/app.py:476-484,714-718`;
`striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md` F2.

### E8 — Low: Keep the desktop fallback bounded; the rendered-bbox test is the right gate

RFC 0035 §Proposal 7 keeps the manual offset fallback
(`desktop.py:245-248`) only while the installed Matplotlib lacks
`label_location` support. From a user's point of view the fallback
produces a slightly tighter label-to-track distance than
`label_location="bottom"` would, but the existing
`tests/test_desktop_layout.py` bbox assertions prevent any clipping or
overlap regression, and the user-visible labels stay 7.5 pt and
unambiguously inside the figure.

How to apply: no code change beyond what the RFC already specifies.
Document the removal condition (`label_location` available on the
project's Matplotlib floor) in a single comment next to
`_SLIDER_SUPPORTS_LABEL_LOCATION` and in the user guide section if
one exists. Do not loosen the bbox test thresholds; they are the only
mechanical guard against the fallback drifting under future
window-height changes.

Source: `kayakgen/ui/desktop.py:47-49,233-250`;
`striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md` M1.

## Compactness And Predictability Check

Reviewed every proposed change against "does this make the UI less
compact or less predictable?":

- **Validity badge (E1).** Compactness unchanged: the badge is a single
  `VChip` at the foot of the rail; the new logic produces strings of
  the same length classes as today. Predictability *improves*: the
  badge now matches what desktop reports for the same hull.
- **Preset edit semantics (E6).** Compactness unchanged. Predictability
  is the same as shipped behavior; the only delta is a user-guide
  sentence.
- **Dead branch cleanup (E7).** Compactness improves marginally
  (~10 fewer lines in `app.py`). Predictability unchanged: the branch
  is unreachable in normal interaction.
- **Export menu single source (E2, E3).** Compactness unchanged or
  slightly improved if the shorter shipped subtitles are adopted;
  predictability *improves* because the visible menu and the read
  model become provably the same source.
- **State snapshot hygiene.** Not user-visible. Out of ergonomics
  scope; no design impact.
- **CSS scoping (E5).** Compactness improves at the CSS source-level;
  no visible-styling change. Predictability *improves* (one fewer
  surface where `:root` tokens could be redefined).
- **Slider accessibility wrapper (E4).** Compactness unchanged.
  Predictability improves if the role/`aria-label` cardinality is
  locked by a test.
- **Desktop fallback (E8).** Compactness unchanged. Predictability
  unchanged; the fallback's removal condition becomes explicit.

No proposal reduces compactness or predictability. The RFC's stated
non-goals (no desktop parity rewrite, no Qt-native rewrite, no new
backend or claim surface, no new tokens, no broader redesign) protect
the rest of the workspace.

## Out Of Scope (Confirmed)

- Desktop parity rewrite or Qt-native slider replacement.
- New parameter-rail visual signals for non-canonical hull sliders.
- A web focus ring beyond Vuetify defaults.
- Persistent inline numeric values next to slider thumbs.
- Toolbar/drawer preset-selector consolidation. Both controls stay.
- Mesh-package authoring UI, Stability JSON authoring UI, hosted CFD,
  calibrated drag, final-prediction copy, real high-angle GZ, or any
  RFC 0033/0034 deferred capability.
- New typography, color, or surface tokens.
- Changes to `SLIDER_DEFS`, `PARAMETER_GROUPS`, REST routes, controller
  read-model shapes, or evaluator behavior.

## Concrete Source References

- `kayakgen/ui/web/app.py:104-138` — `EXPORT_MENU_ROWS` table.
- `kayakgen/ui/web/app.py:201-210` — `PARAMETER_RAIL_CSS` and the
  duplicated `:root` block.
- `kayakgen/ui/web/app.py:246-254` — `_param_row_raw_attrs` (the
  wrapper `role`/`aria-label`).
- `kayakgen/ui/web/app.py:445-484` — preset apply, slider bounds, and
  `_state_matches_preset_seed`.
- `kayakgen/ui/web/app.py:711-731` — hull/view parameter listeners.
- `kayakgen/ui/web/app.py:925-934,962-974` — toolbar `VSelect` and
  drawer `VRadioGroup` preset controls.
- `kayakgen/ui/web/app.py:975-993` — slider row wrapper and
  `VSlider`.
- `kayakgen/ui/web/app.py:1062-1106` — `_render_export_menu`.
- `kayakgen/ui/web/controllers.py:128-141` — `validity_badge_from_state`.
- `kayakgen/ui/desktop.py:47-49,221-250,384-398` — slider build with
  `label_location` shim, classifier, neighbouring controls.
- `kayakgen/ui/theme.py:337-352,373-382` — contrast manifest and
  `css_root_block`.
- `docs/rfcs/0035-ui-follow-up-cleanup.md` — successor RFC under
  review.
- `striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md` F1-F5,
  `striatum/0046-slider-label-visibility/final/FINAL_REVIEW.md` M1-M3 —
  upstream findings.
- `tests/test_web_layout.py:60-163` — current static contract.

## Commands And Checks Run

- File reads on `AGENTS.md`, `docs/workflows/0047-ui-follow-up-cleanup/
  prompts/review_ergonomics_design.md`,
  `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`,
  `docs/rfcs/0035-ui-follow-up-cleanup.md`, `kayakgen/ui/web/app.py`
  (full module skimmed; rail/menu/listener sections read line-by-line),
  `kayakgen/ui/web/controllers.py` (badge + class envelope sections),
  `kayakgen/ui/desktop.py` (`_build_sliders`, `_classify`, neighbouring
  controls), `kayakgen/ui/theme.py` (contrast manifest, root block),
  `tests/test_web_layout.py`, plus the prior workflow final reviews and
  the workflow 0047 RFC-scope synthesis
  (`striatum/0047-ui-follow-up-cleanup/rfc_scope/RFC_SCOPE.md`).
- Targeted greps for `EXPORT_MENU_ROWS`, `subtitle`/`title=`,
  `class_preset`, and the rail wrapper helpers to confirm the renderer
  and read-model paths and find duplicate copy.
- No product/runtime files were modified. No tests were run. No
  Striatum mutation commands, commits, pushes, or `.striatum/` edits
  occurred. No co-author trailer or attribution metadata beyond the
  required `author:` line at the top of this artifact.

## Sub-Agent And Parallel Helper Use

Two paired file-reads were issued in parallel where the targets are
independent (`AGENTS.md`/prompts/SOURCES/RFC; rail/listener slices in
`app.py`; controllers + theme). No sub-agents were spawned: the
surface fits inside the main session and the findings are tightly
cross-referenced, so a single coherent reading produces a more
consistent review than fan-out.
