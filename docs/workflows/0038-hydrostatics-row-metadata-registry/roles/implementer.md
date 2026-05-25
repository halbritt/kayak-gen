# Role: implementer

You close audit batch R3 (AUD-O-005) from the 2026-05-25
release_candidate audit by landing RFC 0062 and its implementation:
the third application of the D043 "presentation-layer registry per
surface family" pattern (after RFC 0060 hull parameters and RFC
0061 desktop sliders), this time for hydrostatics rows.

You add:

- `kayakgen/ui/hydrostatics_metadata.py` — `HydrostaticsRowMetadata`
  value object (frozen Pydantic model with `parameter`, `label`,
  `unit`, `description`) plus the `HYDROSTATICS_ROW_METADATA`
  registry, keyed by row id (`displacement`, `wetted_surface`,
  `waterplane_area`, `gm0`, `cp_actual`, `cm_actual`,
  `l_over_bwl`). Mirror the shape of
  `kayakgen/ui/parameter_metadata.py` (which has `parameter`,
  `label`, `unit`, `description`).

- `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` — the RFC
  itself. Follow the RFC 0060 / RFC 0061 structure (Status, Date,
  Context, Problem, Goals, Non-Goals, Proposal, Acceptance,
  Open Questions). Cite RFC 0060, RFC 0061, D043, and audit
  finding AUD-O-005. Status starts as `landed` since the
  implementation lands in the same commit.

- `tests/test_hydrostatics_row_metadata.py` — mirror the regression-
  net shape of `tests/test_hull_parameter_metadata.py`. At minimum:

  - **Schema coverage**: every key referenced by
    `analysis_view_model::hydro_rows` exists in the registry.
  - **Registry contract**: each `HydrostaticsRowMetadata` instance
    has a non-empty `label` and `description`.
  - **Wire-payload stability**: `hydro_rows_from_state(state)`
    output is byte-stable across the refactor for a fixed `Hull`
    input. (Build the expected snapshot from the current source
    behavior before the registry refactor; commit the snapshot as
    a constant in the test file, then refactor the source and
    assert.)

You edit:

- `kayakgen/services/evaluation.py::analysis_view_model` — replace
  the hardcoded `("Displacement", ..., "kg")` tuples with lookups
  against the new registry. The `value` slot keeps its existing
  numeric formatting (`f"{hydro.displaced_mass_kg:.1f}"` etc.); only
  the `label` and `unit` slots are sourced from the registry.

- `docs/rfcs/README.md` — add the 0062 row after 0061, matching the
  existing column shape and style.

You do not touch:

- `kayakgen/services/evaluation.py::mesh_diagnostics_rows_from_state`
  (workflow 0037 owns it; if 0037 has already landed against
  `evaluation.py`, your changes rebase cleanly).
- `kayakgen/services/evaluation.py::hydro_rows_from_state` — it
  stays a pass-through to `analysis_view_model`.
- `kayakgen/ui/parameter_metadata.py` — the sibling registry, read-
  only.
- `kayakgen/ui/web/` — R2 territory.
- `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py` — desktop is unaffected.
- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/audits/README.md`, audit `FINDINGS.md` / `SYNTHESIS.md` /
  `REMEDIATION_PLAN.md` files — parent agent's job.

## Operator-facing copy rules

The seven row descriptions should be one or two sentences each, in
the same voice as the existing `HULL_PARAMETER_METADATA`
descriptions:

- `displacement` — "Displaced mass at the design waterline. Equals
  the kayak's weight including paddler and load when the hull sits
  at the modelled waterline."
- `wetted_surface` — "Hull surface area below the waterline. Drives
  viscous resistance: lower is faster at low speeds."
- `waterplane_area` — "Cross-section area at the waterline.
  Influences pitch and heave responses."
- `gm0` — "Initial metacentric height. Larger values mean stiffer
  initial stability; very small or negative values mean the hull is
  unstable at zero heel."
- `cp_actual` — "Prismatic coefficient computed from the current
  hull geometry. Compare against the rail-input `Cp` to see how
  closely the generated hull tracks the requested shape."
- `cm_actual` — "Midship coefficient computed from the current hull
  geometry. Compare against the rail-input `Cm`."
- `l_over_bwl` — "Length-to-beam ratio at the waterline. Used by
  the class-envelope validity badge."

Adjust freely if a more accurate one-sentence description fits.

## Forbidden behavior changes

- `analysis_view_model(state)` MUST return the exact same dict
  shape (top-level keys + value types) it did before. Only the
  internal *labels* sourced from the new registry change. The
  numeric `value` fields keep their formatting.
- `hydro_rows_from_state(state)` MUST return the same `[{"label",
  "value"}]` shape with the same label strings the registry now
  carries. The regression test pins this.
- No new claim_state literals, no new readiness levels, no new
  contracts. This is a label-source refactor only.

## Coordination with workflow 0037

Both workflows touch `kayakgen/services/evaluation.py`. The two
functions are disjoint:

- 0037 owns `mesh_diagnostics_rows_from_state`.
- 0038 owns `analysis_view_model::hydro_rows`.

If 0037 has already landed on `main`, rebase your branch against
the post-0037 tree before editing. If 0037 has NOT landed yet,
your edits MUST NOT touch the `mesh_diagnostics_rows_from_state`
function body — keep your diff strictly localized to
`analysis_view_model`.
