author: operator [self-declared: operator-0047-review-ops]
kind: finding
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_c8b5fd59b70a48eba5a4c21c946eb8e8
job: job_run_489eb28aa3e0453b916113addacd02e3_review_ops
lease: lease_f989712f042845ca8e56a95c98f98935
date: 2026-05-14
verdict_intent: accept_with_findings

# Review Ops - Workflow 0047 UI Follow-Up Cleanup

## Verdict

`accept_with_findings`

RFC 0035 is reviewable as a narrow maintenance/test cleanup successor. The
current code still contains the exact debt the RFC names, but none of the ops
findings require widening scope or sending the packet back for revision before
ledgering. Implementation should stay focused on source-of-truth cleanup,
accessibility proof, and tests that pin the intended behavior.

I used four read-only helper agents for independent web-maintainability,
test-gate, desktop/ops, and traceability/docs checks. Their findings converged
on the same small risk set below.

## Findings

### O1 - Badge class semantics need an explicit test target before coding

Severity: Medium

`validity_badge_from_state` still checks only the selected preset
(`kayakgen/ui/web/controllers.py:128-141`), while `_matching_kayak_class`
already scans all classes but is unused (`controllers.py:1034-1038`). RFC 0035
correctly scopes the all-class cleanup, but the phrase "same class-envelope
badge outcome as the desktop classifier" needs a test-level decision: desktop
`_classify` scans all classes using length and beam fields only
(`kayakgen/ui/desktop.py:384-393`), while the web class helper checks the five
canonical preset fields, including `draft_m` and `Cp`
(`controllers.py:45-51`, `controllers.py:1041-1053`).

Gate this with read-model tests for:

- `class_preset="custom"` and hull values inside a known canonical class,
  expecting `In <class> envelope`.
- A hull that matches desktop's length/beam check but fails the five-field
  web envelope, so the ledger pins whether RFC 0035 means desktop parity or
  five-field canonical-class semantics.
- Existing sub-touring, beyond-elite, and `Custom (L/B_wl=X.X)` strings.

### O2 - The preset seed short-circuit is still plausibly dead, but removal needs one guard test

Severity: Low

`_state_matches_preset_seed` is defined at `kayakgen/ui/web/app.py:476-484`
and used only inside `_on_hull_param_change` at `app.py:711-722`. Normal slider
interaction changes the value before the listener runs, so the branch should
not be the steady-state user path. Existing static and browser tests cover
preset reseeding, narrowed bounds, and manual edit to `custom`, but they do not
prove a reachable no-op or queued-listener sequence for this branch.

Implementation should either remove the branch and keep the existing browser
preset-selection coverage green, or retain it with a focused event-sequence
test that documents why a same-value hull-field event must preserve the
selected preset.

### O3 - Export menu rendering still duplicates the row contract

Severity: Low

`EXPORT_MENU_ROWS` declares the menu data at `kayakgen/ui/web/app.py:104-138`
and is copied into state at `app.py:353`, but `_render_export_menu` still
hard-codes labels, shorter subtitles, disabled flags, row classes, and actions
at `app.py:1062-1106`. The current test
`tests/test_web_layout.py:147-163` locks the row table, not that rendered rows
are sourced from it.

Before implementation, choose the exact visible-copy source: either make
`EXPORT_MENU_ROWS["description"]` the visible subtitle text, or split the row
schema into separate visible subtitle/guidance fields. Then render from the
row schema and add tests that fail when visible labels, disabled states, or
guidance copy drift from `EXPORT_MENU_ROWS`.

### O4 - `_state_snapshot` needs a declared schema and compatibility test

Severity: Low

`_state_snapshot` hand-rolls a growing key list at
`kayakgen/ui/web/app.py:518-537`, including legacy CFD aliases consumed by
`_cfd_status_from_state` (`kayakgen/ui/web/controllers.py:1083-1105`). It also
includes optional keys such as `mesh_package_ref` that are not initialized on
every app instance. This is a maintenance issue, not a runtime bug today.

Move the key list into a named schema, preferably near
`kayakgen/ui/web/state.py`, and add a compatibility test that preserves the
current snapshot keys and controller behavior for `mesh_package_ref`,
`cfd_mesh_package_ref`, `cfd_status`, `status`, `cfd_payload`,
`cfd_job_payload`, `cfd_last_payload`, and `cfd_status_lines`. Do not change
REST payload shapes.

### O5 - `PARAMETER_RAIL_CSS` root-token cleanup is only safe if a global token injection remains

Severity: Low

`PARAMETER_RAIL_CSS` prepends `theme.css_root_block()` at
`kayakgen/ui/web/app.py:201-210` and is injected at `app.py:919`. I did not find
another active web-layout root-token injection path. A blind deletion would
drop variables such as `--type-label` and `--text-secondary` from the page.
The current static test also expects token definitions inside
`PARAMETER_RAIL_CSS` (`tests/test_web_layout.py:92-103`).

The cleanest implementation is to inject `theme.css_root_block()` once as a
global style and leave `PARAMETER_RAIL_CSS` as only the scoped slider-label
rule. If the ledger chooses not to split that injection, this review records
the rationale RFC 0035 allows for retaining the duplicate root block. In both
cases, update tests so they assert token usage in rail CSS and token
definitions through the chosen global theme path.

### O6 - Slider wrapper accessibility proof is close but too permissive

Severity: Low

The wrapper adds `role="group"` and `aria-label` in
`kayakgen/ui/web/app.py:246-254`, around the `VSlider` rows at
`app.py:980-993`. Static tests prove the canonical label strings and wrapper
attrs (`tests/test_web_layout.py:60-90`), and browser tests prove rendered
label geometry plus that the label appears somewhere in row aria values
(`tests/test_web_browser.py:320-423`). RFC 0035 asks for one clear accessible
name per slider row; the current browser assertion is not strict enough for
that.

Add Playwright assertions for the chosen semantics, such as exactly one named
`group` per parameter row and a synchronized accessible slider name or
described-by relationship for the control inside that row. Keep the existing
geometry checks; they are useful and not screenshot-brittle.

### O7 - Docs and changelog are in scope, but only for visible cleanup

Severity: Low

`AGENTS.md` requires changelog updates for RFC/workflow/user-facing changes,
and RFC 0035 acceptance explicitly includes docs/changelog alignment. The
workflow source packet lists `docs/USER_GUIDE.md` but not `CHANGELOG.md` or the
workflow 0045 ledger, even though the 0045 ledger carries the prior validation
and docs/changelog discipline.

Implementation should update `docs/USER_GUIDE.md` for user-visible semantic
changes such as the badge behavior and preset edit wording. `CHANGELOG.md`
should record the landed cleanup/workflow status. Invisible refactors such as
snapshot-schema centralization do not need standalone user-guide prose.

## Recommended Gates

Minimum focused gates for the implementation lane:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_read_models.py tests/test_ui_theme.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

Run the full non-browser suite before final review if both web and desktop
surfaces are touched:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

Keep the forbidden-copy regression in
`tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
as the primary no-claims gate; supplemental grep is useful in review, but docs
and RFC no-goal sections intentionally contain deferred/forbidden terms.

## Validation Performed

I ran these checks from the repository root:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_web_read_models.py tests/test_ui_theme.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

Results: `git diff --check` produced no output; web layout/read-model/theme
passed `34 passed`; desktop layout/gui params passed `4 passed`; browser
acceptance passed `1 passed`.

I did not run the full non-browser suite because this was a first-pass review
artifact, not an implementation landing.
