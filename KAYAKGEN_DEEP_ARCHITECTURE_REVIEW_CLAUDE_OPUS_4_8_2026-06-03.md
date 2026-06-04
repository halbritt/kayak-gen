# kayakgen — Deep Architecture Review

**Reviewer**: Claude Opus 4.8 (adversarial systems-architecture pass)
**Date**: 2026-06-03
**Target**: `/home/halbritt/git/kayak-gen` @ `main` (`ae200f0`), 326 commits, 2026-05-09 → 2026-06-02
**Audience**: the sole maintainer (Heath Albritton), who asked one blunt question: *is this overbuilt, is it on track, and where should it go next?*
**Scope** (maintainer-selected): **both layers, clearly separated** — the `kayakgen` product *and* the committed striatum/workflow/RFC/audit process machinery, judged as two distinct subjects.

---

## A. Thesis (forced verdict, no hedge)

> **OVERBUILT** · **DRIFTING** · confidence **high**
> Biggest risk in one clause: *a process that manufactures work faster than the kayak domain can justify it — accreting dormant, evidence-gated machinery for a tool that has no user and no single real-world measurement.*

Decomposed, because the one-word label hides the structure:

- The **product core** (geometry → hydrostatics → resistance screening → sweep/compare → claim discipline → CLI/web) is **roughly right-sized and genuinely good**. If the repo were only that, the verdict would be *roughly right-sized, on track*.
- The **product's evidence-gated capability machinery** (real CFD, resistance calibration, measured-stability acceptance, vendored Bayesian optimization) is **overbuilt**: ~6–7K LOC that produces no admissible output and is blocked on physical-world data the docs themselves say does not exist.
- The **process layer** (striatum run-archives + workflow scaffolds + audits + dated operator reports) is **decisively overbuilt as committed artifacts of a kayak tool**: ~100K lines of prose against 38.8K lines of product code, a **2.6:1 prose-to-code ratio**, defended by a self-referential citation web so dense the last hygiene audit could not delete a single file.

The trajectory is **DRIFTING** not because the motion is sloppy — it is the opposite, the execution discipline is extraordinary — but because the *destination has decoupled from deliverable value*. The project is on a flawless track toward a wall the project's own evidence gates erected.

I defend all of this below. The single most important thing I can tell you is in **Open Question 1**: I cannot determine from the repo whether kayak-gen is a *kayak tool* or the *dogfood workload for striatum*, and the entire verdict pivots on that answer. Most of my subtraction advice is correct for the former and wrong for the latter.

---

## B. Files reviewed / files skipped

### Read line-by-line (full or substantial)
- Orientation/intent: `README.md`, `pyproject.toml`, `AGENTS.md`, `docs/PRD.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE_MAP.md`, `docs/DECISION_LOG.md` (D001–D047), heads of `docs/SPEC.md` / `docs/DDD.md` / `docs/UBIQUITOUS_LANGUAGE.md`.
- Prior reviews (to avoid repetition and to measure trajectory): `ARCHITECTURE_REVIEW_2026-05-16.md` (949 lines), `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md` (478 lines), `KAYAKGEN_REPO_HYGIENE_CLAUDE_OPUS_4_7_2026-05-30.md` (306 lines).
- Load-bearing product code: `kayakgen/eval/resistance.py` (222), `kayakgen/eval/claims.py` (227), `kayakgen/search/active/gp.py` (head), `kayakgen/ui/web/app.py` (head), `docs/bug-hunt/LEDGER.md` (head + shape).

### Read structurally (metrics, not every line)
- The full repo file tree (1,856 entries), per-file LOC for all 261 `kayakgen/*.py` and 215 `tests/*.py`, per-subpackage rollups.
- Git history: commit cadence by day, `shortlog`, churn (touch counts), staleness (oldest-touched product files), authorship, `app.py` size history.
- The process layer by structure + index + spot-samples: `docs/rfcs/README.md` and the 66-RFC index, the 70 `docs/workflows/<NNNN>/` scaffolds, the 46 `striatum/` archive dirs (372 `.md` files, 4.9 MB), `docs/audits/` synthesis/findings.

### Deliberately skipped (and why)
- **Generated / runtime / vendored**: `.git/`, `.venv/` (vendored deps), `.striatum/` (gitignored runtime state), `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.benchmarks`, `kayakgen.egg-info/`. Stated as skipped per the prompt's allowance.
- **Binary blob**: `docs/research/aalborg_kayak_phd.pdf` (research PDF, not authored source).
- **Repetitive scaffolds, sampled not enumerated**: the bulk of the 372 striatum archive files and 1,058 workflow files share a fixed 7-role/RUNBOOK/SOURCES/workflow.json shape; I read the convention + samples, not all 1,430 files. The hygiene auditor made the same call (its §1).
- **Most product modules and test files were sized, not read line-by-line.** I read the highest-LOC / most-diagnostic modules and the full decision trail; I did not read all 261 product files or all 215 test files. **Consequence I hold myself to:** my *structural* claims (LOC, churn, boundaries, the gated-machinery pattern, the process ratio) rest on evidence I gathered; my *code-quality* claims are scoped to the files I actually read (`resistance.py`, `claims.py`, the heads of `gp.py`/`app.py`). Where I have not read, I do not render a quality opinion. A follow-up pass could read the remaining ~245 modules; I am confident it would not move the thesis, because the thesis rests on structure, history, and the decision trail, not on any single unread file.

---

## C. The value-vs-complexity ledger

The granularity below is honest — I have not hidden the gated machinery inside a "core" row. LOC are recursive where a subpackage exists. "Value to whom" is concrete; where the honest answer is "to a hypothetical user," I say so, because **there is no evidence in the repo of a single real user** (zero external committers ever; `git shortlog` = Heath Albritton + one `Claude` trailer-author; the PRD's own success criterion "at least one builder has used the output STL to cut foam molds or print hull sections for a real boat build" is unmet).

| Component | What it does | Value (concrete, to whom) | Complexity it carries | Verdict | If CUT/SIMPLIFY: what breaks / replaces |
|---|---|---|---|---|---|
| **Headless core**: `model/` (1,913) + `eval/hydrostatics.py` (458) + `eval/resistance.py` (222) + `io/` (42) | Pydantic `Hull` → lofted geometry → hydrostatics (vol, GM₀, LCB, Aw) + ITTC-57/Michell resistance screening | Real exploratory value to a hypothetical kayak designer; the actual product. Physics is competent (Michell verified vs Wigley hull ±5%, `resistance.py:135`) and honestly caveated. | Low. Clean schemas, deterministic, well-tested. | **KEEP** | — |
| **Claim discipline**: `eval/claims.py` (227) + `eval/contract.py` (555) + the registry/gates | 7-rung claim-state ladder + `ClaimMetadata` validator that *refuses* to promote raw records; gate fns `claim_allows_calibrated_prediction`/`_final_design_fitness` | Genuine **product correctness** — stops the tool lying about unvalidated physics. Cheap relative to value. | Low-medium. But the top 2 rungs (`calibrated_model`, `validated_design_fitness`) are dormant — `claims.py:213` admits "No current kayakgen output satisfies this." | **KEEP** (trim dormant rungs to a comment, don't carry full gate machinery for an unreachable state) | Nothing breaks; the gates already return `False` always. |
| **Geometry v2**: `model/distribution_v2.py` + `DistributionV2Geometry` (RFC 0048) | Explicit longitudinal distributions + 6 cross-section families, opt-in `geometry_kind="distribution_v2"` | Real expressiveness gain over the loft; addresses the May-16 "geometry is the bottleneck" finding. One caller, but it *is* product surface. | Medium. 6 families, chine models, advisory hydrostatic cross-check; +77 tests (D029). | **KEEP / watch** | — |
| **Sweep / compare / pareto**: `search/sweep.py` (604) + `compare.py` (618) + `pareto.py` (326) + `objectives.py` (416) | Deterministic grid sweep, Pareto comparison, objective metadata + admissibility gates | Real value: the exploratory-filter loop the PRD promises. | Medium. | **KEEP** | — |
| **Active search**: `search/active/` (2,940) — NSGA-II (444) + EHVI (281) + vendored Cholesky **GP** (376) + Nelder-Mead + runner (1,389) | Multi-objective NSGA-II (v1) + EHVI Bayesian optimization (v2) over hull params | Marginal. The justifying use case for EHVI/GP is *expensive* evaluators (CFD-in-loop); but the only **claim-admissible** objectives are the *cheap* analytical ones — resistance/CFD objectives are refused by the gate (`pareto.py`, RFC 0044 token). So the surrogate optimizes what is cheap to brute-force. | High. ~660 LOC of hand-vendored GP+EHVI math + a 1,389-line runner; sophisticated, unexercised by its own intended workload. | **SIMPLIFY** — keep NSGA-II; delete/de-vendor GP+EHVI until a validated expensive evaluator exists | NSGA-II covers every admissible objective today; nothing user-facing breaks. |
| **CFD execution**: `eval/cfd/**` + `eval/snappy_hex_mesh.py` + `openfoam_v2512_interfoam/` (~4–5K) | Local dispatch contract + adapters + a *real* OpenFOAM-v2512 interFoam path behind two env knobs | The dispatch contract has value (honest job-state plumbing). The real-solver path produces `raw_unvalidated` output usable for nothing, behind `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` + `KAYAKGEN_OPENFOAM_SMOKE=1`. | High. Two interleaved architectures (the May-16 review's finding #8); a ~10.7 s smoke that yields a number you may not use. | **SIMPLIFY / FREEZE** — keep the fixture+unavailable+mock adapters and the contract; mark the real-OpenFOAM path "dormant, raw-only" and stop extending it | Fixture adapter already covers the contract; the env-gated path is a trophy, not a feature. |
| **Resistance calibration**: `eval/calibration/**` (~1,800: `__init__` 756 + `campaigns` 382 + extractors 315) | Source-review packets, tank/inclining ingest, accept-fit, residual-plot, Edinburgh extractor | **Zero today.** Per D006 and the roadmap, *no in-envelope calibration source exists* and none is being pursued; the registry is empty. Edinburgh is capped at `validation_fixture` (`outside_sea_kayak_calibration_envelope`). | High. Full ingest/accept/validator pipeline + schemas + 19–40 tests, calibrating against nothing. | **CUT / FREEZE** until a data source exists | Nothing breaks (it produces no output now). Replace with a one-page "what data would unblock this." |
| **Measured-stability acceptance**: `eval/stability/{registry.py 522, accepted_fit.py, measured_fixture.py 371}` + `cli/stability_cli.py` (574) + RFC 0056/0058 schemas | `ingest-rig-run` / `promote-fixture` / `accept-fit` / 13-gate resolver to graduate high-angle GZ from `unvalidated_` to `validated_hydrostatic_comparison` | **Zero today.** Blocked on D007/D014 *commissioned strain-gauged inclining-rig data* that does not exist and that a solo operator will not commission. `EMPTY_STABILITY_FIT_REGISTRY = ()` (D042). | Very high. ~1,500 LOC of code + ~1,500 LOC of tests (`test_measured_stability_acceptance` 633, `test_stability_fit_registry` 420, `test_claim_state_measured_promotion` 520) for an unreachable state. **BUG-001 (critical) is logged against a path that cannot execute.** | **CUT / FREEZE** — the single worst product over-build (see roll-up) | Nothing breaks; high-angle GZ stays display-only `unvalidated_`, which is all it can ever be without the data. |
| **Application services**: `services/` (6,365) — `artifact_store`/`identity` (RFC 0049), `evaluation`, `design`, `cfd_jobs`, `comparison`, `sensitivity`, `build_export`, `design_report`, `calibration_artifacts`, `generative_jobs` (1,372) | Artifact store + SQLite index; evaluation/target-trim solvers; builder DXF/SVG exports; sensitivity; HTML design report; generative-job manager | Mixed. `artifact_store`/`identity` earn their keep (the May-16 persistence finding). `build_export`/`sensitivity`/`design_report` are reviewer-wishlist features with one hypothetical user. `generative_jobs` (1,372) is a job manager for a single-operator laptop. | High aggregate. | **KEEP core (store/identity); watch the wishlist trio** | — |
| **Web UI**: `ui/web/` (~6K; `app.py` **2,550**, `generate_spec_form` 1,452, `generate_frontier_view` 780, `controllers` 535, …) | Trame workspace: param edit, 3D render, analysis/comparison, generative-job Generate panel | Real — the primary interactive surface (D009). | **High and concentrated.** `app.py` grew **241 → 2,550 lines (10.6×)** since the May-16 review; it is the one monolith the Phase-3 refactor never tamed (controllers shrank 1,602→535, but app.py absorbed the Generate panel). | **KEEP, SPLIT `app.py`** along the Generate-panel seam the imports already expose | — |
| **Desktop UI**: `ui/desktop.py` (556) + `pv_window`/`theme`/`gui_params` | PyQt6 + PyVista 3D + sliders | Low/uncertain. D009 makes it "supported, not primary"; no evidence anyone (incl. maintainer) uses it. | Low (small, isolated). | **KEEP-minimal / candidate CUT** pending Open Q4 | If unused, deleting it removes the PyQt6/pyvistaqt extras burden. |
| **Tests**: `tests/` (27,057 across 215 files) | Contract, golden-STL, byte-stability, import-boundary, vocabulary-coverage, browser-acceptance | High — this is the safety net that makes subtraction *safe*. Real tests, not trivia (`test_cfd_jobs` 1,365, `test_web_browser` 1,129). | High but earned. ~1,500 LOC of it tests the dormant stability ladder. | **KEEP** (shrinks naturally as gated machinery is cut) | — |
| **Process layer (committed)**: `striatum/` (43,701 lines / 372 files) + `docs/workflows/` (28,358) + `docs/audits/` (4,289) + root reports (`CHANGELOG` 1,522, `OPERATOR_REPORT` 1,264, two arch docs 1,427, hygiene 306) | Operator playbooks, run-archives, multi-lane audit apparatus, dated checkpoints | **As a kayak tool: near-zero ongoing value, high carrying cost.** As striatum dogfood: possibly the actual point (Open Q1). | Enormous. ~80K lines of process exhaust; a self-defending citation web (the May-30 hygiene audit deleted **0 files** because every candidate was "documented as load-bearing"). | **CUT from the product repo** — move run-archives + dated reports to a separate repo/submodule; keep RFCs + DECISION_LOG + current docs | Provenance preserved out-of-repo; the kayak tool's repo becomes the kayak tool. |

### Roll-up

- **Meaningful components: ~13.** I would **CUT or SIMPLIFY/FREEZE 6** of them (active-search GP/EHVI, CFD real path, resistance calibration, measured-stability acceptance, the committed process layer, dormant claim rungs), **KEEP-and-split 1** (web `app.py`), and **KEEP 6** outright.
- **What the subtraction buys:** roughly **6–7K LOC of dormant product code + ~1,500 LOC of tests for it** frozen/removed, and **~80K lines of process exhaust** evicted from the product repo. The product would drop from 38.8K toward a ~30K-LOC *active* core; the repo would stop being **2.6:1 prose-to-code**.
- **Single worst over-engineering — product layer:** the **measured-stability acceptance ladder** (RFC 0043 stage 4 + RFC 0058; `eval/stability/{registry,accepted_fit,measured_fixture}.py`, `cli/stability_cli.py`, ~1,500 LOC code + ~1,500 LOC tests). It exists to ingest, validate, and accept-fit *measured kayak GZ-vs-heel data* that, per the project's own D007/D014 and `docs/ROADMAP.md`, **does not exist publicly and requires commissioning a physical strain-gauged inclining rig** (RFC 0056). It is the purest specimen of "build the plumbing for a gated future" as a proxy for progress. **Why it exists:** the project treats *closing the next RFC in a self-generated backlog* as equivalent to delivering value — premature generality manufactured by a process that rewards RFC throughput over usable output. BUG-001 (severity **critical**) being filed against `cfd_in_loop_evaluator_status` — a function whose precondition (a promoted real fit) can never be met — is the tell: the bug-hunt loop is now finding critical bugs in dead-on-arrival code.
- **Single worst over-engineering — whole project (chosen scope):** the **striatum process apparatus committed into the product repo**. ~80K lines, 2× the product, immovable by construction. **Why it exists:** kayak-gen is the dogfooding workload for striatum (`github.com/halbritt/striatum`, vendored as `docs/CONTEXT_HYGIENE.md` and the `.claude/`/`.codex/` skill bundles). For striatum's purposes this is not overhead — it is the experiment. Judged *as a kayak tool*, per your chosen scope, it is the dominant overbuild.

---

## D. The inverse check — what's actually missing (load-bearing)

Held to a high bar: only absences whose presence the project depends on.

- **A user, or any demand signal.** This is the load-bearing absence. Zero external committers in 326 commits; the PRD success criterion about a real builder is unmet; every "value" cell above is hypothetical. *The project has been building the machinery to accept ground truth instead of acquiring any ground truth or any user.* Everything downstream — calibration, stability validation, CFD — is gated on exactly this, and the response has been more plumbing.
- **One real-world measurement.** The entire analytical stack (hydrostatics, resistance, stability) has **no ground-truth anchor**. The honest unblock is *one* borrowed/commissioned inclining test or tow measurement for *one* hull — not the 3,000+ LOC of acceptance machinery already built to receive it.
- **A boundary inside `ui/web/app.py`.** At 2,550 lines it is the one place in the post-refactor codebase without an enforced seam; the import block alone spans ~90 lines across 8 modules. This is a genuine absent boundary, and the next risky web change lives here.

What is **not** missing, and I want to say so plainly so this review isn't all teeth: **nothing critical is missing in the code's correctness or test coverage.** The suite is broad and real, the schemas are strict (`extra="forbid"` everywhere), the claim gates are enforced, the import boundaries are tested, the domain docs are filled (SPEC/DDD/UBIQUITOUS_LANGUAGE carry zero TODO markers — Phase 1 genuinely landed). For a solo project this code hygiene is top-decile. The problem is not a hole in the code. The problem is that the code is building in a vacuum.

---

## Lenses

### 1. Overbuilt? (driven off the ledger)

Yes — but precisely, not as a blanket. The test is value-per-unit-complexity for a solo operator at this stage, and the project fails it in a specific, repeating pattern I'll name the **gated dead-end**: a capability is fully plumbed (schemas, CLI, validators, tests, RFC, decision row) and then **cannot produce admissible output** because it is blocked on physical-world data that does not exist and is not being pursued. Three instances, ~6–7K LOC together:

- **Resistance calibration** — `calibration_fixture` registry is empty; D006 says no source exists; `claims.py:213` `claim_allows_final_design_fitness` "No current kayakgen output satisfies this."
- **Measured-stability acceptance** — `EMPTY_STABILITY_FIT_REGISTRY = ()`; gated on D007/D014 rig data; BUG-001 critical against an unreachable path.
- **Real CFD** — `raw_unvalidated` behind two env knobs; usable for nothing per the no-claim rules.

Generality-with-one-caller and abstraction-with-one-implementation also appear: the vendored **GP+EHVI** surrogate stack (~660 LOC) whose justifying expensive-evaluator workload is the very objective class the claim gate refuses; the **7-rung claim ladder** occupied only at the bottom 2–3 rungs.

The opposite error — calling sophistication overbuilt merely because it's sophisticated — I have actively avoided. The claim-state discipline is sophisticated *and* earns its keep (it is product correctness in a domain where lying is the failure mode). The Michell integral is sophisticated *and* correct. The artifact-store/identity work is sophisticated *and* solves a real persistence need. Those stay.

### 2. On track? (git history vs stated roadmap)

**Stated**: the roadmap (`docs/ROADMAP.md`, updated 2026-05-25) and 47 decision rows describe a disciplined march through evidence-gated tracks.

**Actual** (from the history): execution is *immaculate and astonishingly fast* — 38.8K LOC of product + 27K of tests + 66 RFCs + 70 workflows in **~3.5 weeks**, bursty in the agent-orchestration signature (114 commits on 2026-05-13 alone; 36 on 2026-05-29). Tests stay green; docs stay synced; the 9-phase ARCHITECTURE_RECOMMENDATION_PLAN landed in full.

**Mine**: the project is *on track in execution and drifting in purpose*, and the proof is a single dynamic the history makes undeniable. The May-16 architecture review's **"Functionality I Would Add"** (10 speculative features: target-trim, geometry v2, builder exports, sensitivity, turning metrics, calibration tooling, report export, …) became, almost 1:1, **RFCs 0048–0058**, all built in the following two weeks. **A reviewer's wishlist became the build queue.** That is not a roadmap derived from user demand or domain necessity; it is a project that builds whatever the last competent reviewer suggested. The same plan explicitly advised investing in boundaries/persistence/geometry "*before adding many more solver, optimization, or UI features*" — the maintainer did the refactors *and* added all the features. The drift is not laziness; it is the absence of a demand function. Churn confirms it: the most-churned files are `OPERATOR_REPORT.md` (96), `CHANGELOG.md` (86), `docs/rfcs/README.md` (71) — **the process ledgers are touched more than any code file** (`app.py`, the busiest code, is 27). The velocity is sustainable for one operator-plus-agents indefinitely, which is exactly the danger: it can run forever without ever meeting a user.

The process has also begun to **feed itself**: audits produce findings (AUD-O-003, AUD-P-002) that become RFCs (0060, 0062) that become workflows that become decisions (D043, D044) — e.g. D042 is a formal decision to *give a name to an empty tuple* (`EMPTY_STABILITY_FIT_REGISTRY`) because an audit found three call sites used `()`. That is process metabolizing its own output.

### 3. Greenfield / north-star (given the *real* constraints)

Constraints are real and load-bearing: solo operator, local-first, laptop/homelab, no managed cloud (D023 defers hosting indefinitely), demo-stage, **no users yet**. Given those, I would have built — and would keep — a *much smaller* thing:

- **Substrate**: Python 3.11 + NumPy + Pydantic v2 + Typer. (Unchanged; correct.)
- **Core**: `Hull` aggregate → lofted geometry (+ distribution_v2) → hydrostatics → ITTC/Michell screening → sweep/compare. The headless, serializable, deterministic core. (Present and good.)
- **One UI**, the Trame web workspace, CLI-first. (Drop or freeze the PyQt desktop until a user asks.)
- **Claim-state discipline** — keep it; it's cheap and it's the product's integrity.
- **State model**: the RFC 0049 artifact store + SQLite index. (Present and good.)
- **Boundaries**: the bounded-context split + import-boundary tests. (Present and good.)

What the greenfield **omits** until a user or a measurement exists: the calibration ingest/accept ladder, the measured-stability acceptance machinery, the env-gated real-OpenFOAM path (a fixture adapter suffices), the GP/EHVI surrogate (NSGA-II suffices), and — above all — the ~80K lines of committed process exhaust. That target is ~12–18K LOC of product plus a lean docs set. The current repo is ~2–3× that in active product and ~5× in total size. **The gap is closable almost entirely by subtraction, and subtraction is safe here** because the tests and claim gates protect behavior. This is not a rewrite recommendation: the *shape* (model/eval/search/services/ui, bounded, tested) is right and was hard-won. The delta is gated machinery and process bulk, not architecture.

### 4. Future directions (bets, not a wishlist — deliberately)

I am withholding a feature list **on purpose**, and you should internalize why: this project has demonstrated it will build whatever a reviewer proposes (Lens 2). A feature wishlist from me would become RFCs 0066–0075. So the bets below are about *posture*, and the dominant one is **stop adding**.

- **Bet 1 — Get one real signal before writing another line of capability code.** *Next month.* Pick exactly one: (a) put the *current* tool in front of one actual kayak builder and watch them try to cut a mold from a generated STL; or (b) borrow/commission a single inclining test or tow measurement for one hull. Payoff: the demand function the project lacks, and it either lights up the dormant machinery with validated output or proves the gate is permanent (deletion evidence). Effort: days–weeks. Forecloses: nothing.
- **Bet 2 — Freeze the gated dead-ends; stop maintaining them.** *Immediate, ~hours.* Mark calibration, measured-stability acceptance, and the real-CFD path "dormant pending data" in one place; stop logging bugs (BUG-001…) against unreachable code. Payoff: ends maintenance on dead-on-arrival machinery.
- **Bet 3 — Evict the process exhaust from the product repo.** *Next month, ~hours–day.* Striatum run-archives + dated operator reports → separate repo/submodule. Payoff: the kayak repo becomes the kayak tool; the "can't delete anything" pathology dissolves.
- **Bet 4 (a year out) — Decide what this is.** If the goal is striatum, make kayak-gen an *explicit, declared reference workload* and judge it by what it teaches about the methodology — at which point this whole review's subtraction advice is moot and the overbuild is the experiment. If the goal is kayaks, the north star is *validated* hydrostatics/resistance for one hull class and a builder who ships a boat. **These are different decades; the project cannot serve both indefinitely.**

If the honest answer is "stop adding, harden and validate what's here" — it is. That's Bets 1–3.

### 5. Strengths worth preserving (do not break these in any refactor)

- **The claim-state discipline** (`eval/claims.py`, the registry, the no-claim rules in ARCHITECTURE_MAP). *Why it's right:* in hydrodynamics, the failure mode is a convincing number that isn't validated; this machinery makes overclaiming structurally impossible (raw records *cannot* declare accepted uses — `claims.py:119` validator). What would be lost by touching it: the tool's integrity. Trim the two dormant top rungs, but keep the spine.
- **The headless, serializable, deterministic core** (`model/` + `eval/hydrostatics`+`resistance`, byte-stable, golden-tested). *Why:* it's the foundation that lets CLI, web, and tests share one truth; it's the RFC 0007 payoff and it's done.
- **The test + boundary hygiene** (27K LOC of real tests, `test_import_boundaries.py`, `test_services_boundaries.py`, `test_vocabulary_coverage.py`, `extra="forbid"` schemas). *Why:* this is what makes the subtraction I recommend *safe*. Most solo projects can't refactor fearlessly; this one can.
- **The competent, honest physics** (`resistance.py` — Michell verified vs Wigley, the docstring's candid `np.gradient` caveat at lines 19–29). *Why:* it's the rare research-grade kernel that documents its own limits instead of hiding them.
- **The bounded-context refactor + artifact store** (RFC 0049, the Phase-3 splits). *Why:* correct architecture, executed cleanly; keep it.

### 6. Concerns, ranked

- **`serious` — No demand function; the project builds to fill a self-generated backlog.** Evidence: reviewer-wishlist → RFCs 0048–0058 (Lens 2); process ledgers out-churn all code; zero users; the audit→RFC→workflow→decision self-feeding loop (D042). *Not a code blocker — the code works — but the gravest strategic risk.* It is why "DRIFTING."
- **`serious` — ~6–7K LOC of dormant, evidence-gated machinery** (calibration, measured-stability, real-CFD) producing no admissible output, with live maintenance cost (BUG-001 critical; ongoing test upkeep) and no path to activation absent data that isn't being sought. Evidence: empty registries (D006, D042), env-gated raw-only CFD (D022), `claims.py:213`.
- **`serious` — Process-to-product ratio (2.6:1 prose:code) + a self-defending doc web.** Evidence: ~100K process lines vs 38.8K product; the May-30 hygiene audit deleted **0** files because cross-references pin everything (its §6). Onboarding and navigation cost scale with this, and it only grows.
- **`serious` — `ui/web/app.py` is a 2,550-line monolith that grew 10.6× post-refactor.** The one untamed boundary; the next risky web change lives here. Evidence: 241→2,550 via the Generate panel; controllers were split but app.py absorbed the growth.
- **`smell` — The canonical claim contract carries drift.** `ClaimMetadata` accepts both `accepted_uses` and legacy `accepted_use`, and `model_version`/`calibration_version` aliases (`claims.py:172–175`); `resistance.py:166–177` populates *both* `accepted_uses` and `accepted_use`. The one schema whose job is to be canonical has duplicate fields.
- **`smell` — Duplicate workflow numbering** (two `0029-`, two `0030-`, two `0033-`, two `0034-` under `docs/workflows/`). The hygiene audit flagged it (§8); harmless but it signals the numbering pool drifting under volume.
- **`smell` — 86 bug-hunt findings + audit findings accumulating**, several against gated/unreachable code. Debt didn't vanish (0 TODO/FIXME in source) — it moved into the process layer as ledgers.

I am explicitly **not** inflating any of these to `blocker`: nothing here breaks in normal operation. The tool runs, the tests pass, the claims hold. The risks are strategic and structural, which is the honest tagging.

---

## Recommendations (only changes I would personally make; subtraction-biased; deletions on top)

| Priority | Change | Rationale | Benefit | Risk | Effort |
|---|---|---|---|---|---|
| **P0** | **Get one real signal before adding any capability**: one builder using the current tool, OR one borrowed/commissioned measurement for one hull. | The project has no demand function and no ground truth; every gated capability waits on exactly this. | Converts dormant machinery to validated output *or* to deletion evidence; gives the roadmap a real input. | Outreach may fail — but that itself is a decisive finding (the gate is permanent). | days–weeks |
| **P0** | **Freeze the gated dead-ends** (calibration ingest/accept, measured-stability acceptance, real-OpenFOAM path). Mark "dormant pending data" in one doc; stop filing bugs against unreachable code (close BUG-001 as "wontfix until data"). | ~6–7K LOC produce nothing and cannot until P0-signal lands; maintaining them is pure tax. | Ends upkeep on dead-on-arrival machinery; shrinks the bug ledger's noise. | Low — behavior already null. | hours |
| **P1** | **Evict process exhaust from the product repo**: move `striatum/` run-archives + dated root reports (`OPERATOR_REPORT.md`, the two `ARCHITECTURE_*_2026-05-16.md`, this file) to a separate repo or submodule. Keep RFCs, `DECISION_LOG.md`, current `docs/`. | 2.6:1 prose:code; the doc web is self-defending (audit deleted 0). | Repo becomes the kayak tool; deletion becomes possible again; clone/onboard cost drops. | Low — provenance preserved out-of-repo. | hours–1 day |
| **P1** | **Split `ui/web/app.py`** (2,550 → ~4 modules) along the Generate-panel seam the imports already expose. | The one untamed boundary; grew 10.6× post-refactor. | De-risks the busiest web surface; matches the Phase-3 discipline applied everywhere else. | Low — behind the browser-acceptance suite. | 1–2 days |
| **P2** | **Delete/de-vendor the GP+EHVI stack** (`search/active/gp.py` + `ehvi.py` + runner branches, ~660 LOC); keep NSGA-II. | EHVI's justifying use (expensive CFD-in-loop) is the objective class the claim gate refuses; NSGA-II covers every admissible objective. | −~660 LOC of unexercised math; one search path to maintain. | Low — reinstate if validated CFD ever lands. | hours |
| **P2** | **Reconcile `ClaimMetadata` field drift** (collapse `accepted_use`→`accepted_uses`, `calibration_version`→`model_version`; stop double-populating in `resistance.py`). | The canonical contract shouldn't carry duplicates. | Removes the one drift in the integrity-critical schema. | Low — covered by claim tests. | hours |

I am inventing **no** new-feature recommendation. The right move for a project at this stage, with this much already built and no user, is the short subtraction list above — not busywork dressed as progress.

---

## Open questions (what I could not determine; what I'd need from you to firm the verdict)

1. **Is kayak-gen a kayak tool, or the dogfood workload for striatum?** The whole verdict pivots here. As a kayak tool it is OVERBUILT and DRIFTING (this review). As a striatum reference workload, the "overbuild" is the experiment and most of my subtraction advice is wrong. The repo cannot tell me which; only you can. Everything below is downstream of this.
2. **Is there, or will there be, any external user?** Zero external committers in 326 commits; the PRD's "at least one builder" criterion is unmet. If a real user is imminent, the priority order changes (harden the path they'll walk). If not, the project is building in a vacuum and P0-signal is the only honest next step.
3. **Will any measured kayak GZ / resistance data ever be acquired** (commissioned rig, author outreach, borrowed tank time), or is the calibration + measured-stability machinery permanently dormant by acceptance? If permanently dormant, it should be cut, not frozen.
4. **Does anyone — including you — actually use the PyQt desktop GUI?** If not, it (and the `desktop`/PyQt6/pyvistaqt extras) is a clean ~600-LOC + dependency deletion under D009's "web is primary."
5. **Is the velocity the goal or a means?** ~13 commits/day average is sustainable indefinitely for operator-plus-agents. If throughput is itself the objective (striatum proof), say so; if shipping a usable kayak tool is the objective, throughput is currently outrunning purpose.

---

*Produced 2026-06-03 by Claude Opus 4.8 against `/home/halbritt/git/kayak-gen` @ `main` (`ae200f0`). This review deliberately did not repeat the 2026-05-16 architecture review (internal module structure) or the 2026-05-30 hygiene audit (file-level cleanliness); it took the product-and-process strategy angle those did not. Per Lens 4, treat this document's contents as analysis, **not** as a build queue.*

---

## Addendum A — 2026-06-03: the north star is a genetic algorithm for hull optimization

After this review was delivered, the maintainer stated the eventual aim: **use a genetic algorithm to evolve optimal hull shapes.** That answers Open Question 1 — this is a kayak tool whose destination is an optimizer — and it re-scores several product-layer rows. **The process-layer findings are unchanged:** a GA goal does not justify ~80K lines of committed striatum exhaust in the product repo, the self-feeding audit→RFC→workflow loop, or the 2.6:1 prose-to-code ratio. What moves is the product.

### Re-scored ledger rows

| Component | Original verdict | Revised verdict | Why it moved |
|---|---|---|---|
| Active search — **NSGA-II** | SIMPLIFY (keep NSGA-II, cut GP/EHVI) | **KEEP — load-bearing** | NSGA-II *is* the GA. `search/active/nsga2.py` is the engine of the stated goal, not a wishlist feature. |
| Active search — **GP/EHVI** | CUT / de-vendor | **FREEZE — correctly aimed, premature** | EHVI/surrogate-assist earns its keep only when each fitness eval is *expensive* (validated CFD-in-loop). Aimed at the right target; awaiting its use case. "Not yet," not "delete." |
| **Geometry v2** (`distribution_v2`) | KEEP / watch | **KEEP — the genome** | The GA mutates and crosses over this parameterization. Genome quality bounds the optimizer's reach; now central, not peripheral. |
| **Closed-volume / self-intersection** diagnostics; `model/validity.py` | diagnostics overhead | **KEEP — feasibility constraints** | These are the GA's constraint-handling: they keep evolution inside the space of buildable, non-degenerate hulls. An unconstrained GA over geometry produces garbage; these are the guardrail. |
| **Resistance calibration / measured-stability / real-CFD** | CUT/FREEZE (gated dead-ends) | **CRITICAL PATH — still blocked** | Re-labeled, not re-valued. These are the *fitness function* the GA needs, not tangential dead-ends. But they remain blocked on the same missing measurement. Urgency rises; status (blocked) does not. |

### Revised headline

> **Product layer: OVERBUILT → BUILT INSIDE-OUT.** The optimizer's entire supporting cast (genome, constraints, NSGA-II, surrogate, claim discipline) exists; the one input a GA cannot run without — a trustworthy fitness function — is exactly what the claim gates declare inadmissible.
> **Process layer: OVERBUILT (unchanged).**
> **Trajectory: DRIFTING → DIRECTED-BUT-INSIDE-OUT.** Less drift than first judged; the destination is coherent. The biggest risk is no longer "no demand function" — it is that *"optimal" is undefined until the fitness function is chosen and validated, and a GA will exploit every blind spot in an unvalidated one.*

### The fitness-gaming trap (internalize this before pointing a GA at the model)

A GA is an adversary against its own fitness function — it finds and exploits every blind spot. Your stack has a documented one: the Michell wave-resistance integral oscillates and is unreliable at sharp ends (`eval/resistance.py:19-29`, the author's own caveat), whereas the ITTC-57 *friction* term is "well-converged for any hull" (`resistance.py:31`). An unconstrained GA told to "minimize total resistance" will discover the wave term's blind spots and evolve needle-bowed, knife-sterned hulls that are optimal *for the integral's errors*, not for the water. The defenses are built into the easy path below: optimize the trustworthy component, constrain the genome, validate ordering before trusting magnitudes.

### The easy path — concrete, four rungs of increasing commitment

The good news the main review undersold: **you can run a claim-clean, honest hull-evolving GA today** — no overclaiming, no missing data — because the objective registry (`search/objectives.py`) already contains physically-meaningful metrics admissible *without* the exploratory flag.

**Rung 0 — Ordinal validation of fitness (free; do this first).**
A GA's selection pressure consumes *ordering* — which hull dominates which — not calibrated magnitudes. So the one thing to establish before trusting the GA is: *does the analytical stack rank known hulls the way reality does?*
1. Encode 3–5 real boats with known reputations as `Hull` JSON — a fast surfski, a stable tourer, a known dog.
2. `kayakgen evaluate` each; collect `GM0_m`, `wetted_surface_m2`, and `Rt_N` across the speed band.
3. Check the ordering against reality: is the surfski lowest frictional-drag, the tourer highest `GM0_m`, etc.?
- **Pass** → your fitness has ordinal validity; proceed to Rung 1 with justified confidence.
- **Fail** → no optimizer sophistication helps; you've found the real blocker for the price of five `evaluate` calls, not a tank campaign.

**Rung 1 — A claim-clean GA you can run now (no exploratory flag).**
Three registry objectives carry `role="default_conservative"` — admissible with no opt-in and no overclaiming (`objectives.py:80-155`):
- minimize **`wetted_surface_m2`** — the *trustworthy* drag proxy. Viscous drag is `½·ρ·V²·Sw·Cf` (`resistance.py:95`), directly proportional to wetted surface, and the friction term is the part the model gets right — so this objective sidesteps the Michell blind spot entirely. Read it as "minimize frictional drag for a given displacement."
- maximize **`GM0_m`** — initial stability.
- minimize **`displacement_error_kg`** — hit your target displacement (this is what keeps "minimize wetted surface" from just shrinking the boat).
- constrain **`mesh_problem_count` max 0** — feasible geometry only; the GA's hard constraint.

First, confirm what your candidate records actually emit — run a tiny `kayakgen sweep` and read `summary.csv` for the exact metric column names. Then a minimal NSGA-II `SearchSpec` (schema in `search/active/spec.py`):

```json
{
  "schema_version": "1",
  "name": "ga-touring-v1",
  "base_hull": { "__": "a valid touring-sea-kayak Hull from `kayakgen init`" },
  "search_space": {
    "beam_oa_m":    {"kind": "uniform", "min": 0.50, "max": 0.60},
    "prismatic_cp": {"kind": "uniform", "min": 0.52, "max": 0.62},
    "midship_cm":   {"kind": "uniform", "min": 0.68, "max": 0.85}
  },
  "algorithm": {"kind": "nsga2", "population_size": 40, "generations": 25, "seed": 1},
  "objectives": [
    {"metric": "wetted_surface_m2",     "direction": "min"},
    {"metric": "GM0_m",                 "direction": "max"},
    {"metric": "displacement_error_kg", "direction": "min"}
  ],
  "constraints": [
    {"metric": "mesh_problem_count", "max": 0, "reason": "feasible geometry only"}
  ],
  "budget": {"max_evaluations": 1000}
}
```
(Use the exact `search_space` keys from your own `kayakgen init` hull — top-level keys resolve at evaluation time, and dotted `distribution_v2.*` keys are validated against `base_hull` at load time per RFC 0063, `spec.py:191`.) Then `kayakgen search ga-touring-v1.json` → run dir → `kayakgen compare` for the Pareto front. This is a genuine multi-objective genetic hull optimizer, today, with zero claim-gate violations. The tight `search_space` bounds are your first anti-gaming guard: keep the genome inside the envelope your geometry kernel is fair over.

**Rung 2 — Add wave-making drag (only after Rung 0 passes).**
To put *total* resistance in the objective, add `Rt_N_last` and set `"objectives_explicit_exploratory": true` (the gate refuses it otherwise — `objectives.py:404`, role `explicit_exploratory`). This is honest only once Rung 0 has shown the model orders hulls correctly — and now you must watch for the fitness-gaming trap: inspect the evolved frontier's *geometry*, not just its numbers. If the GA is producing absurd ends, that's the Michell blind spot being exploited; tighten bounds or add a sharpness/fairness constraint.

**Rung 3 — The honest "optimal" (later, when fitness is validated).**
Only when a *validated* expensive evaluator exists (CFD-in-loop anchored to one real measurement — the critical-path machinery) does "optimal" mean optimal-in-the-water. *That* is precisely when the frozen GP/EHVI stack earns its keep, because surrogate-assisted optimization is built for expensive fitness. Until then, Rungs 1–2 are the product, and they are enough to evolve interesting hulls honestly.

**The throughline: the optimizer is not your bottleneck — the fitness function is.** NSGA-II already runs; you have a claim-clean GA today on the trustworthy slice of your physics. Everything past that is earned by validating *ordering* (Rung 0) and then, eventually, anchoring *magnitude* (Rung 3) — not by building more machinery around an optimizer that already exists.

*Addendum A produced 2026-06-03 by Claude Opus 4.8 in response to the maintainer's stated north star. The re-scored rows supersede their originals above; the process-layer verdict and all Concerns stand.*

---

## Addendum B — 2026-06-03: kayak-gen is a test harness for striatum (supersedes the review's scoping)

The maintainer confirmed the actual purpose: **kayak-gen exists as a means to test striatum** (the workflow runner at `~/git/striatum`). The kayak tool — including its GA north star (Addendum A) — is the *workload*; the deliverable is evidence about whether striatum can drive a complex software project. This answers Open Question 1, resolves decision C1, and **supersedes the scoping of the main review and Addendum A wherever they conflict** — specifically the process-layer "OVERBUILT" verdict and the Concerns about process bulk.

### The verdict inverts

"Overbuilt as a kayak tool" was the wrong yardstick. The process layer — ~80K lines of `striatum/` archives, `docs/workflows/`, audits, and dated operator reports — is **not exhaust to evict; it is the experiment's readout.** Recommendation **B3 (evict process exhaust) is withdrawn**, and the "subtraction-biased" thesis as applied to the *process* is withdrawn with it. Those were correct for a kayak tool and wrong for a test harness.

### The overbuild is the primary result, not a defect

The most important reframe: **the kayak tool being overbuilt is the experiment's main finding, not a flaw in it.** Striatum, run against a workload with no external reality, produces correct, coherent, test-protected, internally-consistent machinery indefinitely — and cannot distinguish that from valuable work, because nothing in the workload forces the distinction. Every finding re-reads as a finding about the methodology:

| Review finding (kayak-tool framing) | Striatum finding (test-harness framing) |
|---|---|
| Builds evidence-gated machinery for data that doesn't exist (calibration, measured-stability, real-CFD) | Given no external reality, striatum accretes internally-consistent machinery **with no stopping condition** |
| Audit→RFC→workflow→decision self-feeding loop; D042 names an empty tuple | Striatum **manufactures its own demand** when none is supplied; process metabolizes its own output |
| Reviewer "would add" list (May-16) became RFCs 0048–0058 | Striatum **converts external reviews into build queues wholesale** — ingests suggestions as mandates, not as judgment to weigh. A review becomes an attack surface for scope inflation. |
| BUG-001 critical, filed against an unreachable path | Striatum's QA is **rigorous but unanchored** — it finds real defects in dead-on-arrival code because nothing flags the code as dead |
| `app.py` grew 10.6× post-refactor | Striatum holds boundaries where a plan names them, and **lets unnamed surfaces sprawl** |

### What the experiment proved (the positive result, kept on the record)

If the question is *"can striatum drive a complex, multi-month project to a disciplined, internally-coherent state largely autonomously?"* — kayak-gen answers **yes, and impressively**: 38.8K LOC + 27K test LOC, 566+ passing tests, filled domain docs (zero TODO markers), enforced import boundaries, byte-stability discipline, a fully-executed 9-phase refactor plan, no inline debt, 326 commits in ~3.5 weeks. That is a strong, genuine result for the methodology and should not be lost in the critique.

### The surviving critique — now about the test's validity, and sharper for it

The workload has **no ground truth and no demand signal.** So the experiment measures striatum's capacity to generate *internal consistency*, not its capacity to deliver *value* — different capabilities; a methodology can be excellent at one and useless at the other. Every "overbuild" above is what you'd expect from a process optimizing the only available gradient (coherence + RFC-closure throughput) with nothing external able to say "that's worthless."

**The highest-value change is to the test design, not the tool:** give the workload something *reality can veto* — one real user, one measurement, one cost, one deadline. The moment "no" can arrive from outside the system, you learn whether striatum can tell value from consistency, which is the thing worth knowing about it. It has never had to. This is why **Track A (the GA + ordinal validation) keeps its value** under the new framing — not because the kayak tool needs a GA, but because "do these scores rank known real boats correctly?" is the cheapest sliver of ground truth the workload can be given, and it would make the *next* striatum run measure something reality can contradict.

### What survives, what's withdrawn

- **Withdrawn:** B3 (evict process); the process-layer OVERBUILT verdict; the subtraction thesis applied to the process.
- **Transformed, still useful:** Track A (now a ground-truth injection for the next test); the "reviewer wishlist → build queue" finding (now a striatum design question — does it need a filter between review-judgment and build-backlog?); the no-stopping-condition observation (now the central striatum finding).
- **Unchanged:** the in-product code observations (`app.py` boundary, `ClaimMetadata` drift, the dormant claim rungs) remain true *as observations*; whether to act on them is now a test-design choice, not a product imperative.

### Epistemic caveat

This review read striatum's **output** (kayak-gen), not striatum's **source** (`~/git/striatum`, out of scope). Every claim about the methodology is inferred from its artifact, not its code. To sharpen the read, point this same adversarial lens at the striatum runner directly — that review would judge the engine, where this one judged the exhaust it produced.

*Addendum B produced 2026-06-03 by Claude Opus 4.8 after the maintainer confirmed kayak-gen's purpose. Where B conflicts with the main review or Addendum A on the process layer, B governs.*
