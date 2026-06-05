---
schema_version: striatum.synthesis.v1
artifact_kind: synthesis
inputs:
  - striatum/refactoring/kayakgen-smoke-1/00-goal/PROBLEM_BRIEF.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/TRADEOFF_LEDGER.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/proposals/GOAL_A.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/proposals/GOAL_B.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/proposals/GOAL_C.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/scorecards/SCORECARD_A.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/scorecards/SCORECARD_B.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/scorecards/SCORECARD_C.md
  - striatum/refactoring/kayakgen-smoke-1/00-goal/DISSENT_REVIEW.md
author: arbitrator-claude-002
---

# Arbitrator Synthesis — kayakgen-smoke-1 Goal Selection (Revision 2)

author: arbitrator-claude-002

Date: 2026-06-05
Run: `run_08d0beb1f0959b071475ff4400dc1d97`, stage 0 (arbitrate), attempt 2
Evidence: problem brief, tradeoff ledger, proposals A/B/C, scorecards
A/B/C, the attempt-1 synthesis (`arbitrator-claude-001`), the dissent
review (`needs_revision`), and a fresh browser-acceptance run executed by
this arbitrator (§2).

---

## 1. Decision

**Selected goal — Goal B:** split `kayakgen/ui/web/app.py` (2,550 lines)
along the Generate-panel seam into focused sibling modules inside
`kayakgen/ui/web/`, leaving `app.py` as a ≤~600-line integrator that
still exports `create_app` and `KayakgenApp` unchanged, exactly as scoped
in `proposals/GOAL_B.md` (brief candidate C1; `TODO.md` B2/P1; the
architecture review's "one untamed boundary").

The campaign executes Goal B as proposed: five move-only slices
(presentation constants → VTK scene helpers → generative-jobs panel
wiring → layout → handlers), with the full suite + ruff per slice and the
Playwright browser-acceptance run as a **mandatory hard gate for slices
4–5** (proposal B §7). Nothing from proposals A or C is composed in.

## 2. What changed since attempt 1 — and how it was verified

Attempt 1 selected Goal A and rejected Goal B on one ground: B's
preservation story for its payoff-bearing slices was conditional on an
undemonstrated environment capability (a runnable, green Playwright
browser-acceptance profile), and "no evidence in the record" showed the
profile had ever run here. Attempt 1's own Revisit Condition 1 stated
that if the suite is demonstrated green on unmodified `main` in the
executing environment, "B's disqualifying conditionality is discharged
and the A-vs-B payoff question (5 vs 9) deserves re-arbitration."

The dissent review (verdict `needs_revision`) reported exactly that
demonstration: 4 passed, 2 deselected. The dissent's claim arrived
without a transcript, and an unverifiable discharge of an unverifiable
assumption would discharge nothing — so this arbitration re-ran the gate
first-hand rather than taking the claim on faith:

- Command: `.venv/bin/python -m pytest tests/test_web_browser.py
  -m browser_acceptance -q`
- Tree: unmodified `main` (425ad76) plus untracked campaign scaffold
  (no `kayakgen/` or `tests/` code touched); Playwright 1.59.0 installed.
- Result: **4 passed, 2 deselected in 34.29s** — green, and identical in
  shape to the dissent's reported run.

Revisit Condition 1 is therefore discharged on direct evidence, twice
over and independently. The decision below follows from attempt 1's own
stated logic; no other fact in the record changed.

## 3. Why Goal B now wins

Applying the selection rules in order, with the new evidence:

1. **No goal is disqualified on `preservation_verifiability`** — A: Very
   High (9/10), B: High (8/10), C: High (8/10). None is low.
2. **The preflight-checkability rule no longer separates A from B.**
   B's single biggest unverified assumption per the ledger (§4) — the
   browser suite runs green in this environment — is no longer an
   assumption; it is a checked fact (§2). The ledger's B-1/B-2
   disagreements (scorecard verbiage understating the browser-gate
   dependency) are now practically moot: the gate the proposal demands is
   demonstrated runnable, so slices 4–5 can be gated exactly as proposal
   B §7 requires. B's *remaining* assumptions are all cheap stage-1
   preflight checks: the `cli/main.py:657` private-import redirect
   (pinned by `test_cli_serve.py`), and the `[web]`-extras leak guard
   (one run of the non-web suite without extras). Nothing about B is
   any longer "higher payoff but unverifiable."
3. **With verification parity established, payoff decides.** B: Very
   High (9/10) — decomposing the repo's largest module and retiring the
   architecture review's one untamed boundary — against A's Moderate
   (5/10) navigability cleanup. The dissent's payoff-adequacy critique
   (running a full multi-lane campaign for eleven import-line redirects)
   is accepted as an operator-weighted exercise of attempt 1's Revisit
   Condition 4; under that weighting and rule 2 now satisfied, the
   9-vs-5 gap is decisive. B's remaining card is strong across the
   board: blast radius Low (3/10), frozen-surface risk Low (2/10),
   reversibility High (8/10), sliceability Very High (9/10).

One notch of raw `preservation_verifiability` (A 9 vs B 8) is the only
dimension A still wins, and the selection rules do not award the
campaign to the safest goal — they bar unverifiable goals and prefer
cheap-to-check assumptions, both of which B now satisfies.

## 4. Runner-up — Goal A, and why it lost

A (retire internal shim traffic, 11 import sites across 10 files) was
attempt 1's winner and remains the safest goal on the board: preservation
Very High (9/10), reversibility 10/10, blast radius 2/10. It lost
because its sole decisive advantage evaporated:

- Attempt 1 chose A *only* through selection rule 2 — B's payoff was
  conceded to be far higher, but B's verification was conditional on an
  undemonstrated environment. That conditionality is now discharged by
  direct demonstration (§2), and rule 2 no longer prefers A.
- A's payoff (Moderate, 5/10) is honest about its ceiling: a truthful
  dependency graph, no module simplification. The dissent is right that
  this under-fills a full campaign when the repo's pre-identified P1
  structural debt (`TODO.md` B2) is verifiably executable.
- A is not discarded: it is small, well-understood, fully scoped, and
  its evidence does not age. It remains the natural fallback goal (see
  revisit conditions 1–2) or a future hygiene-pass candidate.

Goal C remains third, unchanged from attempt 1: it is A plus the one
assumption in the record that **cannot** be discharged at preflight (the
`generator.py`/golden-test redirect is dischargeable only by executing
its slice 4 — ledger §5), and the browser evidence does nothing to cure
that. Rule 2 still bars C while A exists as its verifiable subset.

## 5. Conditions under which this arbitration should be revisited

1. **Browser gate regresses before slice 1.** If the stage-1 preflight
   re-run of `pytest tests/test_web_browser.py -m browser_acceptance` is
   red or unrunnable on unmodified `main` (environment drift: browser
   binaries, display, Playwright version), B's hard gate is gone and the
   selection returns to arbitration with A as the standing alternative.
2. **Move-only premise fails at planning.** If stage-1 falsification
   finds the `app.py` section seams entangled such that any slice cannot
   be a pure code move (semantic edits required to extract layout,
   handlers, or panel wiring), B's preservation-by-construction claim
   fails and all goals return to arbitration.
3. **Blast-radius premise breaks.** If planning finds importers of
   `app.py` internals beyond `cli/main.py:657` (e.g. monkeypatches or
   reach-ins into private helpers from tests or other packages that
   inspection missed), the Low blast-radius score is wrong and the
   selection should be re-examined.
4. **Operator re-weights toward minimum risk.** If the operator decides
   the first full campaign run should optimize for near-certain
   preservation over payoff (the smoke-test framing), A is the
   already-arbitrated alternative; its record needs no rework.

## 6. Notes for downstream lanes

- The decision record should carry forward proposal B's slice table and
  verification commands verbatim (proposal B §5), preserving the
  mandatory browser-acceptance gate for slices 4–5 — it is the goal's
  load-bearing preservation evidence, not optional belt-and-braces.
- Stage-1 preflight should: (a) re-run the browser suite on `main` at
  execution time and record the transcript (this arbitration's run ages
  the moment the environment changes); (b) verify `test_cli_serve.py`
  pins the generative-jobs-root resolution before slice 3, adding the
  one-line characterization test proposal B §6 describes if it does not;
  (c) run the non-web suite once without `[web]` extras to pin the
  extras-leak guard.
- The trame widget-construction-order risk (proposal B §9) is the main
  regression channel; slice diffs must stay move-only, and reviewers
  should treat any non-move edit in slices 4–5 as a stop-the-slice
  finding.
- Carry forward unchanged from attempt 1: the stale-evidence correction
  that root `generator.py` is a legacy adapter class, not a pure
  re-export (proposals A §6 and C §2, correcting the brief's C6 wording),
  so future briefs do not repeat it.
- Dissent should probe hardest at: (a) whether one demonstrated green
  run constitutes sufficient evidence that the browser gate will hold
  across five slices, and (b) whether slices 1–3 carry enough
  independent verification to land if the environment degrades mid-
  campaign (they do per proposal B §5 — headless suites gate them — but
  the dissent lane should check that reading).
