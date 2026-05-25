# Review prompt — workflow 0037

You are reviewing the implementer's inline-help additions that
close audit batch R2 (AUD-O-001/002/003/004/006 + AUD-O-007 in-app
copy) from the 2026-05-25 release_candidate audit.

Read in order:

1. `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md` batch R2.
2. `docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`
   for the finding IDs.
3. `docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/PATCH_SUMMARY.md`
   — the implementer's report.
4. The three modified source files + the new test file.
5. `tests/test_web_layout.py` for the pre-existing layout-test
   contract that the new tests must not break.

## Acceptance criteria (verify each)

1. **AUD-O-001 (validity badge title).** `kayakgen/ui/web/app.py`
   adds a `validity_badge_title` (or equivalent) state field and
   binds it to the VChip. The four documented envelope states each
   produce a non-empty plain-text title. The new test
   `tests/test_web_inline_help.py::test_validity_badge_title_covers_all_states`
   exercises every state and asserts the title content.

2. **AUD-O-002 (comparison-source toggle subtitle).** The
   `ComparisonSourceToggle` (or surrounding markup) now carries a
   subtitle or per-button tooltip explaining `live_frontier` and
   `imported_report` in plain English. The test asserts the
   subtitle strings appear in the rendered HTML.

3. **AUD-O-003 (mesh chip-pair tooltip).** Both chips
   (`mesh-no-package-chip` and `mesh-live-readiness-chip`) carry a
   `v-tooltip` or `title=` attribute clarifying their independent
   meanings. The test asserts both tooltips are present.

4. **AUD-O-004 (submit-button disabled reason).** The kind-aware
   VBtn binds `:disabled` to a derived `submit_disabled` state
   field; `aria-describedby` points at a visible span; the span
   renders `submit_blocking_reason` with `v-show="submit_disabled"`.
   The two tests
   (`test_submit_disabled_when_no_variables` and
   `test_submit_enabled_when_form_valid`) exercise both branches.

5. **AUD-O-006 (mesh-diagnostic labels).**
   `mesh_diagnostics_rows_from_state` emits operator-facing labels
   with embedded threshold guidance. No label contains a
   snake_case dict key as its primary user-facing text. The test
   `test_mesh_diagnostics_rows_have_operator_facing_labels` asserts
   no presentation label contains an underscore.

6. **AUD-O-007 (high-angle GZ alert copy).** The alert constant in
   `kayakgen/ui/web/app.py` no longer contains `RFC 0020` or
   `RFC 0024`. The new copy points at `kayakgen stability
   --high-angle-gz` and the Comparison-tab import. The test
   `test_high_angle_gz_alert_drops_rfc_citations` asserts this.

7. **Wire-payload stability (AUD-P-004 regression).** The test
   `test_build_spec_from_form_state_wire_payload_stable` constructs
   two states and asserts the returned dict shape is unchanged. This
   pins the audit's pipeline-integrity invariant.

8. **`hydro_rows_from_state` unchanged.** Verify with `git diff` (or
   the implementer's PATCH_SUMMARY) that
   `kayakgen/services/evaluation.py::hydro_rows_from_state` is
   untouched. That change belongs to workflow 0038.

9. **Scope discipline.** The implementer touched ONLY:
   - `kayakgen/ui/web/app.py`
   - `kayakgen/ui/web/generate_spec_form.py`
   - `kayakgen/services/evaluation.py` (only
     `mesh_diagnostics_rows_from_state` and adjacent helpers)
   - `tests/test_web_inline_help.py`
   - `docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/`

   No diffs on `CHANGELOG.md`, `docs/USER_GUIDE.md`,
   `docs/DECISION_LOG.md`, audit SYNTHESIS / REMEDIATION_PLAN /
   FINDINGS, `docs/audits/README.md`, `docs/rfcs/`,
   `kayakgen/ui/web/generate_frontier_view.py`,
   `kayakgen/ui/web/controllers.py`, or
   `kayakgen/ui/parameter_metadata.py`.

10. **Verification suite passes.** Run

    ```bash
    .venv/bin/pytest \
      tests/test_web_inline_help.py \
      tests/test_web_layout.py \
      tests/test_web.py \
      tests/test_ui_theme.py \
      tests/test_vocabulary_coverage.py \
      -q
    ```

    in the implementer's venv. All must pass.

## Operator-facing copy review (adversarial)

For each new tooltip / subtitle / reason string, ask: would a first-
time operator who has never read an RFC understand what to do? Flag
any leak of internal vocabulary (`claim_state`, `convergence_flag`,
RFC numbers, evaluator type names) in operator-facing copy. Flag
any tooltip that is shorter than the question it answers (e.g. a
tooltip just saying "Validity" tells the operator nothing).

## Artifact

Write
`docs/audits/2026-05-25-code-doc-audit/follow-ups/0037/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check
results (pass / fail with file:line evidence), copy-review notes,
and any deferrals.
