author: implementer-claude-opus-4.7-002

# Frontier-view colour wiring patch summary (RFC 0058 stage 3 / D-13)

## Scope

Wire `resolve_analytical_claim_label(hull, fit_registry=())` into
`kayakgen/ui/web/generate_frontier_view.py` so the Pareto-frontier
scatter point for each row reports the analytical-claim CSS class
(`kg-state-validated` or `kg-state-raw`) when the row carries a hull
reference. Default behaviour (no hull on the row, `fit_registry=()`)
is byte-stable.

## Changes

- Imported `resolve_analytical_claim_label` from
  `kayakgen.eval.stability.high_angle_contracts`.
- Added two private mappings in
  `kayakgen/ui/web/generate_frontier_view.py`:
  - `_ANALYTICAL_CLAIM_LABEL_CSS_CLASS` mapping each
    `AnalyticalClaimLabel` literal to its CSS class
    (`validated_hydrostatic_comparison` → `kg-state-validated`,
    `unvalidated_hydrostatic_comparison` → `kg-state-raw`).
  - `_ANALYTICAL_CSS_CLASS_THEME_TOKEN` mapping each new CSS class
    to the existing theme token used to render it
    (`kg-state-validated` → `state-success`,
    `kg-state-raw` → `state-raw`). No new theme token is introduced.
- Added the private helper `_resolve_claim_label_color_token` that
  returns the analytical-claim CSS class for a row when the row
  carries a `hull` reference, and `None` otherwise. The helper calls
  `resolve_analytical_claim_label(hull, fit_registry)` per D-13/D-4.
- Extended `build_frontier_view_model` with an `Iterable[Any]`
  `fit_registry` keyword argument that defaults to `()` (preserves
  the existing public default). The argument is passed straight to
  the helper.
- Added the additive `claim_label_color_token` key to both row dicts
  and scatter-point dicts. The value is one of
  `{"kg-state-validated", "kg-state-raw", None}`. Existing scatter
  fields (`color`, `color_class`, `color_token`, `claim_state`, etc.)
  are unchanged.
- Updated `frontier_view_css()` to emit the two new CSS rules
  `.kg-state-validated { fill: var(--state-success); }` and
  `.kg-state-raw { fill: var(--state-raw); }`, both keyed off
  existing theme tokens.
- Updated `refresh_frontier_view` to pass the empty `fit_registry=()`
  default explicitly so the call site is grep-able.

## Tests

Added two focused tests in `tests/test_generate_frontier_view.py`:

- `test_build_view_model_hull_with_empty_registry_marks_scatter_kg_state_raw`
  — builds a payload whose only row carries a hull (`SimpleNamespace`
  with `hull_class` and `design_hash`) and the default empty
  `fit_registry=()`. Asserts the scatter and table row both carry
  `claim_label_color_token == "kg-state-raw"`.
- `test_build_view_model_hull_with_covering_accepted_fit_marks_scatter_kg_state_validated`
  — builds the same hull-bearing row plus a one-record
  `SimpleNamespace` fit registry (`acceptance_verdict="accepted"`,
  matching `hull_family_scope`, `kind="analytical"`). Asserts the
  scatter and table row both carry
  `claim_label_color_token == "kg-state-validated"`.

The existing scatter-point shape tests (color/color_class/color_token
fall-back, deterministic ordering, forbidden-key scrub, third
objective handling) continue to pass — the new behaviour is purely
additive on rows that already carry a hull reference.

## Boundary preservation

- `kayakgen/ui/web/generate_frontier_view.py` does not import from
  `kayakgen.services.generative_jobs` at module top level (the
  existing lazy import inside `refresh_frontier_view` is preserved).
- No new theme token is added to `kayakgen/ui/theme.py`.
- No new claim-state literal is introduced. The two literals used —
  `validated_hydrostatic_comparison` / `unvalidated_hydrostatic_comparison`
  — already exist in `kayakgen/eval/stability/high_angle_contracts.py`
  from the stage 2 `claim_label` track.
- The scatter-point public shape is preserved; only an additive key
  is introduced.
- No new hex / color-literal strings in `kayakgen/ui/`; the CSS rules
  reference existing `state-success` and `state-raw` tokens via CSS
  variables.

## Verification

- `.venv/bin/pytest tests/test_generate_frontier_view.py -x -q` →
  11 passed.
- `.venv/bin/pytest tests/test_ui_theme.py tests/test_web_layout.py tests/test_web_read_models.py tests/test_resolve_analytical_claim_label.py -q`
  → 54 passed (ui-theme orphan, forbidden-claim, claim-label resolver
  surfaces stay green).
- `.venv/bin/pytest tests/ -q --ignore=tests/test_openfoam_smoke.py`
  → 1091 passed, 4 skipped (env-gated OpenFOAM smoke).
- `.venv/bin/ruff check kayakgen/ui/web/generate_frontier_view.py tests/test_generate_frontier_view.py`
  → all checks passed.
