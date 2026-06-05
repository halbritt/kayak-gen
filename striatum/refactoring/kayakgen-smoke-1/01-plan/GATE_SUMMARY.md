---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
inputs:
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_1/FALSIFIER.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/falsifier_2/FALSIFIER.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/adjudicator/COLLABORATION_LEDGER_cycle_1.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md"
---

author: adjudicator-claude-001

# Gate Summary — kayakgen-smoke-1 stage-1 plan gate

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (gate_summary)

## Verdict

**The gate clears: `accept_with_findings`, over seven binding constraints
(C1–C7), all discharged in the committed plan.** The refusal branch was
checked and not taken — no constraint required a production behavior
change, an undischargeable frozen-surface conflict, or a goal change.
Revisit conditions 2 and 3 were ruled **not to fire** (condition 2
conditional on C1/C2 landing in the committed plan; they land). Goal B
stands; selection does not return to arbitration. No `needs_revision`
cycle was used: the dialogue had substance on the first round — both
falsifiers produced tree-verified, line-numbered evidence, partitioned
their postures without overlap, and pre-stated the plan-holder's strongest
rebuttals honestly.

Stage 2's input contract is
`striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md` —
the holder plan with every binding constraint discharged in place and
nothing else changed.

## Binding constraints and where the committed plan discharges them

| # | Constraint (one line) | Source | Discharged at |
|---|---|---|---|
| C1 | Declare the S4 repair for the `render_fork_button` monkeypatch (`tests/test_generative_jobs_web.py:547`) before slicing | falsifier 1, O1 | §4 F2; §7 Table B row S4t (patch-target redirect chosen over carve-out) |
| C2 | Amend F2 with per-function recipes (`test_web_layout.py:68` split read, `:397` union expansion incl. new S5t row) and the post-split scope of all 8 negative assertions | falsifier 1, O2 | §4 F2 (C2 i–iii); §7 Table B rows S1t/S4t/S5t |
| C3 | Restate rollback as LIFO-only with the halt-at-Sn reverse-order unwind declared; drop per-slice independent revert | falsifier 1, O3 | §7 preamble |
| C4 | Re-scope stage-2 `execute_slices.allowed_paths` to the exact files-touched envelope before `run prepare` (critical: scaffold allows only nonexistent `src/example/`) | falsifier 2, O1 | §11, carried verbatim (operator action; see below) |
| C5 | Gating S4/S5 browser runs use strict mode (`KAYAKGEN_BROWSER_ACCEPTANCE=1`) so an un-runnable gate fails instead of skipping | falsifier 2, O2 | §8 rows 3–4; §9 stop condition 6 |
| C6 | Flip §6's `generate_panel.py` trame cell to "yes"; rationale rests on the `cli/main.py:648` extras gate | falsifier 2, O3 | §6 table + corrected rationale |
| C7 | Declare ledger-anchored execution: ledger entry + commit per slice; retries diff-and-resume, never replay; mid-table stops escalate to the operator | falsifier 2, O4 | §12 |

Full rulings, evidence, and the probed-and-cut record (not to be
re-litigated mid-campaign) are in the collaboration ledger.

## The committed plan stage 2 must execute

**Shape:** six ordered slices — S0 → S1(+S1t) → S2 → S3 → S4(+S4t) →
S5(+S5t). One commit per slice; companion test-edit rows (S1t/S4t/S5t)
land in the same commit as their parent move.

- **Move-only slices (5):** S1 `presentation.py` (~655 gross / ~60 net),
  S2 `scene.py` (~64/~25), S3 `generate_panel.py` + ≤2-line cli redirect
  (~295/~50), S4 `layout.py` (~781/~60), S5 `handlers.py` (~401/~70).
  Method moves are byte-identical mixin moves; constant moves use by-name
  re-exports. `app.py` settles ≈400–450 lines (cap ~600).
- **Edit slices:** S0 characterization (~4 net, standalone commit) plus
  the declared same-commit test edits S1t (~16), S4t (~32, includes the
  C1 redirect), S5t (~10).
- **Total estimated size:** ~2,196 gross moved lines, ~227 net
  non-relocation lines across 6 commits; per-slice net caps 10–100, a cap
  breach is a campaign stop.
- **Verification per slice:** full suite (bar: failure set exactly the F3
  singleton `test_services_does_not_import_ui_or_cli[path2]`), ruff exit
  0, extras-less import check; strict-mode browser acceptance mandatory
  after S4 and S5 (bar: 4 passed, 2 deselected); extras-less full suite
  once after S5 (bar: identical failure/error id set).
- **Rollback:** LIFO-only; halt at Sn unwinds Sn → S1 in reverse order.
- **Execution discipline:** step-ledger entry + commit per slice before
  the next; retries diff the branch against the ledger and resume, never
  replay; mid-table stop conditions escalate to the operator (stage 2 has
  no adjudicator).

## Operator action required before stage 2

1. **C4 (critical, blocks everything):** re-scope stage-2
   `execute_slices.allowed_paths` from the scaffold placeholder
   (`src/example/` — nonexistent) to: `kayakgen/ui/web/`,
   `kayakgen/cli/main.py`, `tests/test_cli_serve.py`,
   `tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
   `tests/test_hydro_tab_descriptions.py`,
   `tests/test_generative_jobs_web.py`, and
   `striatum/refactoring/kayakgen-smoke-1/02-execution/STEP_LEDGER.md`.
   No gated job can write `workflow.json`; only the operator can do this.
   If refused, the campaign stops here.
2. **Baseline reproduction:** stage 2 re-runs the §8 commands on its
   unmodified starting tree before S0 and must reproduce the recorded
   baseline (F3 singleton, ruff 0, strict browser 4 passed/2 deselected,
   import check clean). A non-reproducing baseline is a stop before any
   write.

## Provenance notes

- Falsifier 2's artifact carries byline `operator` (session twice
  recovered via `register-session --replace` after daemon-restart lease
  stalls); it was authored by the claude falsifier lane and is treated as
  a falsifier-lane artifact with operator-attested provenance.
- The full-suite baseline is red on unmodified `main` inside a frozen
  "must stay green" file; the committed plan's honest restatement (failure
  set stays exactly the F3 singleton, file untouched) is adopted gate-wide.
