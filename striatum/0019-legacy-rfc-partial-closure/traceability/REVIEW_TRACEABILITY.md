author: operator [self-declared: operator-traceability-review]

# REVIEW_TRACEABILITY.md

Verdict intent: needs_revision before RFC 0004/0006 can be marked landed.

Focused verification: `./.venv/bin/python -m pytest -q tests/test_plumb_bow.py tests/test_classes.py tests/test_gui_params.py tests/test_hydrostatics.py tests/test_mesh_diagnostics.py tests/test_mesh_package.py` passed: 35 tests.

## Findings

### T-001 - RFC 0004 near-plumb geometry landed, exact-stem criterion did not

`bow_rake`, blended `_end_decay`, default golden identity, plumb keel profile,
waterplane blend, and monotonic displacement behavior are implemented and
tested. However, RFC 0004 requires non-zero area at `x = -L/2`; current
geometry still has zero exact-end section area, and the test checks an inboard
station instead.

Required action: either implement explicit plumb stem/end-cap semantics, or
revise RFC 0004 acceptance to say "near the stem / inside the transition zone"
and keep exact-end area deferred.

### T-002 - RFC 0004 watertight STL wording is still overclaimed

Current hull/deck meshes are separate open surfaces. Mesh diagnostics explicitly
report boundary edges and "not a closed volume"; `test_stl_watertight_at_plumb_bow_rake_zero`
only checks file existence and mesh shape, not watertightness.

Required action: do not mark watertight STL acceptance landed. Split this into a
named future end-cap/solid-mesh decision, or add actual watertight closure plus
topology tests.

### T-003 - RFC 0004 deck/freeboard behavior remains only partially aligned

The hull keel/waterplane use `_end_decay`, but `deck_centreline()` still uses
`_get_deck_height_scaling()` independent of `bow_rake`. The proposal's
"maintained bow freeboard" behavior is therefore not fully represented,
especially at the exact stem.

Required action: either apply bow-rake semantics to deck/freeboard and test it,
or explicitly defer maintained stem freeboard in RFC 0004.

### T-004 - RFC 0004 Cp/center-box interaction lacks acceptance-level proof

Tests cover bow-rake volume monotonicity and default golden identity, but not
the stated interaction that `center_box_ratio` and `Cp` continue to behave
correctly with `bow_rake`.

Required action: add focused tests varying `Cp`, `center_box_ratio`, and
`bow_rake`, or narrow the acceptance wording.

### T-005 - RFC 0006 model core mostly landed, but API wording is stale

The constraints doc exists, four presets exist, touring/elite defaults are
tested, `beam_wl_m` affects displacement, explicit invalid waterline beam values
are rejected, and hydrostatics includes `GM0_m`. However, RFC wording names
`kayak_classes.py`, `KayakGenerator(beam_wl=...)`, and
`generator.evaluate_hydrostatics()`, while implementation lives in
`kayakgen.model.classes`, `Hull`, and `kayakgen.eval.hydrostatics.evaluate`.

Required action: update RFC 0006 to reflect the package API, or add
compatibility shims if legacy `KayakGenerator` acceptance remains required.

### T-006 - RFC 0006 desktop GUI acceptance is not fully proven

Desktop class selection now seeds values and mutates slider ranges. A
class/advisory line is present in metrics via `_classify()`, but there is no
focused test for class range mutation, custom-range relaxation, live clamp
behavior, or the `<50 ms` advisory update claim. The yellow validation
banner/dismissal behavior from RFC 0006 is not implemented.

Required action: add GUI helper tests or explicit manual verification notes for
range/advisory behavior; defer or implement the validation banner. Do not mark
desktop acceptance fully landed yet.

### T-007 - RFC/README status should remain partial after this review

`docs/rfcs/README.md` correctly keeps RFC 0004 and RFC 0006 as partial. RFC
0004's status note is accurate. RFC 0006's status note slightly overstates
"advisory text" unless the metrics class label is accepted as the advisory.

Required action: keep both RFCs partial until T-001/T-002 and T-006 are
resolved or explicitly deferred with renamed acceptance criteria.
