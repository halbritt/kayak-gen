---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Ops Review

Verdict: `accept_with_findings`.

I did not find an RFC/workflow scaffold contradiction, missing required context,
or unsafe condition that would make this impossible to send to the ledger. The
remaining issues are implementable code, test, documentation, and evidence gaps.
Under the clarified pre-implementation contract in
`docs/workflows/0035-high-angle-gz-generated-body-handoff/prompts/review_ops.md:9`,
those belong in `accept_with_findings`, not `needs_revision`.

# Findings

## High - RFC 0024 generated-body GZ handoff is not implemented yet

RFC 0024 requires `evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)`
to emit real kayak GZ only after a generated closed body passes diagnostic
gates, and to return unavailable output with warnings and no synthetic GZ values
when any gate fails
(`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:46`,
`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:58`). The same RFC
requires synthetic fixtures to be labeled `fixture_only` and excluded from
comparison, sweep, and UI stability claims
(`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:62`), and extends the
`GZCurve` JSON contract with `body_ref`, body type, diagnostic ref, heel grid,
assumptions, warnings, and summary metrics
(`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:69`,
`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:124`).

Current stability code still exposes the older boundary: `evaluate_gz_curve()`
ignores all arguments and raises `GZNotImplementedError` with
`closed_volume_body_not_defined`
(`kayakgen/eval/stability.py:501`). The serialized `GZCurve` model still has
only `angles_deg` and `gz_m` (`kayakgen/eval/contract.py:109`), and
`StabilityResult` can only carry that minimal optional curve under the current
initial/equilibrium stability read model (`kayakgen/eval/contract.py:241`).
The test suite locks the old exception behavior instead of asserting RFC 0024
unavailable status, generated-body traceability, fixture-only labeling, or
summary metrics (`tests/test_stability.py:131`).

Generated closed-body APIs and diagnostics are now present
(`kayakgen/eval/closed_volume.py:300`,
`kayakgen/eval/closed_volume.py:366`), but the stability evaluator does not
consume `body_ref` or closed-volume diagnostics. The ledger should therefore
track an implementation slice that adds the generated-body validation boundary,
unavailable result shape, canonical warnings such as
`generated_closed_body_not_available`, `None` summary metrics for unavailable
results, and JSON-compatible optional fields for the extended `GZCurve`
contract.

## Medium - Fixture-only GZ summary provenance needs an explicit comparison guard

The current CLI, sweep, and web surfaces do not emit high-angle GZ metrics:
the CLI stability command writes only initial/equilibrium stability
(`kayakgen/cli/main.py:254`), sweep summaries include initial/equilibrium fields
but no secondary-stability metrics (`kayakgen/search/sweep.py:282`), and the web
review card labels high-angle GZ unavailable (`kayakgen/ui/web/app.py:205`,
`kayakgen/ui/web/app.py:1106`). That is the right current behavior.

The risk is at the future handoff boundary. `CandidateRecord.summary` is an
arbitrary dictionary (`kayakgen/search/sweep.py:96`), comparison promotes every
finite numeric summary key into candidate metrics
(`kayakgen/search/compare.py:213`), CLI objective parsing accepts arbitrary
metric names (`kayakgen/search/compare.py:94`), and comparison claim gating
currently recognizes resistance and design-fitness metrics only
(`kayakgen/search/compare.py:366`). A future fixture or hand-authored
`max_gz_m`, `GZ_max`, or similar numeric field could become a Pareto objective
without generated-body provenance unless the RFC 0024 slice adds an explicit
fixture-only exclusion/warning path.

Before any GZ fixture math or summary export lands, sweep/comparison records
should either omit fixture-only secondary-stability metrics from public metrics
or carry provenance that makes them ineligible for objectives and UI claims.
Add a regression test with a crafted candidate record containing fixture-only
GZ-like numeric fields to prove comparison does not treat them as real kayak
stability.

## Medium - High-angle deterministic and non-convergence coverage is absent

RFC 0024 requires deterministic curves over a declared heel grid for passing
generated-body fixtures, fixture-only math tests, unavailable behavior for
failed generated diagnostics, and exclusion from user-facing stability claims
(`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md:130`). RFC 0020 also
requires per-heel convergence or warnings and summary metrics derived from the
computed curve (`docs/rfcs/0020-high-angle-gz-secondary-stability.md:77`).

Current tests cover load-case serialization, design-waterline GM0,
upright/equilibrium trim behavior, the old `GZNotImplementedError`, and upright
non-convergence (`tests/test_stability.py:119`, `tests/test_stability.py:131`,
`tests/test_stability.py:206`, `tests/test_stability.py:269`). Closed-volume
tests cover synthetic diagnostic serialization and topology failure modes
(`tests/test_closed_volume.py:70`, `tests/test_closed_volume.py:126`). They do
not cover the RFC 0024 high-angle contract: declared heel-grid echoing,
diagnostic failure returning unavailable status, fixture-only labels, missing
heel-point warnings, per-heel non-convergence, or derivation of summary metrics
from `gz_m`.

The ledger should require focused tests for unavailable generated-body refs,
synthetic fixture-only outputs, deterministic generated-body fixture curves,
summary metric derivation, non-convergence warnings, and JSON round trips for
the extended GZ fields.

# Clean Checks

- The current evaluator does not emit placeholder high-angle values:
  initial/equilibrium paths set `gz_curve=None`, and the explicit GZ function
  raises before returning data (`kayakgen/eval/stability.py:362`,
  `kayakgen/eval/stability.py:477`, `kayakgen/eval/stability.py:501`).
- Current CLI and web UI behavior hides high-angle output rather than presenting
  secondary-stability claims (`kayakgen/cli/main.py:254`,
  `kayakgen/ui/web/app.py:205`, `kayakgen/ui/web/app.py:1106`).
- Closed-volume diagnostics distinguish synthetic and generated body types and
  never promote them to `cfd_ready` (`kayakgen/eval/closed_volume.py:16`,
  `kayakgen/eval/closed_volume.py:265`, `kayakgen/eval/closed_volume.py:398`).
- No scaffold blocker was found in the review lane wiring: the review job is
  review-only, writes only the ops artifact, forbids `.striatum/`, and feeds the
  findings ledger (`docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json:112`,
  `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json:121`,
  `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json:219`).

# Evidence Reviewed

- Required workflow inputs: `AGENTS.md`,
  `docs/workflows/0035-high-angle-gz-generated-body-handoff/SOURCES.md`,
  `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json`, and
  `docs/workflows/0035-high-angle-gz-generated-body-handoff/prompts/review_ops.md`.
- Required RFC and implementation sources listed in `SOURCES.md`: RFCs 0011,
  0014, 0016, 0020, and 0024; `kayakgen/eval/closed_volume.py`;
  `kayakgen/eval/hydrostatics.py`; `kayakgen/eval/stability.py`;
  `kayakgen/cli/main.py`; `tests/test_closed_volume.py`; and
  `tests/test_stability.py`.
- On-demand ops surfaces for JSON/sweep/UI compatibility:
  `kayakgen/eval/contract.py`, `kayakgen/search/sweep.py`,
  `kayakgen/search/compare.py`, `kayakgen/ui/web/app.py`, and
  `tests/test_generated_closed_body.py`.
- One read-only helper pass independently rechecked verdict semantics,
  implementation findings, and scaffold blockers.

# Validation

- Static review used `sed`, `nl -ba`, `rg`, `find`, and `git status --short`.
- Focused tests were attempted with:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_stability.py tests/test_closed_volume.py`.
  They did not run because the environment has no installed `pytest` module.
- UI hiding was checked statically; no Trame/browser runtime was launched.
