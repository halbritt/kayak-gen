# Goal C — Migrate in-package importers off compatibility shims to canonical homes

author: proposer-c-claude-001

Date: 2026-06-05
Source candidate: C6 in `PROBLEM_BRIEF.md`
Repository: `kayak-gen` @ `main` (425ad76)

## 1. The goal

**Internal-importers-off-shims**: redirect every in-package importer of the
three compatibility-shim families — `kayakgen/eval/cfd/jobs.py`,
`kayakgen/cli/high_angle_gz.py`, and root-level `generator.py` — to the
canonical modules each shim documents, leaving every shim in place,
byte-identical, as a pure external alias; then pin the new state with a
boundary ratchet test so internal fan-in to the shims stays at zero.

This is a dependency-direction cleanup with no semantic movement at all: no
function bodies move, no modules split, no names change. Only import
statements change which module they name, binding the *same objects*.

## 2. Re-verified evidence (2026-06-05, against the current tree)

The brief's claims hold, and the importer inventory is larger than its
examples. Verified directly:

- `kayakgen/eval/cfd/jobs.py` is 180 lines and contains **zero local
  definitions** — only re-export imports and an `__all__` (line 109). Its
  docstring names canonical homes: `records`, `profiles`, `job_store`,
  `manifest_validation`, `provenance`, `parsers.openfoam_forces`, `adapters`.
- Canonical homes confirmed for spot-checked names:
  `CFD_RAW_RESULTS_WARNING`, `CFD_FIXTURE_RESULTS_WARNING`,
  `OPENFOAM_CASE_TEMPLATE_VERSION` → `eval/cfd/profiles.py:16-25`;
  `OpenFoamProvenanceProbe` → `eval/cfd/provenance.py:29`.
- **Ten in-package import sites** route through the `jobs` shim:
  1. `kayakgen/eval/cfd/__init__.py:5` (~35 names)
  2. `kayakgen/eval/cfd/fixture_command.py:11`
  3. `kayakgen/eval/cfd/openfoam_v2512_interfoam/case_render.py:33`
  4. `kayakgen/eval/cfd/openfoam_v2512_interfoam/evidence.py:17`
  5. `kayakgen/eval/snappy_hex_mesh.py:33`
  6. `kayakgen/eval/evidence/openfoam.py:14`
  7. `kayakgen/ui/web/controllers.py:16`
  8. `kayakgen/services/artifacts.py:16`
  9. `kayakgen/services/cfd_jobs.py:18`
  10. `kayakgen/cli/main.py:28` (module-level) and `:252` (function-local)
- `kayakgen/cli/high_angle_gz.py` (32 lines, pure re-export) has exactly one
  in-package importer: `kayakgen/cli/main.py:12`.
- The monkeypatch hazard the shim docstring warns about is **already
  defused**: `tests/test_stability_cli_high_angle.py:176-180` patches the
  *eval* module's call site, with a comment saying so, and
  `eval/high_angle_gz.py:175` resolves the body builder through its own
  module global. Redirecting `cli/main.py:12` is therefore inert; the shim's
  `generated_hull_plus_deck_body` re-export stays for external patchers.
- Root `generator.py` (57 lines) is **not** a pure re-export: `KayakGenerator`
  is a subclass of `LoftedHullGeometry` adapting the legacy positional
  constructor into `Hull(...)`. Its only importers are
  `tests/test_golden.py:41` and `tests/golden/regenerate.py:20`.
- The other root shims (`gui.py`, `pyvista_view.py`) have **zero** in-package
  importers — already clean; nothing to do there.
- `tests/test_import_boundaries.py` currently contains no shim-related rule,
  so the end-state is not yet pinned by any guard.

## 3. Blast radius

- **Edited files (import lines only):** the 10 `jobs`-shim sites above,
  `cli/main.py:12` (high_angle_gz), `tests/test_golden.py`,
  `tests/golden/regenerate.py` — 12 files, ~14 import statements.
- **New/extended tests:** one shim-equivalence characterization test (new
  file, e.g. `tests/test_legacy_shims.py`) and one ratchet rule in
  `tests/test_import_boundaries.py`.
- **Untouched:** all shim files themselves, all function bodies, all public
  entrypoints (`kayakgen.cli.main:app` console script), all generated
  sources, all docs (no public behavior change ⇒ the RELEASE_DISCIPLINE doc
  checklist is deliberately *not* triggered, which is itself a check).
- **Test-side shim imports left alone by design** (see §8): the deliberate
  compat smoke at `tests/test_stability_cli_high_angle.py:11` and the
  incidental shim imports in `tests/test_compare.py:10`,
  `tests/test_web.py:277`, `tests/test_web_read_models.py:5` — these are
  free extra compat coverage from outside the package, exactly what shims
  are for.

## 4. Frozen surfaces nearby, and why none is crossed

- **Compatibility aliases / legacy import paths (§3 of the brief, directly
  adjacent).** Every shim file is left byte-identical; external
  `from kayakgen.eval.cfd.jobs import ...`, `kayakgen.cli.high_angle_gz`,
  and `from generator import KayakGenerator` keep working unchanged. The
  brief explicitly scopes C6 to internal importers only; this proposal honors
  that line and adds a test asserting shim ↔ canonical object identity.
- **Package-`__init__` re-export surfaces.** `eval/cfd/__init__.py` keeps
  re-exporting the same ~35 names; only the upstream module path changes,
  binding identical objects, so `from kayakgen.eval.cfd import X` is
  observationally unchanged. Same for `eval/evidence/openfoam.py`, which
  keeps re-exporting `OpenFoamProvenanceProbe` sourced from `provenance`
  instead of from the shim that itself sources `provenance`.
- **Public CLI surface.** `cli/main.py` binds the same function objects under
  the same names; command registration, options, output, and exit behavior
  cannot change. The function-local import at `main.py:252` stays
  function-local (placement preserved; only the module path changes).
- **Byte-stable golden STL.** `KayakGenerator(...)` ≡
  `LoftedHullGeometry(Hull(...))` by construction (the subclass only adapts
  the constructor); the golden test's own byte-assert is the verifier for
  the slice that redirects it.
- **Event ordering / claim vocabulary / schemas / artifact store.** Not
  touched: no code that emits events, claims, or records is edited beyond
  import lines.

## 5. Slice decomposition

Each slice lands and reverts independently; reverting any slice is reverting
import lines.

| # | Slice | Preservation claim | Verification |
|---|---|---|---|
| 1 | Add `tests/test_legacy_shims.py`: for each shim, walk `__all__` and assert every re-exported name `is` the canonical object; assert `KayakGenerator(defaults)` produces a mesh byte-identical to `LoftedHullGeometry(Hull(defaults))`. Additive only. | No production code touched. | `.venv/bin/python -m pytest -q` green; new test passes. |
| 2 | Redirect the six `eval/`-internal `jobs`-shim sites (`eval/cfd/__init__.py`, `fixture_command.py`, `case_render.py`, `openfoam_v2512_interfoam/evidence.py`, `snappy_hex_mesh.py`, `eval/evidence/openfoam.py`). | Same objects bound under the same names; `from kayakgen.eval.cfd import X` unchanged (slice-1 test proves identity). | Full pytest + `ruff check kayakgen tests`; recommended extra evidence: `KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 pytest tests/test_openfoam_v2512_smoke.py -q` since edited files sit beside CFD adapters. |
| 3 | Redirect the consumer-layer sites: `services/artifacts.py`, `services/cfd_jobs.py`, `ui/web/controllers.py`, `cli/main.py:28`, `:252`, and `:12` (high_angle_gz). | Same objects bound; CLI/web observable behavior pinned by existing suites. | Full pytest + ruff; `tests/test_import_boundaries.py`, `tests/test_services_boundaries.py`, web tests green. Optional: `pytest -m browser_acceptance`. |
| 4 | Redirect `tests/test_golden.py:41` and `tests/golden/regenerate.py:20` to canonical construction. | Golden STL bytes unchanged — the redirected test is itself the verifier; slice-1 keeps the legacy entry covered. | `pytest tests/test_golden.py -q` + full suite. |
| 5 | Ratchet: add an import-boundary rule forbidding `kayakgen/`-internal imports of the three shim modules. | Additive guard; encodes the end-state. | Full pytest; rule passes on the tree, fails on any reintroduction. |

## 6. Existing coverage and characterization needs

Every redirect site is exercised at import time by the full suite (215 test
files), and the specific guards named in the brief sit directly on this blast
radius: `test_golden.py` (byte-stable STL), `test_import_boundaries.py`,
`test_services_boundaries.py`, the web suites for `controllers.py`, and the
compat smoke in `test_stability_cli_high_angle.py`. Because no semantics
move, the only characterization gap is shim↔canonical object identity, which
slice 1 closes *before* any redirect lands — converting today's incidental
shim coverage (golden test happening to import through `generator.py`) into
explicit, named coverage.

## 7. Expected payoff

- **Dependency direction restored.** Canonical modules become the single
  in-tree truth; the shims drop to zero internal fan-in — a state that is
  grep-checkable, test-pinned (slice 5), and matches what the shims' own
  docstrings say new code should do.
- **Future deprecation becomes one decision.** Once internal fan-in is zero,
  retiring any shim is a purely external-compatibility question; today that
  question is entangled with 13 internal call paths.
- **Navigability.** Every importing module names the real home
  (`provenance`, `profiles`, `records`…), so readers and agents stop chasing
  one extra indirection hop on every CFD symbol; new names added to canonical
  modules no longer need threading through `jobs.py` for internal callers.
- **For this campaign**, the goal's every slice is verified by the standard
  gates alone, making it a clean first exercise of the stage-1/stage-2
  machinery with minimal confound risk.

## 8. Known risks, and evidence that reduces them

- **A shim re-export might not be identical to its canonical object.**
  Inspection says no (`jobs.py` and `cli/high_angle_gz.py` define nothing);
  slice 1 proves it mechanically over the full `__all__` rather than by
  inspection.
- **Import-order or cycle changes.** The dependency edges already exist —
  `jobs.py` itself imports exactly the canonical siblings — so the redirect
  removes an indirection hop and cannot introduce a new edge. Full-suite
  import coverage plus `python -c "import kayakgen"` per slice is the check.
- **The function-local import at `cli/main.py:252` may exist to defer cost.**
  Preserved as function-local; only the module path changes.
- **Golden-test redirect could weaken legacy-entry coverage.** Slice
  ordering removes this: explicit compat coverage (slice 1) lands before the
  incidental coverage is redirected (slice 4).
- **Monkeypatch-point breakage.** Verified not in play: tests patch the eval
  call site (`test_stability_cli_high_angle.py:176`), and the shim's patch
  point survives regardless.

## 9. Explicitly deferred

- Any shim removal, deprecation warning, or alias retirement — all shims are
  frozen surface and stay byte-identical.
- Redirecting *test-side* shim imports other than the two `generator.py`
  consumers the brief names: `test_compare.py:10`, `test_web.py:277`,
  `test_web_read_models.py:5` keep importing through `cli/high_angle_gz`
  (incidental but harmless external-style compat coverage), and
  `test_stability_cli_high_angle.py:11` is a deliberate compat smoke.
- Module splits (C1–C5, C8) and the C7 alias dedup — orthogonal; this goal
  makes none of them harder and slightly de-risks C3/C5-style splits by
  ensuring future moved code imports canonical names.
- Doc updates — no public behavior changes, so the doc checklist correctly
  stays untriggered.
