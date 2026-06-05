# Problem Brief — Behavior-Preserving Refactoring Campaign (kayakgen-smoke-1)

author: problem-framer-claude-001

Date: 2026-06-05
Repository: `kayak-gen` @ `main` (425ad76)
Scope: stage 0 (goal selection) of a behavior-preserving refactoring campaign.
A refactor here changes code shape — boundaries, ownership, names, duplication,
dependency direction, test seams, or module layout — and does not change
observable behavior.

This brief is factual. It surveys candidates, records the verification
commands, and inventories the frozen surfaces. It does not rank or choose.

---

## 1. Candidate refactoring goals

Each candidate is concrete and bounded. Line counts measured 2026-06-05.

### C1 · Split `kayakgen/ui/web/app.py` (2,550 lines) along the Generate-panel seam
The largest module in the repo grew 241 → 2,550 lines post-refactor by
absorbing the Generate panel, and its import block already exposes the seam
(`generate_spec_form`, `generate_frontier_view`, `generate_fork_button`,
`generate_state_listener`, `read_models`, `state`, `controllers`), so the
panel-construction and state-wiring responsibilities can move to sibling
modules behind the existing web-layout and browser-acceptance tests.
(Pre-identified as item B2 in `TODO.md` and as "the one untamed boundary" in
the 2026-06-03 deep architecture review.)

### C2 · Split `kayakgen/cli/main.py` (1,049 lines) into per-domain command modules
The `cfd`, `calibration`, `runs`, and `stability` groups are already mounted
as sub-apps (`main.py:47-54`) while ~15 root commands (init / generate /
evaluate / mesh-check / mesh-package / mesh-evidence / view / serve / sweep /
search / compare / build-export …) remain inline, so moving command bodies to
sibling modules in `kayakgen/cli/` follows the established pattern with the
registered command surface unchanged.

### C3 · Split `kayakgen/services/generative_jobs.py` (1,372 lines) along its schema/orchestration seam
One module currently carries the generative-job record schemas and the
`SubprocessGenerativeJobManager` process-orchestration logic, and separating
contracts from orchestration would mirror the Phase-3A `eval/cfd` split
(records / job_store / adapters) that the package already treats as canonical.

### C4 · Split `kayakgen/search/active/runner.py` (1,389 lines)
The active-search runner is the second-largest non-UI module and mixes spec
resolution, the evaluation loop, and run-artifact emission; splitting it into
focused siblings inside `kayakgen/search/active/` would bring it in line with
the rest of the `search/` package (sweep 604, compare 618, nsga2 444).

### C5 · Move `kayakgen/eval/calibration/__init__.py` (756 lines) implementation into named sibling modules
The calibration package keeps its registry, schemas, and validator
implementations inside `__init__.py`, unlike the sibling `eval/closed_volume/`
and `eval/stability/` packages whose `__init__.py` files are thin re-export
surfaces over named modules — repeating that precedented split keeps the
public import surface byte-identical. (Note: this code is dormant pending
data per `TODO.md` B1; a layout-only split does not change that disposition.)

### C6 · Migrate in-package importers off compatibility shims to canonical homes
`kayakgen/eval/cfd/jobs.py` documents itself as a compatibility shim whose
canonical homes are `records`/`profiles`/`job_store`/`manifest_validation`/
`provenance`/`parsers`/`adapters`, yet in-package code still imports through
it (e.g. `eval/snappy_hex_mesh.py:33`, `eval/evidence/openfoam.py:14`), and
the same pattern applies to `kayakgen/cli/high_angle_gz.py` and the root-level
`generator.py` consumed by `tests/test_golden.py` / `tests/golden/regenerate.py`
— redirecting internal importers leaves every shim in place as a pure external
alias (dependency-direction cleanup; the shims themselves are frozen surface,
see §3).

### C7 · Collapse `ClaimMetadata` legacy-alias double-population
`claims.py:172-175` carries `accepted_use`→`accepted_uses` and
`calibration_version`→`model_version` legacy aliases that `resistance.py:166-177`
still double-populates, and consolidating producers onto the canonical fields
(while keeping the alias acceptance for inbound records) removes duplication
from the integrity contract under existing claim tests. (Pre-identified as
item B5 in `TODO.md`; serialized claim records border the frozen surface —
see §3 — so the producer-side dedup and any alias retirement are separable
slices.)

### C8 · Split `kayakgen/ui/web/generate_spec_form.py` (1,452 lines)
The Generate-panel spec form is the second-largest UI module and bundles form
schema/state definitions with widget rendering; splitting the
declaration/rendering seam inside `kayakgen/ui/web/` reduces the blast radius
of future Generate-panel changes behind the same web test suite.

"Refactor this repo" and whole-layer rewrites are rejected as too broad and
are not listed.

---

## 2. Verification commands

Inferred from `pyproject.toml`, `docs/RELEASE_DISCIPLINE.md` (pre-merge
requirements), and `tests/`. There is no Makefile and no CI config in the
repo (`.github/workflows` absent); verification is local.

| Command | Role |
|---|---|
| `.venv/bin/python -m pytest -q` | Full suite (215 test files, ~27K LOC; `testpaths=["tests"]`, `addopts="-ra"`). Must be green or skipped. |
| `.venv/bin/python -m ruff check kayakgen tests` | Lint gate (`line-length=100`, `target-version=py311`). Must pass. |
| `KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 .venv/bin/python -m pytest tests/test_openfoam_v2512_smoke.py -q` | Opt-in OpenFOAM smoke; recommended when a change touches CFD adapters, case templates, or the provenance probe. Skips unless both env knobs are set. |
| `pytest -m browser_acceptance` (with `[browser]` extra / Playwright) | Real-browser acceptance profile for the web frontend (`tests/test_web_browser.py`); relevant to any `ui/web` candidate. |

Additional notes:

- `mypy>=1.10` is in the `[dev]` extra but no mypy configuration section
  exists in `pyproject.toml`; it is not an enforced gate.
- Guard tests that any candidate must keep green: `tests/test_golden.py`
  (byte-stable golden STL), `tests/test_import_boundaries.py`,
  `tests/test_services_boundaries.py`, `tests/test_vocabulary_coverage.py`,
  plus the forbidden-copy/no-claim regressions cited in
  `docs/RELEASE_DISCIPLINE.md`.
- Release discipline also requires: no force-push to `main`, agent co-author
  attribution, and the public-behavior-change doc checklist (USER_GUIDE,
  PRD, ROADMAP, rfcs/README, DECISION_LOG, CHANGELOG, ARCHITECTURE_MAP,
  UBIQUITOUS_LANGUAGE, OPERATOR_REPORT) — a behavior-preserving refactor
  should not trigger that checklist, which is itself a useful invariant.

---

## 3. First-pass frozen-surface inventory

Surfaces no candidate may change. Sources: `docs/RELEASE_DISCIPLINE.md`,
`docs/ARCHITECTURE_MAP.md`, module docstrings, test suite.

**Public CLI surface** — the `kayakgen` console script
(`kayakgen.cli.main:app`): root commands (init, generate, evaluate,
mesh-check, mesh-package, mesh-evidence, view, serve, sweep, search, compare,
build-export, …) and mounted sub-apps `cfd` (prepare/status/run/profiles),
`calibration` (ingest-tank-test/ingest-inclining-test/accept-fit/
residual-plot), `runs`, `stability` (including the hidden `legacy`
subcommand). Command names, options, output text, and exit behavior are
observable behavior.

**Public JSON schemas** — Pydantic models carrying `schema_version` across
~20 modules (Hull spec, `eval/contract.py` EvaluationResult/GZCurve,
mesh-package manifest, closed-volume schemas, CFD records, SearchSpec,
calibration/campaign records, stability accepted-fit and measured-fixture
schemas, generative-job records, sensitivity/design-report payloads,
`model/validity.py`). Schemas are `extra="forbid"`; field names, types,
defaults, and `schema_version` values are frozen.

**Byte-stable generated outputs** — golden STL fixtures
(`tests/golden/default_hull.stl`, `default_deck.stl` + `regenerate.py`); the
byte-deterministic OpenFOAM case render
(`eval/cfd/openfoam_v2512_interfoam/case_render.py` + 15 vendored case-dict
templates); sweep output formats including `summary.csv` column names that
downstream `compare` consumes.

**Claim/readiness vocabulary and no-claim invariants** — the claim-state
ladder and accepted-use literals in `eval/claims.py`, gate functions
(`claim_allows_calibrated_prediction` / `_final_design_fitness`), readiness
literals, named tokens (e.g. `CALIBRATION_PROMOTION_REQUIRES_ACCEPTED_FIT`,
`EMPTY_STABILITY_FIT_REGISTRY`), and the forbidden-copy / vocabulary-coverage
regressions that pin them. Serialized claim records — including the
`accepted_use`/`calibration_version` legacy aliases accepted on inbound
records — are compatibility surface (bears directly on C7).

**Compatibility aliases / legacy import paths** — root shims `generator.py`
(`KayakGenerator`), `gui.py` (`KayakGUI`), `pyvista_view.py`
(`PyVistaWindow`); package shims `kayakgen/eval/cfd/jobs.py`,
`kayakgen/cli/high_angle_gz.py`, and the `kayakgen/eval/evidence/*` and
package-`__init__` re-export surfaces (`eval/closed_volume`,
`eval/stability`). External `from kayakgen.eval.cfd.jobs import ...` and
`from generator import KayakGenerator` imports must keep working byte-stably
(C6 may redirect *internal* importers only).

**Durable artifacts and storage** — the RFC 0049 artifact store and its
SQLite index (`services/artifact_store.py`, `services/identity`): durable
artifact names, locations, and identity scheme; the user config file format
`~/.config/kayakgen/cfd.json` (`eval/cfd/config.py`); CFD run-record
persistence (`eval/cfd/job_store.py`).

**Test/boundary contracts** — import-boundary and services-boundary tests
encode the allowed dependency directions; any module move must land with
those tests green, not weakened. The `browser_acceptance` pytest marker name
is referenced in `pyproject.toml` and must survive.

**Event ordering** — generative-job state transitions observed by
`generate_state_listener` and the web UI, and CFD job-state plumbing
(prepare → run → status records); refactors may move this code but not
reorder observable state transitions.

There is no database schema beyond the artifact-store SQLite index and no
network wire format (local-first, D023); no migration framework exists.

---

## 4. Fixed scorecard dimensions

Every goal proposed from this brief is scored on exactly these dimensions:

- `preservation_verifiability` — how completely existing tests/gates can
  demonstrate behavior is unchanged.
- `blast_radius` — how much of the codebase the change touches or risks.
- `payoff` — what the new shape buys future work.
- `reversibility` — how cheaply the change can be backed out.
- `frozen_surface_risk` — proximity to the §3 inventory.
- `sliceability` — how well the work decomposes into independently
  landable, independently verifiable slices.

---

## 5. Out of scope for every candidate

Features, bug fixes, schema changes, dependency upgrades, broad rewrites,
speculative abstractions, and cleanup findings small enough for a hygiene
pass. Additionally out of scope per repo decisions: any change to claim-state
promotion rules (the no-claim invariants are load-bearing product integrity),
and eviction of the process layer (withdrawn as B3 in `TODO.md` after the C1
framing decision of 2026-06-03).
