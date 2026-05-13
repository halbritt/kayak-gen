# Architecture and domain review - 0010

author: operator
Date: 2026-05-12
Reviewer: gemini
Verdict intent: needs_revision

## Summary

The RFC 0007 package extraction is substantially present and the local venv
test suite passes, but several RFC 0004-0007 domain contracts are either not
implemented, weakened by compatibility defaults, or not protected by tests.
The highest-risk gaps are around `beam_wl` validation/default semantics,
plumb-bow deck/freeboard behavior, hydrostatic stability outputs, and
resistance depending on private loft internals.

## Findings

### F-ARCH-001 - `beam_wl` contract is not canonical or validated

- Severity: major
- RFC: 0006 sections 3-6; constraints sections 4 and 9
- File(s): `kayakgen/model/hull.py:32`, `kayakgen/model/geometry.py:75`,
  `kayakgen/ui/desktop.py:54`, `kayakgen/ui/web/app.py:33`,
  `tests/test_classes.py:49`
- What you found: `beam_wl_m=None` falls back to full overall beam, while RFC
  0006 specifies `0.92 * beam` and the constraints document says waterline
  beam is the stability-driving parameter. The model also accepts
  `beam_wl_m > beam_oa_m` and negative `beam_wl_m`; GUI/web sliders expose
  ranges outside the canonical `B_wl` envelope.
- Suggested remediation: Add Pydantic validation for `0 < beam_wl_m <=
  beam_oa_m`, decide whether legacy shims explicitly pass full beam while
  `Hull()` defaults to `0.92 * beam_oa_m`, and align GUI/web ranges with
  constraints. Add invalid-input and default-semantics tests.
- Evidence: Targeted probe accepted `Hull(beam_oa_m=0.55, beam_wl_m=0.90)`
  and `Hull(beam_wl_m=-0.10)`.

### F-ARCH-002 - Plumb bow does not preserve deck/freeboard semantics

- Severity: major
- RFC: 0004 goals and acceptance criteria
- File(s): `docs/rfcs/0004-plumb-bow.md`, `kayakgen/model/geometry.py:146`,
  `kayakgen/model/geometry.py:243`, `tests/test_plumb_bow.py:55`
- What you found: `_end_decay` affects hull/waterline/keel, but
  `deck_centreline()` still uses `_get_deck_height_scaling()` independent of
  `bow_rake`, so a fully plumb bow still has zero deck height at the stem.
  The exact end-station area is also zero; tests moved the assertion to
  `x = -0.45L` and the watertight test checks only file size/mesh shape.
- Suggested remediation: Resolve the RFC's exact-end ambiguity, then apply
  plumb/freeboard behavior to deck scaling and add tests for stem freeboard,
  exact station semantics, and boundary-edge watertightness.
- Evidence: Probe results: `section_area(-L/2) == 0.0`; plumb deck centerline
  is zero at the stem.

### F-ARCH-003 - Resistance bypasses the `HullGeometry` boundary

- Severity: major
- RFC: 0007 section 3 and acceptance boundary discipline
- File(s): `docs/rfcs/0007-architectural-revisit.md`,
  `kayakgen/eval/resistance.py:54`
- What you found: `_half_breadth_grid()` calls `geom._end_decay(x)` and
  reconstructs the loft formula from `Hull` fields. That couples resistance
  to `LoftedHullGeometry` internals and weakens the intended replaceable
  geometry abstraction.
- Suggested remediation: Add a public geometry method for half-breadth/depth
  sampling, or build the grid from `section()` without private calls. Add a
  fake/alternate `HullGeometry` test proving resistance consumes only the
  public interface.
- Evidence: `rg -n "_end_decay" kayakgen` shows the private call in
  `kayakgen/eval/resistance.py`.

### F-ARCH-004 - Hydrostatics omits required stability output and misreports `Cm_actual`

- Severity: major
- RFC: 0006 section 5; 0007 section 4; constraints section 2
- File(s): `docs/rfcs/0006-design-constraints.md`, `kayakgen/eval/hydrostatics.py:18`,
  `kayakgen/eval/hydrostatics.py:91`, `tests/test_hydrostatics.py:35`
- What you found: `GM0_m` exists in the schema but is never populated,
  despite RFC 0006 specifying a KG placeholder. `Cm_actual` divides submerged
  midship area by overall beam even when the submerged section was generated
  from `beam_wl_m`, underreporting section fullness for flared hulls.
- Suggested remediation: Compute `GM0_m` from waterplane `I_T / volume + KB -
  KG`, set `gz_curve` intentionally empty until the stability RFC, and compute
  `Cm_actual` against waterline beam. Add monotonic GM0 tests over
  `beam_wl_m`.
- Evidence: Probe with `beam_oa_m=0.60`, `beam_wl_m=0.50` reported
  `Cm_actual=0.5835`; using `B_wl * draft` gives `0.7002`.

### F-ARCH-005 - PyVista preview drops new hull parameters

- Severity: major
- RFC: 0004, 0006, 0007 compatibility shims/package consumers
- File(s): `kayakgen/ui/desktop.py:36`, `kayakgen/ui/desktop.py:267`,
  `kayakgen/ui/pv_window.py:13`
- What you found: Desktop plots/metrics pass `beam_wl` and `bow_rake`, but
  `pv_window.py` maps only legacy fields into `Hull`. The 3D preview silently
  renders raked/full-waterline geometry while the 2D views and metrics may
  show plumb or narrowed-waterline geometry.
- Suggested remediation: Centralize GUI-state-to-`Hull` conversion and reuse
  it in desktop, PyVista, and web controllers. Add a non-rendering test that
  PyVista conversion preserves `beam_wl_m` and `bow_rake`.
- Evidence: `pv_window.py` lacks `beam_wl` and `bow_rake`; desktop's mapping
  includes both.

### F-ARCH-006 - Resistance regression tests do not protect RFC 0005 acceptance criteria

- Severity: major
- RFC: 0005 acceptance criteria
- File(s): `docs/rfcs/0005-cfd-resistance.md`, `tests/test_resistance.py`,
  `kayakgen/eval/resistance.py`
- What you found: The Wigley benchmark test implements a local `michell()`
  function instead of exercising production `wave_resistance_michell()`. The
  performance test allows 5000 ms while RFC 0005 requires 200 ms; it also
  omits the Fn 0.1 and Fn 0.5 wave/viscous ratio criteria and the
  beam-increases-drag criterion.
- Suggested remediation: Refactor production Michell code so a Wigley
  geometry/grid can be passed through the real evaluator, restore RFC
  threshold tests, and separate slow benchmark tests from fast unit tests if
  needed.
- Evidence: Local probe measured default `resistance_curve(Hull())` at about
  275 ms; the suite still passed because the test allows 5000 ms.

### F-ARCH-007 - RFC 0007 package/schema surface is incomplete

- Severity: minor
- RFC: 0007 package layout, schema, CLI
- File(s): `docs/rfcs/0007-architectural-revisit.md`, `kayakgen/cli/main.py`
- What you found: The package has `model`, `eval`, `io`, `ui`, and `cli`, but
  no `model/schema.py`, `eval/cfd.py`, or `search/` package, and the CLI has
  no `sweep` command. If intentionally deferred, the RFC completion state
  should say so explicitly.
- Suggested remediation: Add minimal stubs/tests for the reserved surfaces or
  amend the completion criteria to mark them deferred.
- Evidence: `find kayakgen -maxdepth 2 -type d | sort` returned no
  `kayakgen/search`; CLI commands are `init`, `generate`, `evaluate`, `view`,
  and `serve`.

## Commands used

Read-only file inspection, `rg`, `find`, `.venv/bin/python -m pytest -q`, and
targeted numerical probes.
