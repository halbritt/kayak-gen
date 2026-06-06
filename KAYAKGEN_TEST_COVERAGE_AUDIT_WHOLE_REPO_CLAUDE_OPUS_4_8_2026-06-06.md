# KAYAKGEN Test Coverage Audit (Whole Repo, Post-Remediation) — Claude Opus 4.8 — 2026-06-06

Second audit of the day. The morning audit (`KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`,
at `aaa64ed`, verdict **MIXED**) produced a remediation plan; four striatum
workflows (0062–0065) landed all P0/P1 items and most P2 items the same day.
This audit answers two questions: **did the remediation actually close the
ledger, and did the ~5,100 inserted lines introduce new unprotected
behavior?** The morning report is treated as inherited evidence at zero-day
staleness; drift since `aaa64ed` is exactly the 29-commit remediation wave
(verified by diffstat — no other area changed).

---

## 0. Audit Basis

**Repo state.** `main` @ `b38822e`, working tree clean before and after.
Target: whole repo at `/home/halbritt/git/kayak-gen`. Scope: default
two-pass, weighted toward remediation-closure verification. Out of scope:
`.venv/`, `.striatum/`, `__pycache__/`, `kayakgen.egg-info/`, `striatum/`
archives (process provenance).

**Execution authority.** Granted via the operator's autonomous-completion
directive (standing cowboy-mode authorization for kayak-gen). No source,
test, config, or CI file was modified; this report is the only deliberate
write. Read-only byproducts: pytest cache.

**Commands.**

| Command | Status | Result |
|---|---|---|
| `.venv/bin/python -m pytest -q` (documented gate 1) | **ran** | **1324 passed, 4 skipped, 0 failed, 531.91s; exit 0 (PIPESTATUS-verified)** |
| `.venv/bin/python -m ruff check kayakgen tests` (gate 2) | ran | All checks passed; exit 0 |
| User-level `index.sqlite` md5/rowcount before, during, and after the full suite | ran (read-only) | byte-identical (`e0e9a367…`, 90,112 B, mtime unchanged), 0 rows in all 5 tables |
| Coverage profile | not run — unavailable | no coverage tooling configured; installing is forbidden |
| `KAYAKGEN_OPENFOAM_SMOKE=1 … pytest tests/test_openfoam_v2512_smoke.py` | not run — unavailable | OpenFOAM v2512 absent on this host |

**Skip counts (executed).** 4 — exactly the documented OpenFOAM opt-ins
(`test_cfd_run_stages.py` ×2, `test_openfoam_v2512_smoke.py` ×2). All
optional extras are installed in this venv, so the importorskip-gated tests
ran here (1324 > the morning's 1307: the delta is the new remediation
tests). See G1 for why "4 skips" is still not machine-pinned.

**Method.** Three parallel deep-dive subagents (contract decisions
D048/D049; durable state; gate posture + P2 top-ups) with file:line
evidence requirements, plus a fourth first-party deep dive (calibration
campaigns — the morning audit's named confidence-capping residual) and
first-party verification of the headline finding (`scripts/fast-gate.sh`
read directly) and of index-DB isolation (live md5 across the suite run).

**Depth ledger.**

| Area | Pass | Why | Source read | Tests read | Evidence | Tier | Impact / deficit / exposure | Residual risk |
|---|---|---|---|---|---|---|---|---|
| Gate posture (R0/R4) | deep-dive | both SERIOUS, gate is the safety argument | `scripts/fast-gate.sh`, `scripts/install-hooks.sh`, `.git/hooks/pre-push`, `docs/RELEASE_DISCIPLINE.md`, `pyproject.toml` | n/a (gate scripts) | full-suite run; hook file read | executed | gate / D3 silent-skip hole remains | G1, G4 |
| Contract decisions D048/D049 (R1/R2) | deep-dive | I1-analog claims surface | `search/compare.py`, `services/generative_jobs.py`, `eval/stability/accepted_fit.py`, `cli/main.py:762–781`, `docs/DECISION_LOG.md` | `test_compare.py`, `test_cfd_in_loop_evaluator_status.py`, `test_cli.py`, `conftest.py` | suite green incl. these tests | executed + static | closed; residual D0 on CLI flag wiring | G3 |
| Durable state (R3/R5/R6/SHA-PIN) | deep-dive | I2 | `services/artifact_store.py` (incl. full diff vs `aaa64ed`), `services/generative_jobs.py` spawn | `test_artifact_store.py`, `conftest.py`, `test_stability_fit_registry.py` | live DB md5 across suite; suite green | executed + static | R5 read path still I2×D2 | G2, G6, G8, G9 |
| Calibration campaigns | deep-dive (4th; morning's named I2-adjacent residual justifies the extension) | lift the confidence cap honestly | `eval/calibration/campaigns.py`, `rights.py`, `__init__.py:400–450` | `test_calibration_campaigns.py` (full), `test_calibration.py` (negative-path grep) | suite green | executed + static | MAPE/R2 branches untested | G5, G10 |
| P2 top-ups (R7–R10, REASON-ENUM, io/json) | deep-dive (within agent 3) | verify closure quality | `eval/hydrostatics.py`, `eval/stability/registry.py`, `io/json.py` | `test_hydrostatics.py`, `test_generative_jobs_subprocess.py`, `test_stability_fit_registry.py`, `test_hull_roundtrip.py` | suite green | executed + static | none material | — |
| Unchanged remainder (search math, turning/sensitivity, ui/web Trame internals, cfd adapters, CLI breadth) | survey | zero drift since `aaa64ed` (diffstat-verified); morning audit covered at same-day freshness | diffstat only | — | inherited morning report + bug-hunt ledger | inherited (0-day) | morning residuals carry: R12 open-by-plan |

## 1. Verdict

**MIXED**, confidence **high**.

The remediation is real: ten of the morning's twelve actionable rows are
closed with assertion shapes worth imitating (real-record graduation tests,
refusal-token pins, rebuild-not-crash schema tests, an analytic hydro anchor
that would catch a 5% systematic error, a deterministic mid-flight cancel).
Main is green again — executed, with the true exit code this time. Two
things keep the verdict at MIXED: the gate's anti-silent-skip property is
**claimed in the commit subject and in RELEASE_DISCIPLINE.md but was never
implemented** — the one place this re-audit found coverage theater is the
remediation's own gate work — and the artifact store still **serves
content-addressed bytes on read without verification**, so the I2
durable-state row is only half closed (producer protected, consumer not).
Confidence is high rather than the morning's medium because the named
capping residual (calibration durable records) has now been read
test-and-assertion deep, every identified I1/I2 area is read, and the full
suite executed green at HEAD.

## 2. Suite Inventory And Pyramid

90 test files, 1,328 collected (1,324 ran + 4 opt-in skips), 8m52s.
Topology unchanged from the morning report (inherited): broad pytest unit
tier; integration tier for subprocess lifecycle, CFD fixture jobs, web
routes; Playwright browser/visual tier; opt-in real-solver tier. The
remediation wave added ~17 tests concentrated exactly where the ledger
pointed (artifact store +183 lines, registry +145, evaluator status
rewritten, compare +60, hydrostatics +76, conftest +59). Two structural
additions matter beyond their rows: a **session-scoped autouse isolation
floor** (`tests/conftest.py:312–336`) that defends against
background-thread env-restore leaks — the exact mechanism that produced the
morning's 129 phantom DB rows — and the conftest factory now threading
`kind` through real `StabilityFitRecord` construction (`conftest.py:108,212`),
which is what let the evaluator-status tests drop their fakes.

## 3. Gate And Coverage Audit

Two-layer gate, one layer half-built:

- **Full suite** (`pytest -q` + `ruff`) at striatum slice completion —
  documented in `docs/RELEASE_DISCIPLINE.md`, now with "green, with only
  the documented OpenFOAM opt-in skips (expected: 4)". Ran here: green.
- **Fast subset** (`scripts/fast-gate.sh`: ruff + pytest minus 11
  `--ignore`d files and 2 `--deselect`s, ~3 min) installed as a real
  pre-push hook (`.git/hooks/pre-push` read: present, `exec`s the script).

The hole: **the skip-count pin claimed by commit `fbfdf9e` ("fast-gate
pre-push hook + skip-count pin + gate docs") and by RELEASE_DISCIPLINE.md
does not exist as code.** `fast-gate.sh:61–74` is `pytest -q` plus
ignore/deselect flags — no summary-line parse, no `== 4` assertion, nothing
machine-checks skips anywhere in `scripts/`, `conftest.py`, or `kayakgen/`
(grep-verified, then the script read end-to-end first-party). The gate
passes on pytest exit 0 regardless of skip count, so an extras-missing env
where dozens of `importorskip` tests evaporate still reads green. The pin
is prose standing in for enforcement — and the prose *cites the morning
audit* as its justification, which is what makes it theater rather than a
mere doc nit (see G1). No coverage tooling exists (unchanged, and the
remediation plan §7 deliberately declined to adopt it; reasonable at this
maturity). `[dev]` extras are now consistent with the documented gate stack
(mypy removed, 6095b48 — verified no `[tool.mypy]` or doc reference
remains).

## 4. Ranked Gap Ledger

Closure summary of the morning's rows, then the standing ledger.
**Closed with quality** (verified file:line by deep dive): R1 (kind
discriminator + real-record graduation, `accepted_fit.py:117`,
`test_cfd_in_loop_evaluator_status.py:99–105`), R2 (gate call
`compare.py:210–212`, refusal-token tests `test_compare.py:369–411`, old
downgrade test inverted to require opt-in), R3 (env-gated
`_default_index_path`, all `SqliteIndex()` call sites verified, session
floor; **executed**: user DB byte-identical across the 1,324-test run), R5
write side (temp+`os.replace`, corrupt-dedupe repair with planted-truncation
test `test_artifact_store.py:212–247`), R6 (`PRAGMA user_version` +
rebuild-not-migrate, stale-column crash scenario tested end-to-end), R7
(analytic parabolic-body anchor, closed forms `(8/9)·b0·T·L` and
`1/2+c/10`, rtol 1e-2 — a 5% systematic volume error fails it), R8
(deterministic mid-flight cancel via `_inline_spawn`, no race; old racy
tests demoted to labeled smoke, the mid-race `pytest.skip` removed), R9
(`io/json.py` atomic utf-8 writes + non-ASCII round-trip test), R10 (all
three registry micro-branches pinned, incl. the hysteresis-vs-drift
disambiguation by detail string), REASON-ENUM (genuinely
namespace-derived, 16-constant floor matches source), MYPY (clean).

Standing gaps:

| # | Sev | Location | Behavior at risk / mechanism | Impact | Deficit | Exposure evidence | Tier | Smallest closing test |
|---|---|---|---|---|---|---|---|---|
| G1 | **SERIOUS** | `scripts/fast-gate.sh:61–74`; `docs/RELEASE_DISCIPLINE.md` §pre-merge; `pyproject.toml:47–52` | Morning R4, carried + aggravated. The 12-file `importorskip` lattice (incl. the desktop forbidden-copy regression, `test_desktop_layout.py:8,177`) silently skips in any env without the extras — and `[dev]` provisions none of them. The sole proposed defense, the skip-count pin, is **claimed in the commit subject and the release doc but unimplemented**: nothing parses the summary line, the gate passes on exit 0 with any skip count. Theater rule applies — a gate property cited as release evidence that nothing enforces. Held at SERIOUS, not BLOCKER, on executed evidence: this workstation's gate run demonstrably exercised the desktop tests (1324 passed, exactly 4 skips), and the web halves of the forbidden-copy invariant are import-clean and always run. The morning's mitigation stands; the promised second lock does not. | I1-analog × D3 (env-gated), theater-aggravated | D3 | fbfdf9e subject vs. script contents (first-party read); `[dev]` extras list; executed skip count | executed + static | Parse the pytest summary in `fast-gate.sh` and fail unless `skipped == 4` (and wire the same pin into the striatum full-suite gate); or a non-gated test asserting all extras import when `KAYAKGEN_RELEASE_GATE=1` |
| G2 | **SERIOUS** | `kayakgen/services/artifact_store.py:848–852, 863–869` | Morning R5, read side. `_resolve_artifact` serves `get_json`/`get_file` by globbing `_store/<hash>.*` and returning bytes **without rehashing** — a content address corrupted after write is served silently, forever; repair triggers only on the next *put* of identical content. The one read-side rehash that exists (re-derive branch when `_store` is missing) has its mismatch warning untested too. Producer is protected (atomic writes, write-side repair — closed above); consumer is not. | I2 (durable artifact correctness — `_store` is the RFC 0049 provenance substrate) | D2 | BUG-041 family; agent-verified glob + no-rehash read path | static | Corrupt the bytes at `_store/<hash>.*` after a successful `put_json`, call `get_json`, assert detection (refuse/repair/warn) rather than silent corrupt payload — fails today |
| G3 | MINOR | `kayakgen/cli/main.py:762–781` | New, introduced by D048. The `--explicit-exploratory` flag and CLI-level refusal surfacing are D0: all refusal/opt-in coverage is function-level (`build_comparison_report`), never through `runner.invoke`. The broad `try/except → exit 1` wrapper means a wiring regression (flag dropped, token swallowed) would not be caught. Gate logic itself is well covered. | I4 (default `kayakgen compare` surface) | D0 (wiring only) | agent grep: zero CLI-level tests touch the flag | static | One `CliRunner` pair: gated objective without flag → exit 1 + RFC 0044 token in output; with flag → exit 0 + `exploratory_frontier` |
| G4 | MINOR | `scripts/fast-gate.sh` | New, introduced by P0-GATE-ENFORCE. Load-bearing gate logic with no test: the 11-file ignore list can silently rot (a renamed test file makes `--ignore` a no-op), and the header's measured numbers are already stale (says "1309 passed"; reality 1324). | I5→I3-adjacent (relied-on dev gate) | D0 | header comment vs. this run's counts | executed + static | A test (or the script itself) asserting every `--ignore`/`--deselect` path/nodeid still collects |
| G5 | MINOR | `kayakgen/eval/calibration/campaigns.py:366–382` + `__init__.py:435–445` | MAPE and R2 threshold branches are reachable from the D006 promotion gate (it forwards whatever `fit_metric` the on-disk record carries) but untested. Semantic trap verified by reading: an R2 record under the default `threshold_pct=5.0` refuses **every** fit (R2 ≤ 1.0 < 5.0). Fail-closed, so claims discipline holds — but the first real R2 fit will be rejected confusingly, and nothing pins either branch's direction. | I4 (fail-closed quirk on operator surface) | D2 | first-party read of gate call site | static | One MAPE-above-threshold and one R2-below-minimum record through `evaluate_fit_against_threshold`, asserting the structured reason tokens |
| G6 | MINOR | `kayakgen/services/artifact_store.py:719, 726–727, 863–869` | New code, untested branches: `_verify_or_repair_store_file` OSError fallbacks (stat-failure, read-failure) and the re-derive hash-mismatch warning. Error-path behavior is defined but unpinned. | I2-lite | D0 (branches) | agent diff read vs `aaa64ed` | static | Plant an unreadable store file (chmod 000) → assert repair path; plant a canonical file whose bytes don't hash to the ref → assert the mismatch warning |
| G7 | MINOR | `kayakgen/cli/main.py` (float options) | Morning R12, carried: NaN/inf accepted by CLI numeric params; no negative-path CLI tests. **Open by plan** — P2-CLI-NEGATIVES is explicitly deferred to land with the bug-hunt NaN-validator sweep (workflow 0065 SUMMARY). Listed so the deferral stays visible, not as new debt. | I4 | D0 | BUG-073..077 (open); 0065 deferral note | inherited | (As planned: parametrized `CliRunner` × {nan, inf, -1} with the validators) |

Notes (contextual, not promoted): **G8** — SqliteIndex newer-stamp
direction (future-code DB opened by older code) implemented as leave-alone
but untested; benign until `SCHEMA_VERSION` ever bumps. **G9** — BUG-041
concurrent-writer TOCTOU is now benign by construction (atomic
`os.replace`, last-writer-wins on identical bytes) but unpinned by any
test; claimed-safe, not proven-safe. **G10** — CSV-ingest refusal paths
(missing/extra columns, `_coerce_bool` garbage) and the inclining-campaign
`source_id` mismatch validator have refusal code but no tests (tank-side
mismatch is tested). **G11** — morning R11 (absolute-path evidence refs)
deferred indefinitely by documented decision; becomes P1 when
externally-authored fixtures arrive (D006/D007).

## 5. Coverage Theater And Assertion Quality

The morning found "remarkably little theater"; the remediation wave then
produced the single clearest instance in the repo: **a gate property that
exists in the commit subject and the release doc but not in the code**
(G1). It is worth naming precisely because everything *around* it is
honest — the script's header comments are accurate about what the fast
gate is and is not, and the doc's *policy* ("any other skip count means
the run does not count as a gate") is correct; only the enforcement is
missing. Beyond that, assertion quality in the new tests is high: the
isolation regression is a property-pin (default path resolves into pytest
tmp) rather than a post-hoc file check; the intact-dedupe test runs under
`warnings.simplefilter("error")` to prove no spurious repair; the
hysteresis test disambiguates two branches that share a reason code by
asserting the detail string; REASON-ENUM is genuinely namespace-derived.
One labeled-smoke disjunctive final remains in the subprocess tests with a
do-not-tighten comment — acceptable, no longer load-bearing (R8's
deterministic test carries the semantics).

## 6. Missing Failure And Edge Cases

(Not already in the ledger.) Carried from the morning at zero drift:
`_link_or_copy` EXDEV fallback; `events.jsonl` append durability;
positive-path construction for `claim_allows_final_design_fitness`
(deny-only by construction until the first real record). New from this
pass: read-path corruption is G2's row, but its sibling — a *partial*
store file that passes the length screen yet fails rehash on the put path
— is covered only when lengths differ from the original; equal-length
bit-rot relies on the rehash branch (`_verify_or_repair_store_file`
rehash-to-confirm), which is tested for truncation only. The fast-gate's
`KAYAKGEN_PY` override path (striatum worktrees) is also untested.

## 7. Flakiness Risk

Improved since the morning. The two named risks are reduced: the racy
subprocess cancel is now backed by a deterministic test (R8 closed; the
smoke disjunctives remain but no longer mask), and the shared-durable-state
risk is eliminated with executed proof (R3: user DB byte-identical across
the full run, session-scoped floor against thread-leak re-pollution). The
importorskip env-coupling remains the dominant silent variable (G1):
"1324 passed" in this venv is not "1324 passed" anywhere else, and nothing
mechanical would notice. Browser/visual renderer coupling unchanged
(labeled risk, graceful skip + strict opt-in profile). No ports, network,
or wall-clock date coupling in standing tests.

## 8. What Is Well-Protected

Everything in the morning's §8 stands (claims-promotion chain,
forbidden-copy token sweeps, architecture-conformance tests, subprocess
crash realism, deterministic fixtures, claim predicates). The remediation
added to the list: **durable-state write discipline** (atomic
content-address writes with planted-corruption repair tests and a
no-orphan-temp assertion); **schema-evolution behavior** (stale-DB
rebuild-not-crash, current-DB lossless reuse, both directions of the warn
contract); **an external analytic anchor** for the numbers that will
eventually feed GA fitness (volume and LCB against independent closed
forms — shared tetrahedral machinery, independent math, the right shape of
cross-check); **the tamper tripwire** (`fixture_canonical_sha256` pinned to
a literal digest, so a pydantic serialization change fails loudly — the
docstring correctly frames this as an evaluator-version event, not a pin
to bump); and the **calibration promotion gate** (on-disk fit resolution,
unresolved-ref and below-threshold refusals, Edinburgh capped at
`validation_fixture` with a does-not-magically-promote sanity test).

## 9. Residual Risk And Open Questions

- **The pin that isn't.** G1 is one short script edit away from closure;
  until then the release doc overstates the gate. Whoever lands it should
  also decide whether the striatum full-suite gate gets the same check —
  the doc implies both.
- **Unread areas**: search math internals, turning/sensitivity evaluators,
  ui/web Trame internals, CFD adapters — unchanged since the morning
  (diffstat-verified), covered by the inherited same-day survey and the
  bug-hunt ledger (2026-05-29, one wave old, spot-verified rows still
  live). None is I1/I2; headline verdict does not move.
- **Unrun**: OpenFOAM smoke (solver absent) — the real-solver `succeeded`
  path stays design-only until a solver-equipped host runs it. Coverage
  profiling — unavailable, and would not change the top findings, which
  were found by reading gates and read paths, not by line maps.
- **Open question for the maintainer**: is the fast gate intended to ever
  become a *release* gate? Its header says no (full suite remains the
  gate), but it is the only mechanical pre-push enforcement; if reliance
  drifts toward it, the 11 ignored files (incl. `test_compare.py` and the
  subprocess lifecycle) become a standing blind spot at the moment of
  reliance — re-rank G4 upward then.
