# Review prompt — workflow 0033

You are reviewing the implementer's landing of RFC 0060 (web
Generate-panel form labels and tooltips). Closes audit finding
`AUD-O-003`.

Read in order:

1. RFC 0060 (`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`)
   — the spec.
2. `docs/audits/2026-05-22-code-doc-audit/follow-ups/0033/PATCH_SUMMARY.md`
   — the implementer's report.
3. The actual touched files.

## Acceptance criteria (verify each)

1. **Module exists.** `kayakgen/ui/parameter_metadata.py` exports
   `HullParameterMetadata`, `HULL_PARAMETER_METADATA`,
   `label_with_unit`, `description`, with a module-level `__all__`.
2. **Registry size.** `HULL_PARAMETER_METADATA` has exactly 11 entries
   (the keys listed in RFC 0060 §2). Every entry's `parameter` field
   equals its dict key.
3. **Form wiring.** `kayakgen/ui/web/generate_spec_form.py`:
   - imports `label_with_unit`, `description`, and
     `HULL_PARAMETER_METADATA` from `kayakgen.ui.parameter_metadata`;
   - exposes a new Trame state key for the variable-selector picklist
     items with `{"value", "title"}` shape;
   - each rendered base-hull rail field's label uses
     `label_with_unit(key)`;
   - each rail field carries a `:hint` (or `<VTooltip>`) bound to
     `description(key)`;
   - the objectives picklist `items` prop uses
     `[{"value": metric, "title": f"{label} ({unit})"}]` records sourced
     from `OBJECTIVE_METADATA`;
   - the inline `{{ metric }}` template token in the selected-objective
     row is replaced with a label-with-unit form.
4. **Byte stability.** `tests/test_generate_spec_form.py` passes
   unchanged in *shape* — the test bodies are not weakened to mask a
   payload-format change. The submitted JSON for both
   `_sweep_form_state()` and `_search_form_state()` round-trips
   identically.
5. **Regression test.** `tests/test_hull_parameter_metadata.py` asserts:
   - every `BASE_HULL_KEYS` key has a registry entry;
   - every entry's `label`, `description`, and (if non-None) `unit` are
     non-blank trimmed strings;
   - every registry key resolves to a `Hull.model_fields` name;
   - `label_with_unit("length_m") == "Length (m)"`,
     `label_with_unit("Cp") == "Prismatic coefficient (Cp)"`,
     `label_with_unit("unknown_param") == "unknown_param"`.
6. **Vocabulary coverage.** `tests/test_vocabulary_coverage.py` gains
   a parametric assertion that `HullParameterMetadata` appears in
   `docs/UBIQUITOUS_LANGUAGE.md`.
7. **Docs updated.**
   - `docs/USER_GUIDE.md` Generate-panel section briefly mentions
     hover-for-description tooltips.
   - `docs/UBIQUITOUS_LANGUAGE.md` carries a `HullParameterMetadata`
     row under "Sweep, search, and comparison" with a path + role
     definition parallel to existing entries.

## Tests to confirm

```bash
.venv/bin/pytest \
  tests/test_hull_parameter_metadata.py \
  tests/test_vocabulary_coverage.py \
  tests/test_generate_spec_form.py \
  tests/test_generate_frontier_view.py \
  -q
```

All must pass.

## Scope check

The implementer MUST NOT have touched `CHANGELOG.md`,
`docs/rfcs/README.md`, `docs/rfcs/0060-*.md`, or the audit
`FINDINGS.md` files. Flag any drift.

## Artifact

Write `docs/audits/2026-05-22-code-doc-audit/follow-ups/0033/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check results
(pass / fail with file:line evidence), and any deferrals.
