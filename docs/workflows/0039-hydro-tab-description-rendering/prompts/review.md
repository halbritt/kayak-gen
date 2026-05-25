# Review prompt — workflow 0039

You are reviewing the implementer's Hydro-tab description tooltip
rendering that closes audit batch R2 (AUD-O-003) from the
2026-05-25 full_repo audit.

Read in order:

1. `docs/audits/2026-05-25-full-repo-code-doc-audit/REMEDIATION_PLAN.md`
   batch R2.
2. `docs/audits/2026-05-25-full-repo-code-doc-audit/operator-adoption/FINDINGS.md`
   AUD-O-003.
3. `docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/PATCH_SUMMARY.md`
   — the implementer's report.
4. The modified source files + new test file.
5. `kayakgen/ui/hydrostatics_metadata.py` — the registry (read-only).

## Acceptance criteria (verify each)

1. **`hydro_rows_from_state` widening.** The function emits
   `{"label", "value", "description"}` dicts. Each registered
   row's `description` matches
   `HYDROSTATICS_ROW_METADATA[id].description` exactly. Warning
   rows carry `""`.

2. **Approach choice consistency.** PATCH_SUMMARY documents
   whether approach (a) 4-tuple or (b) inverse lookup was used.
   Verify any downstream consumer of
   `analysis_view_model["hydro_rows"]` (specifically
   `hydro_lines_from_state` in `evaluation.py:420`) was updated
   to match.

3. **Hydro tab template renders description.**
   `kayakgen/ui/web/app.py` Hydro-tab `<tr v-for>` carries a
   tooltip activator (`:title='row.description'` OR a `v-tooltip`
   slot) such that each registered row's description appears in
   the rendered HTML.

4. **Empty-description suppression.** Warning rows (whose
   description is `""`) do not render a misleading non-empty
   tooltip. Browser convention is that `title=""` renders no
   tooltip; if `v-tooltip` was used, verify the activator is
   suppressed when description is empty.

5. **Byte-stable widening test.**
   `tests/test_hydrostatics_row_metadata.py::test_hydro_rows_from_state_byte_stable`
   asserts the full `{label, value, description}` shape. Labels
   list unchanged. Descriptions asserted against the registry
   (not as a frozen string fixture; this lets registry edits land
   in the same diff).

6. **Render-verification test.**
   `tests/test_hydro_tab_descriptions.py` iterates the registry
   and asserts each description appears in the rendered HTML.

7. **`build_spec_from_form_state` untouched.** `git diff` shows
   no edits to `kayakgen/ui/web/generate_spec_form.py`.

8. **`analysis_view_model` return shape.** Top-level dict keys
   unchanged. If approach (a) was used, `hydro_rows` widened
   from 3-tuple to 4-tuple; verify this is the only structural
   change to the function and `hydro_lines_from_state` was
   updated to match.

9. **Scope discipline.** The implementer touched ONLY:
   - `kayakgen/services/evaluation.py`
   - `kayakgen/ui/web/app.py`
   - `tests/test_hydrostatics_row_metadata.py` (extended)
   - `tests/test_hydro_tab_descriptions.py` (new)
   - `docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/`

   No diffs on: `CHANGELOG.md`, `docs/USER_GUIDE.md`,
   `docs/DECISION_LOG.md`, audit SYNTHESIS / REMEDIATION_PLAN /
   FINDINGS, `docs/audits/README.md`, `docs/rfcs/`, the SPEC /
   PRD / ROADMAP / ARCHITECTURE_MAP / UBIQUITOUS_LANGUAGE /
   WEB_VERIFICATION docs,
   `kayakgen/ui/hydrostatics_metadata.py`,
   `kayakgen/ui/parameter_metadata.py`,
   `kayakgen/ui/web/generate_spec_form.py`,
   `kayakgen/ui/web/generate_frontier_view.py`,
   `kayakgen/ui/web/controllers.py`,
   `kayakgen/ui/desktop.py`,
   `kayakgen/ui/desktop_slider_ranges.py`,
   `kayakgen/ui/gui_params.py`.

10. **Verification suite passes.** Run

    ```bash
    .venv/bin/pytest \
      tests/test_hydro_tab_descriptions.py \
      tests/test_hydrostatics_row_metadata.py \
      tests/test_web_inline_help.py \
      tests/test_web_layout.py \
      tests/test_web.py \
      -q
    ```

    in the implementer's venv. All must pass.

## Artifact

Write
`docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check
results (pass / fail with file:line evidence), and any deferrals.
