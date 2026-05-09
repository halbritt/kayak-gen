# AGENTS.md

Entry-point reading list for any coding agent (or new contributor)
opening this repo. Six files, in order. Read them in this order on
the first pass; the rest of the repo makes sense afterwards.

The framing this list embodies — short, ordered, with labeled
negative space — comes from `docs/CONTEXT_HYGIENE.md` (item 6
below). If you find yourself reading something not on this list to
get oriented, that is a signal to update this list, not a signal to
keep going.

## Reading list

1. **`AGENTS.md`** (this file) — orientation, current direction,
   labeled negative space. Read first.
2. **`docs/PRD.md`** — who the project serves and what it is for.
   In scope: parametric hull geometry, hydrostatics, analytical
   resistance, desktop and web frontends. The out-of-scope list is
   four items, all genuine domain boundaries (not difficulty walls).
3. **`docs/design/kayak_hull_design_constraints.md`** — the domain
   knowledge the design space rests on. Parameter ranges, class
   boundaries, evaluation metrics, the speed/stability tradeoff
   structure. RFCs 0005–0008 cite it by section number; you will
   want it loaded.
4. **`docs/rfcs/README.md`** — index of accepted/proposed RFCs. Read
   this to know what is being built right now. RFCs 0007 (architectural
   revisit) and 0008 (web frontend) are the load-bearing ones for
   any new work; everything else either feeds them or sits on top.
5. **`generator.py`** — the current implementation. ~180 lines,
   single class, does one thing (lofted hull → STL). Reading the
   code and reading RFC 0007 in tandem makes the planned refactor
   obvious. *Note: `gui.py` and `pyvista_view.py` are co-equal but
   smaller; defer them unless the task touches the UI.*
6. **`docs/CONTEXT_HYGIENE.md`** — vendored from
   [striatum](https://github.com/halbritt/striatum/blob/main/docs/CONTEXT_HYGIENE.md).
   The practices that make sessions in this repo work. Includes the
   replication checklist this `AGENTS.md` is the answer to.

That is the whole list. Anything else is on-demand.

## Labeled negative space

Files and directories that exist but are **not** load-bearing for a
typical task. Read them only if the task explicitly touches their
subject:

- **`docs/SPEC.md`, `docs/DDD.md`, `docs/UBIQUITOUS_LANGUAGE.md`** —
  scaffolding from `striatum init --with-ddd-layout`. Bodies are
  still mostly TODO. Read them to understand the *framework* the
  project follows; do not read them expecting current content.
  Filling these in is its own future RFC.
- **`docs/DECISION_LOG.md`** — only `D001` is a real decision today.
  The rest of the file is template guidance.
- **`docs/workflows/*.json`** — striatum workflow definitions, not
  documents. Touch only when authoring or editing a workflow.
- **`scripts/codex-striatum-adapter.sh`** — adapter, not project
  surface. Do not read for orientation.
- **`__pycache__/`, `*.stl`** at repo root — build artifacts;
  generated, not authored.
- **`docs/rfcs/0001-template.md`** — the RFC template. Copy it for
  new RFCs; do not read it for current direction.

## Project conventions visible in `git log`

- New design docs land as RFCs in `docs/rfcs/NNNN-slug.md`. Commit
  messages follow `Add RFC NNNN — <slug>` for new RFCs and
  `Land RFC NNNN step <n>` for staged implementation work.
- Each commit is co-authored when an agent participated:
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`.
- `main` is the trunk. RFC and feature work happens on
  `claude/<slug>` or `feature/<slug>` branches and merges back.

## Current direction (one paragraph)

The project is mid-pivot from "single-paddler desktop hull
generator" (the PRD scope) to "generative CFD pipeline with desktop
and web frontends" (the RFC 0005–0008 scope). RFC 0007 is the
architectural extraction that unblocks everything else; until it
lands, expect the existing flat-file layout (`generator.py`,
`gui.py`, `pyvista_view.py`) and expect new RFCs to keep adding
parameters that will need re-plumbing afterward. If you are picking
up open work, the highest-leverage place to spend time is RFC 0007's
implementation path step 1 (golden tests against current code).
