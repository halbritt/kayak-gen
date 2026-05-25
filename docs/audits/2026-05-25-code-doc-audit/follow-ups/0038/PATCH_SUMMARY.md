# Workflow 0038 — patch summary

Workflow: `docs/workflows/0038-hydrostatics-row-metadata-registry/`
Audit batch: 2026-05-25 release_candidate audit, batch R3
Finding closed: `AUD-O-005` (hydrostatics row labels not registry-sourced)
RFC landed: `docs/rfcs/0062-hydrostatics-row-metadata-registry.md`
Date: 2026-05-25
Implementer lane: Claude Opus 4.7

## Files changed

| Path | Kind |
| --- | --- |
| `kayakgen/ui/hydrostatics_metadata.py` | new — `HydrostaticsRowMetadata` value object + `HYDROSTATICS_ROW_METADATA` registry (7 rows). |
| `kayakgen/services/evaluation.py` | edit — `analysis_view_model::hydro_rows` block now sources labels and units from the registry; added one import (`HYDROSTATICS_ROW_METADATA as _HYDRO_META`). No other function bodies touched. |
| `tests/test_hydrostatics_row_metadata.py` | new — regression net: registry coverage + count pin + entry well-formedness + `analysis_view_model` wiring assertion + `hydro_rows_from_state` byte-stability assertion + unit-suffix preservation assertion. |
| `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` | new — RFC 0062 (status `landed`). |
| `docs/rfcs/README.md` | edit — one new index row after the RFC 0061 row. |
| `docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/PATCH_SUMMARY.md` | new — this artifact. |

## Test counts

| Path | Result |
| --- | --- |
| `tests/test_hydrostatics_row_metadata.py` | 12 passed |
| `tests/test_hull_parameter_metadata.py` | 33 passed (unchanged) |
| `tests/test_web_layout.py` | 30 passed (unchanged) |
| `tests/test_vocabulary_coverage.py` | 38 passed (unchanged) |

The 12 new tests in `test_hydrostatics_row_metadata.py`:

- `test_registry_covers_expected_keys` — every key consumed by
  `analysis_view_model::hydro_rows` has a registry row.
- `test_registry_has_seven_entries` — count pin (RFC 0062 baseline).
- `test_registry_entries_are_well_formed[<key>]` — 7 parametric
  assertions on `parameter` / `label` / `description` / `unit`
  trimmed-string contracts.
- `test_analysis_view_model_labels_match_registry` — the wiring
  goes through the registry, not a hardcoded fallback.
- `test_hydro_rows_from_state_byte_stable` — `hydro_rows_from_state`
  label list matches the post-`b82b544` / pre-RFC 0062 baseline.
- `test_hydro_rows_from_state_preserves_unit_in_value` — the
  `value` field of dimensional rows ends with the unit suffix; the
  `value` field of dimensionless rows does not.

## `analysis_view_model` return-value dict shape unchanged

The top-level keys (`hydro_rows`, `resistance_rows`,
`design_warnings`, `design_validity`, `resistance_warnings`,
`warnings`, `resistance_metadata`) and their value types are
unchanged. The only edit inside the function body is the
`hydro_rows` literal: a seven-element `list[tuple[str, str, str]]`
in both the before and after state, with byte-equal labels and
units. Pinned by `test_analysis_view_model_labels_match_registry`
in `tests/test_hydrostatics_row_metadata.py` and by every existing
test in `tests/test_web_layout.py` (30 passed) and
`tests/test_web.py` (untouched).

## `hydro_rows_from_state` output byte-stable

The `[{"label", "value"}]` wire shape and its label strings are
preserved verbatim:

- `Displacement`, `Wetted surface`, `Waterplane area`, `GM0`,
  `Cp actual`, `Cm actual`, `L/B wl`.

Pinned by `test_hydro_rows_from_state_byte_stable` and
`test_hydro_rows_from_state_preserves_unit_in_value`. `Warning`
rows (appended after the seven hydrostatics rows for design
warnings) are unchanged.

## `mesh_diagnostics_rows_from_state` not touched

The `mesh_diagnostics_rows_from_state` function body in
`kayakgen/services/evaluation.py` (lines ~452-494 in the current
tree) is untouched. The only edits to that file are:

- One new import line: `from kayakgen.ui.hydrostatics_metadata
  import HYDROSTATICS_ROW_METADATA as _HYDRO_META`.
- The `analysis_view_model::hydro_rows` block (lines ~113-125 in
  the current tree).

`hydro_rows_from_state` and `hydro_lines_from_state` are also
unchanged — they continue to consume
`analysis_view_model(state)["hydro_rows"]` and the tuple shape is
preserved.

This honors the workflow 0037 carve-out (workflow 0037 owns the
`mesh_diagnostics_rows_from_state` body) and the scope discipline
encoded in `docs/workflows/0038-hydrostatics-row-metadata-registry/workflow.json`
`forbidden_paths`.

## Verification suite

Final command:

```bash
cd /home/halbritt/git/kayak-gen && .venv/bin/pytest \
  tests/test_hydrostatics_row_metadata.py \
  tests/test_hull_parameter_metadata.py \
  tests/test_web_layout.py \
  tests/test_vocabulary_coverage.py \
  -q
```

Final pytest line:

```
113 passed in 23.36s
```

All four files green; no skipped, no xfailed, no warnings of
relevance to this workflow.

## Scope discipline

The diff respects every `forbidden_paths` entry in
`workflow.json`:

- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/audits/README.md`, the 2026-05-25 audit
  SYNTHESIS / REMEDIATION_PLAN / FINDINGS files — untouched.
- `kayakgen/ui/parameter_metadata.py`, `kayakgen/ui/web/`,
  `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py` — untouched.
- `mesh_diagnostics_rows_from_state` and `hydro_rows_from_state`
  function bodies in `kayakgen/services/evaluation.py` — untouched
  (only `analysis_view_model::hydro_rows` and one new import line
  were edited).

## Closes

- Audit finding `AUD-O-005`
  (`docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`).
- RFC 0062 Acceptance Criteria 1-6
  (`docs/rfcs/0062-hydrostatics-row-metadata-registry.md` §Acceptance).
- 2026-05-25 audit batch R3 (`REMEDIATION_PLAN.md`).
