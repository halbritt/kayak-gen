author: reviewer-claude-opus-4.7-001

workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
role: reviewer
lane: claude
posture: ergonomics_dx
target: docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md

# REVIEW — design (ergonomics_dx, claude lane)

## Decision

`accept_with_findings`

The synthesized design is operator-discoverable end-to-end. The CLI
shape has a single canonical sub-app (§A), the breaking signature
change on `accept-fit` is explicitly called out with a Typer-side
migration plan (§A.3 lines 214-219), the `claim-status` JSON exposes
`dropped_fit_count` so operators learn from non-debug output when
the registry rejected a fit (§A.4 lines 238, 242-244), every
`REASON_*` constant has an `next_action` template encoded as a
module-level mapping (§E.3 lines 608-628), and the USER_GUIDE
explicitly tells the operator that `intended_use` on the manifest
is a hint and that `promotion.json` is canonical (§E.2 lines
572-574). Two narrow findings below sit at follow-up grade.

## Posture-scoped findings (ergonomics_dx)

### Finding 1 — Surface B: `REASON_FIT_METRICS_OUT_OF_THRESHOLDS` next_action misleads in the tamper case

**Issue.** Gate 11 documents two distinct emergence paths for
`REASON_FIT_METRICS_OUT_OF_THRESHOLDS` — (a) blocked at construction
by `_strict_thresholds` (operator's recovery is to re-fit), and
(b) surfaced by the loader "only when bytes were tampered
post-acceptance" (operator's recovery is to re-accept from clean
inputs, not to re-fit). The §E.3 table emits one copy for both.

**Evidence.** §B.2 gate 11 lines 366-372: "Below-threshold metrics
on a `strict=True` record are blocked at construction by
`_strict_thresholds`; the loader surfaces
`REASON_FIT_METRICS_OUT_OF_THRESHOLDS` only when bytes were
tampered post-acceptance." §E.3 line 628:
`stability_fit_metrics_outside_default_thresholds → "tighten the
fit, or accept with strict=False for inspection only."`

**Impact.** An operator who sees this code from the loader (the
tamper case) reads the next_action and refits clean data, missing
the actual signal (someone or something edited the on-disk fit
JSON after acceptance). The provenance audit trail that §C.3
promises is undermined by a misleading recovery instruction.

**Suggested remediation.** Either (a) split into two codes —
`stability_fit_metrics_outside_default_thresholds` (construction)
and `stability_fit_metrics_tampered_post_acceptance` (loader) —
each with its own next_action; or (b) keep one code and emit a
two-line next_action that names both cases: "if from `accept-fit`,
tighten the fit or accept with `strict=False` for inspection
only; if from the loader, the on-disk fit JSON was edited after
acceptance — restore from git history and re-run `accept-fit`."
Splitting (option a) is cleaner.

### Finding 2 — Surface C: §C.5 leaves the analytical-only user-visible string unpinned

**Issue.** §C.5 names the two color tokens
(`unvalidated_hydrostatic_comparison_color` /
`validated_hydrostatic_comparison_color`) and the Generate-panel
`cfd_in_loop_evaluator_status` admonition graduating to
`first_class` only when both analytical and CFD-in-loop accepted
fits cover the hull. It does not say what the operator sees in
the panel when ONLY the analytical half flips (the load-bearing
new state for stage 4).

**Evidence.** §C.5 lines 465-473. The visible text the operator
reads at "analytical accepted but no CFD-in-loop accepted" is not
specified; the implementer must reverse-engineer it from the
existing `generate_frontier_view.py` admonition table.

**Impact.** The flip is the entire stage-4 deliverable from an
operator perspective. If the panel reads "comparative filter
only" or some other pre-existing copy that does not signal "your
fit accepted and the analytical claim flipped," the operator has
no in-product evidence that `accept-fit` succeeded — they have to
re-run `claim-status` to confirm. The ergonomics_dx posture
specifically asks "will the claim_state flip surface where the
operator will look?" and the panel is exactly where they look.

**Suggested remediation.** §C.5 should either (a) quote the
existing panel admonition copy for the analytical-only state and
confirm it carries the flip's evidence, or (b) call out that the
implementer must update the existing copy and name the file/line
where the copy lives. One sentence at the end of §C.5: "the
implementer verifies that the existing `cfd_in_loop_evaluator_status`
admonition for `analytical_validated` (or equivalent intermediate
state) tells the operator 'analytical hydrostatic comparison
validated; CFD-in-loop fit not yet available' or similar — and
updates the copy in `generate_frontier_view.py` if it does not."

## Open Questions adjudication

- **OQ-1:** agree with synthesizer disposition. Two CLI surfaces
  for the same write path is split vocabulary; one canonical
  sub-app keeps operator commands learnable.
- **OQ-2:** agree with synthesizer disposition. Co-locating
  `manifest.json` and `promotion.json` under one fixture directory
  is filesystem-discoverable; flag-only is opaque.
- **OQ-3:** agree with synthesizer disposition. Scan-on-load is
  zero-ceremony at the expected fit count; `rebuild-fit-index`
  would be operator burden for a non-problem.
- **OQ-4:** agree with synthesizer disposition. `claim-status` is
  the load-bearing read surface — without it, an operator who
  promotes a fixture has no direct command to confirm "yes the
  registry sees it."
- **OQ-5:** agree with synthesizer disposition. The DRY friction
  of requiring `--fixture-id` is softened by §E.3's explicit
  `fit_record_does_not_cite_fixture → "pass --fixture-id matching
  a fixtures[].fixture_id"` next_action.
- **OQ-6:** agree with synthesizer disposition. The
  `evaluator_version_mismatch` next_action in §E.3 ("runtime
  evaluator changed; re-run `accept-fit` to record the new
  version") gives the operator the exact recovery command.
- **OQ-7:** agree with synthesizer disposition. The third
  disposition (persist the packet at `promotion.json`,
  `intended_use` is a hint) is correct, and §E.2 lines 572-574
  now explicitly tell operators the manifest field is a hint —
  closing the ambiguity I would otherwise flag.
- **OQ-8:** agree with synthesizer disposition. The narrowed
  rule is unambiguous and `strict_check_skipped_blocks_acceptance`
  has a clear next_action ("re-fit with `strict=True`").
- **OQ-A / OQ-B / OQ-C:** agree with all three deferrals. No
  operator gap is opened by them in stage 4.

## Out-of-posture observations

- `out-of-posture: §B.2 gate numbering (1, 2, 3, 3a, 3b, 4, 5, …, 11) reads as if attempt-3 inserted 3a/3b and stopped; a flat 1–13 numbering would be easier for the implementer reading linearly. The reason codes themselves are unaffected.`
- `out-of-posture: §D test `test_accept_fit_refuses_below_strict_thresholds` says "Schema validator raises" — the implementer should clarify whether the test invokes the CLI (and asserts on the structured JSON refusal) or constructs an AcceptedFitRecord directly; the surrounding tests all invoke the CLI, so the inconsistency stands out.`
- `out-of-posture: §E.5 upgrade note covers existing fixtures whose manifest.json was mutated by stages 1-3 promote-fixture. Worth one extra sentence: "operators who want a clean on-disk surface can re-ingest the original manifest source JSON; ingest-rig-run refuses overwrite, so they must move the existing manifest.json aside first." Otherwise operators inherit the mutated bytes silently and the audit trail starts from a hint-mutated state.`
- `out-of-posture: §5 lines 699-708 record the codex resistance-side findings as out-of-scope with a follow-up DECISION_LOG.md row. Worth pinning the row's slug (e.g. D028 or similar) in the synthesis so the implementer's PR has a target identifier; "adds a row" without a number can land as a TODO that drifts.`
