# Implement frontier-view colour wiring — RFC 0058 stage 3

Read RFC 0058 (section "Read-model wiring"),
`STAGE_2_3_DECISIONS.md` row D-13, and the existing
`kayakgen/ui/web/generate_frontier_view.py` (focus on the
scatter-point render path).

Wire `resolve_analytical_claim_label(hull, fit_registry=())` into
the scatter render so each point's colour reflects its claim
label:

- Import `resolve_analytical_claim_label` from
  `kayakgen.eval.stability.high_angle_contracts` (provided by the
  `claim_label` track).
- For each scatter point row that carries a `hull` reference,
  call the resolver with `fit_registry=()` (the empty default for
  this workflow — see D-4). When the returned label is
  `"validated_hydrostatic_comparison"`, the point uses the existing
  `theme.kg-state-validated` token; otherwise `theme.kg-state-raw`.
- Do not introduce a new token. Do not change the scatter API
  surface. If the current render does not have a hull reference
  per row, add the minimal plumbing to pass it through the
  existing `_FrontierRow`-style record without changing the public
  shape of the row dataclass beyond the additive field.

Tests in `tests/test_generate_frontier_view.py` (existing — extend
rather than rewrite):

- Add a test that constructs a `_FrontierRow` with a hull whose
  `hull_class` matches an empty registry → asserts the row's
  scatter colour token is `kg-state-raw`.
- Add a test that constructs the row with a hull AND passes a
  one-record fit registry (use a `SimpleNamespace`-style fake
  record with `hull_family_scope`, `acceptance_verdict="accepted"`,
  `kind="analytical"`) → asserts the colour token is
  `kg-state-validated`.
- Existing tests for forbidden-claim copy and frontier-metric
  scrubbing must stay green.

Requirements:

- The frontier-view module must not import from
  `kayakgen.services.generative_jobs` (preserve the import-boundary
  scan).
- Do not introduce a new claim-state literal.
- Run focused tests + the forbidden-claim scan + the
  ui-theme-orphan scan + the import-boundary scan before publishing.

Write scope:
- `kayakgen/ui/web/generate_frontier_view.py`
- `tests/test_generate_frontier_view.py`

Publish the required patch summary artifact under
`striatum/0056-.../implementation/frontier_view_colour/PATCH_SUMMARY.md`.
