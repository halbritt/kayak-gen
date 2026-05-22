# Pipeline-Integrity / Claim-Gate Audit — Findings

Date: 2026-05-22
Lane: Pipeline-integrity / claim-gate
Auditor: Claude Opus 4.7 (single-agent run; see SYNTHESIS.md for lane-diversity caveat)
Scope: `full_repo` preset, current `main` at commit f78e478
Sources of truth read: `kayakgen/eval/claims.py`, `kayakgen/eval/contract.py`,
`kayakgen/eval/stability/{accepted_fit,high_angle_contracts,evaluator}.py`,
`kayakgen/eval/cfd/{records,jobs,profiles}.py`,
`kayakgen/eval/cfd/adapters/{openfoam_v2512,fixture}.py`,
`kayakgen/services/generative_jobs.py`,
`kayakgen/ui/web/{generate_frontier_view,generate_spec_form,read_models}.py`,
`tests/test_resolve_analytical_claim_label.py`,
`tests/test_high_angle_stability_evaluator.py`,
`tests/test_vocabulary_coverage.py`,
`tests/test_stability.py`.

## Findings

### AUD-P-001: `GZCurve.result_semantics` Literal is too narrow for RFC 0058 stage 4 promotion

severity: high
category: claim_gate
status: open
claim: The base `GZCurve.result_semantics` field is declared as
`Literal["unvalidated_hydrostatic_comparison"] | None`, but RFC 0058 stage 2
defines `AnalyticalClaimLabel = Literal["unvalidated_*", "validated_*"]` and
the subclass `GeneratedBodyGZCurve` widens the field to that union. When stage 4
lands a non-empty `fit_registry`, the resolver can return
`"validated_hydrostatic_comparison"`, and any code path that serializes a
`GeneratedBodyGZCurve` and reads it back through the parent `GZCurve` (which is
what `StabilityResult.gz_curve: GZCurve | None` does) will hit a Pydantic
validation error.
evidence:
- `kayakgen/eval/contract.py:175` — `result_semantics: Literal["unvalidated_hydrostatic_comparison"] | None = None`
- `kayakgen/eval/stability/high_angle_contracts.py:24-27` — `AnalyticalClaimLabel = Literal["unvalidated_hydrostatic_comparison", "validated_hydrostatic_comparison"]`
- `kayakgen/eval/stability/high_angle_contracts.py:49` — `GeneratedBodyGZCurve.result_semantics: AnalyticalClaimLabel = "unvalidated_hydrostatic_comparison"`
- `kayakgen/eval/contract.py:397` — `StabilityResult.gz_curve: GZCurve | None`
- `tests/test_stability.py:156` — `EvaluationResult.model_validate_json(result.model_dump_json())` round-trip is exercised today; a stage-4 promotion would break it.
- `kayakgen/eval/stability/evaluator.py:385` — call site already uses `resolve_analytical_claim_label`; only the empty `fit_registry=()` keeps the failure latent today.
impact: Latent breakage of the stage-4 graduation path RFC 0058 explicitly
names. The fix is one Pydantic Literal widening; not catching it now means the
first non-empty fit registry will land + immediately bounce on a round-trip
validation error in `StabilityResult` consumers.
recommended_action: Widen `GZCurve.result_semantics` to the
`AnalyticalClaimLabel` union, add a regression test that round-trips a
`GeneratedBodyGZCurve(result_semantics="validated_hydrostatic_comparison")`
through `StabilityResult` and `EvaluationResult`.
follow_up: source/test work (small slice; can be a single workflow because it
touches one schema literal + one test).

### AUD-P-002: `cfd_in_loop_evaluator_status` is wired with `registry=()` in three sites; intentional but unauditable

severity: low
category: claim_gate
status: open
claim: RFC 0058 stage 2/3 defines `resolve_analytical_claim_label` and
`cfd_in_loop_evaluator_status` and notes (D039) that "defaults stay byte-stable
with an empty fit registry." Today there is no registry loader anywhere in
`kayakgen/`. The three call sites all pass `fit_registry=()` or
`registry=()` literally. There is no comment or assertion documenting that the
empty registry is the intentional default until D007/D014 physical rig data
arrives.
evidence:
- `kayakgen/eval/stability/evaluator.py:385` — `result_semantics = resolve_analytical_claim_label(hull, fit_registry=())`
- `kayakgen/ui/web/generate_frontier_view.py:558` — `fit_registry=()`
- `kayakgen/ui/web/generate_spec_form.py:832` — `status = cfd_in_loop_evaluator_status(registry=(), hull_scope=scope)`
- `grep "load.*fit_registry\|StabilityFitRegistry\|load.*StabilityFit"` returns no results in `kayakgen/` or `tests/`.
- `tests/test_high_angle_stability_evaluator.py:40` — comment "The resolver is wired at the construction site with fit_registry=();" acknowledges the shape but no test pins the contract.
impact: A reader trying to understand the stage-4 promotion path has to follow
the breadcrumb through D039 to figure out the empty tuple is intentional. A
future maintainer adding a fit registry can easily miss one of three sites and
land an inconsistent promotion state.
recommended_action: Add a single shared constant (e.g.
`EMPTY_STABILITY_FIT_REGISTRY` exported from
`kayakgen.eval.stability.accepted_fit`) with a one-line docstring naming D039
and the stage-4 graduation gate; replace all three literal `()` call sites
with the constant.
follow_up: docs / source clarity (touches three lines + one constant +
docstring).

### AUD-P-003: `tests/test_vocabulary_coverage.py` does not cover RFC 0057/0058 schema-level aggregates

severity: medium
category: test_gap
status: open
claim: The vocabulary-coverage regression test only checks `ClaimState`,
`SourceUse`, `SourceReviewVerdict`, six readiness literals, and an explicit
`_DECISION_TOKENS` tuple. It does not cover new aggregate-root types like
`GenerativeJob`, `StabilityFitRecord`, `cfd_in_loop_evaluator_status`, or
`MeasuredStabilityFixture`. The glossary already has parallel entries for
`AcceptedFitRecord` / `TankTestCampaign` / `IncliningTestRun`, so the pattern
exists — the regression net just hasn't been extended.
evidence:
- `tests/test_vocabulary_coverage.py:18` — imports limited to `SourceReviewVerdict, SourceUse, ClaimState`.
- `tests/test_vocabulary_coverage.py:58-65` — `_READINESS_LITERALS` is a hand-maintained tuple.
- `tests/test_vocabulary_coverage.py:73-80` — `_DECISION_TOKENS` is hand-maintained.
- `docs/UBIQUITOUS_LANGUAGE.md` — does not contain `GenerativeJob`, `StabilityFitRecord`, `cfd_in_loop_evaluator_status`, or `MeasuredStabilityFixture` (verified via grep).
impact: Glossary drift can grow silently. The same shape that protected
`AcceptedFitRecord` / `ResistanceFitStatus` is missing for the RFC 0057/0058
generation of schemas.
recommended_action: Extend `_DECISION_TOKENS` with `GenerativeJob`,
`StabilityFitRecord`, `cfd_in_loop_evaluator_status`,
`StabilityFixturePromotionPacket`, and the resolver return labels; land the
matching glossary rows in the same patch.
follow_up: source/test work + docs fix (single coherent slice).

### AUD-P-004: `runs jobs` CLI surface is not pinned by a vocabulary or schema test

severity: low
category: test_gap
status: open
claim: RFC 0057 stage 4 introduces `GenerativeJob` records with a state
vocabulary (`queued/running/succeeded/failed/cancelled/resumable`) and a
public CLI surface (`kayakgen runs jobs --state ...`). The user-guide
documents the state list at `docs/USER_GUIDE.md:477`. There is no regression
test that pins the user-facing state vocabulary against the source enum, so
adding or renaming a state can silently break operator workflows that filter
on `--state cancelled`.
evidence:
- `docs/USER_GUIDE.md:477` — documents the six-state list.
- `kayakgen/services/generative_jobs.py` — defines the state Literal (search
  for `state:`).
- `grep "GenerativeJob.*state\|generative_job_state"` in `tests/` — no
  literal-coverage test for the documented vocabulary.
impact: Low. The user-guide already declares the vocabulary; if it drifts
from source, operators silently lose CLI filters.
recommended_action: Add a small test that asserts the documented six-state
list is exactly `get_args(GenerativeJobState)` (or the equivalent literal).
follow_up: test coverage.

### AUD-P-005: No null findings — claim_state contract on the CFD side is internally consistent

severity: info
category: claim_gate
status: open
claim: The CFD side of the pipeline pins `claim_state="raw_unvalidated"` /
`result_semantics="raw_unvalidated"` consistently across records, adapters,
profiles, and parsers (15+ Pydantic Literal pins). The `RawUnvalidatedClaimFields`
base in `kayakgen/eval/claims.py:104` enforces "no accepted uses, no fixture
ids, no fit evidence, no validity envelope" on any record that inherits it.
The opt-in chain (RFC 0046 three mechanisms) is consistent at the source
level; the operator-facing documentation gap is owned by Lane 3.
evidence:
- `kayakgen/eval/cfd/records.py:108,129,172,223` — every CFD record literal-pins `raw_unvalidated`.
- `kayakgen/eval/cfd/adapters/openfoam_v2512.py:113,127,158` — same.
- `kayakgen/eval/cfd/adapters/fixture.py:76,103,132` — same.
- `kayakgen/eval/claims.py:104-129` — `RawUnvalidatedClaimFields._raw_claim_must_not_promote` validator.
- `tests/test_cfd_jobs.py:162,250,...` — 20+ assertions pin the literal.
impact: No action required. Recording the null finding so future audits can
confirm the contract is intact rather than re-derive the same evidence.
recommended_action: None.
follow_up: wontfix (null finding by intent).
