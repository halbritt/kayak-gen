author: findings-ledger-codex-gpt-5.5-001

# Workflow 0060 Findings Ledger

Source reviews:

- `striatum/0060-rfc-0065-slice3-states/reviews/traceability/REVIEW.md`
- `striatum/0060-rfc-0065-slice3-states/reviews/ops_tests/REVIEW.md`
- `striatum/0060-rfc-0065-slice3-states/reviews/claims/REVIEW.md`

Cross-check source of truth: `docs/workflows/0060-rfc-0065-slice3-states/SLICE_3_DECISIONS.md`.

## Must-fix remediation items

### MF-1 — Extend the forbidden-copy scrub to include the frontier render file

- Source finding: traceability F1.
- Slice decision: D6, with D4 as the claim-truthfulness invariant.
- Evidence: `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces` reads `generate_frontier_view.py` into `frontier_source` and adds it to `new_state_source`, but the actual no-go scrub still runs on `render_source`, which excludes `frontier_source`.
- Required remediation: run the forbidden/no-go scrub across the same rendered-string bundle that includes `frontier_source`, either by including `frontier_source` in `render_source` or by scrubbing `new_state_source`.
- Scope guard: do not change claim copy, state copy, no-go vocabulary, hooks, app behaviour, or frontier semantics. This is test coverage only.

Rationale: D6 says every new rendered string introduced by Slice 3 must be covered by the forbidden/no-go scan. The frontier loading/rendered strings are new Slice 3 rendered strings, so this is a hard-gate coverage gap even though the strings currently present are benign.

## Non-blocking successor items

### NB-1 — Pre-existing services import-boundary failure

- Source finding: ops/tests execution summary; also acknowledged in traceability out-of-scope notes.
- Pointer: follow-up hygiene workflow, not RFC 0065 Slice 3.
- Evidence: known NB-2 `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]` failure from workflow 0059.

Rationale: Slice 3 decisions explicitly mark this failure out of scope. The work-packet prompt also requires treating it as a non-blocking successor, not a Slice 3 remediation item.

### NB-2 — Per-row generative manager lookup efficiency

- Source finding: traceability O2.
- Pointer: later Generate-panel hygiene/performance follow-up, only if it becomes measurable.
- Evidence: the jobs table now calls `_generative_manager.get(job_id)` per row to surface `GenerativeJobError.kind`.

Rationale: This does not violate D3 or D7. D3 explicitly authorizes surfacing `GenerativeJobError.kind`; D7 only forbids new routes, evaluators, analysis surfaces, or claim literals. No Slice 3 remediation is required unless the pattern produces an observed performance issue.

## Accepted concerns requiring no action

### A-1 — Hover/active selectors are narrower than focus/disabled selectors

- Source finding: traceability O1.
- Decision cross-check: D1 requires uniform control states, with special emphasis on reintroducing the focus-ring / `:focus-visible` treatment uniformly after Slice 2 deferred it.
- Disposition: accepted as a review observation; no remediation item.

Rationale: The implemented hard gate is met for the focus and disabled states across buttons, tabs, fields, sliders, toggles, selects, inputs, textareas, and native buttons. Hover/active treatment remains token-sourced on direct button/tab/native controls while Vuetify field, slider, and selection-control internals retain their framework interaction behaviour. Requiring deeper hover/active restyling would risk expanding the presentation choice beyond the settled Slice 3 implementation unless a later visual/a11y pass records it as a concrete defect.

### A-2 — Ops/tests and claims reviews report the forbidden-copy scan as complete

- Source findings: ops/tests item 2; claims review section 5.
- Decision cross-check: D6.
- Disposition: accepted as passing context but superseded by the direct source check behind MF-1.

Rationale: The reviews correctly observed positive assertions for the new state strings, but those assertions are not the same as the no-go scrub. MF-1 is the deduplicated remediation item; no additional action is needed for the duplicate pass statements.

### A-3 — Claims, disabled-copy, hook, token-only, docs-footprint, and RFC 0032 boundary checks passed

- Source findings: all three reviews.
- Decision cross-check: D1-D5, D7, D8.
- Disposition: accepted; no remediation item.

Rationale: The reviews agree that claim/readiness copy remains byte-stable, disabled controls remain honestly disabled, new state hooks are positively asserted, styling is token-only, no new analysis boundary was opened, and the Slice 3 docs footprint stayed limited to `CHANGELOG.md` plus workflow reporting.
