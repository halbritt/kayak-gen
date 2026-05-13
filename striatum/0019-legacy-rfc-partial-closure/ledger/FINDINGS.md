author: operator [self-declared: operator-ledger]

# Findings ledger - 0019

Run: `run_777e1515eafe41c6adc27b3df1ab8ae6`
Job: `findings_ledger`

## Gate result

Proceed to implementation with findings. RFC 0004 and RFC 0006 should remain
partial after this workflow unless the final review verifies every remaining
acceptance item. The implementation round should close the safe compatibility,
test, advisory, and status gaps without changing default geometry or pretending
the current open hull/deck surfaces are watertight solids.

## Stats

- Source findings: 18
- Deduplicated findings: 8
- Actionable now: 7
- Explicit deferrals: 4

## Deduplicated findings

### F-001 - RFC 0004 exact-end and watertight wording overclaims current geometry

Source: T-001, T-002, D-005, O-001, O-002

Current `bow_rake` behavior implements near-plumb inboard fullness and STL
generation, but not non-zero section area at exactly `x = -L/2` and not a
closed/watertight hull-plus-deck solid. A test name also says "watertight"
while it only checks STL generation and array shape.

Required action: rename/reword the plumb-bow test to assert generation/mesh
shape only, add or keep diagnostics that make open boundaries explicit, and
update RFC 0004/README wording so exact end-cap, exact-end non-zero section,
and watertight-solid readiness remain named deferrals.

### F-002 - Coordinate convention is implicit and one test describes the stern as bow

Source: D-001

The code uses `x = -L/2` as the bow and `x = +L/2` as the stern, consistent
with the stern-positive convention recorded in RFC 0010. One plumb-bow test
samples positive `x` while describing it as bow.

Required action: make the convention explicit in geometry/test wording and
adjust bow-specific assertions to sample negative `x`.

### F-003 - Plumb deck/freeboard behavior is not implemented

Source: T-003, D-002

`_end_decay()` affects the keel/waterplane/hull section, but the deck
centreline still uses a bow-rake-independent quadratic taper. RFC 0004 says
plumb bow should maintain bow freeboard and deck height should use the same
blend.

Required action: implement bow-rake-aware deck scaling for non-default
`bow_rake` while preserving default golden geometry. Add focused tests for
plumb deck/freeboard behavior.

### F-004 - Bow-rake interactions with `Cp` and `center_box_ratio` lack tests

Source: T-004

Existing tests cover default identity and plumb displacement monotonicity, but
not whether `Cp` and `center_box_ratio` still produce meaningful geometry when
`bow_rake` is non-default.

Required action: add focused tests for `Cp` monotonicity under plumb rake and
for `center_box_ratio` affecting plumb deck flat length.

### F-005 - RFC 0006 class ranges and API/status wording need reconciliation

Source: T-005, T-007, D-003, O-001

The package implementation has moved from the original flat-file proposal, and
some class ranges have drifted from the design constraints/RFC text. Status
notes also understate what has landed in package/core tests while still needing
to preserve desktop/manual and future-shape deferrals.

Required action: update RFC 0006 and README wording to name package APIs and
landed behavior; align or annotate class ranges to the constraints source.

### F-006 - Shared design advisories are missing from web and incomplete in desktop

Source: T-006, D-004, O-004, O-006

Desktop has a class label and extreme L/B_wl text, but Cp and displacement
warnings are not surfaced through a shared helper. Web can put `beam_wl_m` above
`beam_oa_m` and then show raw validation errors rather than a coherent clamp or
advisory.

Required action: add a shared advisory helper, use it from desktop/web metrics,
clamp web `beam_wl_m` to `beam_oa_m`, and add focused tests. Keep yellow
banner/dismissal and visual manual confirmation deferred unless implemented
explicitly.

### F-007 - Legacy `KayakGenerator` shim omits `beam_wl` and `bow_rake`

Source: T-005, O-003

RFC 0004/0006 text still references the legacy `KayakGenerator` surface. The
package `Hull` supports the parameters, but the shim constructor does not.

Required action: extend the shim with optional `beam_wl` and `bow_rake` while
preserving current default goldens. Add a narrow compatibility test.

### F-008 - CLI coverage does not lock RFC 0004/0006 JSON propagation

Source: O-005

CLI tests do not exercise `evaluate --skip-resistance` or `generate` with
non-default `bow_rake` and explicit `beam_wl_m`.

Required action: add CLI tests covering JSON load/evaluate/generate with
non-default RFC 0004/0006 fields.

## Do not implement in this workflow

- Exact plumb-stem/end-cap geometry at `x = +/-L/2`.
- Watertight hull-plus-deck solid or CFD-ready solid readiness.
- Asymmetric bow/stern rake controls.
- Yellow dismissible desktop validation banner if a shared warning read model
  and status deferral are enough for the safe slice.
- New dependencies or default golden geometry churn.

## Implementation guidance

Use Codex for the integration patch. Use the maximal number of useful
sub-agents with disjoint write scopes. Prefer parallel agents for independent
code, test, docs, and review tasks, but keep one agent responsible for final
integration. Suggested splits: geometry/shim tests, shared advisory/web tests,
and docs/status updates.
