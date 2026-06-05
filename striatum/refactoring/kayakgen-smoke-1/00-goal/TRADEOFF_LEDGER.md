# Tradeoff Ledger — kayakgen-smoke-1 Goal Selection

author: tradeoff-ledger-claude-001

Date: 2026-06-05
Inputs: `PROBLEM_BRIEF.md` (§4 fixed dimensions), `proposals/GOAL_{A,B,C}.md`,
`scorecards/SCORECARD_{A,B,C}.md`.
Role: normalize proposals and scorecards onto one scale, record
disagreements, carry forward each goal's biggest unverified assumption.
This ledger selects nothing; it is evidence for arbitration.

---

## 1. Goals at a glance

| Goal | Title | Brief candidate | Proposal author | Scorecard author |
|---|---|---|---|---|
| A | Retire internal traffic through compatibility shims (excludes `generator.py` importers) | C6 (narrowed) | proposer-a-claude-001 | operator |
| B | Split `kayakgen/ui/web/app.py` (2,550 lines) along the Generate-panel seam | C1 | proposer-b-claude-001 | scorekeeper-agy-001 |
| C | Migrate in-package importers off shims, including `generator.py` redirect + boundary ratchet | C6 (full) | proposer-c-claude-001 | operator |

---

## 2. Score ledger

One row per goal per dimension. Scores are the scorecards' raw values
(label + numeric); justifications are condensed to one line from the
scorecard's own reasoning. Note the mixed scale direction: low raw scores
are favorable on `blast_radius` and `frozen_surface_risk`; high raw scores
are favorable on the other four dimensions. Values are reproduced raw, not
re-oriented.

| Dimension | Goal | Scorecard score | One-line justification (from scorecard) |
|---|---|---|---|
| preservation_verifiability | A | Very High (9/10) | Shims are pure re-exports, so redirects bind identical objects; existing suite plus a mechanical identity check verify completeness. |
| preservation_verifiability | B | High (8/10) | 4,798 lines of web tests across 9 files (incl. Playwright) pin layout and behavior; external surface is only `create_app`/`KayakgenApp`. |
| preservation_verifiability | C | High (8/10) | `jobs`/`high_angle_gz` shims are pure re-exports, but `generator.py` is not; the golden-test redirect needs the slice-1 characterization gate before edits. |
| blast_radius | A | Low (2/10) | Static import lines only, across 10 files; shims untouched; no functional code or public endpoints edited. |
| blast_radius | B | Low (3/10) | Confined to `kayakgen/ui/web/`; sole cross-package touch is one private import in `cli/main.py:657`, easily redirected. |
| blast_radius | C | Low (2/10) | Static import lines only, across 12 files; shims untouched; no functional code or public endpoints edited. |
| payoff | A | Moderate (5/10) | Truthful dependency graph and de-risked future refactors; no module simplification, no user-visible change. |
| payoff | B | Very High (9/10) | Decomposes the repo's largest module; layout, handlers, and the growing Generate-panel become focused, separately reviewable files. |
| payoff | C | Moderate (6/10) | Same truthful-graph payoff as A, plus the boundary ratchet test makes regression of the end-state impossible. |
| reversibility | A | Very High (10/10) | Non-functional import-block edits; whole goal or any slice rolls back with one git command, no stale state. |
| reversibility | B | High (8/10) | Five distinct move-only slices, each independently landable and rollback-able via standard git operations. |
| reversibility | C | Very High (10/10) | Import-line edits plus additive test rules; one-commit revert per slice, no stale state or schema changes. |
| frozen_surface_risk | A | Low (2/10) | Adjacent to the alias surface but never edits shims; zero proximity to schemas, claim vocabulary, or golden STL. |
| frozen_surface_risk | B | Low (2/10) | Web layer owns no schemas, claims, or golden files; the only touchpoint is the redirectable private import. |
| frozen_surface_risk | C | Low (2/10) | Adjacent to the alias surface but never edits shims; zero proximity to schemas, claim vocabulary, or golden STL. |
| sliceability | A | Very High (9/10) | Three independent, risk-ascending slices, each separately landable, linted, and verified. |
| sliceability | B | Very High (9/10) | Five logical move-only slices forming a step-by-step path, each "separately verifiable by the unit tests" (but see disagreement B-1). |
| sliceability | C | Very High (9/10) | Five risk-ascending slices, each separately landable and verifiable "without sequence constraints" (but see disagreement C-2). |

---

## 3. Disagreements between self-assessment and scorecard

Recorded, not resolved.

### Goal A — proposal carries explicit self-scores (§9)

- **A-1 · preservation_verifiability**: proposal self-rates "maximal";
  scorecard awards 9/10 (Very High), one notch below maximal, without
  stating what withholds the last point.
- **A-2 · sliceability**: proposal self-rates "high"; scorecard rates
  *higher* — Very High (9/10).
- All other dimensions align (blast radius "10 files, import statements
  only"; payoff "moderate"; reversibility "trivial"; frozen risk "low by
  construction").

### Goal B — proposal has no numeric self-assessment; compared against its stance text

- **B-1 · verification sufficiency**: proposal §7 declares this "the
  candidate with the *heaviest* verification profile" and makes browser
  acceptance a mandatory gate — a "stop-the-slice blocker" for slices 4–5
  if unrunnable. The scorecard's sliceability justification states each
  slice is "separately verifiable by the unit tests", which contradicts
  the proposal's own claim that slices 4–5 cannot be verified by unit
  tests alone.
- **B-2 · preservation conditionality**: scorecard preservation (8/10)
  says regressions are "readily caught"; the proposal states widget
  construction order is observable only end-to-end in the browser
  profile, making catchability conditional on the execution environment —
  a condition the scorecard moves to its assumption section rather than
  pricing into the score justification.

### Goal C — proposal has no numeric self-assessment; compared against its stance text

- **C-1 · preservation framing**: proposal claims "no semantic movement at
  all" / behavior-preserving by construction; the scorecard withholds the
  top mark (8/10) precisely because `generator.py` is *not* a pure
  re-export and the golden-test substitution is unverified until slice 4.
- **C-2 · sequence constraints**: scorecard sliceability says slices land
  "without sequence constraints"; the proposal imposes an explicit
  ordering — slice-1 characterization coverage must land before the
  slice-4 golden redirect (§8), and the slice-5 ratchet is by design
  last. The justification text and the proposal directly contradict.

---

## 4. Single biggest unverified assumption per goal

Carried forward verbatim in substance from each scorecard.

| Goal | Biggest unverified assumption |
|---|---|
| A | The opt-in OpenFOAM local execution environment (`KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 … test_openfoam_v2512_smoke.py`) is functional on the target runner; if not, integration verification of the case-render/provenance neighborhood in slice 1 degrades to dry-run unit tests. |
| B | The Playwright real-browser acceptance suite (`pytest tests/test_web_browser.py -m browser_acceptance`) can be executed and passes green in the executing environment; if the environment lacks Playwright or browser binaries, slices 4–5 are blocked (the proposal itself classifies this as a stop-the-slice blocker, not a waivable nicety). |
| C | `LoftedHullGeometry(Hull(defaults))` is a drop-in replacement for `KayakGenerator(defaults)` across all assertions in `tests/test_golden.py`; subtle differences in defaults, keyword handling, or downstream type checks could fail tests. Unverified until slice 4 (slice 1 narrows but does not discharge it). |

---

## 5. Normalization notes

Factual observations that affect cross-goal comparability; no ranking
implied.

- **A is a strict subset of C.** Both derive from brief candidate C6.
  C = A's internal redirects + the `generator.py`/golden-test redirect +
  a shim-equivalence characterization test + an import-boundary ratchet.
  Scorecard deltas between them: C trades −1 `preservation_verifiability`
  (9→8) for +1 `payoff` (5→6) relative to A; the other four dimensions
  are scored identically.
- **Scorecard provenance is not uniform.** Scorecards A and C are authored
  by `operator` and share near-verbatim justification text on
  `blast_radius` and `frozen_surface_risk`; scorecard B is authored by
  `scorekeeper-agy-001`. Absolute-score comparability is therefore
  stronger within {A, C} than between {A, C} and B.
- **Environment-dependence of assumptions differs in kind.** A's and B's
  assumptions (OpenFOAM smoke; Playwright profile) are pre-checkable
  before any slice lands by running the respective suite on `main`. C's
  assumption is only fully dischargeable by executing slice 4 itself.
- **Proposal A documents a stale-evidence correction to the brief**
  (§6: root `generator.py` is an adapter class, not a pure re-export
  shim) that proposal C independently confirms (§2) and the brief's C6
  wording does not reflect. The A-vs-C scope split on `generator.py` is a
  deliberate, opposed pair of scoping decisions on the same fact.
