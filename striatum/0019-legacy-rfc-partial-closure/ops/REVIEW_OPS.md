author: operator [self-declared: operator-ops-review]

# REVIEW_OPS.md

Verdict intent: changes required before closure; safe slice is close, but needs
targeted tests/status cleanup and no geometry churn.

## Findings

### O-001 - RFC 0004/0006 status wording is stale for the current safe slice

Current code and focused tests now cover more than the workflow-0010 status
notes say: `beam_wl_m` validation, GM0, desktop range mutation, PyVista
propagation, web routes, and initial-query handling are present. RFC 0006 still
says visual/manual confirmation is pending, while RFC 0004 still carries
exact-end/watertight acceptance text as unresolved.

Required action: update RFC 0004/0006 and the RFC index after implementation to
name the landed safe slice and the remaining explicit deferrals: exact
end-cap/watertight solid semantics, exact x = +/-L/2 nonzero section semantics,
asymmetric bow/stern rake, and any unverified desktop visual acceptance.

### O-002 - Plumb-bow test wording overclaims watertightness

`tests/test_plumb_bow.py` has `test_stl_watertight_at_plumb_bow_rake_zero`, but
it only asserts file existence and mesh array shape. That conflicts with the
workflow requirement not to relabel the current open hull/deck surfaces as
watertight.

Required action: rename/reword the test to assert STL generation/mesh validity
only, or add an explicit diagnostic test proving boundary edges remain an
expected deferral. Do not change geometry to satisfy the old watertight wording
in this workflow.

### O-003 - Legacy `KayakGenerator` shim does not expose RFC 0004/0006 parameters

The package `Hull` supports `beam_wl_m` and `bow_rake`, and desktop/web paths
propagate them. The legacy `generator.KayakGenerator` constructor still accepts
only pre-RFC parameters, while RFC 0004/0006 text and at least one acceptance
item still refer to `KayakGenerator(...)`.

Required action: either extend the shim with optional `beam_wl` and `bow_rake`
while preserving defaults/goldens, or update docs/status to say new semantics
are package-only. Prefer the shim extension plus a narrow compatibility test.

### O-004 - Web UI does not enforce `beam_wl_m <= beam_oa_m` before validation failure

Desktop clamps `beam_wl` live, and `Hull` rejects invalid explicit values. The
web sliders remain independently ranged to 0.90, so users can put state into an
invalid model and get metrics errors instead of a coherent constrained UI/API
behavior.

Required action: add web-side clamping or dynamic max behavior for `beam_wl_m`,
and make REST helpers return a controlled 400-style validation response for
invalid JSON rather than surfacing raw validation failures. Add focused tests.

### O-005 - CLI coverage does not lock RFC 0004/0006 JSON propagation

Current CLI tests cover sweep, compare, mesh, and stability, but not
`generate`/`evaluate` with non-default `bow_rake` and explicit `beam_wl_m`. The
model supports those fields, but closure should lock the JSON/hash/evaluation
path.

Required action: add CLI tests that load a hull JSON with `bow_rake=0.0` and
`beam_wl_m < beam_oa_m`, run `evaluate --skip-resistance` and `generate`, and
assert output JSON/STLs reflect the same hull semantics without changing
default goldens.

### O-006 - Desktop class/advisory behavior lacks focused automated coverage

Desktop code now mutates slider ranges, clamps `beam_wl`, and classifies
out-of-envelope hulls, but tests only cover GUI-to-Hull parameter mapping. The
remaining RFC 0006 desktop closure risk is regression in range/advisory
propagation.

Required action: extract the class/advisory/range logic into testable helpers or
add a narrow GUI-object test that does not require a visible display. If this
remains manual, keep RFC 0006 status partial and name desktop visual/manual
verification as the reason.

## Verification

Focused in-scope suite passed with:

`.venv/bin/python -m pytest tests/test_plumb_bow.py tests/test_classes.py tests/test_gui_params.py tests/test_web.py tests/test_hydrostatics.py tests/test_cli.py -q`

Result: 44 passed.
