---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Ops/Test Review

## Verdict Intent

accept_with_findings

RFC 0034 and the workflow packet are reviewable. I found no packet blocker that
requires a `needs_revision` loop. The items below are implementation, test,
browser-acceptance, package-boundary, and export-safety findings for the ledger.

## Findings

### High - Export scope is the main capability-boundary risk

RFC 0034 requires Export controls for Hull STL, Deck STL, Hydro JSON, Stability
JSON, and Mesh package entries, with unavailable states represented honestly
(`docs/rfcs/0034-workspace-ui-follow-up.md:78`,
`docs/rfcs/0034-workspace-ui-follow-up.md:97`). Current web UI wiring exposes
only `Export Hull STL` and `Export Deck STL` (`kayakgen/ui/web/app.py:623`,
`kayakgen/ui/web/app.py:628`), and the only app export handler is `_export_stl`
(`kayakgen/ui/web/app.py:297`, `kayakgen/ui/web/app.py:477`). Registered web
routes include `/api/evaluate` and `/api/stl`, but no export-specific JSON or
mesh-package route (`kayakgen/ui/web/controllers.py:1424`).

Safe implementation boundary: Hydro JSON can plausibly reuse the existing
`evaluation_payload` route shape. Stability JSON should remain disabled or be
explicitly limited to currently available primary-stability/hydro fields because
`EvaluationResult.stability` is optional and `evaluation_for_state` does not set
it (`kayakgen/eval/contract.py:282`, `kayakgen/ui/web/controllers.py:536`).
Mesh package export should remain disabled/unavailable unless the ledger accepts
a server-local path workflow; `write_mesh_package` is filesystem behavior, not a
browser download API (`kayakgen/eval/mesh_package.py:83`), and the user guide
still says web-side mesh-package creation is a follow-up
(`docs/USER_GUIDE.md:384`).

### High - Preset binding needs a controller read model and event guard

RFC 0034 requires preset selection to reseed canonical hull sliders, narrow
slider bounds to the selected `KayakClass`, and switch back to `custom` after
manual edits (`docs/rfcs/0034-workspace-ui-follow-up.md:88`). Current web state
initializes `class_preset`, but only hull fields plus `target_speed_kt` are
watched (`kayakgen/ui/web/app.py:247`, `kayakgen/ui/web/app.py:433`). Slider
bounds are static constants from `SLIDER_DEFS` (`kayakgen/ui/web/app.py:56`,
`kayakgen/ui/web/app.py:675`).

Do not copy class ranges into `app.py`. `KayakClass` already owns defaults and
ranges (`kayakgen/model/classes.py:53`), and desktop has a working pattern for
range application plus an `_applying_class` guard
(`kayakgen/ui/desktop.py:159`, `kayakgen/ui/desktop.py:178`). RFC 0034 should
land a small controller/helper read model such as `{preset, slider_values,
slider_bounds}` and a web-side guard so programmatic preset updates do not
immediately trigger the manual-edit-to-custom path.

### High - Mesh/readiness status is static and can imply package readiness too early

The app initializes the mesh profile/readiness/status to
`open-wetted-surface` / `cfd_surface_candidate` even when no package is selected
(`kayakgen/ui/web/app.py:248`, `kayakgen/ui/web/app.py:276`), and
`_refresh_status_segments` resets package/readiness to constants
(`kayakgen/ui/web/app.py:394`). The safer `evaluation_summary` path already
returns `readiness.level: None` and "No mesh package selected" when there is no
manifest (`kayakgen/ui/web/controllers.py:262`,
`kayakgen/ui/web/controllers.py:273`).

For RFC 0034, drive the status bar and Mesh tab from `evaluation_summary`,
`mesh_diagnostics_lines_from_state`, and `mesh_package_view_model`. The UI
should not display `cfd_surface_candidate` as package readiness unless it came
from current diagnostics or a manifest-backed package state.

### Medium - Resistance and Mesh read models exist but are not rendered by the app

The safe read models are already present and unit-tested:
`resistance_table_view_model` (`kayakgen/ui/web/controllers.py:200`,
`tests/test_web_read_models.py:126`), `mesh_diagnostics_lines_from_state`
(`kayakgen/ui/web/controllers.py:309`, `tests/test_web_read_models.py:65`), and
`mesh_package_view_model` (`kayakgen/ui/web/controllers.py:338`,
`tests/test_web_read_models.py:86`). The app cards remain mostly static: the
Resistance card shows only copy and a chip, not the `kt | Fn | Rv N | Rw N | Rt
N` rows or target row (`kayakgen/ui/web/app.py:778`), and the Mesh tab shows
static explanatory text plus static readiness copy (`kayakgen/ui/web/app.py:788`).

This is feasible if `app.py` stays a renderer. Keep diagnostics, manifest
parsing, and resistance evaluation in controller/read-model helpers rather than
importing eval/domain internals into the Trame layout.

### Medium - Validity badge should be derived outside the UI shell

RFC 0034 requires the badge to use only the accepted strings and change with hull
state (`docs/rfcs/0034-workspace-ui-follow-up.md:91`). The current badge is
hardcoded to `Custom (L/B_wl from current hull)` (`kayakgen/ui/web/app.py:691`).
The model layer already has selected-class drift semantics
(`kayakgen/model/validity.py:261`), and `design_advisory` accepts
`selected_class` (`kayakgen/model/advisory.py:44`), but the current web summaries
do not pass that class into advisory/validity evaluation
(`kayakgen/ui/web/controllers.py:118`, `kayakgen/ui/web/controllers.py:265`).

Add a `validity_badge_from_state(state)` or equivalent controller helper. The
app should render the returned badge string, not reimplement envelope semantics
in layout code.

### Medium - Browser acceptance passes but does not exercise the RFC 0034 surface

The browser test verifies launchability, nonblank 3D rendering, one slider
mutation, share reload, and `/api/stl` (`tests/test_web_browser.py:306`,
`tests/test_web_browser.py:331`, `tests/test_web_browser.py:345`,
`tests/test_web_browser.py:370`). It does not exercise preset selection,
class-specific bounds, manual-edit-to-custom, responsive breakpoints, export
controls, mesh diagnostics, resistance target-row rendering, or dynamic validity
badge behavior. Static layout tests assert hook constants, but do not measure
the 1440x900 first viewport or sub-960 behavior in a browser
(`tests/test_web_layout.py:19`).

Browser acceptance should be expanded before RFC 0034 is called complete.

### Medium - Forbidden-copy strategy needs a precise render-surface target

RFC 0034 asks for the full RFC 0033 no-go string set
(`docs/rfcs/0034-workspace-ui-follow-up.md:99`). The current static test checks
only `GZ_max`, `heel_angle_max_deg`, and the `cfd_ready` count in `app.py`
(`tests/test_web_layout.py:94`). A broader source grep finds latent positive
labels under `kayakgen/ui/theme.py`, including `Validated design fitness` and a
`cfd_ready` chip spec (`kayakgen/ui/theme.py:226`,
`kayakgen/ui/theme.py:261`).

The implementation should choose and document the assertion boundary. A blanket
grep over all `kayakgen/ui` sources will currently fail; a render-surface grep
over app/browser output is fairer unless the unused positive chip labels are
renamed or removed.

### Medium - Mesh package manifest reading needs containment checks before web exposure

Generated mesh packages use relative manifest paths, and writer tests cover that
(`tests/test_mesh_package.py:116`). The reader side joins manifest quality
report refs directly with `package_path` (`kayakgen/ui/web/controllers.py:379`).
If a hand-edited manifest contains an absolute path or `../`, the UI reader can
attempt to read outside the package directory.

Before exposing mesh package export/readback more prominently in the browser,
resolve each manifest artifact ref, require it to remain under `package_path`,
and add a malicious-manifest regression test.

### Low - STL export lacks browser-facing filename/header assertions

`/api/stl` returns an `application/sla` response without a deterministic
`Content-Disposition` filename (`kayakgen/ui/web/controllers.py:1341`). Browser
coverage asserts content type, length, and triangle count, but not filename,
invalid-part behavior, or user-visible download semantics
(`tests/test_web_browser.py:297`). RFC 0034 export work should add deterministic
filename/header assertions for Hull and Deck STL while adding the new export
entries.

## Test Matrix Recommendations

| Area | Recommended RFC 0034 checks |
| --- | --- |
| Presets | State-level and browser tests for each non-custom preset: slider values reseed from `KayakClass`, bounds narrow to class ranges, and one manual slider edit flips the preset to `custom`. |
| Validity badge | Unit tests over in-envelope, sub-touring, beyond-elite, and custom L/B cases; browser test that the rendered badge updates after preset and manual edits. |
| Resistance | Unit and browser checks that fixed speeds `[2, 3, 4, 5, 6] kt`, `kt | Fn | Rv N | Rw N | Rt N`, and exactly one target row render from `resistance_table_view_model`. |
| Mesh | Unit and browser checks for hull/deck welded-primary counts, raw detail, warnings, missing/malformed package states, and disabled `watertight-solid` copy. |
| Export | Tests for Hull STL, Deck STL, Hydro JSON enabled if using existing `/api/evaluate`, Stability JSON disabled or truthfully limited, and Mesh package disabled/unavailable unless a server-local path flow is accepted. |
| Forbidden copy | Render-surface assertions for the full RFC 0033 no-go list, with explicit allowances for "no hosted worker is running" and "not watertight cfd_ready". |
| Browser layout | 1440x900 visibility for parameters, geometry, metrics, review, and status; sub-960 usable collapse; export overflow at sub-1200. Treat browser skips as missing coverage. |
| Docs/changelog | Focused assertions or checklist review that user guide/changelog describe current safe behavior only. |

## Browser Acceptance Recommendations

- Keep `tests/test_web_browser.py -m browser_acceptance --browser-acceptance` as
  a required gate when web/browser extras are installed.
- Add one preset workflow test in Chromium: select preset, inspect slider values
  and bounds, mutate one slider, assert `custom`.
- Add one review-data workflow test: open Resistance and Mesh tabs and assert
  read-model rows/counts are visible.
- Add one export affordance test: verify all five entries are present and that
  unavailable entries are disabled or carry unavailable copy.
- Add viewport assertions at 1440x900 and below 960 px. Static class hooks are
  not enough for the RFC 0034 layout acceptance surface.

## Export Safety Concerns

- Do not introduce a new mesh package authoring API under the label "export"
  unless the ledger explicitly accepts that capability.
- Hydro JSON is safe if it is a local browser artifact from the existing
  evaluation payload.
- Stability JSON should not imply high-angle GZ, secondary stability, or a
  populated `EvaluationResult.stability` unless that data is actually computed.
- Mesh package export should be disabled/unavailable by default or clearly
  server-local; current packages remain open-surface candidates, not watertight
  `cfd_ready` solver handoffs (`kayakgen/eval/mesh_package.py:156`,
  `kayakgen/eval/mesh_package.py:170`).
- Validate manifest refs on read before exposing package details in the UI.

## Implementation Sequencing

1. Ledger the export decision first: enable Hydro JSON only if it reuses current
   safe payloads; disable or truthfully limit Stability JSON and Mesh package.
2. Add controller read models for preset state and validity badge, using
   `KayakClass` and existing design-validity semantics.
3. Wire `app.py` to existing controller read models for Resistance, Mesh, package
   readiness, and status segments.
4. Expand tests around the read models and add browser coverage for the dynamic
   behaviors, not just static hook presence.
5. Update docs/changelog after behavior is implemented, preserving the no-new
   backend capability and no-claims boundaries.

## Commands And Checks Run

- `git status --short` -> existing dirty files:
  `OPERATOR_REPORT.md` and
  `docs/workflows/0045-workspace-ui-follow-up/OPERATOR_REPORT.md`.
- `git diff --check` -> passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_ui_theme.py tests/test_web_read_models.py tests/test_mesh_package.py -q -p no:cacheprovider`
  -> `58 passed in 6.25s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider`
  -> `1 passed in 5.44s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
  -> `291 passed in 57.77s`.
- `rg -n "OpenFOAM|SU2|worker queue|hosted worker|\\bcloud\\b|calibrated drag|final prediction|design fitness|GZ_max|heel_angle_max_deg|\\bcfd_ready\\b" kayakgen/ui docs/USER_GUIDE.md tests/test_web_layout.py tests/test_web_browser.py`
  -> found allowed docs/test occurrences plus latent positive theme labels noted
  above.
- Four read-only sub-agents independently checked test/reproducibility, browser
  acceptance, package boundaries, and export safety. No Striatum commands,
  commits, pushes, `.striatum` edits, product-code edits, or test/doc edits were
  performed.
