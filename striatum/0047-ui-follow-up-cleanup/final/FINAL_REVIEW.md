author: operator [self-declared: operator-0047-final-review]
schema_version: striatum.final_review.v1
kind: final_review
logical_name: final_review
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_7077d82547f5429f98491789b9b0b21f
job: job_run_489eb28aa3e0453b916113addacd02e3_final_review
lease: lease_78012e1f4d074ef3b6a9a7176e4549f1
date: 2026-05-14

# Final Review — Workflow 0047 UI Follow-Up Cleanup

## Verdict

`accept_with_findings`

The implementation lane stays inside the RFC 0035 / ledger F1-F6 cleanup
boundary. Validity badge classification, preset edit semantics, export-menu
single source, state snapshot schema, slider-label CSS/accessibility split,
and the desktop Matplotlib shim comment are all in place. Focused gates pass
(39 web layout/read-model/theme; 4 desktop; full 333-test suite per the
patch summary, re-checked in this review for the targeted slices). No
backend, solver, calibration, stability, watertight-readiness, hosted, or
desktop-parity surface was widened. The findings below are non-blocking
quality refinements for successor scope.

## Findings

Ordered by severity. None block landing.

### FR1 — Preset seed-listener proof is partial (low)

Ledger F2 allowed retaining `_state_matches_preset_seed`
(`kayakgen/ui/web/app.py:529-542`) only with a focused test that documents
the exact reachable same-value/seed event sequence. The retained test
`test_preset_seed_listener_reapplies_bounds_without_custom_flip`
(`tests/test_web_layout.py:374-388`) directly invokes
`_on_hull_param_change()` after artificially widening
`length_m_min`/`length_m_max`, and asserts the listener re-narrows the
bounds without flipping to `custom`. That pins the steady-state listener
behavior under a no-op same-value call, but does not drive the *Trame*
event sequence the patch summary cites ("Trame can fire same-seed hull
events after preset application"). The browser acceptance test
(`tests/test_web_browser.py:502-512`) exercises the slider-change path
that flips to `custom`, not the same-seed path that keeps the preset.

Why this matters: the ledger's stated reason for keeping the branch was a
real Trame interaction. The current pin is sufficient as a regression
gate for the helper itself, but not as evidence that the cited Trame
event actually exists.

How to apply (successor): add a browser-acceptance step that lands the
slider back to within `1e-9` of the preset seed via ArrowRight/ArrowLeft
nudges and asserts the preset stays non-custom; or remove the branch and
keep the static test as a no-flip regression. Either resolves the residual
gap. Not required for this slice.

### FR2 — Export-row schema carries duplicate guidance fields (very low)

`EXPORT_MENU_ROWS` (`kayakgen/ui/web/app.py:104-166`) keeps both `subtitle`
(used by `_render_export_menu` at `app.py:1119-1130`, matches shipped UI)
and `description` (longer "Download …" sentences, read-model contract).
The visible-copy decision is correctly the conservative one (E2 option 1
from the ergonomics review): shipped subtitles are preserved byte-for-byte
and tests at `tests/test_web_layout.py:191-197` lock them. The cost is two
fields that say almost the same thing on three of five rows.

How to apply (successor): if a future workflow consolidates the read-model
contract, collapse to a single `subtitle` field and remove `description`.
Acceptable today because the existing test surface pins drift in either
field.

### FR3 — Mesh-package label ellipsis remains (very low)

`EXPORT_MENU_ROWS[4]["label"]` is still `"Mesh package..."`
(`kayakgen/ui/web/app.py:151`). The ergonomics review (E3) flagged that
trailing `...` typically signals "opens a dialog," which is misleading
for a permanently disabled row. The ledger explicitly defers this polish
("`Mesh package...` is optional and requires an explicit changelog note
if it lands"), and the patch summary records it as deferred. No
inconsistency, just an acknowledged successor item.

### FR4 — `_state_snapshot` keys overlap with controller alias scan (very low)

`STATE_SNAPSHOT_KEYS` (`kayakgen/ui/web/app.py:241-254`) declares the
schema and the compatibility test at
`tests/test_web_layout.py:219-257` exercises optional/None and
populated-value behavior for `mesh_package_ref`, `cfd_status`,
`cfd_payload`, etc. `_cfd_status_from_state`
(`kayakgen/ui/web/controllers.py:1083-1105`) reads the same alias list.
The list is duplicated across the two files. Acceptable for this cleanup
slice because both copies have explicit tests
(`tests/test_web_read_models.py:135-153`) that fail on drift, and the
ledger forbade backend-shape changes.

How to apply (successor): if `state.py` grows a typed snapshot schema in
a later workflow, collapse the two copies. Out of scope here.

## Scope and No-Claims Check

Verified the patch stays inside the ledger-approved F1-F6 envelope:

- **F1 (validity badge — all envelopes).** `validity_badge_from_state`
  (`kayakgen/ui/web/controllers.py:128-141`) now calls
  `_matching_kayak_class` (`controllers.py:1034-1038`) over all `CLASSES`
  using the five-field web helper (`_hull_in_kayak_class`,
  `controllers.py:1041-1053`) before the existing L/B_wl custom branches.
  Vocabulary (`In <class> envelope`, `Custom — sub-touring`,
  `Custom — beyond elite`, `Custom (L/B_wl=X.X)`) is byte-for-byte
  preserved; tests at `tests/test_web_read_models.py:55-92` cover the
  four allowed strings, custom-flagged hull inside an envelope, and a
  five-field-only boundary that desktop's length/beam classifier would
  match. Class definitions, preset IDs, and reseed/narrow code are
  untouched.

- **F2 (preset edit model).** Five-field reseed/narrow preserved
  (`app.py:486-527`); hull-shaping edits flip to `custom`
  (`tests/test_web_layout.py:359-372`); target speed does not
  (`tests/test_web_layout.py:391-403`); seed short-circuit retained with
  proof (see FR1 for the partial-proof note). No new visual markers, no
  rail grouping change, no selector consolidation.

- **F3 (export menu single source).** `_render_export_menu`
  (`app.py:1109-1130`) iterates `EXPORT_MENU_ROWS`. Schema owns label,
  status/availability/disabled, row class, action key, subtitle, and
  description; visible subtitle copy is byte-identical to the prior UI
  (`tests/test_web_layout.py:160-216`). Enabled rows remain Hull STL,
  Deck STL, Hydro JSON. Stability JSON and Mesh package stay
  `unavailable`.

- **F4 (state snapshot schema).** `STATE_SNAPSHOT_KEYS`
  (`app.py:241-254`) declares the keys; `_state_snapshot`
  (`app.py:576-581`) iterates the tuple. All legacy CFD aliases retained
  (`cfd_status`, `status`, `cfd_payload`, `cfd_job_payload`,
  `cfd_last_payload`, `cfd_status_lines`, `mesh_package_ref`,
  `cfd_mesh_package_ref`) with explicit test coverage. No REST route
  shape change.

- **F5 (slider-label CSS + accessibility).** `ROOT_THEME_CSS` is split
  from `PARAMETER_RAIL_CSS` (`app.py:229-239`) and both are injected
  exactly once each at `app.py:965-966`. Rail CSS uses only
  `var(--type-label)` and `var(--text-secondary)` and contains no
  `:root` block (`tests/test_web_layout.py:93-116`). The
  `slider.label.rail` contrast pair survives at
  `kayakgen/ui/theme.py:340`. Wrapper `role="group"` with canonical
  `aria-label` plus one slider control per row is asserted statically
  (`tests/test_web_layout.py:61-90`) and in the browser
  (`tests/test_web_browser.py:426-453`, including the
  `count() == len(expected)` cardinality check and the strict
  `get_by_role("group", name=…, exact=True).count() == 1` line).

- **F6 (desktop Matplotlib shim).** Single-line removal-condition comment
  added at `kayakgen/ui/desktop.py:47`; `_SLIDER_SUPPORTS_LABEL_LOCATION`
  semantics unchanged; desktop bbox/gui tests pass (4 tests, 3.22 s).
  No Qt-native, `QMainWindow`, layout-redesign, or threshold-loosening
  changes.

No-overclaim boundary preserved:

- `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
  and `test_persistent_claim_readiness_and_cfd_copy_is_static_and_exact`
  both pass in this review run.
- No backend, REST route shape, hosted service, worker queue, cloud
  storage, real solver, calibrated drag, final prediction, design
  fitness, real `GZ_max`/`heel_angle_max_deg`/capsize-range, watertight
  promotion, bare `cfd_ready`, web-side mesh-package authoring, or new
  class/geometry/profile definitions added or implied. The mesh
  watertight-solid row remains `disabled` and the disabled-tooltip copy
  is unchanged.
- `CHANGELOG.md` describes the slice as "maintenance cleanup only" and
  repeats the boundary list. `docs/USER_GUIDE.md` adds only the
  five-field preset rule and the canonical-envelope badge wording,
  inside RFC 0033/0034 vocabulary.

## Validation Reviewed

Re-ran the ledger's required gates from the repository root during this
review (read-only test invocations only):

- `git diff --check` → no output.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
  tests/test_web_layout.py tests/test_web_read_models.py
  tests/test_ui_theme.py -q -p no:cacheprovider` → `39 passed in 9.80s`.
- `PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m
  pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p
  no:cacheprovider` → `4 passed in 3.22s`.

The patch summary additionally records `333 passed in 89.05s` for the
full non-browser suite and `1 passed in 10.41s` for the browser
acceptance suite; both were not re-run here to stay inside the focused
gate envelope. Spot-checks against code/tests confirm:

- The F1 web-canonical five-field boundary test
  (`tests/test_web_read_models.py:80-92`) drives a hull desktop's
  length/beam classifier would match but the five-field web envelope
  rejects, pinning the intentional behavior.
- The F5 cardinality assertion
  (`tests/test_web_browser.py:442-453`) is strict — exactly one
  `role='group'` per row, exactly one `role='slider'` per row, no
  nested groups, visible label byte-for-byte matches the canonical
  label.
- The F6 desktop diff is exactly the comment line and no behavioral
  change.

## Residual Risk / Follow-Up

Non-blocking successor items for a later workflow:

1. **Preset seed-listener Trame proof (FR1).** Either remove
   `_state_matches_preset_seed` or add a browser step that drives the
   same-value/seed Trame event sequence end-to-end so the retention
   rationale is observably true.
2. **Export-row schema consolidation (FR2).** If a future workflow
   touches the read-model contract, collapse `subtitle`/`description`
   into a single field once a successor decides the canonical wording.
3. **`Mesh package...` ellipsis polish (FR3).** Optional label
   normalization (`Mesh package` or `Mesh package (CLI only)`),
   explicitly deferred by the ledger.
4. **Snapshot-schema unification (FR4).** Move the snapshot key tuple
   into `kayakgen/ui/web/state.py` when a typed snapshot type is
   warranted.
5. **Larger deferrals (unchanged from RFC 0035 §Non-Goals and the
   ledger).** Desktop parity rewrite, Qt-native slider replacement,
   `QMainWindow` migration, hosted CFD/demo, real OpenFOAM/SU2 adapters,
   calibrated drag, final prediction, design fitness, real high-angle
   `GZ` / `GZ_max` / `heel_angle_max_deg` / capsize range, web-side
   mesh-package authoring beyond existing safe entries, and watertight
   `cfd_ready` promotion all remain out of scope and unimplied. Any of
   these requires a separate RFC/workflow.
