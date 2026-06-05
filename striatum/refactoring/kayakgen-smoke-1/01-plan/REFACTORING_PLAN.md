---
schema_version: "striatum.work_plan.v1"
artifact_kind: "work_plan"
plan_id: "plan_kayakgen-smoke-1-split-ui-web-app"
scope_kind: "initiative"
scope_ref: "striatum/refactoring/kayakgen-smoke-1/00-goal/GOAL_DECISION.md"
state: "open"
opened_at: "2026-06-05"
closed_at: null
closure_summary: null
supersedes: null
retrieval_priority: "medium"
---

author: plan-holder-claude-001

# Refactoring Plan — kayakgen-smoke-1: split `kayakgen/ui/web/app.py` along the Generate-panel seam

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (author_plan)
Input contract: `striatum/refactoring/kayakgen-smoke-1/00-goal/GOAL_DECISION.md`
(decision `dec_e526052a732d40b385a892b3e78680be`, Goal B accepted)
Tree state at preflight: `main` @ `85aaf94`, working tree clean.

This is the claim the falsifiers will challenge. Challenge completion is not
acceptance; the adjudicator ledger decides whether the gate clears.

---

## 1. Preflight transcript (executed 2026-06-05, this environment)

### 1.1 Dirty-path check

`git status --short` → empty. No dirty paths; no overlap with the blast
radius. No stop condition from tree state.

### 1.2 Baseline verification results

| Command | Result | Time |
|---|---|---|
| `.venv/bin/python -m pytest -q` | **RED: 1 failed, 1307 passed, 4 skipped** | 8:26 |
| `.venv/bin/python -m ruff check kayakgen tests` | PASS (exit 0; 6 benign "invalid `# noqa` directive" warnings in `generate_frontier_view.py`, pre-existing) | <5s |
| `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` | **GREEN: 4 passed, 2 deselected** | 37.79s |
| Extras-less suite (see §1.3) | **20 failed, 1114 passed, 24 skipped, 4 errors** — all pre-existing | 6:12 |

**Pre-existing full-suite failure (named, per the red-baseline rule):**

- `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
  — `kayakgen/services/evaluation.py` imports `HYDROSTATICS_ROW_METADATA`
  from `kayakgen.ui.hydrostatics_metadata`. Deterministic (confirmed by
  isolated rerun: `1 failed, 15 passed in 0.10s`). Entirely outside this
  campaign's blast radius (services ↔ `kayakgen/ui/` root module; nothing in
  `kayakgen/ui/web/`). **The per-slice bar is therefore "no new failures":
  this one test id is the only tolerated failure in every per-slice full-suite
  run.** Fixing it is out of scope (it is a code change in `services/`, not a
  web-package move).
- No flakes observed; nothing needed a rerun beyond the determinism
  confirmation above.

**Decision-text discrepancy, surfaced for the falsifiers/adjudicator:** the
goal decision §3 freezes `tests/test_services_boundaries.py` as "must stay
green, not weakened." It is red on unmodified `main` today. This campaign
cannot make it green (out of scope) and must not weaken it. The honest
restatement this plan adopts: *the file is untouched, and its failure set
must remain exactly `{test_services_does_not_import_ui_or_cli[path2]}` —
no growth, no edits.*

**Browser gate (stage-1 preflight obligation 1, revisit condition 1):**
re-run on unmodified `main` at execution time: **4 passed, 2 deselected in
37.79s** — green, matching the arbitration's run (4 passed, 2 deselected,
34.29s). Revisit condition 1 does **not** fire.

### 1.3 Extras-less run (stage-1 preflight obligation 3)

Method: fresh venv with only kayakgen's core deps (`numpy`, `numpy-stl`,
`pydantic`, `typer`, `click`) plus `pytest`/`pytest-benchmark`; suite run
from the repo with `PYTHONPATH=<repo>`,
`pytest -q -p no:cacheprovider --continue-on-collection-errors`.

Result: **20 failed, 1114 passed, 24 skipped, 4 errors.** Every failure and
error is pre-existing on unmodified `main` and attributable to one mechanism:
**`trame`/`aiohttp` are absent without `[web]` extras, and a set of test
files exercises web code without an `importorskip` guard.** The package
itself does not leak: `import kayakgen`, the CLI module, and all 1114
non-web tests are green.

The named pre-existing extras-less red set:

- **Collection errors (2):** `tests/test_generate_spec_form.py`,
  `tests/test_hull_parameter_metadata.py` — both import
  `kayakgen.ui.web.generate_spec_form`, which imports trame at module level,
  with no guard.
- **Runtime errors (2):** `tests/test_cli_serve.py::test_serve_defaults_to_subprocess_manager`,
  `::test_serve_jobs_in_process_opt_in` — the `mock_server_start` fixture
  patches `kayakgen.ui.web.app.KayakgenApp`, which imports trame.
- **Failures (20):** 4 in `tests/test_generative_jobs_fork.py` + 15 in
  `tests/test_generative_jobs_web.py` (`ModuleNotFoundError: aiohttp` —
  aiohttp arrives only via trame's deps) + the services-boundary failure
  from §1.2.

**Per-slice extras-leak bar:** this exact set must not grow. The cheap
per-slice guard is `noweb-venv python -c "import kayakgen, kayakgen.cli.main"`
(must succeed); the full extras-less suite is re-run once after the final
slice and must reproduce the same failure/error id set.

**Precedent worth naming:** existing sibling `generate_spec_form.py` imports
trame at module level. The "[web] extras gating" frozen surface therefore
does *not* require function-local trame imports in siblings; it requires
that nothing reachable from `import kayakgen` or the gated CLI path imports
trame at import time. Extracted siblings may import trame at module level
exactly as `generate_spec_form.py` does, because only `app.py` (itself
behind the CLI's try/except gate) imports them.

### 1.4 `test_cli_serve.py` jobs-root pin (stage-1 preflight obligation 2)

`tests/test_cli_serve.py` exercises the serve → `_default_generative_jobs_root_for_app`
path with `KAYAKGEN_GENERATIVE_JOBS_ROOT` set, but asserts only
`"jobs_root=" in result.output` — **it never asserts the resolved value.**
If the slice-3 redirect silently broke env-var resolution (alias pointing at
a stale copy), the test would still pass on the home-dir fallback. Proposal
B §6's one-line characterization test is therefore **needed**: assert the
echoed `jobs_root` equals the env-var path (one assertion in each of the two
manager tests). This is step S0, an edit slice that lands before any move.

### 1.5 Generated files in the blast radius

None. No `DO NOT EDIT`/generated markers anywhere in `kayakgen/ui/web/`;
proposal B's "no generated sources" claim re-verified.

### 1.6 Coverage sufficiency decision

Existing coverage is sufficient to proceed: 4,798 test lines across 9 web
test files, DOM-identifier layout pins, lifecycle pins, and a green
real-browser acceptance profile. Exactly one characterization gap was found
(§1.4), closed by S0. No other characterization tests are required before
movement; mechanical verification (full suite + targeted files + browser
gate) covers every slice. The campaign does **not** stop at this gate for
coverage reasons.

## 2. Files read

`kayakgen/ui/web/app.py` (all 2,550 lines: structure, section markers,
import block), `kayakgen/ui/web/__init__.py`, `state.py`, `controllers.py`,
`read_models.py` (import posture), `generate_spec_form.py` (trame-import
precedent), `kayakgen/cli/main.py:630-676` (serve command, both import
sites), `tests/test_cli_serve.py` (whole file), `tests/conftest.py`,
guard/attribute-access audit of all 9 web test files, `pyproject.toml`
(extras, pytest config), `GOAL_DECISION.md`, `proposals/GOAL_B.md`,
stage-1 workflow role/prompt files.

## 3. Current behavior and invariants

`app.py` is the integrator for the trame web UI: module-level presentation
constants/CSS/copy (lines ~98–700), pure helpers (`validity_badge_title_for`,
`_param_row_raw_attrs`, `_pre_html`, `_resistance_table_html`,
`_generative_job_state_flags`), VTK builders (`_build_polydata`,
`_make_actor`), the jobs-root resolver (`_default_generative_jobs_root_for_app`),
then `class KayakgenApp` (no base classes) organized by section markers —
`# ----- parameter rail state -----` (985), `# ----- 3D scene -----` (1045),
`# ----- handlers -----` (1072), `# ----- generative-jobs panel -----`
(1473), `# ----- layout -----` (1752) — and `create_app` (2533).

Invariants this plan preserves:

1. `kayakgen.ui.web.app:create_app` and `KayakgenApp` import paths and
   signatures unchanged.
2. Every module-level name of `app.py` that tests access stays importable
   from `kayakgen.ui.web.app` (see §4 finding F1 — this is a *wider* set
   than the decision's "two symbols").
3. `cli/main.py` serve behavior identical; at most two import lines
   redirected; `_default_generative_jobs_root_for_app` keeps resolving
   `KAYAKGEN_GENERATIVE_JOBS_ROOT` then the home fallback.
4. Generative-job state-transition order observed by
   `generate_state_listener` and the web UI: preserved verbatim.
5. `LAYOUT_TEST_IDS`/`REGION_CLASSES` values, DOM identifiers, widget
   construction order: unchanged (browser gate is the end-to-end witness).
6. `import kayakgen` and the CLI without `[web]` extras keep working; the
   extras-less failure set of §1.3 does not grow.
7. Dependency direction inside the package stays sibling → imported-by-app;
   no sibling imports `app.py`.

## 4. Planning findings the decision did not anticipate

These are surfaced honestly for the falsifiers and the adjudicator rather
than planned around silently.

**F1 — tests reach ~21 module-level names of `app.py`, not 2.** The
decision (§1) and proposal B (§3) claim tests import only
`create_app`/`KayakgenApp`. An attribute-access audit shows web tests also
access `EXPORT_MENU_ROWS`, `REVIEW_TABS`, `STATUS_SEGMENTS`,
`LAYOUT_TEST_IDS`, `REGION_CLASSES`, `RESPONSIVE_CLASS_HOOKS`,
`ROOT_THEME_CSS`, `WORKSPACE_SHELL_CSS`, `PARAMETER_RAIL_CSS`,
`SLIDER_DEFS`, `PARAMETER_GROUPS`, `CLASS_PRESETS`, `CLASS_PRESET_OPTIONS`,
`PERSISTENT_COPY`, `STATE_SNAPSHOT_KEYS`, `HIGH_ANGLE_GZ_COPY`,
`MESH_NO_PACKAGE_CHIP_TITLE`, `MESH_LIVE_READINESS_CHIP_TITLE`,
`validity_badge_title_for`, `_param_row_raw_attrs`,
`_generative_job_state_flags` (plus one `__import__(..., fromlist=["REVIEW_TABS"])`).
*Assessment:* this does not break the production blast-radius premise —
`cli/main.py:657` remains the only production importer of an `app.py`
internal, and the 9 test files were already inside the declared blast
radius. It is handled by explicit by-name re-export imports in `app.py`
(precedent: `STATE_SNAPSHOT_KEYS` is already re-exported from `state.py`
today). Whether this counts as revisit condition 3 ("importers of app.py
internals beyond cli/main.py:657") is the adjudicator's call, not this
plan's; the plan's position is that condition 3 targets production callers
and does not fire.

**F2 — 29 source-text assertions read `app.py`'s own source.** Three
editable test files call `Path(web_app.__file__).read_text()` and assert
substrings of `app.py` source: `tests/test_web_layout.py` (21 sites, mostly
layout/render construction code — slice S4 territory),
`tests/test_web_inline_help.py` (6 sites, constant *content* and usage ids —
the file's own comment says "defined in app.py"; S1/S4 territory),
`tests/test_hydro_tab_descriptions.py` (2 sites). When a slice moves code
out of `app.py`, the assertion substring leaves `app.py`'s source, so the
test would fail with behavior fully preserved. *Consequence:* slices S1, S4
and S5 are **not** pure source moves; each must carry a mechanical
test-pointer redirect in the same commit — repoint the
`read_text()` source target to the module where the moved code now lives,
**assertion strings unchanged**. The frozen file `tests/test_web_browser.py`
does *no* source reading (verified) and stays untouched. *Assessment
against revisit condition 2 ("any slice cannot be a pure code move"):* the
*source* move stays pure and byte-preserving; the test edits are mechanical
pointer redirects that preserve every assertion string. The plan declares
this openly as the falsifiers' cleanest attack surface on the "move-only"
premise; if the adjudicator reads condition 2 strictly to forbid any
same-slice test edit, the decision returns to arbitration per its own
terms. (Rejected alternative: an `app_source` helper concatenating all
package module sources — fewer edits, but it weakens "this string exists in
this file" to "exists somewhere in the package," which trips the
not-weakened bar.)

**F3 — full-suite baseline is red** (§1.2) inside a frozen "must stay
green" file. Bar restated as: failure set stays exactly
`{tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]}`.

**F4 — extras-less profile is red on main** (§1.3, 20F+4E, all named). Bar:
set must not grow; package-level imports stay clean.

## 5. Frozen-surface inventory (verified against the tree)

From decision §3, re-verified at preflight:

| Surface | Witness | Status at baseline |
|---|---|---|
| `kayakgen serve` CLI (name, options, output, exit) | `tests/test_cli_serve.py` (3 tests) | green (with extras) |
| `create_app` / `KayakgenApp` import paths + signatures | 12 import sites across tests + CLI | verified, 2 production sites at `cli/main.py:648,657` |
| `_default_generative_jobs_root_for_app` keeps working for `cli/main.py:657` | `test_cli_serve.py` + S0's strengthened assertion | weakly pinned today (§1.4); S0 closes |
| Generative-job state-transition order | `tests/test_generative_jobs_web.py` | green |
| `browser_acceptance` marker + `tests/test_web_browser.py` untouched | `pyproject.toml:66`; file does no app-source reading | green, 4 passed/2 deselected |
| `tests/test_import_boundaries.py`, `tests/test_services_boundaries.py` not weakened | files untouched by every slice | import-boundaries green; services-boundaries red pre-existing (F3) |
| `[web]` extras gating | §1.3 method + per-slice import check | holds at package level (test-file leaks pre-existing, named) |
| `LAYOUT_TEST_IDS` / `REGION_CLASSES` values, widget order | `tests/test_web_layout.py` + browser profile | green |
| Globally frozen, far from blast radius (schemas, golden STL, claim vocabulary, root shims, artifact store, OpenFOAM case) | n/a | not approached by any slice |

## 6. Target shape and move mechanics

Five new sibling modules inside `kayakgen/ui/web/` (names settled here;
seam boundaries are the decision's):

| Module | Receives | Trame at module level? |
|---|---|---|
| `presentation.py` | constants/CSS/copy (≈98–711) + pure helpers `validity_badge_title_for`, `_param_row_raw_attrs`, `_pre_html`, `_resistance_table_html`, `_generative_job_state_flags` | no (pure) |
| `scene.py` | `_build_polydata`, `_make_actor`, `# ----- 3D scene -----` methods | yes (vtk) — allowed per §1.3 precedent |
| `generate_panel.py` | `# ----- generative-jobs panel -----` methods (1473–1751) + `_default_generative_jobs_root_for_app` | no (state/manager logic; keeps the cli redirect trame-free) |
| `layout.py` | `# ----- layout -----` (1752–2532): `_build_layout`, `_region_attrs`, all `_render_*` | yes (trame widgets) |
| `handlers.py` | `# ----- handlers -----` (1072–1472) | yes (minimal) |

**Method moves use mixins.** `KayakgenApp` has no base classes today.
Method regions move verbatim into `SceneMixin`, `GeneratePanelMixin`,
`LayoutMixin`, `HandlersMixin`; `app.py` declares
`class KayakgenApp(HandlersMixin, GeneratePanelMixin, LayoutMixin, SceneMixin):`
(methods are disjoint, so MRO is inert). This keeps every method body
byte-identical — the strongest available preservation claim — and keeps
`KayakgenApp`'s public surface, attribute set, and trame binding objects
identical. (Rejected alternative: module functions + delegating stubs —
larger net diff, touches every call site internally.)

**Constant moves use by-name re-export imports** in `app.py` (precedent:
the existing `state.py` import block), so every F1 name keeps resolving
via `kayakgen.ui.web.app`. The `# noqa: F401` convention for re-exports
follows the existing tree style.

`app.py` settles as: import/re-export block, `__init__` + parameter-rail
state (985–1044, which stay), mixin composition, `create_app`. Projected
size ≈ 400–450 lines ≤ the goal's ~600 cap, with margin.

## 7. Step table

Every slice: one commit, independently revertible by `git revert` of that
commit; gross-moved lines are relocation; **net diff** = non-relocation
lines (imports, mixin/class declarations, aliases, test-pointer redirects).
A slice exceeding its net-diff cap stops the campaign (stop condition 3).
"Full suite" tolerates exactly the F3 singleton; "import check" =
`noweb-venv python -c "import kayakgen, kayakgen.cli.main"`.

| id | change | files | preservation claim | verification | rollback unit | est. size (gross moved / net) | max net-diff cap |
|---|---|---|---|---|---|---|---|
| S0 (edit) | Characterization: assert echoed `jobs_root` equals `KAYAKGEN_GENERATIVE_JOBS_ROOT` in both manager tests | `tests/test_cli_serve.py` | Documents current resolution; no source change | `pytest -q tests/test_cli_serve.py` + full suite + ruff | revert S0 commit | 0 / ~4 | 10 |
| S1 (move) | Presentation constants/CSS/copy + 5 pure helpers → `presentation.py`; by-name re-exports in `app.py` | `kayakgen/ui/web/presentation.py` (new), `app.py` | Byte-identical constant values and helper bodies; every F1 name still importable from `app.py` | decision row 1 targeted files, then full suite + ruff + import check | revert S1 commit | ~655 / ~60 | 80 |
| S1t (edit, same commit as S1) | Repoint source-reading assertions whose target text moved in S1; strings unchanged | `tests/test_web_inline_help.py`, `tests/test_hydro_tab_descriptions.py`, `tests/test_web_layout.py` (subset) | Same assertions, applied where the code now lives | included in S1's runs | revert S1 commit | 0 / ~12 | 20 |
| S2 (move) | VTK builders + scene methods → `scene.py` (`SceneMixin`) | `kayakgen/ui/web/scene.py` (new), `app.py` | Byte-identical actor/mesh construction; no state-key changes | full suite + ruff + import check | revert S2 commit | ~64 / ~25 | 40 |
| S3 (move) | Generative-jobs panel methods → `generate_panel.py` (`GeneratePanelMixin`) + `_default_generative_jobs_root_for_app` move; redirect `cli/main.py:657`; alias kept in `app.py` | `kayakgen/ui/web/generate_panel.py` (new), `app.py`, `kayakgen/cli/main.py` (≤2 import lines) | Submit/cancel/fork/resume payloads and transition order unchanged; jobs-root resolution value-pinned by S0 | `pytest -q tests/test_generative_jobs_web.py tests/test_cli_serve.py`, full suite + ruff + import check + browser run (cheap insurance, non-gating) | revert S3 commit | ~295 / ~50 | 60 |
| S4 (move) | Layout construction → `layout.py` (`LayoutMixin`) | `kayakgen/ui/web/layout.py` (new), `app.py` | `LAYOUT_TEST_IDS`/`REGION_CLASSES` values, DOM ids, widget construction order unchanged | `pytest -q tests/test_web_layout.py`, full suite + ruff + import check + **browser acceptance (mandatory gate)** | revert S4 commit | ~781 / ~60 | 80 |
| S4t (edit, same commit as S4) | Repoint the bulk of `test_web_layout.py` source assertions to `layout.py`; strings unchanged | `tests/test_web_layout.py`, `tests/test_web_inline_help.py` (usage-id subset) | Same assertions, new source target | included in S4's runs | revert S4 commit | 0 / ~25 | 40 |
| S5 (move) | Handlers → `handlers.py` (`HandlersMixin`); `app.py` settles as integrator ≤~600 lines | `kayakgen/ui/web/handlers.py` (new), `app.py` | `create_app`/`KayakgenApp` paths + signatures unchanged; trame ctrl/state bindings identical | full suite + ruff + import check + **browser acceptance (mandatory gate)** + full extras-less suite re-run (failure set must equal §1.3's) | revert S5 commit | ~401 / ~70 | 100 |

Order: S0 → S1 → S2 → S3 → S4 → S5. Only S5-after-S3/S4 is structurally
forced (handlers reference panel and layout symbols); the rest is
risk-ordered per proposal B.

Per-slice verification cost at baseline rates: ~9 min (full suite + ruff),
+38s browser where gated, +6 min extras-less full run once at S5.

## 8. Verification command inventory

| Command | When |
|---|---|
| `.venv/bin/python -m pytest -q` | every slice (bar: failure set == F3 singleton) |
| `.venv/bin/python -m ruff check kayakgen tests` | every slice (bar: exit 0) |
| `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` | mandatory after S4, S5; insurance after S3 (bar: 4 passed, 2 deselected) |
| Decision §4 slice-targeted file lists | per matching slice |
| `noweb-venv python -c "import kayakgen, kayakgen.cli.main"` | every slice |
| Extras-less full suite (§1.3 method) | once after S5 (bar: failure/error id set identical to §1.3) |

## 9. Stop conditions

The campaign stops (slice aborted, gate escalated to the adjudicator) if:

1. **Behavior change required** — any slice cannot complete as a pure code
   move (modulo the declared mechanical test-pointer redirects of F2 and
   the ≤2-line cli redirect of S3).
2. **Frozen surface blocks progress** — any §5 surface would have to change;
   includes any edit to `tests/test_web_browser.py`,
   `tests/test_import_boundaries.py`, or `tests/test_services_boundaries.py`.
3. **A slice exceeds its declared net-diff cap** (step table §7).
4. **The chosen goal turns out to be wrong** — any decision revisit
   condition fires: browser gate red/unrunnable on unmodified `main`
   (re-checked green at preflight), move-only premise fails beyond F2's
   declared mechanics, a *production* importer of `app.py` internals beyond
   `cli/main.py:657` is found, or the operator re-weights toward minimum
   risk.
5. **Scope creep** — the work crosses into features, bug fixes (including
   the tempting pre-existing F3/F4 reds — they stay red), schema changes,
   or dependency upgrades.
6. **Browser acceptance cannot be run** when S4 or S5 needs it —
   stop-the-slice, never waivable.
7. **New failure appears** in the full suite beyond the F3 singleton, or
   the extras-less failure set grows, or widget order / DOM identifiers
   change under the browser profile.
8. **Tree dirties inside the blast radius** before a slice starts
   (re-check `git status --short` per slice).
9. **Adjudicator reads F1/F2 as firing revisit conditions 2/3** — selection
   returns to arbitration with Goal A standing, per the decision's own
   terms.

## 10. What the falsifiers should attack first (plan-holder's honest list)

1. F2: is "pure move + mechanical test-pointer redirect in the same commit"
   acceptably inside the move-only premise, or revisit condition 2?
2. F1: does the ~21-name test-access surface void the decision's two-symbol
   premise (revisit condition 3), or is by-name re-export sufficient?
3. Mixin composition (§6): does introducing base classes on `KayakgenApp`
   count as a structural behavior change anywhere (MRO, `repr`, pickling,
   introspection-sensitive tests)?
4. The red baselines (F3, F4): does "no new failures" discipline hold up
   operationally across 6 slices, or does it mask regression channels?
5. S3's alias: `_default_generative_jobs_root_for_app` lives in
   `generate_panel.py` with an `app.py` alias — is the alias's lifetime
   ("temporary", per the decision) defined sharply enough?
