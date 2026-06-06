# KAYAKGEN Test Coverage Audit — Claude Opus 4.8 — 2026-06-06

Behavioral test-protection audit of the standing suite. The question answered:
**where does the suite create false confidence about behavior that matters?**

---

## 0. Audit Basis

**Repo state.** `main` @ `aaa64ed`, working tree clean before and after the
audit (verified). Target: whole repo at `/home/halbritt/git/kayak-gen`. Scope:
default two-pass (survey + risk-chosen deep dives). Out-of-scope paths:
`.venv/`, `.striatum/`, `__pycache__/`, `kayakgen.egg-info/`,
`striatum/` archives (process provenance, not product).

**Execution authority.** Granted via the operator's autonomous-completion
directive for this session (standing cowboy-mode authorization for kayak-gen).
Tooling installation remained forbidden; no source/test/CI edits were made.
This report is the only write.

**Commands.**

| Command | Status | Result |
|---|---|---|
| `.venv/bin/python -m pytest -q` (documented pre-merge gate 1) | **ran** | **1 failed, 1307 passed, 4 skipped, 539.71s (8:59)** |
| `.venv/bin/python -m ruff check kayakgen tests` (gate 2) | ran | All checks passed |
| Coverage profile | not run — unavailable | no coverage tooling configured (`pytest-cov` absent); installing is forbidden |
| `KAYAKGEN_OPENFOAM_SMOKE=1 ... pytest tests/test_openfoam_v2512_smoke.py` | not run — unavailable | OpenFOAM v2512 not installed on this host |
| mypy | not run — unavailable | listed in `[dev]` extras but no `[tool.mypy]` config and not part of the documented gates |

Caveat on the pytest run: it was invoked as `pytest -q 2>&1 | tail -40`, so the
recorded shell exit code (0) is the pipe's, not pytest's; the failure is taken
from pytest's own summary line, which is authoritative.

**Skip counts (executed).** 4 skips, all the documented opt-in OpenFOAM env
gates (`tests/test_openfoam_v2512_smoke.py` ×2, `tests/test_cfd_run_stages.py`
×2). All optional extras (desktop/web/browser/calibration/report/builder) are
installed in this venv, so the importorskip-gated tests **ran** here — see R4
for why that is not guaranteed elsewhere.

**Evidence tiers used.** `executed` (this pytest run, ruff, direct SQLite
inspection of the user index DB), `static` (test + implementation reading,
git history), `inherited` (bug-hunt ledger `docs/bug-hunt/` dated 2026-05-29,
~1 week old, all 85 findings still `status: open`; deep-architecture review
dated 2026-06-03). No `measured` tier exists (no coverage tooling).

### Depth ledger

| Area | Pass | Why selected / skipped | Source read | Tests read | Evidence | Impact / deficit / exposure | Residual risk |
|---|---|---|---|---|---|---|---|
| Stability claims-promotion chain (`eval/stability/registry.py`, claim label resolver, promotion CLI paths) | **deep-dive** | Project's self-described "load-bearing safety surface"; I1-analog (claims/authority); BUG-001 critical sits adjacent | `registry.py` (full), `claims.py` predicates, `generative_jobs.py:60–110` | `test_stability_fit_registry.py` (full), `test_claim_state_measured_promotion.py` (key tests), `test_resolve_analytical_claim_label.py` (names), `conftest.py` (full) | executed + static | I1-analog; mostly D-none; strong | Micro-gaps only (R10, R11) |
| CFD-in-loop graduation (`cfd_in_loop_evaluator_status`) | **deep-dive** | BUG-001 (critical, open) alleges mock-erasure | `generative_jobs.py:60–110`, `accepted_fit.py` (grep for `kind`) | `test_cfd_in_loop_evaluator_status.py` (full) | static | I4 high-exposure-on-activation; **D2 (mocked away)** | None — fully read |
| Durable state: `FilesystemArtifactStore` + `SqliteIndex` + `io/json.py` + geometry migration | **deep-dive** | I2 (durable artifacts, content addressing, migration); BUG-041/-078 open | `artifact_store.py` (~450 of 899 lines: schema, `_put_bytes`, `put_json`, `_link_or_copy`, index), `io/json.py`, `migrate_geometry_cli.py` (command body) | `test_artifact_store.py` (full names + isolation fixture), `test_generative_jobs_index.py` (grep), `test_geometry_v2.py` (migration tests) | executed (DB inspected) + static | I2/I3; D2 on failure paths; **live pollution found (R3)** | Concurrency behavior unexercised |
| Generative-jobs subprocess lifecycle | **deep-dive** | I3 (liveness, crash recovery); in-test `pytest.skip` race tolerance | `generative_jobs.py` (partial) | `test_generative_jobs_subprocess.py:98–297` (full) | executed + static | I3; D3 (timing) on integration smoke; deterministic cancel-semantics test exists | Manager thread-safety under concurrent jobs unread |
| Hydrostatics/geometry numerical core | **deep-dive** (4th; justified by maintainer north-star: validated fitness is the critical path) | Fitness inputs for the GA end-state | impl not read line-by-line (assessed via test side; no mocks present) | `test_hydrostatics.py` (full), `test_golden.py` (names + structure) | executed + static | I4 today (outputs claim-labeled unvalidated); D2 vs external truth | Impl internals unread; see R7 |
| Search/Pareto claim admissibility (`compare.py`, `pareto.py`) | survey+ | BUG-026 (high, open) claims gate bypass | `compare.py` gate call sites, RFC 0044 §gating | `test_compare.py:363–415` | static + inherited | I1-analog; D2 at one entry point (R2) | Full `compare.py` unread |
| CLI surface (25+ commands) | survey | High fan-in but bounded impact | command inventory only | `test_cli.py` count (21 tests) | static + inherited (bug-hunt CLI rows) | I4; numeric-boundary negatives missing (R12) | Error-path/exit-code coverage unread |
| CFD/OpenFOAM/mesh-evidence | survey | Env-gated; solver absent on host | skip-gate analysis, docs | skip messages, bug-hunt rows | inherited + static | I3; D3 (env-gated by design, documented) | Real-solver path unverifiable here |
| Web/desktop UI + forbidden-copy regressions | survey+ | Carries 2 of the named no-claim invariant gates | — | `test_web_read_models.py:516–560` (full test), `test_desktop_layout.py` head + names | executed + static | I1-analog; D3 for desktop half (R4) | Trame layout internals unread |
| Calibration campaigns/extractors | **survey only** | I2-adjacent (durable `AcceptedFitRecord`); time-boxed out | — | test counts; bug-hunt rows BUG-011..013/049..052 | inherited | I2-adjacent; extractor gaps documented open | **Unread I2-adjacent area — caps confidence at medium** |
| Search math internals (NSGA-II/EHVI/GP), turning, sensitivity, resistance impl detail, model/validity, remaining services | unread | Lower exposure; bug-hunt tick 7 found strong baselines for search math | — | — | inherited | — | Bounded; inherited evidence 1 week old |

---

## 1. Verdict

**`MIXED` — confidence: `medium`.**

No `BLOCKER`. The claims-integrity chain — the behavior this project itself
declares load-bearing — is among the best-protected surfaces I have audited:
per-gate negative tests with reason-code assertions, byte-level tamper tests,
cache-poisoning regression tests keyed to a written threat model, and
production-path (`Hull`-through-registry) coverage. But the suite's pass
signal is currently writing checks the process can't cash: the documented
mandatory gate is **red on `main` and has been for 12 days** (a working
boundary test caught a real layering violation in commit `313dfdd`,
2026-05-25, and nothing enforced it); the suite **pollutes the operator's
production `runs` index on every run** (129 of 129 rows in
`~/.local/share/kayakgen/index.sqlite` are pytest tmp-path phantoms); one
documented-critical integration behavior is **tested only against
`SimpleNamespace` fakes that cannot exist in production** (BUG-001); and one
of the two named forbidden-copy gates sits behind `importorskip` with
"green-or-skipped" gate semantics. Confidence is capped at medium because
coverage tooling does not exist, and one identified I2-adjacent area
(calibration-campaign durable records) stayed survey-only.

---

## 2. Suite Inventory And Pyramid

- **Shape.** 92 test files, ~27,100 test LOC against 130 source files,
  ~39,000 LOC — a 0.69 test:source ratio. Single language (Python 3.12),
  single runner (pytest, `testpaths=["tests"]`, `addopts="-ra"`). One
  registered marker (`browser_acceptance`).
- **Pyramid.** Mostly fast unit/contract tests; a thick integration band:
  real-subprocess job lifecycle tests (SIGKILL, cancel-flag polling),
  Playwright/Chromium browser acceptance with committed visual baselines
  (`tests/visual_baselines/`), golden STL hash pins (`tests/golden/`), and a
  CFD fixture-command subprocess. Executed wall-clock: **8:59** for the full
  gate — long enough that contributors will be tempted to skip it (and the
  12-day red trunk suggests at least one did).
- **Fixtures.** `tests/conftest.py` provides a deterministic
  acceptance-triple factory (fixture/packet/fit with shared hashes) — high
  quality, frozen timestamps, byte-stable records, opt-in cache-clear
  fixture.
- **Env/skip gates.** Two families: (a) optional-extras `importorskip`
  (desktop: PyQt6/matplotlib; web: trame/vtk; browser: Playwright/Chromium;
  builder: ezdxf; calibration: openpyxl; report: jinja2) — all installed in
  this venv, all ran; (b) opt-in OpenFOAM env knobs
  (`KAYAKGEN_OPENFOAM_SMOKE=1` + `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`) — the only
  4 skips in this run, documented in `docs/RELEASE_DISCIPLINE.md` and
  `docs/USER_GUIDE.md`.
- **Network/DB coupling.** No network in standing tests. SQLite coupling
  exists and is the subject of R3.

## 3. Gate And Coverage Audit

- **There is no CI.** No `.github/workflows`, no other CI config. The
  entire gate posture is two documented local commands
  (`pytest -q`, `ruff check kayakgen tests`) plus striatum process
  discipline. Enforcement is voluntary.
- **The mandatory gate is red on `main` (executed evidence).**
  `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
  fails: `kayakgen/services/evaluation.py:33` imports
  `kayakgen.ui.hydrostatics_metadata`. The test landed 2026-05-16; the
  violating import landed 2026-05-25 (`313dfdd`); every commit since —
  including an entire refactoring campaign whose safety argument was "the
  suite is green" — landed on a red trunk. The test did its job; the gate
  posture did not. (Ledger R0.)
- **Skip-as-pass semantics.** RELEASE_DISCIPLINE gate 1 reads "must stay
  green **or skipped**". Combined with `importorskip` on optional extras,
  a minimal `pip install -e .[dev]` environment silently skips the desktop
  forbidden-copy regression and every web-layout gate while reporting
  success. Nothing asserts "the gates actually ran" (cf. the suite's own
  `--browser-acceptance` strict mode, which exists for exactly this reason
  but covers only the browser profile and is not part of the documented
  gate). (Ledger R4.)
- **No coverage tooling, no coverage theater.** `pytest-cov` is absent, no
  thresholds, no badges. The project does not worship percentages — its
  protection claims live in docs and the bug-hunt ledger instead. The one
  numeric protection claim found ("566+ passing tests" in the 2026-06-03
  architecture review; now 1307) is descriptive, not a gate.
- **mypy is vestigial.** In `[dev]` extras, never configured, not in the
  documented gate stack. Either wire it or drop it from extras; today it
  implies a type gate that does not exist. (NOTE.)

## 4. Ranked Gap Ledger

Severity ordering per the rubric (impact, then deficit, then exposure). No
`BLOCKER` rows: every I1-analog finding below carries a genuine mitigation
that keeps the harm labeled or fail-closed, and the I2-grade candidates are
reversible-state or not-yet-reachable; the conditional branch chosen is cited
per row.

| # | Sev | Location | Behavior at risk / mechanism | Impact | Deficit | Exposure evidence | Tier | Smallest closing test |
|---|---|---|---|---|---|---|---|---|
| R0 | **SERIOUS** | gate posture (`docs/RELEASE_DISCIPLINE.md` §pre-merge vs. `main`) | "Every commit passes the full suite" is the project's safety argument; `main` has been red since `313dfdd` (2026-05-25). Any regression the suite *would* catch can land and persist unnoticed. | spans classes; gate itself | n/a (enforcement, not test) | executed: 1F/1307P this run; git history dates the breakage | executed + static | Not a test: fix the import, then any enforcement that makes red visible (even a `git push` hook or a striatum gate step that runs `pytest -q` and refuses on failure) |
| R1 | **SERIOUS** | `tests/test_cfd_in_loop_evaluator_status.py` vs `kayakgen/services/generative_jobs.py:60–96` | CFD-in-loop graduation requires `record.kind ∈ {"analytical","cfd_in_loop"}`; `StabilityFitRecord` has **no `kind` field**. All 8 tests feed `SimpleNamespace(kind=...)` fakes — the `first_class` branch is unreachable with production records, and the suite asserts the fake instead. Fails closed (stays `opt_in_only`), so claims discipline holds, but the graduation feature is dead on arrival and the green suite says otherwise. | I4 (feature unavailable when activated; fail-closed) — promoted one level: the suite's pass signal is the release evidence | D2 (behavior mocked away) | BUG-001 (critical, open, 2026-05-29); confirmed live by grep this audit | static + inherited | Feed `make_stability_acceptance_triple().fit` (real record) through `cfd_in_loop_evaluator_status` and assert the intended graduation outcome — it fails today, forcing the RFC 0058 `kind` design decision |
| R2 | **SERIOUS** | `kayakgen/search/compare.py:188,196` + `tests/test_compare.py:363` | RELEASE_DISCIPLINE's canonical invariant: `raw_unvalidated`/`uncalibrated_comparative` as search/**Pareto** objective is *refused* unless `objectives_explicit_exploratory: true`. `build_comparison_report` never calls `ensure_objectives_claim_admissible_for_search`; it auto-downgrades to `exploratory_frontier` with warnings, with no opt-in flag on the CLI. The test suite **pins the downgrade behavior as correct**, so the refusal contract at this entry point is not just untested — it is counter-tested. Impact branch: not I1 because no unlabeled value escapes (report_kind, warnings, and provenance annotations are all asserted); the harm is opt-in-free admission, not false labeling. | I1-analog → judged I4-high-exposure (default `kayakgen compare` path) | D2 (refusal path absent; weaker contract pinned) | BUG-026 (high, open); RFC 0044 §188–195; `active/runner.py:441` *does* call the gate — entry points disagree | static + inherited | `build_comparison_report(objectives=[raw metric])` without opt-in → assert it raises the RFC 0044 refusal token (test fails today; resolves the spec drift one way or the other) |
| R3 | **SERIOUS** | `kayakgen/services/artifact_store.py:141–145` + `search/sweep.py:223`, `search/active/runner.py:423`, `cfd/job_store.py:429` | Tests must not mutate durable user state. Sweep/search/CFD runner tests construct `FilesystemArtifactStore` with the **default** `SqliteIndex()` → `~/.local/share/kayakgen/index.sqlite`. Verified: 129/129 `runs` rows are pytest tmp-path phantoms; DB mtime matches this audit's run. The production `kayakgen runs` read-model is 100% noise on this machine, and every mandated pre-merge run makes it worse. Impact branch: not I2-grade corruption — rows are reversible noise, no real-run data lost — but it is durable, default, and self-inflicted by the gate itself. | I3/I4 (operator workflow degradation, reversible) | D0 for the isolation property (nothing asserts it); D3 shared mutable state | executed: direct SQLite query this audit | executed | Autouse conftest fixture setting `KAYAKGEN_INDEX_DB` to `tmp_path`, plus one test asserting the default path is untouched after a sweep-runner test |
| R4 | **SERIOUS** | `tests/test_desktop_layout.py:143` (+ all desktop/web tests) | The desktop half of the two **named** forbidden-copy regressions (per RELEASE_DISCIPLINE no-claim invariants) sits behind `importorskip("PyQt6")`. With "green-or-skipped" gate semantics, a `[dev]`-only env silently never runs it. The web halves (`test_web_read_models.py`) are import-clean and always run — that is the load-bearing mitigation keeping this from the I1×D3-only-gate BLOCKER branch. | I1-analog × D3 (env-gated) | D3 | This venv has extras (verified, the gates ran); nothing pins that property; `[dev]` extra does not include desktop/web | executed + static | A non-gated test that fails when `pytest` ran with the desktop forbidden-copy tests skipped *and* the env claims to be a release gate (e.g., assert `PyQt6` importable when `KAYAKGEN_RELEASE_GATE=1`), or fold extras into the documented gate env |
| R5 | **SERIOUS** | `kayakgen/services/artifact_store.py:636–656` | Content-addressed store writes are non-atomic (`write_bytes`, no temp+rename) and dedupe on `exists()`: a crash mid-write leaves truncated bytes at `_store/<hash>`, and every later put of the same content silently links the corrupt bytes to canonical paths. No test covers truncated/corrupt store files, concurrent writers (BUG-041 TOCTOU), or hash≠content detection on read; existing tests cover round-trip, missing-`_store` redrive, and index rows only. | I2 (durable artifact correctness) | D2 (failure paths untested) | BUG-041 (open); `_store` is the RFC 0049 provenance substrate for every sweep/search run | static + inherited | Write truncated bytes at the hash path, `put_json` the full payload, assert the store detects/repairs rather than linking corrupt bytes (fails today) |
| R6 | **SERIOUS** | `kayakgen/services/artifact_store.py:148–246` | `SqliteIndex` has no schema-version table and no migration path; `CREATE TABLE IF NOT EXISTS` against a durable user-level DB means any future column addition makes every existing operator DB throw `OperationalError` at upsert time — runs/sweeps crash at write. No test exercises "old DB + new code". Recoverable by deleting the DB (it is a rebuildable read-model), hence I3 not I2. | I3 (tool liveness; recoverable) | D0 (no schema-evolution test) | 6.5 MB live DB exists; schema already grew once (`generative_jobs` table) | static | Create a DB missing one column, run an upsert, assert a defined outcome (migrate or clear-and-rebuild) instead of a crash |
| R7 | MINOR | `tests/test_hydrostatics.py` | Golden values are self-generated pins (volume/wetted to 1e-9 from the same code path) — regression protection, not correctness. Good property tests exist (scale-doubling, GM0 monotonicity, Cm vs independent `section_area`). Missing: one analytic external anchor. North-star exposure: these numbers become GA fitness inputs. | I4 (today: outputs claim-labeled unvalidated — the claims layer is the real mitigation) | D2 vs external truth | maintainer north-star; architecture review: "no ground-truth anchor" | static | Hydrostatics of a degenerate analytic body (e.g. wall-sided rectangular section limit) vs closed-form volume/LCB to coarse rtol |
| R8 | MINOR | `tests/test_generative_jobs_subprocess.py:125–212` | Racy integration smoke: cancel/resume tests skip or pass through disjunctive finals (`state in ("succeeded","resumable")`) when the race lands wrong — on a fast machine the cancel path may never execute while staying green. Mitigation: `test_subprocess_runner_cancel_flag_requires_resumable_and_cleans_flag` pins cancel semantics deterministically via a controlled runner, which is why this is not the I3×D3-masking SERIOUS branch. | I3 | D3 | 2× `time.sleep` poll loops; 3 in-test `pytest.skip` race outs | executed + static | Deterministic mid-flight checkpoint hook (controlled runner) for the manager-level cancel, removing the race-skip |
| R9 | MINOR | `kayakgen/io/json.py:15–20` | `save_hull`/`save_evaluation` write without explicit encoding and non-atomically. Round-trip tests exist; `design_hash` key-order invariance is independently tested, so BUG-078's content-addressing concern is contained to file bytes, not hashes. | I2-lite | D2 | BUG-022/-078 (open) | static + inherited | Round-trip a hull with non-ASCII metadata under `LC_ALL=C` (encoding), or crash-simulation for atomicity |
| R10 | MINOR | `kayakgen/eval/stability/registry.py:176–184, 233–239, 313–319` | Untested registry micro-paths: multi-fixture ANY-pass semantics (no test stages a 2-fixture fit), hysteresis branch of gate 3a (only drift tested), gate-9 touching-range boundary (`<=` overlap). | I1-analog surface, but all fail-closed | D2 (boundary/negative subsets) | 13-gate surface otherwise comprehensively negative-tested | static | One 2-fixture fit where only the second clears the chain; one `bound_fraction=0.031` hysteresis rejection; one `(30,60)` vs `(0,30)` touching-range load |
| R11 | NOTE | `kayakgen/eval/stability/registry.py:343–349` | `_resolve_evidence` accepts absolute paths from manifests as-is (existence-checked only). A hostile manifest could "resolve" `/etc/hosts` as trace evidence. Operator-authored files; low realistic exposure; bug-hunt path-traversal family. | I5 | D0 | BUG-012 family | static | Manifest with absolute trace path outside the fixture dir → assert rejection |
| R12 | MINOR | `kayakgen/cli/main.py` (multiple commands) | CLI numeric params accept NaN/inf (`--speed-mps`, `--tolerance-percent`, `--turning-heel-deg`, …, per bug-hunt tick 25); no negative-path CLI tests for these. 21 tests cover 25+ commands, mostly happy-path. | I4 (default surface, workaround: validators downstream are also missing per ledger) | D0 (negatives absent) | BUG-073..077 (open) | inherited + static | Parametrized `CliRunner` test: each float option × {nan, inf, -1} → assert non-zero exit + structured message |

## 5. Coverage Theater And Assertion Quality

Remarkably little theater for a suite this size:

- **AST scan for assertion-free tests: 9 hits, 7 false alarms** (try/raise
  `AssertionError` idioms, `np.testing` calls). The remaining 2 are
  does-not-raise *allow*-paths of refusal gates whose negative paths are
  tested alongside — acceptable shape, not theater.
- **The one real mock-erasure is R1** (`SimpleNamespace(kind=...)` — the
  test suite green-lights a branch production records cannot reach).
- **R2 is the rarer inversion**: a thorough, well-asserted test that pins
  behavior *weaker than the documented invariant*, lending the green suite
  the appearance of contract coverage at that entry point.
- Golden STL hash pins and visual baselines are honest drift detectors with
  a documented regeneration path (`tests/golden/regenerate.py`,
  `--update-visual-baselines`) — not snapshot theater.
- `test_every_reason_has_a_next_action` hand-enumerates the reason-code set
  rather than deriving it from the module's `REASON_*` namespace — a new
  gate constant could silently miss remediation copy. Contextual NOTE.

## 6. Missing Failure And Edge Cases

(Not already in the ledger.) Concurrent `SubprocessGenerativeJobManager`
jobs against one `jobs_root` (manager-level interleaving untested);
`_link_or_copy` fallback when hard-links are unsupported (warning path,
cross-device `EXDEV`); `events.jsonl` append durability after partial
writes; sqlite `database is locked` behavior when a sweep and `kayakgen
runs` query race; `fixture_canonical_sha256` stability across pydantic
upgrades (the hash *is* the security boundary — a pydantic serialization
change would silently invalidate every signed packet; one pinned-bytes
regression test would catch it); positive-path construction for
`claim_allows_final_design_fitness` (deny-only today — right until the
first record exists, then untested by construction).

## 7. Flakiness Risk

Low overall, concentrated and mostly honest:

- **Timing**: poll loops + `time.sleep(0.1)` with 30s deadlines and 180s
  joins in subprocess tests (R8); risk is masked-cancel, not spurious red.
- **Environment**: importorskip lattice (R4) — the suite's content varies
  silently with installed extras; "1307 passed" here is not "1307 passed"
  in another venv.
- **Shared durable state**: the user-level sqlite index (R3) — today
  write-only pollution; becomes order-dependent flakiness the day any test
  asserts on default-DB contents.
- **Browser/visual**: Chromium screenshot baselines are inherently
  renderer-version-coupled; mitigated by graceful skip + explicit
  `--browser-acceptance` strict profile + `--update-visual-baselines`.
  Labeled risk, not confirmed flake.
- No ports, no network, no wall-clock date coupling found in standing tests.

## 8. What Is Well-Protected

Named, because it is worth preserving:

- **The claims-promotion chain** (`registry.py` + `test_stability_fit_registry.py`
  + `test_claim_state_measured_promotion.py` + `test_resolve_analytical_claim_label.py`):
  per-gate rejection tests asserting structured reason codes; post-sign
  byte-tamper tests; cache-poisoning regressions tied to written
  threat-model findings (version-keyed cache, evidence-deletion
  fingerprint); real-`Hull`-through-registry production paths; deny-by-default
  label resolution. This is what test protection of an authority surface
  should look like.
- **Forbidden-copy and vocabulary regressions** (`test_web_read_models.py`
  token sweep with explicit negation scrub-list; `test_vocabulary_coverage.py`)
  — the no-claim invariants are mechanically enforced on the always-run web/
  read-model side.
- **Architecture conformance as tests** (`test_import_boundaries.py`,
  `test_services_boundaries.py`) — currently *proving their worth* by being
  the red test on `main`.
- **Subprocess crash realism** (`test_generative_jobs_subprocess.py`):
  actual SIGKILL of a process group, stale-`running` reconciliation,
  resume-from-checkpoint — rare to see tested for real.
- **Deterministic fixtures**: the conftest acceptance-triple factory and
  seeded search determinism (bug-hunt tick 7 confirmed no global RNG).
- **Claim predicates** (`test_resistance.py:258–305`): deny-by-default with
  enumerated near-miss negatives.

## 9. Residual Risk And Open Questions

- **Unread areas** (depth ledger): calibration-campaign durable records
  (I2-adjacent — the named reason confidence is `medium`), search math
  internals, turning/sensitivity evaluators, most of `ui/web`'s Trame
  internals, `eval/cfd` adapters. The bug-hunt ledger covers these at
  1-week staleness with all findings open; nothing suggests the headline
  verdict moves, but R-row ordering could shuffle.
- **Unrun**: the OpenFOAM smoke (solver absent) — would have shown whether
  the real-solver `succeeded` path and provenance probe still bind; until
  run on a solver-equipped host, that path's protection is design-only.
  Coverage profiling — would primarily sharpen the *unexercised-line* map
  in `ui/desktop.py` and `cli/`; unlikely to change rankings given the
  static read.
- **Inherited staleness**: bug-hunt ledger is 2026-05-29 (one commit-burst
  old); spot-verified rows (BUG-001, BUG-026, BUG-041 sites) were all still
  live in today's tree, so I treated the rest as current.
- **Open questions for the maintainer.** (1) Is the compare-path
  auto-exploratory downgrade (R2) intended as RFC-0044-compliant? The
  answer decides whether R2 is a test gap or a spec-text bug. (2) Is
  `first_class` graduation (R1) meant to be reachable before the RFC 0058
  successor lands `kind`? If not, the honest test is one that *pins*
  unreachability with a real record. (3) Should the documented gate command
  pin "expected skips = 4" (e.g. `-ra` + a wrapper check), closing the
  skip-as-pass hole (R4) without new infrastructure? (4) Is striatum the
  intended enforcement layer for R0, given no CI is planned?

---

*Audit performed read-only except this report. Suite executed once under
operator authorization; no tooling installed; no source, test, config, or CI
files modified.*
