---
schema_version: striatum.findings_ledger.v1
artifact_kind: findings_ledger
summary_count: 4
---

author: findings-ledger-codex-gpt-5.5-001
schema_version: striatum.findings_ledger.v1
kind: findings_ledger
logical_name: findings_ledger
workflow_id: 0056-rfc-0058-stage2-3-burndown
role: findings_ledger

# Workflow 0056 Findings Ledger

## Source Reviews

- `reviews/ops_tests/REVIEW.md` — needs revision with one medium must-fix finding.
- `reviews/traceability/REVIEW.md` — accepted with minor non-blocking successor findings.
- `reviews/claims/REVIEW.md` — accepted; no claim-boundary remediation.
- `prompts/final_review.md` — acceptance-preview cross-check used to keep must-fix scope tied to `STAGE_2_3_DECISIONS.md`.

## Must-fix Remediation Items

### MF-1: First-class CFD-in-loop hides the acknowledgement but serializer still requires it

**Origin:** `reviews/ops_tests/REVIEW.md`

**Decision / contract:** `STAGE_2_3_DECISIONS.md` D-14 says the Generate panel hides the explicit CFD-in-loop acknowledgement checkbox when `cfd_in_loop_evaluator_status(...)` returns `"first_class"`, while the evaluator toggle still renders. RFC 0058 says the acknowledgement is implicit in the graduated first-class label.

**Finding:** The render path hides the acknowledgement control for the `"first_class"` branch, but `build_spec_from_form_state()` still rejects every request with `generative_evaluators.cfd_in_loop=True` and `generative_cfd_in_loop_acknowledged=False`, without checking `generative_cfd_in_loop_status`.

**Risk:** Once the helper is patched or wired to return `"first_class"`, the UI can hide the only control that satisfies form serialization. A user who enables the first-class CFD-in-loop evaluator would then receive `cfd_in_loop_ack_required`, contradicting D-14's graduated branch.

**Required remediation scope:** Make the serializer acknowledgement gate conditional on the same status used by the render branch. Add a regression test where:

- `generative_cfd_in_loop_status == "first_class"`;
- `generative_evaluators.cfd_in_loop is True`;
- `generative_cfd_in_loop_acknowledged is False`;
- `build_spec_from_form_state()` accepts the request instead of raising `cfd_in_loop_ack_required`.

This is a behavior-consistency fix inside D-14. It does not authorize changes to RFC 0046's persistent opt-in API, new evaluator states, new claim-state literals, or real CFD-in-loop graduation evidence.

## Non-blocking Successor Items

### NB-1: Document the hidden legacy CLI compatibility shim

**Origin:** `reviews/traceability/REVIEW.md` F-1.

**Decision anchor:** D-9 names the new `kayakgen stability` sub-app and its four visible schema-only subcommands. The implementation also preserves the pre-existing `kayakgen stability <hull>` command as a hidden `legacy` subcommand through a narrow Typer group parse shim.

**Successor scope:** In a future docs or CLI cleanup workflow, extend D-9 or add a successor decision row recording that the prior top-level stability command is preserved as a hidden compatibility route, including its intended lifecycle.

**Why non-blocking:** The shim preserves existing CLI behavior, is hidden from the new sub-app surface, and does not add a new stability-calibration command or claim. Treating it as a must-fix would either break backwards compatibility or reopen D-9 after the traceability review accepted the choice.

### NB-2: Align `.gitignore` scope with the exact stability data directories

**Origin:** `reviews/traceability/REVIEW.md` F-2.

**Decision anchor:** D-12 names `data/stability/fixtures/` and `data/stability/fits/` as created-on-demand, uncommitted directories. The landed ignore pattern covers the parent `data/stability/`.

**Successor scope:** Either narrow the ignore pattern to the two named subdirectories or update the relevant docs/decision row to authorize the parent-directory ignore.

**Why non-blocking:** No current sibling under `data/stability/` exists, and the broader ignore pattern does not change runtime behavior, schema behavior, validation behavior, or public claims.

### NB-3: Record the stepped-clock test driver helper if the listener seam is documented further

**Origin:** `reviews/traceability/REVIEW.md` F-3.

**Decision anchor:** D-16 and D-17 authorize the opt-in `time_provider` / `clock_step` seam and stepped-clock tests. The implementation adds a public `tick_generate_state_listener` helper and re-exports `GENERATIVE_REFRESH_COALESCE_SECONDS` for deterministic tests.

**Successor scope:** If future docs describe the listener seam in detail, name the synchronous tick helper as the test driver for stepped-clock mode.

**Why non-blocking:** The helper is a mechanical enabler of D-16/D-17 and does not change production polling defaults. Existing wall-clock behavior remains covered.

## Closed / No-action Findings

### C-1: Claims and user-facing boundaries

**Origin:** `reviews/claims/REVIEW.md`.

**Disposition:** No action. The claims review found no claim-boundary findings. The workflow uses only RFC 0058's two analytical labels, keeps the default generated-body GZ label unvalidated with an empty registry, treats `opt_in_only` / `first_class` as evaluator-availability states rather than candidate claim states, and keeps the residual plot explicitly placeholder-backed.

### C-2: Traceability acceptance of settled stage 2 + 3 decisions

**Origin:** `reviews/traceability/REVIEW.md`.

**Disposition:** No action beyond NB-1 through NB-3. The review mapped all 21 decision rows to code or documentation evidence, confirmed D-21 deferrals remain absent, and accepted the workflow with only minor documentation/scope-record findings.

### C-3: Residual-plot refusal hardening

**Origin:** `reviews/ops_tests/REVIEW.md` coverage notes.

**Disposition:** No action in this remediation pass. A direct refusal test for `kayakgen stability residual-plot` would be useful hardening, but the reviewer records the command as indirectly covered by model validation and reports focused and full-suite verification passing. This does not block D-10 or D-11 acceptance.
