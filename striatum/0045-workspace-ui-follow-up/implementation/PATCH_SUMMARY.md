# Patch Summary

## Summary

Implemented the ledger-approved RFC 0034 safe slice for the web workspace:
class presets now reseed canonical hull sliders and narrow ranges, manual hull
edits return the selector to `custom`, the rail validity badge is derived from
current hull/class state, the Resistance and Mesh review cards render existing
read models, and the toolbar now exposes one honest Export menu.

The implementation preserves the RFC 0033 no-new-backend-capability boundary.
It does not add hosted storage, new REST route shapes, web-side mesh-package
authoring, real solver capability, calibrated resistance, high-angle stability,
watertight readiness promotion, commits, pushes, Striatum mutation commands, or
`.striatum/` edits.

## Files Changed

- `docs/USER_GUIDE.md`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `tests/test_web_browser.py`
- `tests/test_web_layout.py`
- `tests/test_web_read_models.py`
- `striatum/0045-workspace-ui-follow-up/implementation/PATCH_SUMMARY.md`

Note: root `OPERATOR_REPORT.md` was already dirty at job start and was left
untouched.

## Findings Resolved

- P0 Export boundary: replaced the two flat STL buttons with one Export menu
  containing Hull STL, Deck STL, Hydro JSON, Stability JSON, and Mesh package
  rows. STL rows stay enabled, Hydro JSON is backed by current local evaluation
  data, and Stability JSON / Mesh package rows remain unavailable with CLI
  guidance.
- P0 Preset binding: added class preset read models, guarded preset seeding,
  dynamic slider bounds for `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`,
  and `Cp`, and manual hull-edit fallback to `custom`. `target_speed_kt`
  remains view state and does not flip the preset.
- P0 Resistance card: moved the sweep table into the Resistance card from the
  existing `resistance_table_view_model`, including fixed rows, target row,
  `kt | Fn | Rv N | Rw N | Rt N`, raw comparative copy, and the
  `uncalibrated_comparative` chip. The Hydrostatics card now renders
  hydrostatics-only text.
- P0 Mesh/readiness: wired live hull/deck diagnostics, welded-primary counts,
  raw detail, warnings, profile options, disabled `watertight-solid` copy, and
  package/readiness state without claiming package readiness when no package is
  selected.
- P0 manifest containment: package manifest artifact refs are resolved under
  the package directory before readback; absolute, URI-like, and parent
  traversal refs fail closed in the view model.
- P1 Validity badge: added an exact web helper and accessible rail rendering
  for `In <class> envelope`, `Custom — sub-touring`,
  `Custom — beyond elite`, and `Custom (L/B_wl=X.X)`.
- P1 forbidden copy: broadened rendered-surface regression coverage for the RFC
  0033 no-go strings with explicit allowed negations.
- P1 browser/accessibility: extended browser acceptance for preset seeding,
  range narrowing, manual custom flip, dynamic badge, Resistance table, Mesh
  diagnostics/profile copy, Export rows, and STL response headers.
- P2 docs: updated the user guide with factual current behavior and explicit
  browser/CLI boundaries.

## Explicit Deferrals

- Hosted/cloud CFD, worker queues, OpenFOAM/SU2, Docker/container solvers, real
  solver adapters, normalized solver output, cancellation guarantees, and
  public hosted execution.
- Calibrated drag, final prediction, validity envelopes, and design fitness.
- High-angle `GZ`, `GZ_max`, `heel_angle_max_deg`, secondary stability, and
  full capsize-range stability.
- Watertight-solid readiness and bare `cfd_ready` promotion.
- Web-side mesh-package authoring or browser mesh-package download beyond a
  future accepted server-local artifact flow.
- New REST route shapes, rich comparison/Pareto UI, multi-variant overlays,
  full mobile authoring, and desktop workspace parity rewrite.
- Per-row resistance claim variance; this slice keeps the
  `uncalibrated_comparative` chip at card scope.

## Validation

- `git diff --check` -> passed.
- `.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_web_read_models.py tests/test_mesh_package.py -q -p no:cacheprovider` -> `58 passed in 13.35s`.
- `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider` -> `1 passed in 9.84s`.
- `.venv/bin/python -m pytest -q -p no:cacheprovider` -> `299 passed in 68.36s (0:01:08)`.

## Proposed Changelog Entry

```markdown
- Landed workflow 0045's RFC 0034 workspace UI follow-up safe slice: web class
  presets reseed canonical hull sliders and narrow ranges, manual hull edits
  return the preset selector to `custom`, the validity badge derives from
  class/envelope state, Resistance and Mesh review cards render existing read
  models, and the Export menu exposes enabled STL rows plus honest local-data or
  unavailable JSON/package states. The slice preserves RFC 0033's no-new-backend
  capability boundary; calibrated drag, final prediction, design fitness,
  high-angle `GZ`, hosted/cloud CFD, real solver adapters, web-side
  mesh-package authoring, watertight `cfd_ready`, and desktop parity rewrite
  remain deferred.
```

## Sub-Agent And Parallel Assistance

- Kierkegaard inspected controller/read-model scope: class preset helpers,
  validity badge semantics, resistance read-model expectations, and manifest
  containment tests.
- Hegel inspected web UI rendering scope: preset guard/state wiring, slider
  bounds, badge accessibility, Resistance/Mesh/Export rendering, and layout
  tests.
- Mendel inspected browser acceptance scope: class/role selectors, preset
  workflow checks, Mesh/Resistance/Export assertions, and STL header coverage.
- Euler inspected docs/artifact scope: user-guide wording, patch-summary shape,
  and exact proposed changelog wording.
- Main-session parallel reads covered workflow docs, RFCs, review artifacts,
  current implementation files, tests, and user documentation. No helper edited
  files or ran Striatum commands.
