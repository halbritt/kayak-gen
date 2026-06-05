# Goal A — Retire internal traffic through compatibility shims (brief C6)

author: proposer-a-claude-001

Date: 2026-06-05
Source brief: `striatum/refactoring/kayakgen-smoke-1/00-goal/PROBLEM_BRIEF.md` (candidate C6)
Champion stance: lowest-risk, most verifiable path. Tradeoffs stated plainly in §7.

---

## 1. The goal

**Internal shim-importer redirection**: every importer *inside* `kayakgen/`
that currently imports through a compatibility shim is redirected to the
symbol's documented canonical home. Every shim file is left byte-identical
and remains the supported external alias. No symbol moves, no module splits,
no signature changes — only the `from X import Y` source module changes at
each internal call site, to the home the shim's own docstring already names.

This is behavior-preserving by construction: each shim re-exports the *same
objects* from the canonical homes (verified — e.g. `eval/cfd/jobs.py` is a
180-line pure re-export block; `cli/high_angle_gz.py` is a pure re-export
with `__all__`), so a redirected importer binds the identical function/class
objects it bound before.

## 2. Blast radius (verified against the tree, 2026-06-05)

**Edited files — 10, import statements only:**

Internal importers of `kayakgen.eval.cfd.jobs` (canonical homes per the
shim's own import block: `records` / `profiles` / `job_store` /
`manifest_validation` / `provenance` / `parsers.openfoam_forces` /
`adapters.*`):

| Site | Symbol(s) | Canonical home |
|---|---|---|
| `kayakgen/eval/cfd/__init__.py:5` | re-export block | per-symbol homes |
| `kayakgen/eval/cfd/fixture_command.py:11` | fixture types | `adapters.fixture` |
| `kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:17` | `OpenFoamProvenanceProbe` | `provenance.py:29` |
| `kayakgen/eval/cfd/openfoam_v2512_interfoam/case_render.py:33` | `OPENFOAM_CASE_TEMPLATE_VERSION` | `profiles.py:25` |
| `kayakgen/eval/evidence/openfoam.py:14` | `OpenFoamProvenanceProbe` | `provenance.py:29` |
| `kayakgen/eval/snappy_hex_mesh.py:33` | `OpenFoamProvenanceProbe` | `provenance.py:29` |
| `kayakgen/services/artifacts.py:16` | `CFD_RAW_RESULTS_WARNING` | `profiles.py:16` |
| `kayakgen/services/cfd_jobs.py:18` | dispatch contracts | per-symbol homes |
| `kayakgen/ui/web/controllers.py:16` | `CFD_RAW_RESULTS_WARNING` | `profiles.py:16` |
| `kayakgen/cli/main.py:28` and `:252` (function-local) | contracts; `probe_openfoam_provenance`, `OPENFOAM_LOCAL_RUN_ENV_VAR` | per-symbol homes |

Internal importer of `kayakgen.cli.high_angle_gz`:

| Site | Symbol(s) | Canonical home |
|---|---|---|
| `kayakgen/cli/main.py:12` | `build_high_angle_gz_block`, `parse_heel_grid_deg` | `kayakgen.eval.high_angle_gz` |

**Deliberately untouched:**

- All shim files: `kayakgen/eval/cfd/jobs.py`, `kayakgen/cli/high_angle_gz.py`,
  root `generator.py` / `gui.py` / `pyvista_view.py` — zero edits, byte-identical.
- The 10 test files importing `kayakgen.eval.cfd.jobs` and
  `tests/test_stability_cli_high_angle.py:11` (explicitly "kept for compat
  smoke") — these *stay on the shims on purpose*: after this goal they are the
  regression suite proving the external alias surface still works.
- `tests/test_golden.py:41` / `tests/golden/regenerate.py:20` off root
  `generator.py` — **scoped out** (stale-evidence correction, §6).
- No generated sources, no docs requiring the public-behavior checklist, no
  public entrypoints.

## 3. Frozen surfaces nearby, and why none is crossed

- **Compatibility aliases / legacy import paths (§3 of the brief)** — this
  goal works *adjacent to* this surface by definition. It does not cross it:
  every shim file is unmodified, and external `from kayakgen.eval.cfd.jobs
  import ...` / `from kayakgen.cli.high_angle_gz import ...` / `from generator
  import KayakGenerator` continue to resolve to the identical objects. The
  brief explicitly licenses this: "C6 may redirect *internal* importers only."
- **Package-`__init__` re-export surfaces** — `eval/cfd/__init__.py` and
  `eval/evidence/openfoam.py` are edited, but only the *source* of their
  re-exports changes (shim → canonical home). The exported names and the
  bound objects are identical, because the shim itself re-exports from those
  same homes. The frozen property is the import surface, not the file bytes;
  the surface is preserved object-for-object.
- **Public CLI surface** — `cli/main.py` edits are import statements only;
  command registration, names, options, help text, and exit behavior are
  untouched lines.
- **Byte-stable generated outputs** — `case_render.py` is touched (one import
  line; the constant it imports is the same string object). Golden STL and
  case-render verification gates run unchanged (§4 slices).
- **Test/boundary contracts** — `tests/test_import_boundaries.py` enforces
  direction at the subpackage level (model/eval/search/ui/cli) and bans
  underscore-prefixed reach-ins. Every redirect keeps the same source→target
  subpackage edge it had through the shim (eval→eval, services→eval, ui→eval,
  cli→eval) and imports only public names, so these tests pass without
  modification — and act as a gate, not a casualty.
- **Monkeypatch points** — verified: no test monkeypatches attributes on the
  `jobs` shim module, and `tests/test_stability_cli_high_angle.py:176-180`
  already patches the *eval* module's call site (comment says so explicitly),
  so redirects cannot change patch visibility.

## 4. Slices

Each slice is independently landable, independently verifiable, and
reverts with a one-commit revert of import lines.

**S1 — eval-internal redirects** (6 sites: `eval/cfd/__init__.py`,
`fixture_command.py`, `openfoam_v2512_interfoam/evidence.py`,
`openfoam_v2512_interfoam/case_render.py`, `eval/evidence/openfoam.py`,
`snappy_hex_mesh.py`).
*Preservation claim:* `kayakgen.eval.cfd` and `kayakgen.eval.evidence.openfoam`
export the same names bound to the same objects; all CFD/mesh/golden tests
unchanged and green.
*Verify:* `.venv/bin/python -m pytest -q` and
`.venv/bin/python -m ruff check kayakgen tests`; additionally
`KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 .venv/bin/python -m pytest tests/test_openfoam_v2512_smoke.py -q`
(this slice touches imports in the provenance-probe and case-render
neighborhoods, which is exactly the brief's trigger for the opt-in smoke).

**S2 — services + ui redirects** (3 sites: `services/artifacts.py`,
`services/cfd_jobs.py`, `ui/web/controllers.py`).
*Preservation claim:* web/services behavior identical;
`tests/test_services_boundaries.py` and the web suite unchanged and green.
*Verify:* `.venv/bin/python -m pytest -q`;
`.venv/bin/python -m ruff check kayakgen tests`. (`pytest -m
browser_acceptance` available if the reviewer wants belt-and-braces; the edit
is one constant's import source.)

**S3 — cli redirects** (3 sites: `cli/main.py:12`, `:28`, `:252`).
*Preservation claim:* registered command surface, options, output text, and
exit behavior byte-identical; CLI tests and the high-angle compat smoke
unchanged and green.
*Verify:* `.venv/bin/python -m pytest -q`;
`.venv/bin/python -m ruff check kayakgen tests`.

Slice order is risk-ascending in surface proximity (eval internals → services/ui
→ public CLI module), but the slices are independent and can land in any order.

## 5. Existing coverage; characterization tests

Coverage near the blast radius is already strong and — unusually for a
refactor — the compatibility property itself is directly pinned:

- 10 test files import through `eval.cfd.jobs` (e.g. `test_cfd_jobs.py`,
  `test_cfd_jobs_openfoam.py`, `test_cfd_run_stages.py`,
  `test_openfoam_v2512_case_render.py`, `test_snappy_hex_mesh_harness.py`,
  `test_web.py`), so the shim's re-export surface is exercised on every run.
- `tests/test_stability_cli_high_angle.py` pins `cli.high_angle_gz` imports
  as deliberate compat smoke.
- `tests/test_golden.py` pins root `generator.py` and byte-stable STL output.
- `tests/test_import_boundaries.py` / `test_services_boundaries.py` pin
  dependency direction.

**No new characterization tests are required before movement**, because no
semantics move — the redirected name binds the identical object. Optional
cheap hardening (recommended, not required): a ~20-line test asserting every
public name in `kayakgen.eval.cfd.jobs` is the *same object* (`is`) as the
attribute of its canonical module, turning the shim's pure-alias property
into an explicit invariant. It would also catch future drift.

## 6. Stale-evidence corrections to the brief

- The brief's C6 says "the same pattern applies to … the root-level
  `generator.py` consumed by `tests/test_golden.py`". Verified: **root
  `generator.py` is not a pure re-export shim** — it defines a legacy
  `KayakGenerator` adapter class that maps the historical constructor
  signature onto `Hull` + `LoftedHullGeometry`. Redirecting the golden tests
  off it is not a mechanical import swap, and the golden test is arguably the
  compat regression *for* that frozen surface. Goal A therefore **excludes**
  the `generator.py` importers; that exclusion is a scoping decision the
  dissent lane can challenge.
- Brief's "e.g." sites verified, and the full census is larger: 11 internal
  import sites across 10 files (table in §2), including a shim-through-shim
  chain — `eval/evidence/openfoam.py` (itself the "neutral home") imports
  `OpenFoamProvenanceProbe` *via the jobs shim* instead of from
  `provenance.py`, its documented canonical home.

## 7. Expected payoff — and its honest ceiling

- The dependency graph stops lying: canonical homes become the only internal
  homes, and `grep -r "eval\.cfd\.jobs" kayakgen/` going to zero becomes a
  durable, mechanically checkable invariant ("shims are external surface
  only") that reviews and future hygiene gates can enforce.
- Eliminates shim-through-shim layering (e.g. evidence→jobs→provenance) that
  misleads readers about what depends on what.
- Directly de-risks future campaigns: C1/C3-style splits get a truthful
  import graph to plan against, and an eventual external-deprecation decision
  for the shims gains a clean internal/external usage signal.
- Ceiling, stated plainly: this buys *navigability and truthful structure*,
  not a smaller `app.py`. If the operator wants the highest-payoff goal, C1
  is that goal and carries proportionally more risk; A is the goal you pick
  when you want near-certain preservation with verification that already
  exists end-to-end.

## 8. Known risks and reducing evidence

| Risk | Status / reducing evidence |
|---|---|
| A test monkeypatches the shim module's attributes, so a redirected caller stops seeing the patch | Verified absent: no `monkeypatch.setattr` against `eval.cfd.jobs`; the high-angle test patches the eval module by design (its own comment). The optional identity test in §5 keeps this pinned. |
| A "canonical home" disagrees with the shim docstring | Each redirect copies the source module from the shim's own import block — the shim *is* the authority; reviewer diffs each line against it. |
| Import-cycle introduced by importing a deeper module directly | Homes are siblings the shim already imports at module load; the import edge already exists transitively. Full-suite import of every module under test plus ruff would surface a cycle immediately. |
| `eval/cfd/__init__.py` re-export drift (name lost in transcription) | The 10 shim-importing test files plus `test_web.py` exercise the surface; optional §5 identity test makes it explicit. |
| Scope creep into "while I'm here" cleanups | Write scope per slice is the listed files' import blocks only; anything else is out of scope by construction. |

## 9. Scorecard self-assessment (for the record, not the scorekeeper)

- `preservation_verifiability`: maximal — identity-preserving rebinds under an
  existing suite that already pins both the shims and the canonical homes.
- `blast_radius`: 10 files, import statements only; zero shim/file deletions.
- `payoff`: moderate — structural truthfulness and future-campaign leverage,
  not user-visible simplification.
- `reversibility`: trivial — per-slice one-commit reverts, no state.
- `frozen_surface_risk`: low by construction — adjacent to the alias surface
  but never edits it; licensed explicitly by the brief.
- `sliceability`: high — three independent slices, each with its own gate.
