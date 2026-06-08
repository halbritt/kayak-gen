# Kayakgen UX Review - Primary Web Workspace - GPT-5 Codex - 2026-06-08

## 0. Review Basis

**Target.** Kayakgen primary web workspace, resolved from the repo and docs as the Trame UI started by `kayakgen serve`. The reviewed surface is the three-region workspace: parameter rail, geometry viewport, review tabs, share/export controls, CFD panel, and Generate panel.

**Target users.** Inferred from `docs/PRD.md`: independent kayak builders, naval architecture enthusiasts, sea-kayak and surfski paddlers, and maker-community designers who understand terms such as length, beam, draft, Cp, GM0, and resistance, and who need fast but honest early-stage design feedback.

**Critical workflows.**

1. Edit hull parameters, inspect the 3D hull, and read hydrostatics/resistance.
2. Load/share a design and continue editing without changing the design identity unexpectedly.
3. Start or inspect local sweep/search jobs from the Generate workflow.

**Repository state.** `git status --short --branch` reported `## main...origin/main` before this report was written. Repo root: `/home/halbritt/git/kayak-gen`; branch `main`; short HEAD `fca494a`. No out-of-scope local changes were present before the report file.

**Authority granted.** The invoked `/tmp/land-main/UX_REVIEW.md` prompt defaults to read-only static inspection and allows only the report write. I did not start a dev server, run tests, run Playwright, install dependencies, or perform browser interaction. Browser/runtime checks are therefore gated and not used as fresh evidence.

**Evidence inventory.** Static source and docs: `AGENTS.md`, `docs/PRD.md`, `docs/design/kayak_hull_design_constraints.md`, `docs/rfcs/README.md`, `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, `kayakgen/model/geometry.py`, `kayakgen/model/hull.py`, `kayakgen/ui/web/app.py`, `layout.py`, `presentation.py`, `state.py`, `handlers.py`, `generate_spec_form.py`, `generate_frontier_view.py`, `tests/test_web.py`, `tests/test_web_browser.py`, `tests/test_web_layout.py`, `tests/test_web_inline_help.py`, and `tests/visual_baselines/README.md`. Screenshot evidence: committed visual baselines `tests/visual_baselines/1440x900.png`, `1024x768.png`, and `960x720.png`.

**Surface/depth ledger.**

| Surface or workflow | Pass | User goal | Evidence | Viewport | Strongest tier | Residual risk |
| --- | --- | --- | --- | --- | --- | --- |
| First-viewport edit plus Hydro analysis | deep-review | Adjust hull and read the important numbers | `layout.py`, `presentation.py`, `theme.py`, visual baselines | 1440x900, 1024x768, 960x720 | observed-screenshot | Runtime interaction not rerun |
| Share/reload hull fidelity | deep-review | Save or share exactly the design being edited | `state.py`, `handlers.py`, `app.py`, `tests/test_web.py`, `docs/USER_GUIDE.md` | static | static-traced | No browser repro was authorized |
| Generate search/sweep form | deep-review | Build a valid job spec and understand blocked submission | `generate_spec_form.py`, `layout.py`, `tests/test_generate_spec_form.py`, `tests/test_web_inline_help.py` | static | static-traced | No live screen-reader or keyboard pass |
| Mesh tab | survey | Understand readiness and diagnostics | `layout.py`, `handlers.py`, `docs/USER_GUIDE.md` | 1440 screenshot | static-traced | Did not inspect every state |
| Comparison tab/frontier | survey | Inspect candidates and apply one | `layout.py`, `generate_frontier_view.py`, `read_models.py` | static | static-traced | No live candidate payload |
| CFD panel | survey | Prepare/run local raw CFD jobs | `layout.py`, `handlers.py`, `controllers.py`, docs | static | static-traced | No live job |
| Desktop GUI and CLI-only flows | unread | Out of target for this review | PRD and user guide only | n/a | supplied-context | Not assessed |

## 1. Verdict

**Verdict: SHIP_BLOCKED. Confidence: medium.**

Finding counts: 1 BLOCKER, 3 SERIOUS, 0 MINOR.

The web workspace is directionally honest about raw/unvalidated claims and has meaningful state, focus, contrast, and visual-regression infrastructure. The ship-blocking issue is simpler: the committed 1024x768 and 960x720 baselines show the core analysis surface clipped off the right edge, including hydro values and later review tabs. That breaks the primary design loop on representative viewports the project itself captures as acceptance evidence. Confidence is capped at medium because this was static plus committed-screenshot review; I did not run the app, Playwright, axe, Lighthouse, or manual keyboard checks.

## 2. Surface And Workflow Summary

The web workspace presents a left parameter rail, a center geometry viewport with a metrics strip, and a right tabbed review panel. The primary user edits length, beam, draft, Cp/Cm, deck form, rake, and target speed, then reads hydrostatics, raw comparative resistance, mesh diagnostics, comparison reports, CFD job status, or Generate jobs. The UI also provides a class preset selector, Reset, Share, Export, and a bottom status bar.

The wide 1440x900 baseline shows the intended composition: parameter rail, geometry viewport, Hydro tab, and status bar all visible in the first viewport. The narrower 1024x768 and 960x720 baselines show a different user experience: the right review pane is clipped horizontally, hydro values are outside the visible viewport, and later tabs are not reachable in the clipped screenshot. The code traces explain why: the drawer is fixed at 360 px, the content uses side-by-side `md=7`/`md=5` columns, table-like content uses fixed `--frontier-max-width: 480px`, and the media query at `max-width: 960px` only changes border/rhythm styling, not the layout model.

The share and reload flow is implemented through a flat web state projection. That is safe for default lofted hulls whose identity is exactly the slider subset, but it does not preserve the newer `distribution_v2` hull record or other non-slider fields. The Generate form has better domain guardrails than a raw JSON box, but some inline controls are raw HTML without explicit accessible names, and the submit-blocking state appears to be recomputed only when helper code is called, not reactively as fields mutate.

## 3. Claims vs Observed

| Claim | Status | Evidence |
| --- | --- | --- |
| Web frontend exposes the core design loop and compact analysis views. | contradicted at 1024/960, verified at 1440 | `docs/PRD.md`; baselines show clipped analysis at 1024/960 |
| Share/reload links restore the same design inputs that were open when copied. | contradicted for non-slider hull fields and `distribution_v2` | `docs/USER_GUIDE.md:1117-1119`; `state.py:19-89`; `handlers.py:339-342` |
| Web visual baselines cover 1440x900, 1024x768, and 960x720. | verified | `tests/test_web_browser.py:56-60`; `tests/visual_baselines/README.md` |
| Browser output remains raw/local/unvalidated where appropriate. | verified in inspected copy | `presentation.py:490-509`; `layout.py:298-311`, `515-606` |
| Under about 960 px the columns stack vertically. | unverifiable below 960; not true at exactly 960 in the committed baseline | `docs/USER_GUIDE.md:1097-1101`; `960x720.png`; `presentation.py:474-486` |

## 4. Findings

### BLOCKER - Representative viewports clip the core analysis workflow

**Location.** `tests/visual_baselines/1024x768.png`, `tests/visual_baselines/960x720.png`; layout in `kayakgen/ui/web/layout.py:105-224`; CSS in `kayakgen/ui/web/presentation.py:178-486`; dimensions in `kayakgen/ui/theme.py:182-193`.

**Evidence tier.** observed-screenshot plus static-traced.

**User scenario.** A builder opens the local web workspace on a 1024 px laptop viewport or a 960 px browser window, edits beam or Cp, and tries to read the resulting displacement, GM0, resistance, or switch to Comparison/Generate.

**Observed or traced mechanism.** The committed 1024x768 baseline clips the review panel: Hydro labels are visible but values are cut off, the Comparison tab label is partly offscreen, and later tabs are not visible. The 960x720 baseline clips the review panel even harder. Source traces show the shell keeps a 360 px drawer, then renders geometry and review as side-by-side `VCol(md=7)` and `VCol(md=5)` regions. Hydro/resistance/tables use fixed `width: var(--frontier-max-width)` with `frontier-max-width` set to `480px`. The only `@media (max-width: 960px)` rule adjusts border radius and margins plus status wrapping; it does not collapse the grid or constrain fixed-width tables.

**User impact.** The important work cannot be completed safely on viewports the project treats as acceptance baselines. Users cannot reliably read the numbers that tell them whether a hull is plausible, cannot see all review tabs, and may miss warnings or unavailable states. This breaks a critical workflow on common desktop/tablet widths.

**Fix direction.** Make the 1024/960 layouts task-complete rather than just pixel-stable. Smallest likely fix: collapse geometry/review earlier, let review tabs wrap or become an explicit overflow menu, set tables to `width: 100%; max-width: 100%` inside the review pane, and add browser assertions that Hydro labels and values, all review tab affordances, and status segments are inside the viewport without horizontal scrolling.

### SERIOUS - Share/load can silently downgrade newer hull records to the web slider subset

**Location.** `kayakgen/ui/web/state.py:19-89`, `kayakgen/ui/web/handlers.py:68-89`, `339-342`, `361-367`, `kayakgen/ui/web/generate_panel.py:331-339`, `kayakgen/cli/main.py:673-675`, `docs/USER_GUIDE.md:1117-1119`.

**Evidence tier.** static-traced.

**User scenario.** A user creates or migrates a `distribution_v2` hull in the CLI, starts `kayakgen serve hull.v2.json`, makes a small browser edit or clicks Share, and expects the URL/exported analysis to represent the same v2 hull.

**Observed or traced mechanism.** `Hull` supports `geometry_kind="distribution_v2"` and a nested `distribution_v2` block, plus fields such as `LCB_frac`, `rocker_bow_m`, and `rocker_stern_m`. The web state projection exposes only `HULL_STATE_FIELDS`: the legacy lofted slider set. `state_dict_from_hull()` drops every field outside that tuple plus `name`; `hull_from_state_dict()` and `hull_from_web_state()` reconstruct a fresh `Hull` from only that subset, defaulting `geometry_kind` back to `lofted`. `Share` encodes `_current_hull()`, so the shared URL can omit the v2 design identity. `load_from_query()` likewise decodes a full hull and then stores only the slider subset before refreshing the surface.

**User impact.** This can turn a newer closed-body distribution design into a default lofted design without an explicit warning. The risk is not just missing a control; it is a silent change to the geometry model and therefore to hydrostatics, resistance, mesh diagnostics, and generated STLs. That can lead a builder to compare or export the wrong hull.

**Fix direction.** Preserve the full loaded `Hull` record as an opaque source-of-truth in web state, and make unsupported web edits explicit. Options: show `distribution_v2` as read-only with a "legacy slider edit will convert to lofted" confirmation, refuse share/export until the user acknowledges the downgrade, or support v2 controls directly. At minimum, update Share/reload tests to include a v2 hull and assert either exact record preservation or an explicit visible downgrade warning.

### SERIOUS - Generate form row controls lack accessible names and clear row-level semantics

**Location.** `kayakgen/ui/web/generate_spec_form.py:1114-1176`, `1270-1304`.

**Evidence tier.** static-traced.

**User scenario.** A keyboard or screen-reader user configures a sweep/search variable row, changes objective direction, or removes a row.

**Observed or traced mechanism.** The Variables section renders raw HTML inside `VCardText`: `<select v-model='row.name'>`, `<select v-model='row.kind'>`, numeric `<input>` fields, a choice-values `<input>`, and a remove `<button>` whose visible text is only `x`. The table headers provide visible context, but the individual controls have no explicit `aria-label`, `aria-labelledby`, or row-indexed name. The objective direction toggle is also raw buttons labelled only `min` and `max`, with active styling but no `aria-pressed` or grouped accessible label naming the metric.

**User impact.** The Generate workflow is the entry point for long-running local jobs. Users relying on keyboard or assistive technology may hear a series of unlabeled "combobox", "spinbutton", or "button x" controls with weak context. That makes it easy to edit the wrong row, submit an unintended variable range, or remove a row accidentally.

**Fix direction.** Keep the current form shape, but add explicit accessible names. For each row control, bind `aria-label` or `aria-labelledby` to the row index plus purpose, e.g. "Variable 1 name", "Variable 1 min", "Remove variable 1". For min/max direction buttons, use a radiogroup or `aria-pressed` buttons labelled with the metric title. Extend browser acceptance to tab into the Generate form and assert accessible names for the row controls, not only top-level toolbar focus.

### SERIOUS - Submit disabled reason appears non-reactive after form mutations

**Location.** `kayakgen/ui/web/generate_spec_form.py:915-1000`, `1047-1057`; `kayakgen/ui/web/layout.py:636-680`; `tests/test_web_inline_help.py:181-242`.

**Evidence tier.** static-traced, unverified-gated for runtime behavior.

**User scenario.** A user clears all objectives, deletes every variable row, or requests CFD-in-loop without ticking the acknowledgement, then expects the Submit button and blocking reason to update before clicking.

**Observed or traced mechanism.** `compute_submit_blocking_reason()` and `refresh_submit_blocking_reason()` produce good operator-facing copy, and the Submit buttons bind `disabled=("generative_submit_disabled",)` with `aria-describedby` pointing at the visible reason span. However, source search found `refresh_submit_blocking_reason()` called during initialization/rendering and in tests, but no `state.change(...)` listener or client-side expression that recomputes it when `generative_variables`, selected objectives, evaluator toggles, or acknowledgement state changes. The tests manually call the refresh helper before asserting disabled state.

**User impact.** The most important form guidance may lag behind the user's actual form state. If the button remains enabled after an invalid edit, the user learns the error only after a failed submit. If it remains disabled after a valid correction, the user may be blocked until another incidental refresh. Either case makes the Generate workflow feel unreliable and increases support burden for a complex feature.

**Fix direction.** Recompute the disabled reason reactively on every form state mutation. The smallest change is a server-side listener for the relevant Trame state keys plus a client-side hook for array mutations in `generative_variables`; alternatively, derive the disabled state entirely in Vue from current form state and keep Python validation as the final guard. Add a browser test that mutates objectives/variables/CFD acknowledgement and observes the button plus reason change without calling the helper manually.

## 5. Accessibility, Responsiveness, And State Checks

Keyboard/focus: source and tests show toolbar focus order, visible focus-ring tokens, and minimum hit-target checks for browser acceptance. I did not run keyboard checks. Generate row controls are the main uncovered a11y risk.

Labels and semantics: parameter sliders carry group labels; Hydro rows have title tooltips from row descriptions; status chips and many state panels have test hooks. Raw Generate table controls need explicit accessible names.

Contrast: the theme has a contrast manifest and browser tests reference it. I did not recompute contrast.

Responsive behavior: committed baselines were inspected. 1440x900 is coherent; 1024x768 and 960x720 clip the review pane and hide critical content.

States: empty/running/failed/cancelled/resumable Generate states, CFD no-job/status states, invalid-hull state, mesh no-package/live-readiness states, and comparison no-report/report-present states exist in source. Runtime transitions were not verified.

## 6. Risk Areas Checked

Claim truthfulness was checked because this product carries raw/unvalidated hydro, resistance, CFD, and stability claims. The inspected copy consistently preserves "raw", "uncalibrated", "not final prediction", "not watertight cfd_ready", and "local filesystem" boundaries.

Decision support was checked because users are making hull design tradeoffs. The responsive clipping finding is the main risk: unreadable values are decision-blocking.

Navigation and information architecture were checked across the three-region shell and tabbed review panel. The high-level structure is understandable at 1440, but tab access degrades at narrower viewports.

Destructive/recovery actions were surveyed. Reset is immediate and could benefit from a confirmation if users lose substantial edits, but that did not rise to a finding because Share/export paths exist and the larger fidelity issue is more material.

## 7. Verification

Run/read-only commands and inspections:

- `sed`/`nl`/`rg` over the review prompt, AGENTS reading list, docs, web source, tests, and visual-baseline metadata.
- `git status --short --branch`, `git diff --stat`, `git rev-parse`.
- Visual inspection of `tests/visual_baselines/1440x900.png`, `1024x768.png`, and `960x720.png`.

Not run, gated by authority:

- `kayakgen serve`
- Playwright/Chromium browser acceptance
- Lighthouse
- axe or other accessibility scanner
- pytest/build/package commands
- Manual keyboard or screen-reader walkthrough

## 8. Residual Risk And Open Questions

The verdict could improve or worsen after a live browser run. Runtime may reveal available horizontal scrolling, tab overflow affordances, or dynamic form updates not obvious from source; it may also reveal additional clipped controls beyond the baselines.

The largest product question for maintainers is whether the web workspace should preserve full `Hull` records as opaque data even when it cannot edit every field. If the intended boundary is "legacy lofted only", the UI and docs need to say that clearly before loading, sharing, exporting, or evaluating non-lofted hulls.

Mobile was not reviewed. The docs describe desktop-first and inspect/triage behavior below 960 px; this report only holds the project to its committed 1024 and 960 browser baselines plus the primary desktop workflow.
