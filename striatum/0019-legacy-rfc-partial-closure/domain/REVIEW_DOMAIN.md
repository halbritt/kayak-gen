author: operator [self-declared: operator-domain-review]

# REVIEW_DOMAIN.md

Verdict intent: partial closure only. RFC 0004 and RFC 0006 are directionally
implemented, but domain closure should be withheld until coordinate convention,
bow_rake/deck semantics, class envelopes, and advisory warnings are tightened.

## D-001 - Stern-positive / bow-left convention is implicit and partly contradicted

The UI labels `x < 0` as forward and `x > 0` as aft, matching the RFC 0004
bow-left expectation (`x = -L/2` bow, `x = +L/2` stern). Geometry itself is
symmetric, so errors are easy to hide. One plumb-bow test describes
positive-end samples as "near the bow", which contradicts the convention.

Required action: make the coordinate convention explicit in geometry/UI docs or
comments and add/adjust tests so bow assertions sample `x < 0` and stern
assertions sample `x > 0`. Keep symmetric `bow_rake` as an accepted RFC 0004
deferral until asymmetric bow/stern controls are designed.

## D-002 - `bow_rake` does not yet carry the promised deck/freeboard semantics

`_end_decay()` correctly changes hull/waterplane/keel fullness, but deck
centreline height still uses `_get_deck_height_scaling()` independent of
`bow_rake`. RFC 0004 explicitly calls out maintained bow freeboard and says
deck height scaling should use the same blend.

Required action: either apply the plumb/raked blend to deck height semantics, or
explicitly amend RFC 0004 to define plumb closure as hull-only with deck
freeboard measured just inboard of the 5% closure zone. Do not mark
deck/freeboard acceptance closed until this is decided.

## D-003 - Class preset ranges need a domain reconciliation pass

The four presets exist, but several ranges are not exact lifts from the
constraints/RFC envelope: touring `B_wl` is wider than the section 4 touring
table, performance length starts at 4.9 m rather than the RFC's 4.6 m sketch,
intermediate surfski total beam omits the wider 0.54 m/stable-surfski edge, and
elite draft allows 0.09 m despite section 9 listing max draft 0.10-0.16 m.

Required action: create one canonical table mapping each preset field to the
source section and either align the ranges or annotate intentional deviations.
Defaults can stay if justified, but ranges should not silently drift from the
adopted domain source.

## D-004 - Advisory warnings are incomplete and split by UI

Desktop shows a class label and L/B_wl extreme text, but not the RFC 0006
warning set for Cp and displacement. Web exposes raw sliders without class
presets, advisory warnings, or a live `beam_wl <= beam_oa` clamp, so invalid
states can become validation errors rather than domain guidance.

Required action: implement a shared advisory/read-model helper used by desktop
and web. It should report L/B_wl, Cp outside 0.50-0.65, and displacement outside
0.075-0.180 m3 as warnings only. The UI may remain permissive, but warnings
must be visible and consistent.

## D-005 - Keep end-cap/watertight and advanced stability work safely deferred

Current RFC 0004 status already says exact plumb-stem/end-cap semantics remain
unresolved. The existing "watertight" plumb test only proves STL generation and
mesh shape, not closed-volume watertightness. RFC 0006 also reserves rocker,
deadrise/chines, GM/GZ depth, and asymmetric ends.

Required action: preserve these as explicit deferrals. Rename or narrow any
tests/acceptance notes that imply true watertight end caps or accepted
high-angle stability. Closure should state that current meshes remain separate
open hull/deck surfaces until an end-cap design RFC lands.
