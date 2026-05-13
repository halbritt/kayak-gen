Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent implementation and verification.
Keep scopes disjoint, preserve this assigned Striatum role, and state what
sub-agent help was used in the artifact.

Implement the safe-now findings from
`striatum/0044-workspace-ui-rework/ledger/FINDINGS.md`.

Use maximal useful sub-agents with disjoint write scopes. Prefer parallel
agents for:

- `kayakgen/ui/theme.py` (colour, type, chip-text tokens; matplotlib
  rcParams; VTK background helper).
- Structured `Advisory` records on `kayakgen/model/advisory.py` (additive
  alongside existing `warnings: tuple[str, ...]`).
- Web shell rework in `kayakgen/ui/web/app.py` and a new
  `kayakgen/ui/web/layout/` package (toolbar, parameter rail, geometry
  viewport, metrics strip, review tabs, status bar).
- Read-model helpers in `kayakgen/ui/web/controllers.py`
  (`evaluation_summary`, `mesh_diagnostics_lines_from_state`,
  `mesh_package_view_model`).
- Desktop touch-ups in `kayakgen/ui/desktop.py`: rename "Generate STLs"
  → "Export STLs", add `Cm` slider via `gui_params.GUI_TO_HULL`, embed
  PyVista via `QDockWidget`, replace hardcoded plot colours with
  `theme.PLOT_PALETTE`, and add the four-segment status bar.
- Tests: `tests/test_web_layout.py` (workspace shell, parameter rail,
  resistance/Stability/Mesh/CFD persistent text, forbidden-string regressions),
  `tests/test_ui_theme.py` (orphan-colour-literal lint and
  `vtk_background_rgb` parity), and accessibility checks where feasible.
- Docs and changelog updates.

Keep one agent responsible for final integration so the chips, banners, and
status bar are sourced from `theme.py` consistently.

Write
`striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md` with files
changed, findings addressed, sub-agent help used, and verification
commands/results.

Do not turn advisory warnings into hard failures. Do not introduce new
backend capabilities. Do not change the JSON shape of `/api/evaluate`,
`/api/stl`, `/api/cfd/*`, or `/api/hulls/*`. Do not change the share URL
round-trip behaviour. Do not update the root `OPERATOR_REPORT.md`. Do not
include any byline or any line beginning with `author:`.
