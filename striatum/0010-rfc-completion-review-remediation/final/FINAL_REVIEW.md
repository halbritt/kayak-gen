# Final review - 0010

author: operator
Date: 2026-05-12
Verdict: accepted

## Coverage check

| Finding | Required action | Status | Evidence |
|---|---|---|---|
| F-001 | fix | pass | `AGENTS.md` and `docs/rfcs/README.md` now distinguish landed vs partial RFCs; RFC 0004/0005/0006/0008 include workflow 0010 status notes. |
| F-002 | fix | pass | `kayakgen/ui/gui_params.py` centralizes GUI-to-Hull conversion; `desktop.py` and `pv_window.py` both use it; `tests/test_gui_params.py` covers `beam_wl` and `bow_rake`. |
| F-003 | fix | pass | `kayakgen/ui/web/controllers.py` adds `/api/evaluate`, `/api/stl`, `/api/hulls`, and 501 job-stub route registration; `tests/test_web.py` covers route registration and payload helpers. |
| F-004 | fix | pass | `hull_from_query_string()` and `create_app(initial_query=...)` seed app state from `?hull=...`; covered by `tests/test_web.py`. |
| F-005 | fix / document compatibility | pass | `Hull` validates explicit `beam_wl_m`; default `None` compatibility is documented and tested in `tests/test_classes.py`. |
| F-006 | fix | pass | `kayakgen/eval/hydrostatics.py` populates `GM0_m` and computes `Cm_actual` against waterline beam; covered by `tests/test_hydrostatics.py`. |
| F-007 | fix abstraction / escalate acceptance gaps | pass | Resistance now uses public `HullGeometry.half_breadth_grid()`. Low-Fn and 200 ms criteria are explicitly xfailed in `tests/test_resistance.py` and RFC 0005 is marked partial. |
| F-008 | fix or defer | pass | Desktop presets now mutate slider ranges and return to global ranges on Custom edits; RFC 0006 status note records that manual visual confirmation is still recommended. |
| F-009 | escalate | pass | RFC 0004 is marked partial and names exact plumb-stem/end-cap semantics as a human design decision. |
| F-010 | defer | pass | RFC 0008 is marked partial and names plot tabs, browser smoke, Lighthouse, and hosted deployment as follow-up work. |
| F-011 | fix / stub | pass | Added `kayakgen sweep` stub plus `kayakgen/model/schema.py`, `kayakgen/eval/cfd.py`, and `kayakgen/search/`; `tests/test_cli.py` covers the CLI stub. |
| F-012 | fix | pass | `Dockerfile` now copies `AGENTS.md` before install; Docker build and `kayakgen --help` smoke succeeded. |
| F-013 | record | pass | `OPERATOR_REPORT.md` and `PATCH_SUMMARY.md` record the dirty/untracked workflow setup as a process finding. |

## Test review

The patch summary's primary gate was rerun from final review:
`.venv/bin/python -m pytest -q` returned 69 passed and 2 xfailed. The two
xfails are the deliberate RFC 0005 acceptance markers for low-Froude
wave/viscous behavior and the 200 ms full-curve budget.

`git diff --check` passed with no whitespace errors. The patch summary also
records successful `.venv/bin/kayakgen --help`, import smoke for
`kayakgen.model.schema` and `kayakgen.eval.cfd`, `docker build -t
kayakgen-striatum-check .`, and `docker run --rm kayakgen-striatum-check
kayakgen --help`. Ruff could not be run because it is not installed in the
repo virtual environment.

## Verdict notes

Accepted. All actionable-now ledger findings are either fixed or explicitly
escalated/deferred in the RFC text and tests. The remaining risks are not
hidden: RFC 0004 exact stem/end-cap semantics need a human decision, RFC 0005
is still an exploratory resistance filter rather than accepted final physics,
RFC 0006 should still get a manual desktop visual check, and RFC 0008 needs
browser/Lighthouse and plot-tab follow-up work.
