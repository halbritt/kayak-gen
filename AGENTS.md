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
- **`docs/workflows/*.json`** — striatum workflow definitions, not
  documents. Touch only when authoring or editing a workflow.
- **`scripts/codex-striatum-adapter.sh`** — adapter, not project
  surface. Do not read for orientation.
- **`__pycache__/`, `*.stl`** at repo root — build artifacts;
  generated, not authored.
- **`docs/rfcs/0001-template.md`** — the RFC template. Copy it for
  new RFCs; do not read it for current direction.

## Release discipline

`docs/RELEASE_DISCIPLINE.md` consolidates the pre-merge requirements,
the public-behavior-change update checklist, the no-claim invariants
and their named evidence gates, and the one-phase-per-RFC rule.
Read it before landing any change that touches a public CLI command,
a Pydantic schema, a claim/readiness literal, or any of the docs in
the architecture-map list.

## Project conventions visible in `git log`

- New design docs land as RFCs in `docs/rfcs/NNNN-slug.md`. Commit
  messages follow `Add RFC NNNN — <slug>` for new RFCs and
  `Land RFC NNNN step <n>` for staged implementation work.
- Each commit is co-authored when an agent participated:
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`.
- `main` is the trunk. RFC and feature work happens on
  `claude/<slug>` or `feature/<slug>` branches and merges back.
- Update `CHANGELOG.md` whenever landing an RFC, workflow, user-facing
  behavior change, or roadmap/status change. Keep entries factual about
  what landed versus what remains deferred.

## Current direction (one paragraph)

The pivot from "single-paddler desktop hull generator" to "generative
CFD pipeline with desktop and web frontends" is now mostly landed.
`kayakgen/` ships a CLI, compat shims, evaluators, golden tests, a Trame
web workspace, hydrostatics, raw-comparative-filter resistance, a
generated closed-body construction with parameter-matrix hardening, a
local CFD dispatch layer, a real OpenFOAM-v2512 `interFoam` succeeded
path behind opt-in env knobs (RFC 0041 / D012; `claim_state` stays
`raw_unvalidated`), a real `snappyHexMesh` evidence harness (RFC 0040
stage 2), the Edinburgh DataShare Pacific-canoe extractor and
validation-fixture-ready packet (RFC 0042 / D018; calibration still
envelope-blocked), staged opt-in high-angle GZ surfacing across CLI,
sweep, comparison, and web (RFC 0043 stages 1-3, stage 4 desktop
intentionally minimal per D021), the `pending` candidate lifecycle and
sweep-side STL artifacts (RFC 0009 partial), and a proposed RFC 0044
NSGA-II active hull-design search. The hosted public demo is deferred
indefinitely per D023; restoring it requires a successor decision.
Genuinely open work: an in-envelope measured kayak resistance source
(D006, requires author outreach — see
`docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md`), measured kayak
GZ-vs-heel data (D007 / D014, requires a commissioned measurement
campaign), and a measured-validation workflow that would let
`uncalibrated_comparative` and `unvalidated_hydrostatic_comparison`
labels evolve.
