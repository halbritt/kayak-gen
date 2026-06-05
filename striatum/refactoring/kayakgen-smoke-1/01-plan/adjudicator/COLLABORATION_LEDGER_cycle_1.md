---
schema_version: "striatum.collaboration_ledger.v1.1"
artifact_kind: "collaboration_ledger"
shape: "falsification_gate"
topic: "kayakgen-smoke-1 stage-1 plan gate: does the plan to split kayakgen/ui/web/app.py along the Generate-panel seam survive falsification?"
participants:
  - "plan-holder-claude-001"
  - "falsifier-claude-001"
  - "operator"
  - "adjudicator-claude-001"
cycle: 1
entries:
  - kind: "claim"
    by: "plan-holder-claude-001"
    refs: ["dialogue:1"]
    text: "Six-slice move-only split of app.py into five siblings via byte-identical mixin moves and by-name re-exports; honest red baselines (F3/F4); per-slice full-suite/ruff/import-check verification with browser gates at S4/S5; per-slice git-revert rollback; findings F1 (21-name test surface) and F2 (29 source-text assertions) surfaced for adjudication."
  - kind: "challenge"
    by: "falsifier-claude-001"
    refs: ["dialogue:2"]
    text: "F1-O1: tests/test_generative_jobs_web.py:547 monkeypatches render_fork_button in app.py's namespace; S4 moves the only consumer into layout.py, whose module namespace the patch never reaches; deterministic red at S4, and the repairing edit is outside every declared edit set, so stop conditions 1 and 7 both fire by the plan's own text."
  - kind: "challenge"
    by: "falsifier-claude-001"
    refs: ["dialogue:2"]
    text: "F1-O2: the 'mechanical pointer redirect, strings unchanged' recipe is not executable for test_web_layout.py:68 (mixed-destination single read, must be split twice) or :397 (union test requiring expansion at S1/S4/S5 while S5 declares no test edits, silently dropping handlers.py from the frozen claim-vocabulary scan); 8 negative assertions shrink scope under partition with no detecting verification."
  - kind: "challenge"
    by: "falsifier-claude-001"
    refs: ["dialogue:2"]
    text: "F1-O3: 'independently revertible by git revert of that commit' is false for S1-S3 once successors land; siblings import presentation.py, so reverting S1 breaks the tree; real unwind is reverse-order multi-revert, declared nowhere, and the High reversibility score was an input to selecting Goal B."
  - kind: "challenge"
    by: "operator"
    refs: ["dialogue:3"]
    text: "F2-O1: stage-2 execute_slices write scope allows only src/example/ (nonexistent) and the step ledger; not one file in the plan's blast radius is writable, and no gated job can repair workflow.json; the campaign scope-blocks at S0's first write unless re-scoped before run prepare."
  - kind: "challenge"
    by: "operator"
    refs: ["dialogue:3"]
    text: "F2-O2: the mandatory browser gate exits 0 when Playwright/Chromium is unavailable (4 skipped, 2 deselected); strict mode (--browser-acceptance / KAYAKGEN_BROWSER_ACCEPTANCE) exists in the frozen witness file and the plan's command inventory does not use it, so stop condition 6 has no mechanical trigger."
  - kind: "challenge"
    by: "operator"
    refs: ["dialogue:3"]
    text: "F2-O3: section 6's 'generate_panel.py: trame at module level? no' is unsatisfiable with byte-identical bodies because the moved panel region calls generate_spec_form names (module-level trame import); every escape trips a different plan clause; behavioral impact none, but the cell must be resolved before an implementer meets it mid-slice."
  - kind: "challenge"
    by: "operator"
    refs: ["dialogue:3"]
    text: "F2-O4: the slice-grain rollback discipline has no anchor in the job-grain machinery; one execute_slices job runs the whole table, recovery re-dispatches the whole table, resume-after-interruption is undeclared, stage 2 has no adjudicator for mid-table stop conditions, and a daemon restart interrupted this very stage-1 run."
  - kind: "rebuttal"
    by: "plan-holder-claude-001"
    refs: ["dialogue:1", "dialogue:2"]
    text: "Probed-and-cut by the tree: mixin hazards (no mangling, no super(), no MRO/pickle/introspection sensitivity), create_app patch path stays in app.py, REVIEW_TABS fromlist read survives re-export, gross-move arithmetic honest, browser witness does no source reading. Against O1-O3 the plan's pre-stated rebuttals are amendments (declared S4t patch-target edit; cap headroom plus slice-time recipes; LIFO-implied unwind), not defenses of the text as written."
  - kind: "rebuttal"
    by: "plan-holder-claude-001"
    refs: ["dialogue:1", "dialogue:3"]
    text: "Section 1.3's precedent licenses module-level trame in siblings, so flipping the section-6 cell to 'yes' costs nothing verifiable (F2-O3, conceded by the falsifier as mostly surviving); the serve extras gate at cli/main.py:648 precedes the :657 import, so extras-less degradation is protected through the S3 redirect; baselines reproduce exactly in the falsifier's environment."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:2"]
    text: "C1: the committed plan must declare the S4 repair for the render_fork_button monkeypatch site - either add tests/test_generative_jobs_web.py:547's patch target to a declared S4t mechanical redirect, or carve _render_generate_job_fork_buttons out of the S4 move as a named carve-out - before any slice lands."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:2"]
    text: "C2: the committed plan must amend F2 with per-function recipes for test_web_layout.py:68 (split read, S1t and S4t) and :397 (union expansion at S1t, S4t, and a new declared S5t row covering handlers.py and generate_panel.py), and state the intended post-split scope of each of the 8 negative source assertions."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:2"]
    text: "C3: the committed plan must restate rollback guarantees as LIFO-only - clean revert only at the head of the stack, S1 load-bearing and unwound last, halt-at-Sn exits via reverse-order multi-revert - replacing the per-slice 'independently revertible' claim."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:3"]
    text: "C4: before stage-2 run prepare, the operator must re-scope execute_slices.allowed_paths to the exact files-touched envelope: kayakgen/ui/web/, kayakgen/cli/main.py, tests/test_cli_serve.py, tests/test_web_layout.py, tests/test_web_inline_help.py, tests/test_hydro_tab_descriptions.py, tests/test_generative_jobs_web.py (per C1), and the step ledger path; the committed plan and gate summary must carry this precondition."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:3"]
    text: "C5: the gating browser-acceptance runs at S4 and S5 must use strict mode (KAYAKGEN_BROWSER_ACCEPTANCE=1 or --browser-acceptance) so an un-runnable gate fails instead of skipping; section 8's command inventory must be amended accordingly."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:3"]
    text: "C6: the committed plan must flip section 6's generate_panel.py trame cell to 'yes' (module-level import of generate_spec_form, licensed by the section-1.3 precedent) and correct the 'keeps the cli redirect trame-free' rationale to rest on the cli/main.py:648 extras gate."
  - kind: "constraint"
    by: "adjudicator-claude-001"
    refs: ["dialogue:3"]
    text: "C7: the committed plan must declare ledger-anchored execution discipline: one step-ledger entry plus commit per slice before the next slice starts; on any retry the executor diffs the branch against the ledger and resumes after the last verified slice, never replays; a stop condition firing mid-table escalates to the operator (stage 2 has no adjudicator)."
verdict: "accept_with_findings"
rationale: "All seven objections are load-bearing and unrebutted as the plan is written, and all seven are dischargeable by amending the plan or its execution preconditions without changing behavior or the goal; none requires a production behavior change, an undischargeable frozen-surface conflict, or a goal change, so the gate clears over binding constraints C1-C7 that the committed plan must discharge. Revisit conditions 2 and 3 are ruled not to fire."
findings:
  - id: "F1-O1"
    severity: "high"
    posture: "maintainability and migration risk"
    status: "converted_to_constraint"
    challenge: "S4 deterministically breaks the generative-jobs witness via a monkeypatch write that by-name re-export cannot preserve; the repair edit is outside every declared edit set, so the plan self-halts at S4."
    source_refs: ["dialogue:2"]
  - id: "F1-O2"
    severity: "high"
    posture: "maintainability and migration risk"
    status: "converted_to_constraint"
    challenge: "The F2 redirect recipe is not mechanical for two named functions; union and negative assertions weaken silently under source partition with a green-test failure mode no named verification detects."
    source_refs: ["dialogue:2"]
  - id: "F1-O3"
    severity: "high"
    posture: "maintainability and migration risk"
    status: "converted_to_constraint"
    challenge: "Per-slice independent revertibility is false for S1-S3 once successors land; the real unwind is reverse-order multi-revert, undeclared; the falsified claim was an input to Goal B's selection."
    source_refs: ["dialogue:2"]
  - id: "F2-O1"
    severity: "critical"
    posture: "frozen surfaces and reversibility"
    status: "converted_to_constraint"
    challenge: "The stage-2 execution envelope cannot write a single file in the plan's blast radius; no gated job can repair it; the gate is the last checkpoint that can say so."
    source_refs: ["dialogue:3"]
  - id: "F2-O2"
    severity: "high"
    posture: "frozen surfaces and reversibility"
    status: "converted_to_constraint"
    challenge: "The never-waivable browser gate exits 0 when it cannot run; the in-tree strict mode is unused by the plan's command inventory."
    source_refs: ["dialogue:3"]
  - id: "F2-O3"
    severity: "high"
    posture: "frozen surfaces and reversibility"
    status: "converted_to_constraint"
    challenge: "Section 6's trame-free cell for generate_panel.py is unsatisfiable with byte-identical bodies; unresolved, it forces an undeclared mid-slice improvisation whose every option trips a plan clause."
    source_refs: ["dialogue:3"]
  - id: "F2-O4"
    severity: "high"
    posture: "frozen surfaces and reversibility"
    status: "converted_to_constraint"
    challenge: "Slice-grain rollback and stop conditions have no anchor in job-grain machinery; resume-after-interruption is undeclared and interruption was demonstrated during this run."
    source_refs: ["dialogue:3"]
constraints:
  - id: "C1"
    posture: "maintainability and migration risk"
    severity: "high"
    kind: "policy"
    binding: true
    text: "Declare the S4 monkeypatch repair (S4t patch-target redirect for tests/test_generative_jobs_web.py:547, or a named carve-out of _render_generate_job_fork_buttons) in the committed plan before slicing."
    source_finding: "F1-O1"
    source_refs: ["dialogue:2"]
    verification:
      expected_stage: "stage-2 S4: full suite green modulo the F3 singleton, including test_generative_jobs_web.py fork-button test"
    final_review_required: true
  - id: "C2"
    posture: "maintainability and migration risk"
    severity: "high"
    kind: "policy"
    binding: true
    text: "Amend F2 with per-function redirect recipes for test_web_layout.py:68 and :397, add a declared S5t union-expansion row, and state the post-split scope of all 8 negative source assertions."
    source_finding: "F1-O2"
    source_refs: ["dialogue:2"]
    verification:
      gate: "committed plan review: F2 inventory enumerates both named functions, an S5t row exists, and the forbidden-claim union covers presentation.py, layout.py, handlers.py, generate_panel.py after S5"
    final_review_required: true
  - id: "C3"
    posture: "maintainability and migration risk"
    severity: "high"
    kind: "policy"
    binding: true
    text: "Restate rollback guarantees as LIFO-only with the halt-at-Sn reverse-order unwind path declared; remove the per-slice independent-revert claim."
    source_finding: "F1-O3"
    source_refs: ["dialogue:2"]
    verification:
      gate: "committed plan review: section 7 preamble carries the LIFO-only paragraph"
    final_review_required: true
  - id: "C4"
    posture: "frozen surfaces and reversibility"
    severity: "critical"
    kind: "gate"
    binding: true
    text: "Re-scope stage-2 execute_slices.allowed_paths to the named files-touched envelope before run prepare; the committed plan and gate summary carry this precondition verbatim."
    source_finding: "F2-O1"
    source_refs: ["dialogue:3"]
    verification:
      expected_stage: "stage-2 run prepare: workflow.json allowed_paths matches the plan's files-touched list"
    final_review_required: true
  - id: "C5"
    posture: "frozen surfaces and reversibility"
    severity: "high"
    kind: "gate"
    binding: true
    text: "Gating browser runs at S4/S5 use strict mode (KAYAKGEN_BROWSER_ACCEPTANCE=1 or --browser-acceptance); amend the section-8 command inventory."
    source_finding: "F2-O2"
    source_refs: ["dialogue:3"]
    verification:
      gate: "step ledger at S4/S5 records the strict-mode command and 4 passed, 2 deselected"
    final_review_required: true
  - id: "C6"
    posture: "frozen surfaces and reversibility"
    severity: "high"
    kind: "policy"
    binding: true
    text: "Flip section 6's generate_panel.py trame cell to 'yes' and correct the rationale to rest on the cli/main.py:648 extras gate."
    source_finding: "F2-O3"
    source_refs: ["dialogue:3"]
    verification:
      gate: "committed plan review: section 6 row for generate_panel.py reads 'yes' with corrected rationale"
    final_review_required: true
  - id: "C7"
    posture: "frozen surfaces and reversibility"
    severity: "high"
    kind: "policy"
    binding: true
    text: "Declare ledger-anchored execution: ledger entry plus commit per slice before the next; retries diff branch against ledger and resume, never replay; mid-table stop conditions escalate to the operator."
    source_finding: "F2-O4"
    source_refs: ["dialogue:3"]
    verification:
      expected_stage: "stage-2 execution: step ledger shows one entry per landed slice, written before the successor slice starts"
    final_review_required: true
---

author: adjudicator-claude-001

# Collaboration Ledger — kayakgen-smoke-1 stage-1 plan gate (cycle 1)

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (adjudicate)
Dialogue trajectory read (and nothing else, per the role):

| ref | document | author byline |
|---|---|---|
| `dialogue:1` | `striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md` | `plan-holder-claude-001` |
| `dialogue:2` | `striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_1/FALSIFIER.md` | `falsifier-claude-001` |
| `dialogue:3` | `striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_2/FALSIFIER.md` | `operator` |

Provenance note: `dialogue:3` was authored by the claude falsifier lane
agent; its byline reads `operator` because the session was twice recovered
via `register-session --replace` after daemon-restart lease stalls, which
reassigned the expected byline. The document itself declares this. I treat
it as a falsifier-lane artifact with operator-attested provenance.

## Verdict

**`accept_with_findings` — the gate clears over seven binding constraints
(C1–C7).** Every objection that survived its strongest rebuttal is
dischargeable by amending the plan text or the stage-2 execution
preconditions, without changing observable behavior, without touching an
undischargeable frozen surface, and without changing the goal. The refusal
branch was checked and not taken: no constraint requires a behavior change;
no frozen-surface conflict is undischargeable; the goal stands.

The dialogue did its epistemic work. The falsifiers did not retread each
other (falsifier 2 explicitly partitioned away from falsifier 1's attacks),
both produced tree-verified evidence with line numbers, both re-executed or
honored the plan's baselines, and both pre-stated the plan-holder's
strongest rebuttal and ruled on it honestly. The plan-holder, for its part,
surfaced F1–F4 and its own attack surface (§10) rather than planning around
them silently. This is the substance the gate exists to detect.

## Rulings, objection by objection

### Falsifier 1 (`dialogue:2`, posture: maintainability and migration risk)

**O1 — S4 monkeypatch breakage of the generative-jobs witness: `binding` (→ C1).**
The evidence is exact and deterministic: `tests/test_generative_jobs_web.py:547`
patches `render_fork_button` into `app.py`'s namespace; S4 moves the sole
consumer (`_render_generate_job_fork_buttons`) into `layout.py`, whose
module globals the patch never reaches; the fake is never called and the
test goes red. By-name re-export preserves reads, not monkeypatch writes —
the F1 audit was read-biased with this site in hand. The plan as written is
internally inconsistent at S4: the repairing edit is outside F2's declared
three-file set, so stop condition 1's modulo clause and stop condition 7
both fire. The pre-stated rebuttal ("two lines, cap headroom exists") is an
amendment, not a defense; it must be declared and chosen (pointer redirect
vs. carve-out) before slicing, because both options touch surfaces the plan
currently promises not to touch.

**O2 — redirect recipe not mechanical; union/negative assertion erosion: `binding` (→ C2).**
Three mechanisms, each verified against named lines: the mixed-destination
single-read function (`test_web_layout.py:68`) has no single redirect target
at any point in the campaign and must be structurally split twice; the
forbidden-claim union test (`:397`) can only be meaning-preserved by union
expansion, and S5 — which moves render-feeding handler code — declares no
test edits, so the globally frozen claim-vocabulary guard silently stops
covering `handlers.py` while staying green; and 8 negative assertions
shrink their guarded scope under partition by construction, the mirror
image of the weakening the plan itself used to reject the concatenation
alternative. The failure mode of (b) and (c) is a green test, which no
named verification detects — that elevates this above test-suite
housekeeping. The plan-holder's position partially survives (caps may
hold; behavior is preserved), but the *characterization* — "mechanical,
pointer, strings unchanged" — is what stop condition 1 and revisit
condition 2 hinge on, and it is false for the two named functions.

**O3 — per-slice revertibility false for S1–S3: `binding` (→ C3).**
Invariant 7 (no sibling imports `app.py`) forces every later sibling to
import `presentation.py` directly; the falsifier verified the consuming
names region by region. After S2 lands, `git revert <S1>` breaks the tree,
and every slice rewrites `app.py`'s import block, so non-LIFO reverts
conflict textually. "Independently revertible" is true only at the head of
the stack. This matters beyond pedantry because reversibility High (8/10)
was an input to selecting Goal B over Goal A, and because O1/O2 make a
mid-campaign halt at S4–S5 a live scenario in which the advertised exit
does not work. The rebuttal ("LIFO is implied, standard discipline") is
operationally right and textually absent; one declared paragraph closes it.

### Falsifier 2 (`dialogue:3`, posture: frozen surfaces and reversibility)

**O1 — stage-2 envelope cannot write the blast radius: `binding` (→ C4), severity critical.**
`execute_slices.allowed_paths` is `["src/example/", ...step ledger...]`;
`src/` does not exist; every file the step table touches is outside the
envelope; and `workflow.json` is inside no stage's write scope, so no gated
job can repair it. As scaffolded, the campaign hard-blocks at S0's first
write — or worse, invites an ad-hoc scope widening that bypasses exactly
the adjudication this campaign exists to demonstrate. The rebuttal ("the
operator localizes envelopes at prepare time") fails as a defense of
silence: the plan is the artifact that knows its files-touched list, and
this gate is the last refusal point. The constraint names the exact
envelope so the scope-checker gets real teeth.

**O2 — browser gate exits 0 when un-runnable: `binding` (→ C5).**
Verified in the witness file itself: without `--browser-acceptance` or
`KAYAKGEN_BROWSER_ACCEPTANCE`, missing Playwright or un-launchable Chromium
*skips* and exits 0. Stop condition 6 — "never waivable" — therefore has no
mechanical trigger, and the strict mode that fixes it is already
implemented in the frozen file. Bar-as-prose ("4 passed, 2 deselected")
delegates a machine-checkable property to transcript diligence at the most
fatigued point of the campaign. One token in §8's command closes it. No
defensible counter exists; the plan-holder's rebuttal concedes the
mechanism and argues diligence.

**O3 — `generate_panel.py` trame-free cell unsatisfiable: `binding` (→ C6).**
The moved panel region calls `build_spec_from_form_state`,
`GenerateSpecFormError`, and `refresh_concurrency_advisory` from
`generate_spec_form`, which imports trame at module level; byte-identical
bodies therefore force `generate_panel.py` to be trame-bearing. Every
escape trips a different plan clause (function-local imports break
byte-identity; importing from `app.py` breaks invariant 7; carving methods
out reshapes S3). The falsifier honestly concedes zero behavioral impact —
the `cli/main.py:648` extras gate precedes the `:657` import — and the
plan-holder's rebuttal ("flip the cell; §1.3 already licenses it") mostly
survives. It is binding rather than rebutted because the discharge is a
plan amendment that must land *before* an implementer meets the
contradiction mid-slice; the objection's force is about when, and "when"
is now, at the gate.

**O4 — slice-grain discipline has no job-grain anchor: `binding` (→ C7).**
One `execute_slices` job runs the whole table; recovery re-dispatches the
whole table to a fresh session and worktree; the plan never instructs
ledger-first commits per slice, diff-and-resume on retry, or operator
escalation for mid-table stop conditions (stage 2 has no adjudicator).
This is not hypothetical: this very stage-1 run was interrupted by a
daemon restart that closed the original falsifier-2 session
(`recovery_stalled_transfer`), and the adjudicator lane itself observed
the restart. The rebuttal ("the step ledger is the checkpoint") is the
right design — and survives only if the plan says it. Three sentences
close it.

## Adjudicator rulings the plan explicitly deferred

The plan (stop condition 9, findings F1/F2) defers two revisit-condition
questions to this ledger. Ruling them explicitly so the committer is not
left to infer:

**Revisit condition 3 (importers of `app.py` internals beyond
`cli/main.py:657`) does not fire.** The ~21-name surface (F1) is test
access, inside the declared blast radius; the only production importer of
an `app.py` internal remains `cli/main.py:657`. The condition targets
production callers; by-name re-export is sufficient for every read-path
name. The one write-path exception (the O1 monkeypatch) is handled as C1
and does not void the premise — it sharpens it.

**Revisit condition 2 (move-only premise fails) does not fire,
conditional on C1 and C2 landing in the committed plan.** The source moves
remain byte-preserving; the test-suite edits are declared,
characterization-preserving migration work — broader than "pointer
redirects" (C2 forces the honest restatement) but never behavior-altering.
The premise that this campaign is a pure structural refactoring of
production code holds. Selection does not return to arbitration; Goal B
stands.

## What the committed plan must do

Discharge C1–C7 by amendment — each is a named, bounded edit to the plan
text or a named operator precondition (C4) — and change nothing else.
Slicing must not begin until the committed plan carries all seven
discharges. If any constraint turns out undischargeable as specified
(e.g., the C4 re-scope is refused, or the C1 repair cannot stay
mechanical), that is a campaign stop per the refusal rule, not a license
to improvise.

## Probed-and-cut record (for the committer's economy)

Attack lines both falsifiers investigated and the tree rebutted, recorded
here so they are not re-litigated: mixin hazards (no mangling, no
`super()`, no MRO/pickle/introspection sensitivity; disjoint method names),
`create_app`'s `KayakgenApp` patch path (resolves in `app.py` through every
slice), the `REVIEW_TABS` fromlist read (re-export-safe), gross-move
arithmetic (verified against marker lines), wheel packaging of new siblings
(setuptools auto-discovery), squash risk at integration (merge-tree
integration preserves per-slice commits), browser-gate substance (4
selected tests include multi-viewport pixel comparison), and the serve
command's extras-less degradation through the S3 redirect (protected by the
`:648` gate). Baselines reproduce exactly in a second environment
(falsifier 2's table), including the F3 singleton failure id.
