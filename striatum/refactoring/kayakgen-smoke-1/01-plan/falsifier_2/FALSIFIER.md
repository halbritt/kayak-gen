# Falsifier 2 — frozen surfaces and reversibility

author: operator

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (falsifier_2)
(Authored by the claude falsifier lane agent; session recovered twice via
operator `register-session --replace` after daemon-restart lease stalls,
which reassigned the expected byline from `falsifier-claude-001` to
`operator`.)
Target: `striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md`
(plan `plan_kayakgen-smoke-1-split-ui-web-app`, author `plan-holder-claude-001`)
Posture: frozen-surface inventory, rollback units, verification commands —
reversibility.
Tree examined: `main` @ `85aaf94`. Named baseline commands were **re-executed**
in this environment (results in §"Baseline reproduction" and "Probed and cut").

Falsifier 1 (`falsifier_1/FALSIFIER.md`) took the monkeypatch/namespace
breakage, the F2 redirect mechanics, and the LIFO rollback-ordering attack.
This challenge does not repeat those; it attacks the campaign's executing
machinery, the verification commands' failure semantics, and one
internally unsatisfiable cell of the target-shape table.

---

## O1 — the stage-2 execution envelope cannot write a single file in the plan's blast radius; the gate is the last checkpoint that can say so

**Attacks:** the plan's executability premise and every "rollback unit"
cell — a slice that can never land has no rollback story at all.

**Evidence:**

- `striatum/workflows/refactoring-campaign-kayakgen-smoke-1/stage-2-execution/workflow.json`,
  job `execute_slices`, `write_scope.allowed_paths`:
  `["src/example/", "striatum/refactoring/kayakgen-smoke-1/02-execution/STEP_LEDGER.md"]`.
- `src/` does not exist in this repository (`ls src` →
  "No such file or directory"); it is an un-localized scaffold placeholder
  (scaffold commit `425ad76`).
- The step table requires writes to `kayakgen/ui/web/` (five new modules +
  `app.py`), `kayakgen/cli/main.py` (S3), and three test files (S0, S1t,
  S4t) — falsifier 1 adds a fourth. **None** is inside the stage-2
  envelope.

**Consequence:** as scaffolded, stage 2 scope-blocks on slice S0's first
write. The repair is an operator-side re-scaffold of stage-2's
`workflow.json` — a file inside **no** stage's write scope, so neither the
plan holder, the adjudicator, nor the committer can fix it through any
gated job. If the gate clears without naming this, the failure surfaces
mid-campaign as either an instant block (best case) or an ad-hoc scope
widening that bypasses the adjudication this campaign exists to
demonstrate (worst case).

**Strongest plan-holder rebuttal:** "The stage-2 scaffold is outside the
plan's control and outside stage-1's blast radius; the operator localizes
envelopes at `run prepare` time."

**Does it survive?** No — as a defense of silence. The plan is the
artifact that knows its files-touched list, and the gate is the last
refusal point before execution. The plan (or the gate summary) must carry
one line: *stage-2 `execute_slices.allowed_paths` must be re-scoped to
`kayakgen/ui/web/`, `kayakgen/cli/main.py`, and the four named test files
before `run prepare`* — an exact, auditable envelope that also gives the
scope-checker real teeth against scope creep (stop condition 5). Clearing
the gate without it converts a planned refusal mechanism into an
improvised exception.

---

## O2 — the load-bearing browser gate exits 0 when it cannot run; the strict mode that fixes this exists in-tree and the plan does not use it

**Attacks:** verification command inventory (§8 row 3), stop condition 6
("Browser acceptance cannot be run … stop-the-slice, never waivable"),
and the §5 frozen-surface row that names the browser profile as witness.

**Evidence:**

- The named command is
  `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q`.
- `tests/test_web_browser.py:63–97`: unless `--browser-acceptance` is
  passed or `KAYAKGEN_BROWSER_ACCEPTANCE` is set, a missing Playwright
  **skips** (`_load_playwright`, `:73–79`) and an un-launchable Chromium
  **skips** (`_launch_chromium`, `:90–97`). A fully un-runnable gate
  yields "4 skipped, 2 deselected", **exit 0**.
- The same file already implements the strict mode
  (`_browser_acceptance_required`, `:63`): with the flag or env var set,
  the same conditions `pytest.fail` instead.
- Enforcement context (stage-2 `workflow.json`): all six slices execute
  inside one `execute_slices` job; preservation review happens **once**,
  post-hoc, `max_iterations: 1`. The only thing standing between a
  skip-degraded S4/S5 gate and a green ledger entry is the author
  noticing "skipped" instead of "passed" in transcript text at the most
  fatigued point of the campaign.

**Consequence:** stop condition 6 — the one the decision calls "mandatory,
not optional" and the plan calls "never waivable" — has **no mechanical
trigger**. Environment drift between preflight and S4 (a Chromium update,
a rebuilt venv, a headless-launch failure — this run's daemon restarted
twice today; environments do drift mid-campaign) silently converts the
goal's load-bearing preservation evidence into an exit-0 no-op.

**Strongest plan-holder rebuttal:** "§8 states the bar as exact output —
'4 passed, 2 deselected' — and the step ledger records the transcript;
count comparison catches a skip."

**Does it survive?** No. The bar-as-prose delegates a machine-checkable
property to transcript diligence, when the one-flag mechanization
(`--browser-acceptance`, or `KAYAKGEN_BROWSER_ACCEPTANCE=1`) is already
implemented in the frozen witness file itself. The fix costs zero risk
and one token in §8's command. There is no defensible reason for the
gating runs at S4/S5 not to use strict mode.

---

## O3 — §6's "`generate_panel.py`: trame at module level? **no**" is unsatisfiable with byte-identical method bodies

**Attacks:** the target-shape table (§6), its rationale "keeps the cli
redirect trame-free", and — indirectly — the precision of the
`[web]`-extras row of the frozen-surface inventory (§5).

**Evidence:** the generative-jobs panel region (1473–1751) that S3 moves
verbatim calls, by module-global name:

- `build_spec_from_form_state` / `GenerateSpecFormError`
  (`app.py:~1489–1490, ~1503–1504`) and `refresh_concurrency_advisory`
  (`~1579`) — imported from `kayakgen.ui.web.generate_spec_form`, which
  **imports trame at module level** (its import block; the plan's own
  §1.3 names it as the trame-import precedent);
- `refresh_frontier_view` (`~1671`), `apply_candidate_to_hull` (`~1725`),
  `undo_candidate_handoff` (`~1739`) from `generate_frontier_view`
  (trame-free — verified);
- `next_default_seed` (`~1702`) from `generate_fork_button` (trame-free).

For byte-identical bodies to resolve, `generate_panel.py` must import
`generate_spec_form` at module level → `generate_panel.py` is
**trame-bearing**. Every escape breaks a different plan claim:

1. function-local imports → bodies no longer byte-identical → stop
   condition 1's own bar;
2. importing the names from `app.py` → violates invariant 7 ("no sibling
   imports `app.py`");
3. carving the spec-form-touching methods out of S3 → changes the
   panel-seam shape, S3's gross/net estimates, and leaves panel logic
   split across two modules.

**Behavioral impact: none** — and the challenge says so honestly. The
serve command's extras gate (`cli/main.py:648` `try/except ImportError`
on `create_app`) executes **before** the `:657` import, so an extras-less
`kayakgen serve` exits gracefully regardless of what `generate_panel.py`
imports; and the §1.3 precedent explicitly permits module-level trame in
siblings. The per-slice import check (`import kayakgen, kayakgen.cli.main`)
is also unaffected (both imports stay lazy).

**Strongest plan-holder rebuttal:** "Flip the cell to 'yes' — §1.3's
precedent already licenses it; the parenthetical was over-claimed but
nothing verifiable depends on it."

**Does it survive?** Mostly — which is why this objection is about
*when* the contradiction gets resolved, not *whether* it can be. The §6
cell is the design rationale the S3 implementer will read; discovering
mid-slice that the stated shape is impossible forces an undeclared
improvisation among options 1–3, each of which trips a different plan
clause. The plan must pick (flip the cell, and say which methods if any
stay behind) **before** slicing. An adjudicated one-line amendment closes
it.

---

## O4 — the plan's slice-grain rollback discipline has no anchor in the job-grain machinery that will execute it; interruption mid-table is undeclared and was demonstrated today

**Attacks:** the step-table rollback column as an *operational* promise,
and stop conditions 1–9's enforcement model.

**Evidence:**

- Stage-2 `workflow.json`: **one** `execute_slices` job runs the entire
  S0→S5 table (`max_active_jobs: 1`, author lane
  `worktree_isolation: per_job`); review is a single post-hoc
  `review_preservation` with a **single** `needs_revision` cycle
  (`max_iterations: 1`); there is **no adjudicator role in stage 2**,
  although stop conditions say "gate escalated to the adjudicator".
- Recovery in this machinery is job-grain, not slice-grain: if the job
  dies between S2 and S3 (daemon restart, lease stall), `retry-job`
  re-dispatches the *whole* step table to a fresh session/worktree. The
  plan nowhere instructs the executor to first inventory which slices
  already exist on the branch and resume idempotently — without that, a
  retry either replays landed slices (duplicate moves that cannot apply)
  or starts a divergent second attempt.
- This is not hypothetical: **during this very stage-1 run** the daemon
  restarted and the original falsifier session was closed
  `recovery_stalled_transfer` (21:31:55Z, visible in
  `striatum list sessions`). A multi-hour six-slice stage 2 should expect
  at least one interruption.

**Consequence for reversibility:** the table's "rollback unit: revert Sn
commit" implicitly assumes a continuously supervised, slice-aware
executor. The machinery provides neither slice-grain checkpoints nor
slice-aware recovery. Combined with falsifier 1's O3 (LIFO-only
revertibility), the *real* reversibility properties are: revert is clean
only at the head of the stack, and resume-after-interruption is undefined.

**Strongest plan-holder rebuttal:** "The step ledger is the slice-grain
checkpoint: each slice records its commit hash and verification
transcript, and an interrupted retry reads the ledger and resumes after
the last verified slice."

**Does it survive?** Only if the plan *says that*. The ledger is indeed
the right anchor — but the plan never instructs: (i) ledger entry +
commit per slice **before** starting the next, (ii) on retry, diff the
branch against the ledger and resume, never replay, (iii) a stop
condition firing mid-table escalates via operator escalation (stage 2 has
no adjudicator). Three sentences in the committed plan close this; their
absence leaves recovery behavior to be invented by whichever session
inherits the wreckage.

---

## Baseline reproduction (named commands re-executed, this environment)

| Plan claim (§1.2) | Re-run result | Verdict |
|---|---|---|
| Full suite: 1 failed, 1307 passed, 4 skipped (8:26); sole failure `test_services_does_not_import_ui_or_cli[path2]` | **1 failed, 1307 passed, 4 skipped in 8:14; identical failure id** | reproduces exactly |
| `ruff check kayakgen tests`: exit 0, 6 "invalid `# noqa`" warnings | **exit 0; zero warnings emitted** (the 6 `# noqa: kg-orphan-color` directives exist at `generate_frontier_view.py:60–65`; current ruff is silent about them) | exit code reproduces; warning claim does not — immaterial |
| Browser gate: 4 passed, 2 deselected (37.79s) | **4 passed, 2 deselected in 35.73s** | reproduces |

The plan's red-baseline honesty (F3/F4) is confirmed, not challenged.

## Probed and cut (clean checks, for the adjudicator's economy)

- **Integration destroys rollback units (squash)?** No — `run.integrate`
  is RFC 0108 Phase 4 merge-tree integration ("never auto-resolves");
  per-slice commits survive to mainline. The revert-unit story holds
  *through integration* (subject to falsifier 1's LIFO caveat).
- **New modules fall out of the wheel?** No — `pyproject.toml:58–60`
  uses setuptools auto-discovery (`include = ["kayakgen*"]`); new
  siblings inside `kayakgen/ui/web/` are packaged automatically.
- **Browser gate is a thin witness?** No — the 2 deselected tests are
  unmarked unit tests of the `_compare_visual_png` helper; the 4 selected
  include multi-viewport visual-baseline pixel comparison plus the serve
  acceptance flow. The gate is substantive (which is why O2's exit-0
  hole matters).
- **`STATE_SNAPSHOT_KEYS` re-export precedent (§6):** confirmed —
  `app.py` already re-imports it from `state.py` (`app.py:87–95`).
- **Serve's extras-less degradation through the S3 redirect:** protected —
  the `:648` gate precedes `:657` (see O3); no behavioral hole.

## Net assessment

The plan's baselines are honest and reproduce; the seam analysis and the
§1.3/§1.4 preflight work are the strongest part of the artifact. What
fails falsification under the reversibility posture is the **machinery
fit**: the executing stage cannot write the blast radius (O1), the
never-waivable gate cannot mechanically refuse (O2), one cell of the
target shape is unsatisfiable as stated and must be amended before an
implementer meets it mid-slice (O3), and the slice-grain rollback
discipline has no declared resume/escalation behavior in a job-grain,
interruption-prone execution environment (O4 — demonstrated live during
this run). All four close with small, specific amendments; none should
be left for stage 2 to discover.
