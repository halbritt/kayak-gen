author: findings-ledger-codex-gpt-5.5-001

# Findings Ledger — Workflow 0059 RFC 0065 Slice 2

## Sources Reviewed

- `striatum/0059-rfc-0065-slice2-shell-layout/reviews/traceability/REVIEW.md`
- `striatum/0059-rfc-0065-slice2-shell-layout/reviews/claims/REVIEW.md`
- `striatum/0059-rfc-0065-slice2-shell-layout/reviews/ops_tests/REVIEW.md`
- `docs/workflows/0059-rfc-0065-slice2-shell-layout/SLICE_2_DECISIONS.md`

## Must-Fix Remediation Items

### M1 — Remove the Slice 3 focus-state application from the Slice 2 patch

Deduped from: traceability F1.

Remediation: remove the new `:focus-visible` rule group in
`kayakgen/ui/web/app.py` for `.kg-status-segment`, `.kg-toolbar-action`,
`.kg-variable-remove-btn`, and Generate variable-table `select` / `input`, or
otherwise revert this interaction-state application from the Slice 2 diff.

Decision cross-check: `SLICE_2_DECISIONS.md` D1 allows Slice 2 to consume the
Slice 1 `focus-ring` / state token vocabulary, but the out-of-scope section
explicitly defers "Control hover/focus/active/disabled states" to Slice 3. The
must-fix action is therefore to remove/defer the current Slice 3 behaviour, not
to expand or tune focus-state design in Slice 2.

### M2 — Add positive D3/D5 assertions for status-bar and Generate hook contracts

Deduped from: traceability F2, traceability F3, ops-tests F1.

Remediation: update `tests/test_web_layout.py` with positive assertions for:

- `data-testid="workspace-status-bar"`
- `data-testid="status-package"`
- `data-testid="status-readiness"`
- `data-testid="status-resistance"`
- `data-testid="status-cfd"`
- the render-site binding for `kg-generate-pick`
- `kg-generate-pick-action`, unless remediation removes that unused class

Decision cross-check: D3 requires the status-bar identity to survive, and D5
requires every renamed / moved / newly introduced internal hook to be reflected
in the same slice's tests. This is in-scope Slice 2 remediation because it
strengthens assertions for contracts Slice 2 already claims to preserve.

## Non-Blocking Successor Items

### S1 — Reintroduce uniform focus styling in RFC 0065 Slice 3

Source finding: traceability F1.

Pointer: RFC 0065 Slice 3; this would override the Slice 2 out-of-scope row in
`SLICE_2_DECISIONS.md` that defers "Control hover/focus/active/disabled states"
to Slice 3.

Successor note: once Slice 3 opens, apply the focus-ring and state tokens
uniformly to controls as part of the authorised control-state pass. Do not keep
the current partial Slice 2 `:focus-visible` implementation as a hidden
exception.

### S2 — Fix the pre-existing services/UI import-boundary violation in a follow-up hygiene workflow

Source finding: ops-tests F2.

Pointer: follow-up architecture / hygiene workflow, not RFC 0065 Slice 2. The
reported issue is `kayakgen/services/evaluation.py` importing
`HYDROSTATICS_ROW_METADATA` from `kayakgen.ui.hydrostatics_metadata`, causing
`tests/test_services_boundaries.py` to fail.

Decision cross-check: this file is not touched by the Slice 2 diff, and moving
the metadata registry into a lower-level package would create design scope
outside the presentation-only re-flow in D7 and outside the Slice 2 source list.
If final review requires a fully green repo-wide suite, the operator should
either open the follow-up workflow before final acceptance or explicitly record
that this unrelated pre-existing failure is outside Workflow 0059 remediation.

## Accepted Review Concerns Requiring No Action

### A1 — Claim-line and user-facing boundary checks are accepted as verified

Source: claims review findings 1-7 and traceability D6/D7 checks.

Decision cross-check: D6 and D7 are satisfied. `CHIP_SPECS` /
`CHIP_LABELS` / `CHIP_CLASSES` remain byte-stable, persistent captions remain
byte-stable, no raw/advisory chip is recoloured into the success palette, no
new `claim_state` / `Readiness` / `accepted_uses` literal or REST route is
introduced, and RFC 0033 forbidden-copy boundaries remain intact. No
remediation item is needed.

### A2 — Token-only styling and collapse-breakpoint tokenization are accepted as verified

Source: traceability D1/D4 checks and ops-tests F3 positives.

Decision cross-check: D1 and D4 are satisfied. The new
`DENSITY["collapse-breakpoint"]` token is additive, non-colour, and used to keep
the existing 960 px collapse breakpoint tokenized; the collapse hooks and
conservative mobile posture remain intact. No remediation item is needed.

### A3 — Determinism and basic repository hygiene checks are accepted as verified

Source: ops-tests F3.

Decision cross-check: no wall-clock sleeps were found in the core UI tests,
`git diff --check` passed, the orphan-literal lint passed, and the
forbidden-copy scan passed. No remediation item is needed beyond M1/M2.
