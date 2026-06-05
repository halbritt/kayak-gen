---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
inputs:
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_1/FALSIFIER.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_2/FALSIFIER.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/adjudicator/COLLABORATION_LEDGER_cycle_1.md"
  - "striatum/refactoring/kayakgen-smoke-1/00-goal/GOAL_DECISION.md"
---

author: committer-claude-001

# Committed Plan — kayakgen-smoke-1: split `kayakgen/ui/web/app.py` along the Generate-panel seam

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (commit_plan)
Supersedes: `striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md`
(plan `plan_kayakgen-smoke-1-split-ui-web-app`, author `plan-holder-claude-001`)

This is the stage-2 input contract. It is the holder plan with every binding
constraint from the adjudicator ledger discharged in place, and nothing else
changed.

## 0. Gate record and discharge map

The adjudicator ledger
(`striatum/refactoring/kayakgen-smoke-1/01-plan/adjudicator/COLLABORATION_LEDGER_cycle_1.md`,
cycle 1) records verdict **`accept_with_findings`**: the gate clears over
seven binding constraints C1–C7. The refusal branch was checked and not
taken. Revisit conditions 2 and 3 were ruled **not to fire** (conditional,
for condition 2, on C1 and C2 landing in this document — they land below).
Goal B stands; selection does not return to arbitration.

| Constraint | Discharged at | Discharge |
|---|---|---|
| C1 | §4 F2 (amended), §7 Table B row S4t | S4t patch-target redirect for `tests/test_generative_jobs_web.py:547` (chosen over the carve-out) |
| C2 | §4 F2 (amended), §7 Table B rows S1t/S4t/S5t | Per-function recipes for `test_web_layout.py:68` and `:397`; new S5t row; post-split scope of all 8 negative assertions stated |
| C3 | §7 preamble | Rollback restated LIFO-only; per-slice independent-revert claim removed; halt-at-Sn unwind path declared |
| C4 | §11 | Stage-2 `execute_slices.allowed_paths` re-scope precondition, carried verbatim |
| C5 | §8 rows 3–4, §9 stop condition 6 | Gating S4/S5 browser runs use strict mode (`KAYAKGEN_BROWSER_ACCEPTANCE=1`) |
| C6 | §6 table | `generate_panel.py` trame cell flipped to "yes"; rationale corrected to the `cli/main.py:648` extras gate |
| C7 | §12 | Ledger-anchored execution discipline declared |

Each discharge is marked **[discharges Cn]** where it lands. Per the
ledger's closing instruction, slicing must not begin until stage 2 holds
this document; if any constraint turns out undischargeable as specified,
that is a campaign stop per the refusal rule, not a license to improvise.

---

## 1. Preflight transcript (executed 2026-06-05; reproduced independently by falsifier 2)

### 1.1 Dirty-path check

`git status --short` → empty at preflight. No dirty paths; no overlap with
the blast radius. Stage 2 re-checks per slice (stop condition 8).

### 1.2 Baseline verification results — the recorded baseline

| Command | Result | Time |
|---|---|---|
| `.venv/bin/python -m pytest -q` | **RED: 1 failed, 1307 passed, 4 skipped** | 8:26 (falsifier 2 re-run: 8:14, identical failure id) |
| `.venv/bin/python -m ruff check kayakgen tests` | PASS, exit 0 | <5s |
| `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` | **GREEN: 4 passed, 2 deselected** | 37.79s (falsifier 2 re-run: 35.73s) |
| Extras-less suite (§1.3 method) | **20 failed, 1114 passed, 24 skipped, 4 errors** — all pre-existing | 6:12 |

**Pre-existing full-suite failure (named, per the red-baseline rule):**

- `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
  — `kayakgen/services/evaluation.py` imports `HYDROSTATICS_ROW_METADATA`
  from `kayakgen.ui.hydrostatics_metadata`. Deterministic. Entirely outside
  this campaign's blast radius. **The per-slice bar is "no new failures":
  this one test id is the only tolerated failure in every per-slice
  full-suite run.** Fixing it is out of scope.

**Decision-text discrepancy (carried from the holder plan):** the goal
decision §3 freezes `tests/test_services_boundaries.py` as "must stay
green"; it is red on unmodified `main`. The honest restatement this plan
adopts: *the file is untouched, and its failure set must remain exactly
`{test_services_does_not_import_ui_or_cli[path2]}` — no growth, no edits.*

**Browser gate:** green on unmodified `main` at preflight (4 passed,
2 deselected), matching the arbitration's run. Revisit condition 1 does
not fire.

### 1.3 Extras-less run

Method: fresh venv with only kayakgen's core deps (`numpy`, `numpy-stl`,
`pydantic`, `typer`, `click`) plus `pytest`/`pytest-benchmark`; suite run
from the repo with `PYTHONPATH=<repo>`,
`pytest -q -p no:cacheprovider --continue-on-collection-errors`.

Result: **20 failed, 1114 passed, 24 skipped, 4 errors**, every one
pre-existing and attributable to one mechanism: `trame`/`aiohttp` absent
without `[web]` extras, and a set of test files exercising web code without
an `importorskip` guard. The named set:

- **Collection errors (2):** `tests/test_generate_spec_form.py`,
  `tests/test_hull_parameter_metadata.py`.
- **Runtime errors (2):** `tests/test_cli_serve.py::test_serve_defaults_to_subprocess_manager`,
  `::test_serve_jobs_in_process_opt_in`.
- **Failures (20):** 4 in `tests/test_generative_jobs_fork.py` + 15 in
  `tests/test_generative_jobs_web.py` + the services-boundary failure
  from §1.2.

**Per-slice extras-leak bar:** this exact set must not grow. The cheap
per-slice guard is `noweb-venv python -c "import kayakgen, kayakgen.cli.main"`
(must succeed); the full extras-less suite is re-run once after the final
slice and must reproduce the same failure/error id set.

**Precedent worth naming:** existing sibling `generate_spec_form.py`
imports trame at module level. The "[web] extras gating" frozen surface
does *not* require function-local trame imports in siblings; it requires
that nothing reachable from `import kayakgen` or the gated CLI path imports
trame at import time. Extracted siblings may import trame at module level
exactly as `generate_spec_form.py` does.

### 1.4 `test_cli_serve.py` jobs-root pin

`tests/test_cli_serve.py` asserts only `"jobs_root=" in result.output`,
never the resolved value. S0's characterization edit closes this: assert
the echoed `jobs_root` equals the `KAYAKGEN_GENERATIVE_JOBS_ROOT` path in
both manager tests, before any move.

### 1.5 Generated files in the blast radius

None. No `DO NOT EDIT`/generated markers anywhere in `kayakgen/ui/web/`.

### 1.6 Coverage sufficiency decision

Existing coverage is sufficient to proceed. Exactly one characterization
gap (§1.4), closed by S0. The campaign does not stop at this gate for
coverage reasons.

## 2. Files read

Carried from the holder plan §2: `kayakgen/ui/web/app.py` (all 2,550
lines), `__init__.py`, `state.py`, `controllers.py`, `read_models.py`,
`generate_spec_form.py`, `kayakgen/cli/main.py:630-676`,
`tests/test_cli_serve.py`, `tests/conftest.py`, guard/attribute-access
audit of all 9 web test files, `pyproject.toml`, `GOAL_DECISION.md`,
`proposals/GOAL_B.md`, stage-1 workflow role/prompt files. The falsifiers
additionally verified the monkeypatch site, the union test, the negative
assertions, the stage-2 scaffold, and the browser witness's skip semantics
against the tree.

## 3. Current behavior and invariants

`app.py` is the integrator for the trame web UI: module-level presentation
constants/CSS/copy (lines ~98–700), pure helpers, VTK builders, the
jobs-root resolver, then `class KayakgenApp` organized by section markers —
parameter rail state (985), 3D scene (1045), handlers (1072),
generative-jobs panel (1473), layout (1752) — and `create_app` (2533).

Invariants this plan preserves:

1. `kayakgen.ui.web.app:create_app` and `KayakgenApp` import paths and
   signatures unchanged.
2. Every module-level name of `app.py` that tests access stays importable
   from `kayakgen.ui.web.app` (§4 F1).
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

## 4. Findings, as amended by the gate

**F1 — tests reach ~21 module-level names of `app.py`, not 2.** Handled by
explicit by-name re-export imports in `app.py` (precedent:
`STATE_SNAPSHOT_KEYS` re-export from `state.py`). The adjudicator ruled
revisit condition 3 does **not** fire: the condition targets production
callers; `cli/main.py:657` remains the only production importer of an
`app.py` internal. By-name re-export is sufficient for every **read**-path
name. The one **write**-path exception — the monkeypatch below — is
handled by C1 and sharpens, not voids, the premise.

**F2 (amended) — source-text assertions and the test-migration inventory.
[discharges C1, C2]**

Four editable test files (not three) carry declared, string-preserving
edits in the same commit as the move that displaces their target text:
`tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
`tests/test_hydro_tab_descriptions.py`, and — per C1 —
`tests/test_generative_jobs_web.py`. The frozen file
`tests/test_web_browser.py` does no source reading and stays untouched.
The default edit remains the mechanical pointer redirect: repoint the
`read_text()` source target to the module where the moved code now lives,
assertion strings unchanged. The named exceptions, with their per-function
recipes:

- **C1 — the `render_fork_button` monkeypatch
  (`tests/test_generative_jobs_web.py:547`). [discharges C1]**
  `monkeypatch.setattr(app_module, "render_fork_button", fake_render_fork_button)`
  writes to `app.py`'s namespace; S4 moves the sole consumer
  (`_render_generate_job_fork_buttons`, `app.py:2476–2495`) into
  `layout.py`, whose module globals the patch would never reach. Chosen
  repair: **S4t patch-target redirect** — in the same commit as S4, the
  test imports `kayakgen.ui.web.layout` and the setattr target becomes the
  layout module's namespace; the fake, the assertion
  `calls == ["done-job"]`, and every other string are unchanged (~2
  lines). Chosen over the carve-out because it preserves S4's "all
  `_render_*` move" shape and keeps the panel/layout seam clean. This is a
  declared edit to a frozen-surface **witness** file in the same commit as
  the move it witnesses; it is named here at the gate precisely so it is
  not an undeclared mid-slice discovery. Verification: stage-2 S4 full
  suite green modulo the F3 singleton, **including** the fork-button test.

- **C2(i) — the mixed-destination single read
  (`test_web_layout.py:68`,
  `test_parameter_slider_labels_spacing_and_accessibility_contract`).
  [discharges C2]** One `read_text()` feeds assertions whose targets land
  in two different modules. Recipe, executed as a declared split (a
  structural edit to the read, with every assertion string unchanged):
  - **S1t:** add
    `presentation_source = Path(web_app.__file__).with_name("presentation.py").read_text()`
    and move the `f'aria-label="{escaped_label}"'` assertion (target:
    `_param_row_raw_attrs`, moved by S1) onto it. All other assertions
    keep reading `app_source`.
  - **S4t:** add the analogous `layout.py` read and move the four
    slider-construction assertions (`thumb_label=True`,
    `'thumb_label="always"' not in`,
    `classes=f"kg-param-slider kg-param-{key} mt-3"`,
    `... mt-2"' not in`) onto it.

- **C2(ii) — the forbidden-claim union test
  (`test_web_layout.py:397`,
  `test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`).
  [discharges C2]** The only meaning-preserving edit is **union
  expansion**, never substitution; allowed-phrase and forbidden-vocabulary
  strings are unchanged throughout:
  - **S1t:** add `presentation.py` to the union (via the existing
    `with_name(...)` idiom).
  - **S4t:** add `layout.py` to the union.
  - **S5t (new declared row, §7 Table B):** add `handlers.py` and
    `generate_panel.py` to the union.
  After S5 the scanned union covers `app.py`, `controllers.py`,
  `generate_spec_form.py`, the frontier render hook, **and**
  `presentation.py`, `layout.py`, `handlers.py`, `generate_panel.py` — the
  globally frozen claim-vocabulary guard never stops covering a
  render-feeding module.

- **C2(iii) — post-split scope of the 8 negative source assertions.
  [discharges C2]** All eight guard widget-construction vocabulary whose
  post-split home is `layout.py`. Their intended post-split scope is the
  **union of `app.py` and `layout.py`** — for a negative assertion, union
  widening is strictly stronger, and this union is never narrower than the
  guarded surface. Implemented at S4t by asserting each against both
  reads. Stated per assertion:

  | Site | Assertion (unchanged) | Guarded surface | Post-split scope |
  |---|---|---|---|
  | `test_web_layout.py:86` | `'thumb_label="always"' not in` | slider construction | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:89` | `'... kg-param-{key} mt-2"' not in` | slider construction | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:343` | `'title="Hull STL"' not in` | export-menu render loop | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:344` | `'subtitle="Current open hull inspection surface"' not in` | export-menu render loop | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:652` | `'label="Shareable URL"' not in` | layout (field must not render) | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:675` | `"kg-class-preset-radio" not in` | param-rail radio removal | `app.py` ∪ `layout.py` |
  | `test_web_layout.py:710` | `"Refresh Analysis" not in` | Hydro-tab button removal | `app.py` ∪ `layout.py` |
  | `test_hydro_tab_descriptions.py:112` | `"Warning tooltip" not in` | tooltip-activator absence | `app.py` ∪ `layout.py` |

  Where a function holding a negative assertion also holds positive
  assertions whose target text moves at S5 (e.g. the
  `"Shareable URL copied"` companion at `test_web_layout.py:653`, handlers
  region), the C2(i) split-read recipe applies at S5t, strings unchanged.

**F3 — full-suite baseline is red** inside a frozen "must stay green" file.
Bar restated as: failure set stays exactly
`{tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]}`.

**F4 — extras-less profile is red on main** (§1.3, 20F+4E, all named).
Bar: set must not grow; package-level imports stay clean.

## 5. Frozen-surface inventory (verified against the tree)

| Surface | Witness | Status at baseline |
|---|---|---|
| `kayakgen serve` CLI (name, options, output, exit) | `tests/test_cli_serve.py` (3 tests) | green (with extras) |
| `create_app` / `KayakgenApp` import paths + signatures | 12 import sites across tests + CLI | verified, 2 production sites at `cli/main.py:648,657` |
| `_default_generative_jobs_root_for_app` keeps working for `cli/main.py:657` | `test_cli_serve.py` + S0's strengthened assertion | weakly pinned today (§1.4); S0 closes |
| Generative-job state-transition order | `tests/test_generative_jobs_web.py` — receives exactly one declared, string-preserving S4t patch-target redirect (C1); transition-order pins untouched | green |
| `browser_acceptance` marker + `tests/test_web_browser.py` untouched | `pyproject.toml:66`; file does no app-source reading | green, 4 passed/2 deselected |
| `tests/test_import_boundaries.py`, `tests/test_services_boundaries.py` not weakened | files untouched by every slice | import-boundaries green; services-boundaries red pre-existing (F3) |
| `[web]` extras gating | §1.3 method + per-slice import check | holds at package level (test-file leaks pre-existing, named) |
| `LAYOUT_TEST_IDS` / `REGION_CLASSES` values, widget order | `tests/test_web_layout.py` + browser profile | green |
| Globally frozen, far from blast radius (schemas, golden STL, claim vocabulary, root shims, artifact store, OpenFOAM case) | claim-vocabulary guard kept whole-package by C2(ii) union expansion | not approached by any slice |

## 6. Target shape and move mechanics

Five new sibling modules inside `kayakgen/ui/web/`:

| Module | Receives | Trame at module level? |
|---|---|---|
| `presentation.py` | constants/CSS/copy (≈98–711) + pure helpers `validity_badge_title_for`, `_param_row_raw_attrs`, `_pre_html`, `_resistance_table_html`, `_generative_job_state_flags` | no (pure) |
| `scene.py` | `_build_polydata`, `_make_actor`, 3D-scene methods | yes (vtk) — allowed per §1.3 precedent |
| `generate_panel.py` | generative-jobs panel methods (1473–1751) + `_default_generative_jobs_root_for_app` | **yes** — module-level import of `generate_spec_form` names (`build_spec_from_form_state`, `GenerateSpecFormError`, `refresh_concurrency_advisory`), licensed by the §1.3 precedent **[discharges C6]** |
| `layout.py` | layout region (1752–2532): `_build_layout`, `_region_attrs`, all `_render_*` | yes (trame widgets) |
| `handlers.py` | handlers region (1072–1472) | yes (minimal) |

**[discharges C6]** Corrected rationale for the S3 cli redirect: the
extras-less safety of `kayakgen serve` does **not** rest on
`generate_panel.py` being trame-free — it rests on the `cli/main.py:648`
`try/except ImportError` extras gate, which executes before the `:657`
import. Byte-identical panel bodies require the module-level
`generate_spec_form` imports, so `generate_panel.py` is trame-bearing,
with zero behavioral impact. No method stays behind in `app.py` on this
account.

**Method moves use mixins.** `KayakgenApp` has no base classes today.
Method regions move verbatim into `SceneMixin`, `GeneratePanelMixin`,
`LayoutMixin`, `HandlersMixin`; `app.py` declares
`class KayakgenApp(HandlersMixin, GeneratePanelMixin, LayoutMixin, SceneMixin):`
(methods are disjoint, so MRO is inert; mixin hazards probed and cut by
falsifier 1). Every method body stays byte-identical.

**Constant moves use by-name re-export imports** in `app.py`, so every F1
name keeps resolving via `kayakgen.ui.web.app`. `# noqa: F401` per tree
style.

`app.py` settles as: import/re-export block, `__init__` + parameter-rail
state (985–1044), mixin composition, `create_app`. Projected ≈400–450
lines ≤ the goal's ~600 cap.

## 7. Final step table

**Rollback discipline — LIFO-only. [discharges C3]** Rollback guarantees
are LIFO-only: a clean `git revert` exists only at the **head** of the
landed stack. Every slice rewrites `app.py`'s import/re-export block, and
every later sibling imports `presentation.py` directly (invariant 7), so
S1 is load-bearing for every successor and is unwound **last**. A halt at
Sn exits via **reverse-order multi-revert** — revert Sn, then Sn-1, …,
then S1, resolving `app.py`'s import block at each step. The per-slice
"independently revertible" claim of the superseded plan is removed. The
rollback-unit cells below name the revert **commit**; their guarantee is
positional (head-of-stack), not independent.

Every slice: one commit. Gross-moved lines are relocation; **net diff** =
non-relocation lines (imports, mixin/class declarations, aliases,
test-pointer edits). A slice exceeding its net-diff cap stops the campaign
(stop condition 3). "Full suite" tolerates exactly the F3 singleton;
"import check" = `noweb-venv python -c "import kayakgen, kayakgen.cli.main"`.

### Table A — move-only slices

| id | change | files | preservation claim | verification | rollback unit | est. (gross/net) | net cap |
|---|---|---|---|---|---|---|---|
| S1 | Presentation constants/CSS/copy + 5 pure helpers → `presentation.py`; by-name re-exports in `app.py` | `kayakgen/ui/web/presentation.py` (new), `app.py` | Byte-identical constant values and helper bodies; every F1 name still importable from `app.py` | decision row 1 targeted files, then full suite + ruff + import check | revert S1 commit (LIFO: last unwound) | ~655 / ~60 | 80 |
| S2 | VTK builders + scene methods → `scene.py` (`SceneMixin`) | `kayakgen/ui/web/scene.py` (new), `app.py` | Byte-identical actor/mesh construction; no state-key changes | full suite + ruff + import check | revert S2 commit | ~64 / ~25 | 40 |
| S3 | Generative-jobs panel methods → `generate_panel.py` (`GeneratePanelMixin`) + `_default_generative_jobs_root_for_app` move; redirect `cli/main.py:657`; alias kept in `app.py` | `kayakgen/ui/web/generate_panel.py` (new), `app.py`, `kayakgen/cli/main.py` (≤2 import lines) | Submit/cancel/fork/resume payloads and transition order unchanged; jobs-root resolution value-pinned by S0 | `pytest -q tests/test_generative_jobs_web.py tests/test_cli_serve.py`, full suite + ruff + import check + browser run (cheap insurance, non-gating, non-strict) | revert S3 commit | ~295 / ~50 | 60 |
| S4 | Layout construction → `layout.py` (`LayoutMixin`) | `kayakgen/ui/web/layout.py` (new), `app.py` | `LAYOUT_TEST_IDS`/`REGION_CLASSES` values, DOM ids, widget construction order unchanged | `pytest -q tests/test_web_layout.py`, full suite + ruff + import check + **strict browser acceptance (mandatory gate)** [discharges C5] | revert S4 commit | ~781 / ~60 | 80 |
| S5 | Handlers → `handlers.py` (`HandlersMixin`); `app.py` settles as integrator ≤~600 lines | `kayakgen/ui/web/handlers.py` (new), `app.py` | `create_app`/`KayakgenApp` paths + signatures unchanged; trame ctrl/state bindings identical | full suite + ruff + import check + **strict browser acceptance (mandatory gate)** [discharges C5] + full extras-less suite re-run (failure set must equal §1.3's) | revert S5 commit (head of stack at campaign end) | ~401 / ~70 | 100 |

### Table B — edit slices

S0 is a standalone commit. S1t/S4t/S5t land **in the same commit as their
parent move slice** (the reviewability discipline of the superseded plan,
now covering S5 as well); their verification is their parent's runs.

| id | change | files | preservation claim | est. net | net cap |
|---|---|---|---|---|---|
| S0 | Characterization: assert echoed `jobs_root` equals `KAYAKGEN_GENERATIVE_JOBS_ROOT` in both manager tests | `tests/test_cli_serve.py` | Documents current resolution; no source change. Verification: `pytest -q tests/test_cli_serve.py` + full suite + ruff. Rollback: revert S0 commit | ~4 | 10 |
| S1t (with S1) | Pointer redirects for text moved in S1; C2(i) split-read step 1 (`presentation_source` for the aria-label assertion); C2(ii) union expansion adds `presentation.py` | `tests/test_web_inline_help.py`, `tests/test_hydro_tab_descriptions.py`, `tests/test_web_layout.py` (subset) | Same assertion strings, applied where the code now lives **[discharges C2]** | ~16 | 20 |
| S4t (with S4) | Bulk `test_web_layout.py` redirects to `layout.py`; C2(i) split-read step 2 (slider assertions → `layout_source`); C2(ii) union expansion adds `layout.py`; C2(iii) negatives asserted against `app.py` ∪ `layout.py`; **C1 patch-target redirect** at `tests/test_generative_jobs_web.py:547` (~2 lines) | `tests/test_web_layout.py`, `tests/test_web_inline_help.py` (usage-id subset), `tests/test_generative_jobs_web.py` | Same assertion strings, new source targets; monkeypatch fake and assertions unchanged **[discharges C1, C2]** | ~32 | 40 |
| S5t (with S5) | C2(ii) union expansion adds `handlers.py` + `generate_panel.py`; pointer redirects for handler strings displaced at S5 (e.g. `test_web_layout.py:653`) | `tests/test_web_layout.py` | Same assertion strings; forbidden-claim union covers every render-feeding module after S5 **[discharges C2]** | ~10 | 20 |

Order: S0 → S1(+S1t) → S2 → S3 → S4(+S4t) → S5(+S5t). Only
S5-after-S3/S4 is structurally forced; the rest is risk-ordered per
proposal B.

Per-slice verification cost at baseline rates: ~9 min (full suite + ruff),
+38s browser where gated, +6 min extras-less full run once at S5.

## 8. Verification command inventory

| Command | When |
|---|---|
| `.venv/bin/python -m pytest -q` | every slice (bar: failure set == F3 singleton) |
| `.venv/bin/python -m ruff check kayakgen tests` | every slice (bar: exit 0) |
| `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` | **mandatory gate after S4 and S5** (bar: 4 passed, 2 deselected; strict mode makes an un-runnable gate **fail** instead of skip) **[discharges C5]** |
| `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` | insurance after S3 (non-gating, non-strict) |
| Decision §4 slice-targeted file lists | per matching slice |
| `noweb-venv python -c "import kayakgen, kayakgen.cli.main"` | every slice |
| Extras-less full suite (§1.3 method) | once after S5 (bar: failure/error id set identical to §1.3) |

The strict-mode token (`KAYAKGEN_BROWSER_ACCEPTANCE=1`, equivalently
`--browser-acceptance`) is already implemented in the frozen witness file
(`tests/test_web_browser.py:63–97`); with it set, missing Playwright or an
un-launchable Chromium `pytest.fail`s rather than skipping, so stop
condition 6 has a mechanical trigger. The step ledger at S4/S5 records the
strict-mode command and its `4 passed, 2 deselected` output.

## 9. Stop conditions

The campaign stops (slice aborted, escalated to the **operator** — stage 2
has no adjudicator, see §12) if:

1. **Behavior change required** — any slice cannot complete as a pure code
   move, modulo the declared edits of amended F2 (the four-file inventory,
   the C2(i) split reads, the C2(ii) union expansions, the C1
   patch-target redirect) and the ≤2-line cli redirect of S3.
2. **Frozen surface blocks progress** — any §5 surface would have to
   change beyond its declared discharge; includes any edit to
   `tests/test_web_browser.py`, `tests/test_import_boundaries.py`, or
   `tests/test_services_boundaries.py`.
3. **A slice exceeds its declared net-diff cap** (§7 tables).
4. **The chosen goal turns out to be wrong** — any decision revisit
   condition fires: browser gate red/unrunnable on unmodified `main`,
   move-only premise fails beyond amended F2's declared mechanics, a
   *production* importer of `app.py` internals beyond `cli/main.py:657`
   is found, or the operator re-weights toward minimum risk. (The
   adjudicator has already ruled conditions 2 and 3 do not fire on the
   facts known at the gate.)
5. **Scope creep** — the work crosses into features, bug fixes (including
   the pre-existing F3/F4 reds — they stay red), schema changes, or
   dependency upgrades.
6. **Browser acceptance cannot be run** when S4 or S5 needs it — the
   strict-mode command fails rather than skips **[discharges C5]**;
   stop-the-slice, never waivable.
7. **New failure appears** in the full suite beyond the F3 singleton, or
   the extras-less failure set grows, or widget order / DOM identifiers
   change under the browser profile.
8. **Tree dirties inside the blast radius** before a slice starts
   (re-check `git status --short` per slice).
9. *(Discharged at the gate.)* The superseded plan deferred to the
   adjudicator whether F1/F2 fire revisit conditions 2/3; the ledger rules
   they do not (condition 2 conditional on C1/C2, which land in this
   document). Retained for the record; no longer an open trigger.

## 10. Adjudicated record carried forward

The ledger's probed-and-cut record binds stage 2's economy: mixin hazards,
the `create_app` patch path, the `REVIEW_TABS` fromlist read, gross-move
arithmetic, wheel packaging, integration squash risk, browser-gate
substance, and the serve extras-less degradation path were all
investigated and rebutted by the tree. They are not to be re-litigated
mid-campaign. Baselines reproduce exactly in a second environment
(falsifier 2's table), including the F3 singleton failure id.

## 11. Stage-2 entry preconditions [discharges C4]

**Precondition (carried verbatim, per C4): before stage-2 `run prepare`,
the operator must re-scope `execute_slices.allowed_paths` to the exact
files-touched envelope: `kayakgen/ui/web/`, `kayakgen/cli/main.py`,
`tests/test_cli_serve.py`, `tests/test_web_layout.py`,
`tests/test_web_inline_help.py`, `tests/test_hydro_tab_descriptions.py`,
`tests/test_generative_jobs_web.py` (per C1), and the step ledger path
(`striatum/refactoring/kayakgen-smoke-1/02-execution/STEP_LEDGER.md`).**
The scaffolded envelope (`src/example/`, which does not exist in this
repository) cannot write a single file in the plan's blast radius, and
`workflow.json` is inside no gated job's write scope — only the operator
can perform this re-scope. The gate summary carries this precondition as
well. If the re-scope is refused, that is a campaign stop per the refusal
rule.

**Baseline reproduction before the first slice:** stage 2 must re-run the
verification commands of §8 on its unmodified starting tree and reproduce
the recorded baseline of §1.2 before S0 — full suite failure set exactly
the F3 singleton; ruff exit 0; **strict-mode** browser gate 4 passed,
2 deselected; import check clean. A baseline that does not reproduce is a
stop before any write.

## 12. Ledger-anchored execution discipline [discharges C7]

Stage 2's machinery is job-grain (one `execute_slices` job runs the whole
table); the slice-grain discipline below is therefore declared, not
implied:

1. **One step-ledger entry plus one commit per slice, written before the
   next slice starts.** Each entry records the slice id, its commit hash,
   and its verification transcript (including the strict-mode browser
   output at S4/S5).
2. **On any retry or re-dispatch, the executor first diffs the branch
   against the step ledger and resumes after the last verified slice —
   never replays a landed slice.** An interrupted slice with no ledger
   entry is unwound (LIFO, §7) before resuming.
3. **A stop condition firing mid-table escalates to the operator** via
   escalation, and execution halts at the current head of the stack —
   stage 2 has no adjudicator, and improvised continuation is the failure
   mode this discipline exists to prevent.
