# RFC traceability review - 0010

author: operator
Date: 2026-05-12
Reviewer: claude
Verdict intent: needs_revision

## Summary

The repo has substantial implementation for RFCs 0002-0008 and the local
test suite passes under `.venv`, but the RFC index, AGENTS guidance, and
several acceptance claims are stale or over-broad. The largest traceability
gaps are RFC 0004 plumb-bow behavior in the 3D window, RFC 0005 numerical
acceptance, RFC 0006 GUI constraints, and RFC 0008 web/API completion.

## RFC acceptance matrix

| RFC | Criterion | Status | Evidence | Gap |
|---|---|---|---|---|
| 0002 | Slider labels/layout, debounced 3D, opening feedback, metrics, key nudge, save dialog | pass | `kayakgen/ui/desktop.py:92`, `kayakgen/ui/desktop.py:250`, `kayakgen/ui/desktop.py:298` | Mostly code-evidence only; no visual acceptance test. |
| 0003 | Sheer Plan rename, station slider, cursor lines, dynamic section title | pass | `kayakgen/ui/desktop.py:215`, `kayakgen/ui/desktop.py:349` | No automated GUI visual check. |
| 0004 | `bow_rake` model field and decay implementation | partial | `kayakgen/model/hull.py:43`, `kayakgen/model/geometry.py:123`, `tests/test_plumb_bow.py:23` | Package path exists, but legacy `generator.KayakGenerator` constructor lacks `bow_rake`. |
| 0004 | Plumb bow station at x = -L/2 has non-zero area | fail | RFC criterion in `docs/rfcs/0004-plumb-bow.md`; probe returned `area=0.0` | Test checks near the end, not exact stem. |
| 0004 | 3D mesh updates for `bow_rake` and `beam_wl` | fail | `desktop.py` maps both; `kayakgen/ui/pv_window.py:13` omits both | 3D window cannot reflect those sliders. |
| 0004 | STL watertight at all bow-rake values | fail | boundary-edge probe found open boundary edges | RFC wording conflicts with current separate open-surface model. |
| 0005 | Resistance module and live metrics | partial | `kayakgen/eval/resistance.py`, `kayakgen/ui/desktop.py:298` | Backend/live metric exists; acceptance physics/perf do not all pass. |
| 0005 | Low-Fn and high-Fn wave/viscous acceptance | fail | Fn 0.1 probe returned wave/viscous ratio about 162340 | Low-speed wave drag criterion is violated by orders of magnitude. |
| 0005 | Resistance curve UI | fail | no `Resistance Curve` UI found | Only metrics and backend curve helper exist. |
| 0005 | `resistance_curve` under 200 ms | partial | default runs measured about 269-298 ms; test allows 5000 ms | Test budget no longer matches RFC budget. |
| 0006 | Constraints doc vendored | pass | `docs/design/kayak_hull_design_constraints.md` | None. |
| 0006 | Four presets and defaults | pass | `kayakgen/model/classes.py:50`, `tests/test_classes.py:10` | None for model defaults. |
| 0006 | GUI class selection sets ranges and advisory behavior | partial | `kayakgen/ui/desktop.py:137` only sets values | Slider ranges remain broad; advisory is absent. |
| 0006 | Validation banner | fail | `docs/rfcs/0002-0003-audit.md` explicitly leaves it out | RFC was not updated to defer/remove this commitment. |
| 0007 | Package, CLI, shims, golden tests | pass | `pyproject.toml:41`, `kayakgen/cli/main.py:19`, `tests/test_golden.py` | Good implementation evidence. |
| 0007 | No private geometry access from UI | partial | literal grep hits a docstring in `desktop.py` | Stale literal grep criterion; no call-site issue. |
| 0008 | `kayakgen serve`, web sliders, VTK view, metrics | partial | `kayakgen/cli/main.py:85`, `kayakgen/ui/web/app.py:204` | Core app exists; operational acceptance is incomplete. |
| 0008 | REST API and heavy-CFD job stubs | fail | no route registration found in `kayakgen/ui/web` | No `/api/evaluate`, `/api/stl`, `/api/hulls`, or `/api/jobs` routes. |
| 0008 | Plot tabs and parity with desktop views | fail | app content only creates `VtkRemoteView` | Cross-section, sheer plan, and plan view are not ported. |
| 0008 | Playwright/Lighthouse/Docker proof | partial | `tests/test_web.py` says full app/Playwright are manual/deferred | No automated browser smoke, Lighthouse result, or Docker build evidence. |

## Findings

### F-TRACE-001 - RFC status and project guidance are stale

- Severity: major
- RFC: 0002-0008 index/status
- File(s): `docs/rfcs/README.md`, `AGENTS.md`, `pyproject.toml`, `kayakgen/cli/main.py`
- What you found: The RFC index still marks every non-template RFC through
  0008 as `proposed`, and AGENTS says RFC 0007 has not landed and to expect
  the flat-file layout. The code now has a package, CLI, tests, shims, web
  module, and Dockerfile.
- Suggested remediation: Update RFC statuses with accepted/landed/partial
  state, and update AGENTS current direction so future agents do not treat
  the package extraction as pending.
- Evidence: `rg --files` shows `kayakgen/`, `tests/`, `pyproject.toml`, and
  `Dockerfile`; `.venv/bin/python -m pytest -q` returned 59 passed.

### F-TRACE-002 - RFC 0004 plumb-bow acceptance is not met end-to-end

- Severity: major
- RFC: 0004 acceptance criteria
- File(s): `docs/rfcs/0004-plumb-bow.md`, `kayakgen/model/geometry.py`,
  `kayakgen/ui/pv_window.py`, `tests/test_plumb_bow.py`
- What you found: The package model supports `bow_rake`, but exact-stem
  section area at x = -L/2 is zero. The PyVista 3D window drops `bow_rake`
  and `beam_wl` when rebuilding from GUI params, so the 3D acceptance path
  cannot reflect those sliders. The mesh has open boundary edges, so the
  RFC's watertight wording is not true for the current separate surface model.
- Suggested remediation: Either implement an explicit plumb stem/end-cap or
  amend the RFC to say near the stem/inside transition. Add `bow_rake` and
  `beam_wl` to `kayakgen/ui/pv_window.py` mapping and add GUI-to-3D parity
  tests.
- Evidence: Probe returned `section_area(-L/2) == 0.0`; boundary-edge check
  found open boundary edges.

### F-TRACE-003 - RFC 0005 resistance acceptance is over-claimed

- Severity: major
- RFC: 0005 acceptance criteria
- File(s): `docs/rfcs/0005-cfd-resistance.md`, `kayakgen/eval/resistance.py`,
  `tests/test_resistance.py`, `kayakgen/ui/desktop.py`
- What you found: The code documents a known Michell limitation, and the
  low-Fn acceptance criterion fails badly: at Fn = 0.1, wave drag should be
  less than 5 percent of viscous drag, but the measured ratio was about
  162340. The default `resistance_curve` also exceeded the RFC's 200 ms
  budget in this environment, while the test budget is 5000 ms. There is no
  desktop or web Resistance Curve button despite the RFC proposal.
- Suggested remediation: Fix or gate the Michell implementation before
  claiming RFC 0005 acceptance, restore tests to the RFC thresholds, and add
  the curve UI or explicitly defer it in the RFC.
- Evidence: Probe returned `Fn=0.1 Rv=1.716727 Rw=278694.014553`; default
  curve runs were about 269-298 ms.

### F-TRACE-004 - RFC 0006 GUI constraints are only partially landed

- Severity: major
- RFC: 0006 GUI changes and validation banner
- File(s): `docs/rfcs/0006-design-constraints.md`, `kayakgen/ui/desktop.py`,
  `docs/rfcs/0002-0003-audit.md`
- What you found: Class presets exist and seed values, but selecting a class
  does not set slider ranges, switching to Custom does not relax to the RFC
  0006 global envelope, and the validation banner is explicitly left out in
  the audit while the RFC still presents it as proposed behavior.
- Suggested remediation: Implement class-specific range mutation and the
  advisory/banner behavior, or revise RFC 0006 to mark those pieces deferred
  and update acceptance criteria accordingly.
- Evidence: Current sliders still expose broad ranges such as beam
  0.30-0.90 m; class selection only calls `set_val`.

### F-TRACE-005 - RFC 0008 web completion is materially incomplete

- Severity: major
- RFC: 0008 REST API, tests, acceptance criteria
- File(s): `docs/rfcs/0008-web-frontend.md`, `kayakgen/ui/web/app.py`,
  `kayakgen/ui/web/controllers.py`, `tests/test_web.py`
- What you found: The Trame app has sliders, a VTK view, metrics, and STL
  helper functions, but there are no REST route registrations for
  `/api/evaluate`, `/api/stl`, `/api/hulls`, or `/api/jobs`. The plot tabs
  described by the RFC are absent, and tests explicitly avoid launching the
  full app or running Playwright.
- Suggested remediation: Split RFC 0008 into core Trame shell landed and
  API/ops parity pending, or implement the missing routes, plot tabs,
  Playwright smoke, Docker build check, and Lighthouse check.
- Evidence: Search for API route registrations found only controller
  docstrings and tests.

### F-TRACE-006 - Acceptance tests drift from RFC criteria

- Severity: major
- RFC: 0004, 0005, 0008
- File(s): `tests/test_plumb_bow.py`, `tests/test_resistance.py`,
  `tests/test_web.py`
- What you found: The test suite passes, but several tests verify weaker or
  different claims than the RFCs. RFC 0004's exact stem criterion is tested
  near the stem; RFC 0005's Wigley check reimplements a local calculation
  rather than exercising production geometry through the standard hull API;
  RFC 0005's performance budget is relaxed to 5000 ms; RFC 0008 browser
  smoke is manual/deferred.
- Suggested remediation: Add a traceability test list keyed to RFC criteria,
  with explicit `xfail` or `deferred` markers where the team intentionally
  postpones acceptance.
- Evidence: `.venv/bin/python -m pytest -q` passed all 59 tests despite the
  command-level RFC 0004 and RFC 0005 failures above.
