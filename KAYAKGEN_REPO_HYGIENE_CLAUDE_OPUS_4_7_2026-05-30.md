# kayakgen — repo hygiene audit (2026-05-30)

**Auditor**: Claude Opus 4.7
**Branch**: `cleanup/2026-05-30` (off `main` at `e0e6c80`)
**Project name**: `kayakgen` (from `pyproject.toml` and `README.md`)
**Scope**: the project rooted at `/home/halbritt/git/kayak-gen`, single
repo (operator chose "Just kayak-gen" in the fan-out scoping question).

## 0. What I checked

Top-level walk (every directory, depth 2 or deeper where notable):

- `./` — root inventory: `AGENTS.md`, `README.md`, `CHANGELOG.md`,
  `OPERATOR_REPORT.md`, `ARCHITECTURE_REVIEW_2026-05-16.md`,
  `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`, `pyproject.toml`,
  `requirements-dev.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`,
  `generator.py`, `gui.py`, `pyvista_view.py`.
- `kayakgen/` — production package: `cli/`, `eval/`, `io/`, `model/`,
  `search/`, `services/`, `ui/`. 1,661 tracked files total in the repo;
  ~600 are under `kayakgen/`.
- `docs/` — `ARCHITECTURE_MAP.md`, `BACKLOG_EXECUTION_PLAN.md`,
  `CONTEXT_HYGIENE.md`, `DDD.md`, `DECISION_LOG.md`, `PRD.md`,
  `RELEASE_DISCIPLINE.md`, `ROADMAP.md`, `SPEC.md`,
  `UBIQUITOUS_LANGUAGE.md`, `USER_GUIDE.md`, `WEB_VERIFICATION.md`,
  plus subdirs: `audits/`, `bug-hunt/`, `design/`, `examples/`,
  `research/`, `rfcs/` (62 RFCs + index + template), `workflows/`
  (40+ scaffolds).
- `tests/` — 100+ test files; `fixtures/openfoam/`,
  `fixtures/snappy_hex_mesh/` (gitkeep-only).
- `striatum/` — 941 tracked files of historical operator-report
  archives from past striatum runs (0010..0055-ish). Per RFC 0059 §2,
  this is provenance; I read directory names + a few PATCH_SUMMARY.md
  files to understand the convention but did not enumerate every file.
- `prompts/` — operator prompts (`CLAUDE_DESIGN_UI_REWORK_PROMPT.md`,
  `web_ui_second_pass_rework_2026-05-22.md`); both currently load-bearing.
- `scripts/` — single file: `codex-striatum-adapter.sh`.
- `.codex/agents/` — tracked codex skill bundles (mirror of
  `.claude/skills/` which is gitignored).
- `.vscode/` — `settings.json` (1 file, intentional editor config).

**Skipped** (read-only sample only):
- `.git/`, `.venv/`, `.striatum/` — runtime / VCS state.
- `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.benchmarks/`,
  `kayakgen.egg-info/` — generated, already gitignored (one entry
  was added this audit; see §3).
- `.claude/worktrees/` — gitignored worktrees.

## 1. Executive summary

- **3 commits landed** on `cleanup/2026-05-30`. One docs-only `.gitignore`
  patch and two stale-claim fixes in `AGENTS.md`. No file was deleted,
  moved, or flattened.
- **The repo is already remarkably clean.** No tracked `__pycache__`,
  no `.DS_Store`, no editor scratch, no obvious build output, no
  conflicted-merge backups. The existing `.gitignore` covers the
  large hitters (`.striatum/`, `.venv/`, `__pycache__/`, `*.egg-info/`,
  `.pytest_cache/`, `.claude/worktrees/`, `data/stability/…/`,
  `/*.stl`, `.claude/`).
- **The two finds that were genuinely actionable were both small.**
  `.ruff_cache/` and `.benchmarks/` exist at the repo root in normal
  dev work but were missing from `.gitignore`; added. `AGENTS.md`
  item 5 described `generator.py` as "the current implementation
  ~180 lines" — the RFC 0007 refactor has landed and that file is a
  57-line shim; rewritten to point at `kayakgen/model/geometry.py`.
- **`AGENTS.md`'s `docs/workflows/*.json` glob** was hiding 40+ active
  workflows from any agent reading the orientation file. Fixed to
  describe the current `docs/workflows/<NNNN-slug>/` convention and
  label the four legacy `.json`-suffix directories as pre-numbering
  provenance.
- **The "be aggressive on root files" instruction did not produce
  deletions.** Every candidate I considered (`generator.py`, `gui.py`,
  `pyvista_view.py`, the two `ARCHITECTURE_*_2026-05-16.md` docs,
  `OPERATOR_REPORT.md`) failed verification: each is documented as
  load-bearing by an active doc (Dockerfile / AGENTS.md / USER_GUIDE
  for the shims; CHANGELOG / DDD / multiple RFCs for the architecture
  docs; RELEASE_DISCIPLINE.md §9 explicitly pins `OPERATOR_REPORT.md`
  at root as the project-level checkpoint document). Verification
  notes per file are in §6.
- **The four legacy `.json`-suffix workflow directories** (`docs/workflows/{3d-rendering-design,3d-rendering-implement,gui-usability,layout-station-view}.json/`)
  predate the numbered workflow convention. No external doc references
  them, but they document landed work (RFC 0002, RFC 0003) and per the
  project's own RFC 0059 §2 provenance discipline they are provenance,
  not orphans. Deferred to §6.
- **Single-file directories** that I considered flattening
  (`docs/design/`, `docs/examples/`, `kayakgen/services/design_report_templates/`,
  `tests/fixtures/snappy_hex_mesh/`, `scripts/`) all passed the
  exception test for conventional structure. `docs/design/` is the
  borderline one and is recorded as a follow-up in §8.
- **Smoke checks**: `pytest tests/test_vocabulary_coverage.py
  tests/test_hull_parameter_metadata.py
  tests/test_hydrostatics_row_metadata.py tests/test_web_layout.py
  tests/test_web_inline_help.py tests/test_web.py -q` passes 152/152
  after the last commit. No production code was touched.

## 2. Branch and commits

Branch: `cleanup/2026-05-30`, forked from `main` at commit `e0e6c80`
(the final bug-hunt-loop termination commit from the prior session).
No `git push` performed; the branch lives locally for the maintainer
to merge / rebase / drop.

| SHA | Subject |
|---|---|
| `625c3eb` | cleanup: gitignore `.ruff_cache` + `.benchmarks` |
| `86e45a8` | cleanup: AGENTS.md item 5 — point to landed RFC 0007 package |
| `8feeb26` | cleanup: AGENTS.md — describe current workflow scaffolds correctly |

Each is independently revertible: `git revert <sha>` undoes one
category without touching the others. The commits are sequenced
gitignore → docs1 → docs2 so revert order does not matter.

## 3. Done: deletions

None. The repo had no tracked artifacts that needed removal. The
caches at the working-tree root (`__pycache__/`, `.pytest_cache/`,
`.ruff_cache/`, `.benchmarks/`, `kayakgen.egg-info/`) are all
untracked. `git ls-files | grep -E "(__pycache__|\.pyc$|\.pytest_cache|\.ruff_cache|\.benchmarks|egg-info|\.DS_Store|\.swp$|\.bak$|\.tmp$|\.log$|\.orig$|~$)"`
returns zero matches.

The `.gitignore` additions in `625c3eb` cover two of those caches
that were not yet listed (`.ruff_cache/`, `.benchmarks/`) — pure
gitignore hygiene, no files removed.

## 4. Done: moves and flattenings

None. Every candidate failed verification; see §6 for the detail.

## 5. Done: doc updates and merges

### `86e45a8` — `AGENTS.md` item 5

**What was wrong**: item 5 of the reading list described `generator.py`
as "the current implementation. ~180 lines, single class, does one
thing (lofted hull → STL). Reading the code and reading RFC 0007 in
tandem makes the planned refactor obvious."

**Evidence of staleness**:
- `wc -l generator.py` = 57 lines (not 180).
- The file's own docstring opens with "Legacy entry point — re-exports
  the lofted geometry under its old name. Use
  `kayakgen.model.geometry.LoftedHullGeometry` directly in new code."
- The RFC 0007 architectural revisit is marked `landed` in
  `docs/rfcs/README.md` and `docs/rfcs/0007-architectural-revisit.md`.
- The production code lives under `kayakgen/model/geometry.py`
  (`class LoftedHullGeometry`) plus `kayakgen/model/hull.py`.

**What I changed**: item 5 now points to `kayakgen/model/geometry.py`
as the canonical lofted-geometry surface and labels the three root
shims (57, 11, 7 lines respectively) as backward-compat re-exports
preserved for legacy importers — which the file's own docstring and
AGENTS.md's prior "co-equal but smaller" note already implied. The
reading order is unchanged; readers now reach the post-refactor code
on the first pass.

### `8feeb26` — `AGENTS.md` workflow glob

**What was wrong**: the labeled-negative-space entry was
`docs/workflows/*.json` — a glob that matches only the four legacy
directories whose names end in `.json`. The current convention is
`docs/workflows/<NNNN-slug>/workflow.json` and there are 40+ such
scaffolds (numbered 0009 through 0039 plus the audit-cadence pieces).

**Evidence of staleness**:
- `ls docs/workflows/ | grep -c "^[0-9]"` = 40+.
- `ls docs/workflows/ | grep "\.json$"` returns exactly four directories.
- The four `.json`-suffix dirs were created `2026-05-09` (initial
  commit and a couple of follow-ups); the numbered convention has
  been in use since the 0009 multi-lane review and is now the only
  pattern used for new work.

**What I changed**: the entry now describes
`docs/workflows/<NNNN-slug>/` as the current pattern and labels the
four legacy `.json`-suffix directories as pre-numbering provenance.
No path is renamed; the goal is to keep agents reading AGENTS.md from
mis-glossing 90% of the workflow surface.

## 6. Deferred: needs maintainer decision

### Stop condition: "would touch a file whose intent isn't obvious from the code"

- **`OPERATOR_REPORT.md` (root, 1,264 lines)** — operator-owned
  checkpoint document, last `Updated: 2026-05-17`. Many checkpoint
  entries are now historical (e.g. references to the cowboy 2026-05-15
  session, batches 1–8 from `docs/BACKLOG_EXECUTION_PLAN.md`). It is
  not stale in the "claim disagrees with code" sense — it is a
  point-in-time log. **Question for maintainer**: should the
  pre-2026-05-25 checkpoints be archived (move to
  `docs/operator-reports/2026-05-17.md` and start a fresh root-level
  doc) or left as-is per the project's own provenance discipline?

### Stop condition: "larger than ~50 lines of net diff for a single finding"

- **`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md` (478 lines, root)**
  and **`ARCHITECTURE_REVIEW_2026-05-16.md` (949 lines, root)** —
  dated planning / review docs. Convention for dated archives in this
  project is `docs/research/<DATED-SLUG>.md` (cf.
  `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md`,
  `docs/research/STRAIN_GAUGED_GZ_RIG_DESIGN_2026-05-16.md`). But:
  - `grep -l ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16` shows it
    is cited by `CHANGELOG.md`, `docs/RELEASE_DISCIPLINE.md`,
    `docs/DDD.md`, `docs/rfcs/README.md`, and at least five RFC
    bodies (0049, 0050, 0052, 0054, 0055).
  - `ARCHITECTURE_REVIEW_2026-05-16` is cited from the same set plus
    `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md` itself.
  - Moving them under `docs/research/` would touch ~10 files of
    cross-references — past the ~50-line cleanup threshold, into
    refactor territory.

  **Question for maintainer**: do you want these moved under
  `docs/research/` (matching the 2026-05-16 sibling docs already
  there) as a separate, deliberate refactor, or kept at root with
  their current cross-link surface?

### Stop condition: "filename pattern suggests it could be loaded dynamically by name"

- **`docs/workflows/3d-rendering-design.json/`,
  `docs/workflows/3d-rendering-implement.json/`,
  `docs/workflows/gui-usability.json/`,
  `docs/workflows/layout-station-view.json/`** — four pre-numbering
  workflow scaffolds. Authored by the maintainer between
  2026-05-09 and 2026-05-10 (`git log --diff-filter=A`). The RFCs they
  produced are landed (RFC 0002 GUI usability, RFC 0003 layout +
  station view). Striatum's `striatum/` run-record archive contains
  no run for any of these workflow_ids. They are referenced only by
  their own internal files (workflow.json ↔ prompts ↔ roles).
  - On one reading, these are provenance for landed RFCs and should
    be preserved per RFC 0059 §2.
  - On another reading, the work product of a landed RFC is the RFC
    itself plus the implementation commit; the workflow scaffold is
    scaffolding that has served its purpose.

  **Question for maintainer**: are these kept for provenance, or do
  you want them removed? If kept, the AGENTS.md update in §5 already
  labels them correctly; if removed, that label can be deleted in the
  same commit.

### Stop condition: "ambiguous claim, code could be interpreted either way"

None this pass.

## 7. Verified clean

- **Editor / OS scratch files**: zero matches for `.DS_Store`,
  `Thumbs.db`, `.swp`, `.bak`, `.tmp`, `.log`, `.orig`, `~`.
- **Build output committed by accident**: zero matches for `*.pyc`,
  `__pycache__` under `git ls-files`. Caches at the working-tree
  root are all untracked.
- **`.vscode/` and `.codex/`**: both are tracked single-purpose
  agent / editor configs that the project intentionally ships
  (the codex skills mirror the gitignored Claude skills).
- **Single-file directories under `tests/fixtures/`**: each holds a
  fixture pinned to its source (openfoam force.dat, snappyHexMesh
  `.gitkeep` placeholder). Convention; leave.
- **`scripts/`**: holds one adapter script and is a project-convention
  holding directory. Leave.
- **`docs/examples/`, `docs/research/`, `docs/rfcs/`, `docs/audits/`,
  `docs/bug-hunt/`, `docs/workflows/`**: all are documented
  conventions; none had stale or orphaned content I could verify.
- **Striatum run archives under `striatum/`**: 941 tracked files
  spread across ~50 historical workflow directories. Provenance per
  RFC 0059 §2; not surveyed file-by-file but spot-checked five
  PATCH_SUMMARY.md files for plausibility.

## 8. Follow-ups

These emerged from the audit but are out of scope for an inline-execute
cleanup pass.

- **`docs/design/` is a single-file directory** holding
  `kayak_hull_design_constraints.md`. It is referenced from
  `docs/PRD.md`, `AGENTS.md` (reading-list item 3), and several
  workflow `SOURCES.md` files. A maintainer-led decision: flatten to
  `docs/kayak_hull_design_constraints.md` and update the ~6 references
  in one PR, OR explicitly mark `docs/design/` as a forward-looking
  container (in which case the AGENTS.md item-3 entry could note that
  more design docs are expected to land there).
- **`docs/workflows/` has duplicate-numbering** (e.g. both
  `0029-code-doc-audit/` and `0029-web-cfd-job-routes/`, both
  `0030-stability-claim-gate-literal/` and
  `0030-resistance-calibration-fixture/`, several more). This is
  apparently deliberate — different concerns reusing numbers as the
  numbering pool drifted — but it is confusing on `ls`. If the
  project wants a single linearised numbering, that is a refactor
  affecting ~20 directories plus their references.
- **The `OPERATOR_REPORT.md` archiving question** (see §6) is one
  the maintainer could resolve once and then the audit cadence would
  pick up the new pattern.
- **The four legacy `.json`-suffix workflow directories** (see §6).
  Resolution is binary: delete or document-and-keep.
- **`AGENTS.md` item 2** lists "desktop and web frontends" as in scope.
  The web frontend recently received the b82b544 second-pass redesign,
  workflow 0037 inline-help additions, and workflow 0039 description
  tooltips — all landed during this session's predecessor sessions.
  AGENTS.md's "current direction" paragraph (lines 84-114) was
  written before those landed and now reads as historical with
  respect to the web tab structure and the form-builder. A standalone
  AGENTS.md refresh is worth doing as a single small PR rather than
  patching individual claims piecemeal.

---

*Produced 2026-05-30 by Claude Opus 4.7 against
`/home/halbritt/git/kayak-gen` at branch `cleanup/2026-05-30`,
parented at `main` `e0e6c80`. Three commits: `625c3eb`, `86e45a8`,
`8feeb26`. No remote push performed; the maintainer chooses the
disposition of the branch.*
