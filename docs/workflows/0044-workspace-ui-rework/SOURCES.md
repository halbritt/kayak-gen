# Sources - workflow 0044 workspace UI rework

## Required reading

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/design/kayak_hull_design_constraints.md`
- `docs/rfcs/0008-web-frontend.md`
- `docs/rfcs/0010-cfd-ready-mesh-contract.md`
- `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md`
- `docs/rfcs/0018-web-cfd-job-routes.md`
- `docs/rfcs/0025-cfd-calibration-claim-gates.md`
- `docs/rfcs/0031-design-constraint-surfacing-revision.md`
- `docs/rfcs/0033-workspace-ui-rework.md`
- `CLAUDE_DESIGN_UI_REWORK_PROMPT.md`
- `docs/workflows/0042-design-constraint-surfacing-revision/workflow.json`
- `kayakgen/eval/claims.py`
- `kayakgen/eval/mesh_diagnostics.py`
- `kayakgen/eval/mesh_package.py`
- `kayakgen/eval/cfd/jobs.py`
- `kayakgen/model/advisory.py`
- `kayakgen/model/classes.py`
- `kayakgen/model/hull.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/state.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/gui_params.py`
- `kayakgen/ui/pv_window.py`
- `tests/test_web.py`

## Origin

The product brief for this workflow is the Claude Design "UI Rework
Handoff" bundle authored on 2026-05-13 (chat transcript and
`UI Rework Handoff.md`). RFC 0033 distils the handoff into the
project's RFC conventions. The bundle itself is not stored in the
repo; treat RFC 0033 as the canonical source of record for scope,
copy, and acceptance criteria.

The supporting HTML mock (`Workspace.html` plus `tweaks-panel.jsx`)
shipped with the bundle is illustrative only. Recreate the visual
output via the target codebase (Trame/Vuetify for web, PyQt6 +
matplotlib + PyVista for desktop); do not copy the prototype's React
component structure.

The scaffold includes a dedicated ergonomics/design review lane. That
review must evaluate workflow usability, first-viewport scan path,
control affordances, responsive collapse behavior, accessibility, and
desktop/web conceptual parity before the findings ledger narrows the
implementation slice.
