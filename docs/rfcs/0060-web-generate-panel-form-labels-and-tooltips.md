# RFC 0060: Web Generate-Panel Form Labels and Tooltips

Status: landed
Date: 2026-05-22
Context:
[`RFC 0057`](0057-generative-search-jobs-and-web-workspace.md),
[`RFC 0059`](0059-three-lane-code-and-doc-audit-workflow.md),
[`docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`](../audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md)
finding AUD-O-003,
[`kayakgen/ui/web/generate_spec_form.py`](../../kayakgen/ui/web/generate_spec_form.py),
[`kayakgen/ui/desktop.py`](../../kayakgen/ui/desktop.py),
[`kayakgen/search/objectives.py`](../../kayakgen/search/objectives.py)
`ObjectiveMetadata`

## Problem

The audit finding AUD-O-003 (medium) names a real UX gap in the RFC 0057
stage-4 Trame Generate panel:

- `kayakgen/ui/web/generate_spec_form.py:86-92` declares
  `BASE_HULL_KEYS = ("length_m", "beam_oa_m", "beam_wl_m", "draft_m",
  "Cp")` and the form-builder uses the raw JSON parameter names as field
  labels in the variable-selector picklist + as default-row content.
- The same raw key appears in
  `DEFAULT_VARIABLE_ROW = {"name": "beam_wl_m", ...}` (line ~98 onward)
  with no human-readable hint of what `beam_wl_m` controls.
- The objectives picklist (lines ~1016-1050) renders each selected
  metric as the bare metric name (`GM0_m`, `displaced_mass_kg`) inside
  a `<span class='kg-generate-objective-metric'>`. The metric registry
  already carries a friendly `label` and `unit` on
  `kayakgen.search.objectives.ObjectiveMetadata` (lines 36-39); the web
  form does not consult them.
- The desktop GUI (`kayakgen/ui/desktop.py:83-96` `SLIDERS` table) has
  friendly labels for the same parameters ("Beam WL (m)", "Prismatic
  Coeff") under different keys (`beam_wl` vs `beam_wl_m`). The desktop
  UX is the better one and the gap is visible to anyone who uses both.

The pattern of "raw schema name surfaced as UI label" is the classic
file-as-control-plane sibling: not a correctness issue, but it slows down
the first kayak designer who is not also a kayakgen developer.

## Goals

- Define a single `HullParameterMetadata` value object that carries
  `label`, `unit`, and `description` for each hull parameter accessible
  from the web Generate panel.
- Land a registry `HULL_PARAMETER_METADATA` keyed by JSON parameter name
  (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`,
  `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`,
  `stern_rake`, plus the existing distribution-v2 controls if the form
  exposes them today; the registry can grow additively).
- Render the registry's labels as field labels + the descriptions as
  Vuetify tooltips in:
  - the variable-selector picklist (`<VSelect>` items list);
  - the base-hull rail (each rendered key's section header);
  - the default-variable-row pre-population (preserve the JSON name as
    the form value but show the label in the UI).
- For the objectives picklist, source labels + units from the existing
  `OBJECTIVE_METADATA[metric].label` + `.unit` rather than re-defining
  them.
- Keep the form's submission payload byte-stable. The label registry is
  presentation-only. Existing snapshot tests and the form's submitted
  spec JSON must not change.
- Land a small regression test that asserts every key in
  `BASE_HULL_KEYS` (plus any other keys the form actually renders today)
  has a registry entry — same regression-net shape as
  `tests/test_vocabulary_coverage.py` (D001).

## Non-Goals

- Migrating the desktop GUI's `SLIDERS` table to the new registry. The
  desktop UX is already adequate; converging the two surfaces is a
  follow-up RFC.
- Internationalization or operator-configurable labels.
- Adding tooltips elsewhere in the Trame workspace (frontier hover,
  comparison report, etc.). Scope is the Generate panel only.
- Introducing new hull parameters or new evaluators. The registry is a
  presentation layer over the existing schema.
- Changing the form's submitted JSON payload. Round-trip equality with
  current snapshot fixtures is a hard requirement.
- Changing what is admissible as an objective (RFC 0044 admissibility
  gates remain authoritative).

## Proposal

### 1. The value object

Add `kayakgen/ui/parameter_metadata.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class HullParameterMetadata(BaseModel):
    """Presentation-layer label / unit / description for one hull
    parameter exposed by the web Generate panel form.

    Fields are presentation-only; the form's submitted JSON payload uses
    the original parameter name (the registry key), not any of these
    fields.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str | None = None
    description: str = Field(min_length=1)
```

### 2. The registry

Same module:

```python
HULL_PARAMETER_METADATA: dict[str, HullParameterMetadata] = {
    "length_m": HullParameterMetadata(
        parameter="length_m",
        label="Length",
        unit="m",
        description="Overall length, bow tip to stern tip.",
    ),
    "beam_oa_m": HullParameterMetadata(
        parameter="beam_oa_m",
        label="Beam OA",
        unit="m",
        description="Overall beam at the widest cross-section.",
    ),
    "beam_wl_m": HullParameterMetadata(
        parameter="beam_wl_m",
        label="Beam WL",
        unit="m",
        description="Beam at the design waterline.",
    ),
    "draft_m": HullParameterMetadata(
        parameter="draft_m",
        label="Draft",
        unit="m",
        description="Vertical distance from waterline to deepest point.",
    ),
    "deck_height_m": HullParameterMetadata(
        parameter="deck_height_m",
        label="Deck height",
        unit="m",
        description="Vertical distance from waterline to deck sheer.",
    ),
    "Cp": HullParameterMetadata(
        parameter="Cp",
        label="Prismatic coefficient (Cp)",
        unit=None,
        description=(
            "Volume coefficient: displaced volume divided by midship "
            "area times waterline length. Higher = fuller ends."
        ),
    ),
    "Cm": HullParameterMetadata(
        parameter="Cm",
        label="Midship coefficient (Cm)",
        unit=None,
        description=(
            "Midship-section coefficient: midship area divided by "
            "(beam_wl × draft). Higher = fuller midsection."
        ),
    ),
    "deck_flatness": HullParameterMetadata(
        parameter="deck_flatness",
        label="Deck flatness",
        unit=None,
        description=(
            "Dimensionless deck-crown flatness control; higher = flatter "
            "deck (less crown)."
        ),
    ),
    "center_box_ratio": HullParameterMetadata(
        parameter="center_box_ratio",
        label="Parallel mid-body ratio",
        unit=None,
        description=(
            "Fraction of length occupied by the parallel mid-body "
            "section (0 = pure fish-form, 1 = fully prismatic)."
        ),
    ),
    "bow_rake": HullParameterMetadata(
        parameter="bow_rake",
        label="Bow rake",
        unit=None,
        description=(
            "Bow-end fullness: 0 = plumb stem, 1 = legacy raked taper. "
            "Dimensionless; reverse rake and values outside [0, 1] are "
            "invalid."
        ),
    ),
    "stern_rake": HullParameterMetadata(
        parameter="stern_rake",
        label="Stern rake",
        unit=None,
        description=(
            "Stern-end fullness: 0 = plumb transom, 1 = legacy raked "
            "taper. Same shape as bow_rake."
        ),
    ),
}
```

If the form later exposes distribution-v2 controls, those land
additively in the same registry (one entry per parameter).

### 3. Helper API

Same module:

```python
def label_with_unit(parameter: str) -> str:
    """Return ``label (unit)`` for use as a Vuetify field label.

    Returns the raw parameter name if the registry has no entry for it.
    Callers should not rely on this fallback in production; the
    regression test below pins the contract.
    """

    metadata = HULL_PARAMETER_METADATA.get(parameter)
    if metadata is None:
        return parameter
    if metadata.unit is None:
        return metadata.label
    return f"{metadata.label} ({metadata.unit})"


def description(parameter: str) -> str | None:
    """Return the tooltip text for ``parameter``, or ``None`` if not in the registry."""
    metadata = HULL_PARAMETER_METADATA.get(parameter)
    return metadata.description if metadata is not None else None
```

### 4. Form wiring

In `kayakgen/ui/web/generate_spec_form.py`:

- Import the registry helpers.
- Build `generative_variable_picklist_items` (a new Trame state key) as
  a list of `{"value": "<parameter>", "title": "<label (unit)>"}`
  records — Vuetify's `<VSelect>` `items` prop already supports the
  `value`/`title` shape.
- Render each base-hull section header using `label_with_unit(...)`
  instead of the raw key.
- Attach `description(...)` to each rendered field via Vuetify
  `<VTooltip>` (or an `:hint` prop where the existing field is a
  `<VTextField>`).
- For the objectives picklist, set its `items` prop to
  `[{"value": metric, "title": f"{OBJECTIVE_METADATA[metric].label} ({OBJECTIVE_METADATA[metric].unit})"} ...]`
  rather than the bare metric names.
- The submission payload keeps using the original parameter / metric
  names. Verify by re-running the existing snapshot tests.

### 5. Regression test

`tests/test_hull_parameter_metadata.py`:

- Assert every key in `BASE_HULL_KEYS` has a `HULL_PARAMETER_METADATA`
  entry.
- Assert every entry's `label`, `description`, and (if non-None) `unit`
  are non-blank trimmed strings.
- Assert the registry has no entries for keys not in the form's actual
  parameter surface (catches stale registry rows after a form refactor).
- Snapshot the submission JSON for the default form state to confirm
  the payload is byte-stable through the wiring change.

## Acceptance Criteria

- `kayakgen/ui/parameter_metadata.py` lands with the value object, the
  registry, and the two helper functions.
- The web Generate-panel form renders friendly labels + tooltips for
  every key in `BASE_HULL_KEYS` and for every objective metric the
  objectives picklist surfaces.
- `kayakgen/ui/web/generate_spec_form.py` continues to submit a
  byte-stable JSON payload; existing snapshot / round-trip tests pass.
- `tests/test_hull_parameter_metadata.py` lands and pins the registry
  contract.
- `tests/test_vocabulary_coverage.py` gains a parametric assertion that
  every `HULL_PARAMETER_METADATA` key resolves to a `Hull` field name
  (i.e. the registry cannot drift from the actual schema).
- `docs/USER_GUIDE.md` Generate-panel section briefly mentions the
  hover-for-description affordance.
- `docs/UBIQUITOUS_LANGUAGE.md` gains a `HullParameterMetadata` glossary
  entry.

## Open Questions

- Should `HullParameterMetadata` carry a `default_min` / `default_max`
  pair so the default-variable-row range comes from the registry too?
  (Today `DEFAULT_VARIABLE_ROW` hard-codes `0.46`-`0.54` for
  `beam_wl_m`.) Defer to a successor.
- Should the desktop `SLIDERS` table migrate to the same registry?
  Recommended: yes, in a separate small RFC.
- Should objective-metric descriptions land on `ObjectiveMetadata`
  itself (additive field) rather than living in a parallel UI-only
  registry? Recommended: yes if descriptions remain stable; otherwise
  keep them in the web-side label module to avoid coupling the search
  layer to presentation concerns.
- Should `availability_conditions` be surfaced as a "why is this metric
  greyed out?" tooltip on objectives that fail the admissibility gate?
  Defer to a successor.

## Implementation Path

- Step 1 — Land this RFC as `proposed` and add its row to
  `docs/rfcs/README.md`.
- Step 2 — Scaffold `docs/workflows/0033-web-generate-panel-labels/`
  with the standard workflow.json + RUNBOOK + prompts + roles shape.
- Step 3 — Drive workflow 0033: land `parameter_metadata.py`, wire the
  form, write the regression test, and verify byte-stable submission.
- Step 4 — Promote this RFC to `landed` once Step 3 is complete. Add a
  `CHANGELOG.md ### Added` entry referencing AUD-O-003 and the workflow
  run.

## Domain Modeling

`HullParameterMetadata` is a value object in DDD terms — frozen,
extra-forbidden Pydantic model, no identity. The `HULL_PARAMETER_METADATA`
registry is a service catalog: a single source of truth that the
presentation layer consults. It does NOT participate in any aggregate
boundary; the `Hull` aggregate's invariants remain owned by
`kayakgen.model.hull.Hull` and its validators.

The decision not to add `description` to `ObjectiveMetadata` (per Open
Question 3) keeps the search-layer model focused on admissibility and
display formatting; presentation prose lives in the UI layer. A future
RFC may merge the two if the description text proves invariant under
search refactors.
