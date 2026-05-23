# Review prompt — workflow 0035

You are reviewing the implementer's two new render-verification tests
that close audit batch R4 (AUD-O-009 and AUD-O-010) from the
2026-05-23 release_candidate audit.

Read in order:

1. `docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md` batch R4.
2. `docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md`
   for the two finding IDs.
3. `docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/PATCH_SUMMARY.md`
   — the implementer's report.
4. The two new test files.
5. The source modules they exercise (read-only for this workflow):
   `kayakgen/ui/parameter_metadata.py`,
   `kayakgen/ui/web/generate_spec_form.py`,
   `kayakgen/ui/desktop.py`.

## Acceptance criteria (verify each)

1. **`tests/test_generate_panel_label_rendering.py` exists** and
   actually inspects the rendered widget arguments (not the form-state
   defaults alone, and not a source-string regex over the form-builder
   file). The load-bearing check is that some hook captures the
   `v3.VTextField.__init__` call arguments (or an equivalent
   render-tree traversal) and asserts the `hint` kwarg equals
   `description(key)` for every `BASE_HULL_KEYS` entry.

2. **AUD-O-009 regression coverage.** If a hypothetical future patch
   dropped the `:hint=` wiring on the base-hull rail
   `VTextField` (e.g. by removing the `hint=description(_hull_key) or ""`
   keyword in `render_spec_form_section`), the new test must fail.
   This is the audit's core ask. Sanity check: the assertion is on the
   captured-call dict, not on the state-seeded values.

3. **State-seeded picklist checks present.** The new test also
   asserts that `web.state.generative_objective_picklist_items` and
   `web.state.generative_variable_picklist_items` carry the registry-
   sourced titles (per the per-item shape documented in the
   implement prompt). These are the upstream truth value the Vue
   template renders from.

4. **`tests/test_desktop_slider_labels.py` exists** and constructs a
   real `KayakGUI()` headlessly, then asserts each
   `gui.sliders[key].label.get_text()` equals `label_with_unit(key)`
   for every row in `KayakGUI.SLIDERS`.

5. **AUD-O-010 regression coverage.** If a hypothetical future patch
   replaced the registry-sourced `label_with_unit(key)` call with a
   stale hardcoded literal, the new test would fail (either via the
   `KayakGUI.SLIDERS`-iterating assertion or via one of the three
   named spot checks for `Cp`, `length_m`, and `target_speed_kt`).

6. **Scope discipline.** The implementer touched ONLY
   `tests/test_generate_panel_label_rendering.py`,
   `tests/test_desktop_slider_labels.py`, and files under
   `docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/`. No diffs
   on `CHANGELOG.md`, the RFC sources, the audit `FINDINGS.md` files,
   `docs/DECISION_LOG.md`, or any of the three read-only production
   modules.

7. **Verification suite passes.** Run

   ```bash
   .venv/bin/pytest \
     tests/test_generate_panel_label_rendering.py \
     tests/test_desktop_slider_labels.py \
     tests/test_web_layout.py \
     tests/test_desktop_layout.py \
     tests/test_hull_parameter_metadata.py \
     tests/test_generate_spec_form.py \
     -q
   ```

   in the implementer's venv. All must pass.

## Scope check

The implementer MUST NOT have touched `CHANGELOG.md`,
`docs/rfcs/0060-*.md`, `docs/rfcs/0061-*.md`, `docs/rfcs/README.md`,
`docs/DECISION_LOG.md`, the audit `FINDINGS.md` files, or any of
`kayakgen/ui/parameter_metadata.py`,
`kayakgen/ui/web/generate_spec_form.py`,
`kayakgen/ui/desktop.py`. Flag any drift.

## Artifact

Write
`docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check results
(pass / fail with file:line evidence), and any deferrals.
