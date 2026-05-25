# Review prompt — workflow 0038

You are reviewing the implementer's RFC 0062 +
`HydrostaticsRowMetadata` registry that close audit batch R3
(AUD-O-005) from the 2026-05-25 release_candidate audit.

Read in order:

1. `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md` batch R3.
2. `docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`
   AUD-O-005.
3. `docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/PATCH_SUMMARY.md`
   — the implementer's report.
4. `kayakgen/ui/hydrostatics_metadata.py` (new).
5. `kayakgen/services/evaluation.py` (the `analysis_view_model`
   edit specifically).
6. `tests/test_hydrostatics_row_metadata.py` (new).
7. `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (new).
8. `docs/rfcs/README.md` (one-row diff).
9. `kayakgen/ui/parameter_metadata.py` — the sibling registry the
   implementer mirrors (read-only for this workflow).

## Acceptance criteria (verify each)

1. **Registry shape mirrors RFC 0060.** The new file defines
   `HydrostaticsRowMetadata` as a frozen Pydantic model with
   `parameter`, `label`, `unit`, `description` fields, matching
   `HullParameterMetadata`. The registry covers exactly the seven
   expected keys (`displacement`, `wetted_surface`,
   `waterplane_area`, `gm0`, `cp_actual`, `cm_actual`,
   `l_over_bwl`).

2. **`analysis_view_model` wiring.** The function in
   `evaluation.py` no longer contains the seven hardcoded
   `("Displacement", ...)` tuples; the labels and units come from
   the registry. The numeric value formatting is unchanged.

3. **`analysis_view_model` return shape.** The function still
   returns a dict with the same top-level keys (`hydro_rows`,
   `resistance_rows`, `design_warnings`, `design_validity`,
   `resistance_warnings`, `warnings`, `resistance_metadata`) and
   the `hydro_rows` value is still a list of `(label, value,
   unit)` 3-tuples.

4. **`hydro_rows_from_state` byte-stable.** The regression test
   `test_hydro_rows_from_state_byte_stable` pins the post-refactor
   output against the b82b544 baseline. Verify the expected list
   in the test matches what the post-refactor source produces.

5. **`mesh_diagnostics_rows_from_state` unchanged.** Verify with
   `git diff kayakgen/services/evaluation.py` that the function
   body is untouched by this workflow.

6. **Registry coverage test.** The test asserts every key
   `analysis_view_model` uses is present in the registry, matching
   the `test_hull_parameter_metadata.py` regression-net shape.

7. **RFC 0062 internal consistency.** Status `landed`, Date
   `2026-05-25`, Context cites RFC 0060 + RFC 0061 + D043 + audit
   AUD-O-005, Problem narrates the audit finding, Proposal
   matches the landed code, Acceptance names the regression test
   as the discipline gate. The RFC is between 1500 and 4000 words
   (rough heuristic for the project's RFC density).

8. **`docs/rfcs/README.md` row.** The new row is placed after
   0061, follows the existing column shape, states `landed` + the
   one-line topic.

9. **Scope discipline.** The implementer touched ONLY:
   - `kayakgen/ui/hydrostatics_metadata.py` (new)
   - `kayakgen/services/evaluation.py` (only `analysis_view_model`)
   - `tests/test_hydrostatics_row_metadata.py` (new)
   - `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (new)
   - `docs/rfcs/README.md` (one-row diff)
   - `docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/`

   No diffs on `CHANGELOG.md`, `docs/USER_GUIDE.md`,
   `docs/DECISION_LOG.md`, audit SYNTHESIS / REMEDIATION_PLAN /
   FINDINGS files, `docs/audits/README.md`, `docs/SPEC.md` /
   `docs/PRD.md` / `docs/ROADMAP.md` / `docs/ARCHITECTURE_MAP.md`
   / `docs/UBIQUITOUS_LANGUAGE.md`,
   `kayakgen/ui/parameter_metadata.py`,
   `kayakgen/ui/web/`,
   `kayakgen/ui/desktop.py`,
   `kayakgen/ui/desktop_slider_ranges.py`, or
   `kayakgen/ui/gui_params.py`.

10. **Verification suite passes.** Run

    ```bash
    .venv/bin/pytest \
      tests/test_hydrostatics_row_metadata.py \
      tests/test_hull_parameter_metadata.py \
      tests/test_web_layout.py \
      tests/test_vocabulary_coverage.py \
      -q
    ```

    in the implementer's venv. All must pass.

## RFC review (adversarial)

For RFC 0062, ask: does it describe what landed? Does it cite the
audit finding correctly? Does it explain why a registry beats the
hardcoded tuples? Does the Non-Goals section explicitly defer the
mesh-tab and resistance-row registries to future passes? Are the
Open Questions section's deferred items the right scope (i.e. not
already obviously needed by the next audit)?

## Artifact

Write
`docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check
results (pass / fail with file:line evidence), and any
deferrals.
