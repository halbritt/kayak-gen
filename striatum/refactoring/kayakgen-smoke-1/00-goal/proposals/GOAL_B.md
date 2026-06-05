# Goal B — Split `kayakgen/ui/web/app.py` along the Generate-panel seam

author: proposer-b-claude-001

Date: 2026-06-05
Brief candidate: C1
Repository state verified against: `main` (worktree at 425ad76 + campaign scaffold)

---

## 1. The goal

**Decompose `kayakgen/ui/web/app.py` (2,550 lines) into focused sibling
modules inside `kayakgen/ui/web/`, along the seams its own section markers
and import block already expose, leaving `app.py` as a ≤~600-line
integrator that still exports `create_app` and `KayakgenApp` unchanged.**

One named, behavior-preserving structural change: code moves out of one
module into siblings in the same package; no public symbol, state-variable
name, rendered DOM identifier, command, or schema changes.

This is the highest-structural-payoff candidate in the brief: the single
largest module in the repository, pre-identified as `TODO.md` B2 (P1) and
as "the one untamed boundary" in the 2026-06-03 deep architecture review.
Every other candidate tidies a module that already has a precedented shape;
this one retires the only boundary the architecture review flagged as
untamed.

## 2. Claims re-verified against the current tree (2026-06-05)

All of the brief's C1 claims check out, with one addition:

- `kayakgen/ui/web/app.py` is **2,550 lines** (`wc -l`), the largest module
  in the repo. The rest of `ui/web/` is already sibling-shaped:
  `generate_spec_form.py` 1,452, `generate_frontier_view.py` 780,
  `controllers.py` 535, `generate_state_listener.py` 279,
  `read_models.py` 271, `state.py` 109, `generate_fork_button.py` 74.
- The import block (`app.py:23-80`) imports from all seven siblings —
  the seam the brief describes is real and current.
- `TODO.md` line 95 carries B2 verbatim: "Split `kayakgen/ui/web/app.py`
  (2,550 lines) — P1, 1-2 days … Behind the browser-acceptance suite."
- The module has explicit internal section markers that name the split:
  module-level constants/helpers (lines 1–805), `KayakgenApp` with
  `# ----- parameter rail state -----` (985), `# ----- 3D scene -----`
  (1045), `# ----- handlers -----` (1072), `# ----- generative-jobs
  panel -----` (1473), `# ----- layout -----` (1752), and `create_app`
  (2533).
- **Addition the brief does not mention:** `kayakgen/cli/main.py:657`
  imports the *private* `_default_generative_jobs_root_for_app` from
  `app.py`. This cross-package private import is in the blast radius and
  must keep working (or be redirected in the same slice that moves it,
  with the CLI `serve` test green).

## 3. Blast radius

**Target:** `kayakgen/ui/web/app.py`.

**New modules (proposed, all inside `kayakgen/ui/web/`):** presentation
constants/copy, VTK scene helpers, generative-jobs panel wiring, layout
construction, handler wiring. Names bikesheddable at plan stage; the seam
boundaries are what matter.

**Call sites:**
- `kayakgen/cli/main.py:648` (`create_app` inside `serve`) and `:657`
  (`_default_generative_jobs_root_for_app`).
- `kayakgen/ui/web/__init__.py` (lazy docstring reference only; imports
  nothing eagerly).
- Sibling modules are *imported by* app.py, not importers of it —
  dependency direction within the package stays one-way toward the
  integrator.

**Tests (4,798 lines across 9 files, all currently importing only
`create_app` and `KayakgenApp` from app.py):** `test_web.py` (793),
`test_web_layout.py` (954), `test_web_browser.py` (1,129, real-browser
acceptance profile), `test_web_inline_help.py` (361),
`test_generative_jobs_web.py` (573), `test_web_read_models.py` (561),
`test_generate_panel_label_rendering.py` (236),
`test_hydro_tab_descriptions.py` (112), `test_cli_serve.py` (79).

**Generated sources:** none. **Docs:** `docs/ARCHITECTURE_MAP.md` mentions
the web layer at module granularity; a follow-up doc touch may be needed
but no public-behavior doc checklist triggers.

**Public entrypoints:** `kayakgen serve` (CLI, frozen) and the
`kayakgen.ui.web.app:create_app` factory (12 import sites in tests + CLI).

## 4. Frozen surfaces this goal comes near — and why it does not cross them

- **Public CLI surface** (`kayakgen serve`): the refactor never touches
  command names, options, or output; `cli/main.py` edits are limited to
  (at most) redirecting two import lines, with `test_cli_serve.py` green.
- **Event ordering** (generative-job state transitions observed by
  `generate_state_listener` and the web UI): panel wiring *moves*, but the
  listener wiring and transition order are preserved verbatim;
  `test_generative_jobs_web.py` pins the observable sequence.
- **`browser_acceptance` marker:** referenced in `pyproject.toml`; the
  marker and `test_web_browser.py` are untouched.
- **Test/boundary contracts:** new modules live inside `kayakgen/ui/web/`,
  so `test_import_boundaries.py` rules (ui imports services/read-models
  only, no private evaluator reach-ins) are unaffected by construction.
- **No JSON schema, golden STL, claim vocabulary, or artifact-store
  surface is anywhere near this code.** The web layer renders read models;
  it owns no schema_version-bearing model.

One deliberate guard: `ui/web` imports are gated behind the `[web]` extra
(trame/vtk). Every extracted module must keep its trame/vtk imports
module-local exactly as app.py does today, so that `import kayakgen` and
the CLI without `[web]` extras keep working — `test_cli_serve.py` and the
suite's import-time behavior pin this.

## 5. Slice decomposition

Each slice is a pure code move + re-import, independently landable,
independently revertible, with its own preservation claim and command.

| # | Slice | Moves | Preservation claim | Verification |
|---|---|---|---|---|
| 1 | Presentation constants & pure helpers | CSS blocks, copy constants, `SLIDER_DEFS`, validity-badge titles, `validity_badge_title_for`, `_pre_html`, `_resistance_table_html`, `_param_row_raw_attrs`, `_generative_job_state_flags` (≈ lines 254–805) | Byte-identical rendered copy and CSS; constants re-exported from app.py | `.venv/bin/python -m pytest -q tests/test_web.py tests/test_web_layout.py tests/test_web_inline_help.py tests/test_generate_panel_label_rendering.py tests/test_hydro_tab_descriptions.py` then full `-q` suite + ruff |
| 2 | VTK scene helpers | `_build_polydata`, `_make_actor`, `# ----- 3D scene -----` methods | Identical actor/mesh construction; no state-key changes | full `-q` suite + ruff |
| 3 | Generative-jobs panel wiring | `# ----- generative-jobs panel -----` (≈ 1473–1751) + `_default_generative_jobs_root_for_app`, redirecting `cli/main.py:657` (alias kept in app.py) | Job submit/cancel/fork/resume payloads and state-transition order unchanged | `pytest -q tests/test_generative_jobs_web.py tests/test_cli_serve.py` then full suite + ruff |
| 4 | Layout construction | `# ----- layout -----` (≈ 1752–2532): `_build_layout`, `_region_attrs`, export menu, drawer/toolbar sections | `LAYOUT_TEST_IDS`/`REGION_CLASSES` DOM identifiers and widget order unchanged | `pytest -q tests/test_web_layout.py` + full suite + ruff + **browser acceptance run** |
| 5 | Handler wiring + final shape | `# ----- handlers -----` (≈ 1072–1472); app.py settles as integrator (`KayakgenApp` shell + `create_app`), target ≤~600 lines | `create_app`/`KayakgenApp` import paths unchanged; trame ctrl/state bindings identical | full `-q` suite + ruff + **browser acceptance run** |

Slices 1–2 are low-risk warm-ups that prove the move mechanics; 3–5 carry
the structural payoff. Order is forced only by 5-after-3/4 (handlers
reference panel + layout symbols).

## 6. Existing coverage; characterization-test need

Coverage near the blast radius is unusually strong for a UI module:
4,798 lines of tests including DOM-identifier layout assertions
(`test_web_layout.py`), inline-help and label-rendering pins, generative-
job lifecycle tests, and a real-browser acceptance profile. The external
import surface is two symbols. **No new characterization tests are needed
before semantic movement**, with one small exception: a one-line test
pinning that `kayakgen.cli.main`'s serve path resolves the generative-jobs
root identically after slice 3 (if `test_cli_serve.py` does not already
exercise it — verify at plan stage; cheap either way).

## 7. Verification burden — explicit

This is the candidate with the *heaviest* verification profile, and that
must be priced in honestly:

- Full suite per slice: `.venv/bin/python -m pytest -q` (215 test files)
  + `.venv/bin/python -m ruff check kayakgen tests`.
- **Browser acceptance is mandatory, not optional, for slices 4–5** (and
  cheap insurance after 3): `pytest tests/test_web_browser.py
  -m browser_acceptance` with the `[browser]` extra and Playwright
  installed. The brief lists it as "relevant to any ui/web candidate";
  for this goal it is the gate, per `TODO.md` B2's own framing ("behind
  the browser-acceptance suite").
- The headless web tests cover most regressions, but widget *construction
  order* inside trame layouts is exactly the kind of behavior only the
  browser profile observes end-to-end — so the environment cost (Playwright
  + browser binaries) is part of this goal's price. If the browser profile
  cannot be run in the executing environment, that is a **stop-the-slice
  blocker for slices 4–5**, not a waivable nicety.

## 8. Expected payoff

- The repo's largest module drops ~2,550 → ~600 lines; the "one untamed
  boundary" from the architecture review is retired, completing the shape
  the `ui/web` package already established (7 sibling modules).
- Future Generate-panel work — the panel is the active growth surface and
  grew this module 10.6× — lands in focused modules with small diffs,
  instead of appending to a 2,550-line integrator.
- Review cost drops where it is currently highest: layout, handlers, and
  panel wiring become separately reviewable and separately testable.
- Direct unit seams appear for layout and panel construction that today
  can only be reached by building the whole app.

## 9. Known risks and evidence that would reduce them

| Risk | Severity | Reducing evidence |
|---|---|---|
| trame state/ctrl bindings are construction-order-sensitive; moving layout code could silently reorder widgets | Main risk | `test_web_layout.py` DOM-identifier assertions + browser acceptance run after slices 4–5; slice diffs kept move-only |
| Import cycles between app.py and new siblings (spec form docstring already notes the integrator boundary) | Moderate | Keep dependency direction strictly sibling → imported-by-app; ruff + import-boundary tests; smoke `python -c "from kayakgen.ui.web.app import create_app"` |
| `[web]` extras leak: an extracted module imports trame/vtk at a path reachable without extras | Moderate | `test_cli_serve.py` + running the non-web test suite in an env without `[web]` extras once |
| `cli/main.py:657` private-import break | Low | Redirect + alias in slice 3; `test_cli_serve.py` |
| Hidden state-key initialization order between `__init__` and handlers | Low | Full web test files instantiate the app; transitions pinned by `test_generative_jobs_web.py` |

Pre-work evidence that would further de-risk: a quick check that the
browser-acceptance profile actually runs green on `main` in the executing
environment *before* slice 1, so a later red browser run is attributable
to the refactor and not the environment.
