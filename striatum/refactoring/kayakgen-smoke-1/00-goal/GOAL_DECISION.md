---
schema_version: striatum.decision.v1
artifact_kind: decision
decision_id: "dec_e526052a732d40b385a892b3e78680be"
run_id: "run_08d0beb1f0959b071475ff4400dc1d97"
owner: human
outcome: accepted
follow_up_required: false
title: "kayakgen-smoke-1 goal: split kayakgen/ui/web/app.py along the Generate-panel seam (Goal B)"
created_at: "2026-06-05T20:55:36Z"
author: principal-decider-claude-001
---

# Goal Decision — kayakgen-smoke-1

author: principal-decider-claude-001

Date: 2026-06-05
Run: `run_08d0beb1f0959b071475ff4400dc1d97`, stage 0 (record_goal_decision)
Decision ID: `dec_e526052a732d40b385a892b3e78680be`

This artifact is the input contract for stage 1 (the plan gate). The plan
holder reads this artifact, and nothing else from this run, as
authoritative.

---

## 1. The selected goal

**Decompose `kayakgen/ui/web/app.py` (2,550 lines) into focused sibling
modules inside `kayakgen/ui/web/`, along the seams its own section markers
and import block already expose, leaving `app.py` as a ≤~600-line
integrator that still exports `create_app` and `KayakgenApp` unchanged.**

One named, behavior-preserving structural change: code moves out of one
module into siblings in the same package. No public symbol, state-variable
name, rendered DOM identifier, CLI command, or schema changes.

**Bounded surface:**

- Target: `kayakgen/ui/web/app.py`.
- New modules: siblings inside `kayakgen/ui/web/` only — presentation
  constants/copy, VTK scene helpers, generative-jobs panel wiring, layout
  construction, handler wiring (names settled at plan stage; the seam
  boundaries are fixed).
- Call sites outside the package: `kayakgen/cli/main.py:648`
  (`create_app` inside `serve`) and `:657`
  (`_default_generative_jobs_root_for_app` — private import, redirected
  with an alias kept in `app.py`). Nothing else imports `app.py`
  internals (revisit condition 3 below if planning finds otherwise).
- Provenance of the candidate: brief candidate C1; `TODO.md` B2 (P1); the
  2026-06-03 deep architecture review's "one untamed boundary".

## 2. Provenance

- **Winning proposal:** Goal B
  (`striatum/refactoring/kayakgen-smoke-1/00-goal/proposals/GOAL_B.md`,
  author `proposer-b-claude-001`), executed exactly as proposed — nothing
  from proposals A or C is composed in.
- **Arbitration rationale** (`ARBITRATOR_SYNTHESIS.md`, revision 2,
  `arbitrator-claude-002`): Attempt 1 rejected B solely because its hard
  gate — a green Playwright browser-acceptance profile — was undemonstrated
  in the executing environment, and the arbitrator discharged that
  condition first-hand by running the suite on unmodified `main` (425ad76):
  4 passed, 2 deselected in 34.29s. With verification parity established,
  payoff decides: B's 9/10 (decomposing the repo's largest module) beats
  A's 5/10, with blast radius Low (3/10), frozen-surface risk Low (2/10),
  reversibility High (8/10), and sliceability Very High (9/10).
- **Dissent verdict:** `accept` (`DISSENT_REVIEW.md`,
  `dissent-reviewer-agy-002`, attempt 2). Attempt 1's dissent was
  `needs_revision`, which forced the re-arbitration; attempt 2's dissent
  accepts the revised selection with no carve-outs beyond the slice
  discipline recorded below.

## 3. Frozen surfaces (narrowed to this goal's blast radius)

Copied forward from the problem brief §3; these are the surfaces this
campaign may not change. Stage 1 must treat any plan step that crosses one
as a falsifier.

- **Public CLI surface:** `kayakgen serve` — command name, options, output
  text, and exit behavior. `cli/main.py` edits are limited to redirecting
  at most two import lines, with `tests/test_cli_serve.py` green.
- **Public entrypoints:** `kayakgen.ui.web.app:create_app` and
  `KayakgenApp` — import paths and signatures unchanged (12 import sites
  across tests + CLI import only these two symbols).
- **Compatibility of the private cross-package import:**
  `_default_generative_jobs_root_for_app` consumed by `cli/main.py:657`
  must keep working through the move (redirect + temporary alias in the
  same slice; CLI serve test green).
- **Event ordering:** generative-job state transitions observed by
  `generate_state_listener` and the web UI. Panel wiring moves; listener
  wiring and observable transition order are preserved verbatim
  (`tests/test_generative_jobs_web.py` pins the sequence).
- **`browser_acceptance` pytest marker:** referenced in `pyproject.toml`;
  the marker name and `tests/test_web_browser.py` are untouched.
- **Test/boundary contracts:** `tests/test_import_boundaries.py` and
  `tests/test_services_boundaries.py` must stay green, not weakened. New
  modules live inside `kayakgen/ui/web/`, so the rules hold by
  construction.
- **`[web]` extras gating:** every extracted module keeps its trame/vtk
  imports module-local exactly as `app.py` does today, so `import
  kayakgen` and the CLI without `[web]` extras keep working.
- **Rendered DOM identifiers:** `LAYOUT_TEST_IDS` / `REGION_CLASSES`
  values and widget order — observable via `tests/test_web_layout.py` and
  the browser profile.

The brief's remaining frozen surfaces — public JSON schemas, golden STL
byte-stability, claim/readiness vocabulary, root compatibility shims
(`generator.py`, `gui.py`, `pyvista_view.py`), the artifact store, and the
OpenFOAM case render — are nowhere near this goal's blast radius (the web
layer renders read models and owns no schema_version-bearing model). They
remain frozen globally; this goal simply must not drift toward them.

## 4. Verification commands stage 1 must baseline against

Per slice (every slice):

| Command | Role |
|---|---|
| `.venv/bin/python -m pytest -q` | Full suite (215 test files). Must be green or skipped. |
| `.venv/bin/python -m ruff check kayakgen tests` | Lint gate. Must pass. |

Slice-targeted, per proposal B §5 (carried forward verbatim):

| # | Slice | Verification |
|---|---|---|
| 1 | Presentation constants & pure helpers | `.venv/bin/python -m pytest -q tests/test_web.py tests/test_web_layout.py tests/test_web_inline_help.py tests/test_generate_panel_label_rendering.py tests/test_hydro_tab_descriptions.py` then full `-q` suite + ruff |
| 2 | VTK scene helpers | full `-q` suite + ruff |
| 3 | Generative-jobs panel wiring (+ `cli/main.py:657` redirect) | `pytest -q tests/test_generative_jobs_web.py tests/test_cli_serve.py` then full suite + ruff |
| 4 | Layout construction | `pytest -q tests/test_web_layout.py` + full suite + ruff + **browser acceptance run** |
| 5 | Handler wiring + final shape | full `-q` suite + ruff + **browser acceptance run** |

The browser-acceptance gate —
`.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q`
— is **mandatory, not optional, for slices 4–5** (and cheap insurance
after 3). It is the goal's load-bearing preservation evidence. If it
cannot be run, that is a stop-the-slice blocker for slices 4–5, not a
waivable nicety.

Stage-1 preflight obligations (before slice 1, from the arbitration §6):

1. Re-run the browser suite on unmodified `main` at execution time and
   record the transcript (the arbitration's green run — 4 passed,
   2 deselected — ages the moment the environment changes).
2. Verify `tests/test_cli_serve.py` pins the generative-jobs-root
   resolution before slice 3; add the one-line characterization test
   proposal B §6 describes if it does not.
3. Run the non-web suite once without `[web]` extras to pin the
   extras-leak guard.

## 5. Non-goals

- **Goal A (runner-up): retire internal compatibility-shim traffic**
  (11 import sites across 10 files; brief C6). Attempt 1's winner; lost
  when its sole decisive advantage — B's then-unverifiable browser gate —
  was discharged by direct demonstration. It is not composed into this
  campaign in any part. It remains the standing fallback if revisit
  conditions 1–2 fire, and a future hygiene-pass candidate.
- **Goal C: shim retirement plus the root `generator.py`/golden-test
  redirect.** Barred by selection rule 2: its `generator.py` redirect
  assumption cannot be discharged at preflight (only by executing its own
  slice 4), and A exists as its verifiable subset.
- **Any non-move edit inside the slices.** The campaign is move-only by
  construction; reviewers must treat any semantic edit in slices 4–5 as a
  stop-the-slice finding (trame widget construction order is the main
  regression channel).
- **Everything the brief rules out for every candidate** (§5): features,
  bug fixes, schema changes, dependency upgrades, broad rewrites,
  speculative abstractions, hygiene-pass-sized cleanups, any change to
  claim-state promotion rules, and eviction of the process layer.
- **Doc churn:** `docs/ARCHITECTURE_MAP.md` mentions the web layer at
  module granularity; a follow-up doc touch may be needed but no
  public-behavior doc checklist triggers for a behavior-preserving move.

## 6. Revisit conditions (decision void if any fires)

Carried from the arbitration §5; if any fires, the selection returns to
arbitration with Goal A as the standing alternative:

1. **Browser gate regresses before slice 1** — the stage-1 preflight
   re-run of `pytest tests/test_web_browser.py -m browser_acceptance` is
   red or unrunnable on unmodified `main`.
2. **Move-only premise fails at planning** — stage-1 falsification finds
   the `app.py` section seams entangled such that any slice cannot be a
   pure code move.
3. **Blast-radius premise breaks** — planning finds importers of `app.py`
   internals beyond `cli/main.py:657`.
4. **Operator re-weights toward minimum risk** — the operator decides the
   first full campaign should optimize for near-certain preservation over
   payoff; A's record needs no rework.
