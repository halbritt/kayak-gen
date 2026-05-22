# Implement prompt — workflow 0033

You are landing RFC 0060 (web Generate-panel form labels and tooltips).
Read the RFC first; it is the spec. Read `SOURCES.md` for the per-run
context manifest.

## Deliverables

1. **`kayakgen/ui/parameter_metadata.py`** — exactly per RFC 0060 §1
   (the `HullParameterMetadata` value object), §2 (the 11-row
   `HULL_PARAMETER_METADATA` registry), §3 (the helpers
   `label_with_unit` and `description`). Add a module-level `__all__`
   listing the exported names.

2. **`kayakgen/ui/web/generate_spec_form.py`** — wire the registry per
   RFC 0060 §4:
   - Import `label_with_unit`, `description`, and
     `HULL_PARAMETER_METADATA` from `kayakgen.ui.parameter_metadata`.
     `OBJECTIVE_METADATA` is already imported from
     `kayakgen.search.objectives`.
   - Build a new Trame state key `generative_variable_picklist_items`
     populated as
     `[{"value": p, "title": label_with_unit(p)} for p in BASE_HULL_KEYS]`
     (or the current variable-selector source if different).
   - Render each base-hull rail field's label with `label_with_unit(key)`
     and attach `description(key)` via Vuetify's `:hint` prop on the
     `<VTextField>` (one-line attribute change; tooltips are not
     required for the rail).
   - Replace the objectives picklist `items` prop with
     `[{"value": metric, "title": f"{label} ({unit})"}]` sourced from
     `OBJECTIVE_METADATA[metric].label` and `.unit`. Replace the inline
     `{{ metric }}` template token in the selected-objective row with
     a label-with-unit form via a helper state key (e.g.
     `generative_objective_metric_titles`).
   - The submission payload MUST stay byte-stable. Verify by reading
     the existing snapshot tests under `tests/test_generate_spec_form.py`
     before submitting — your changes must not alter what the form
     serializes.

3. **`tests/test_hull_parameter_metadata.py`** — per RFC 0060 §5:
   - Every key in `BASE_HULL_KEYS` (import from
     `kayakgen.ui.web.generate_spec_form`) has a
     `HULL_PARAMETER_METADATA` entry.
   - Every entry's `label`, `description`, and (if non-None) `unit` are
     non-blank trimmed strings.
   - Every key resolves to a `Hull` field name
     (`Hull.model_fields.keys()` from `kayakgen.model.hull.Hull`).
   - `label_with_unit("length_m") == "Length (m)"`,
     `label_with_unit("Cp") == "Prismatic coefficient (Cp)"`,
     `label_with_unit("unknown_param") == "unknown_param"`.

4. **`tests/test_vocabulary_coverage.py`** — add `HullParameterMetadata`
   to the parametric list that asserts presence in
   `docs/UBIQUITOUS_LANGUAGE.md`, following the workflow 0031 pattern
   used for the RFC 0057/0058 aggregate-root terms.

5. **`docs/USER_GUIDE.md`** — add a brief paragraph to the
   Generate-panel section (search for `kayakgen serve` / `Generate` tab)
   mentioning hover-for-description tooltips on every parameter field.

6. **`docs/UBIQUITOUS_LANGUAGE.md`** — add a `HullParameterMetadata`
   glossary entry under "Sweep, search, and comparison" (parallel to
   the existing `ObjectiveMetadata` references).

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_hull_parameter_metadata.py \
  tests/test_vocabulary_coverage.py \
  tests/test_generate_spec_form.py \
  tests/test_generate_frontier_view.py \
  -q
```

All tests must pass. The byte-stability gate is
`tests/test_generate_spec_form.py`. If it breaks, your wiring change
altered the submitted payload — fix the wiring, do not touch the test.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`
- `docs/audits/2026-05-22-code-doc-audit/docs-decision-drift/FINDINGS.md`
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
- `docs/rfcs/README.md`
- `docs/rfcs/0060-*.md`

Those are the parent agent's job. The workflow's `forbidden_paths`
encodes this contract; do not work around it.

## Artifact

Write
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0033/PATCH_SUMMARY.md`
with: files changed, registry entry count (must be 11), test counts per
file, byte-stability confirmation, and the exact glossary entry text.
