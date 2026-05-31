# SOURCES — 0040 nested-key search variables

Per-run context manifest. Every entry is required reading for both
the implementer and the reviewer; the workflow loader pins them on
each job's fresh session.

## RFC + Motivation

- `docs/rfcs/0063-nested-key-search-variables.md` — the RFC being
  landed. Read this first; it owns the design.
- The 2026-05-30 Epic 18X Sport search exercise that surfaced the
  gap. Empirically, attempting to vary
  `distribution_v2.cross_section_family` across NSGA-II / EHVI ticks
  forced a hand-authored fallback: 5 hull JSONs evaluated via
  `kayakgen evaluate` per family, no Pareto direction signal across
  the categorical axis. RFC 0063 references this as the motivating
  observation.

## Code to edit

- `kayakgen/search/active/runner.py:166-169` — the current
  `_hull_from_genome` implementation:

  ```python
  def _hull_from_genome(spec: SearchSpec, genome: dict[str, Any]) -> tuple[Hull, dict[str, Any]]:
      attempted = dict(spec.base_hull) | dict(genome)
      hull = Hull.model_validate(attempted)
      return hull, attempted
  ```

  RFC 0063 §"Proposal" step 2 sketches the replacement.

- `kayakgen/search/active/spec.py:165-189` — `SearchSpec` itself.
  Add a `model_validator(mode="after")` that walks each dotted-path
  key in `search_space.keys()` against
  `Hull.model_validate(spec.base_hull)` and surfaces a clear error
  for missing paths. Per RFC 0063 §"Proposal" step 3.

## Code to mirror (read-only)

- `kayakgen/model/hull.py` — the Hull aggregate. Read to understand
  which fields a dotted path can legitimately target.
- `kayakgen/model/distribution_v2.py` — the `DistributionV2Spec`
  and the `CrossSectionFamily` literal. The motivating use case is
  varying `cross_section_family` (categorical) and `deadrise_deg`
  (continuous). Note the discriminated-union `LongitudinalDistribution`
  shape; RFC 0063 explicitly excludes varying the `kind` discriminator
  itself (§"Open Questions" recommends rejecting that).

## Examples / tests to mirror

- `docs/examples/search_touring_sea_kayak_pareto.json` — the
  existing flat-key example. The new RFC must keep this byte-stable
  (Acceptance Criteria #3).
- `tests/` — pick the closest existing active-search test as the
  shape to mirror. Look for files matching
  `test_active_search*` or `test_search_spec*`; copy the import and
  setup patterns rather than reinventing them.

## Cross-references

- RFC 0044 — defines NSGA-II v1 + the original
  `SearchSpec.search_space` shape.
- RFC 0047 — defines EHVI v2; same `search_space` consumer.
- RFC 0048 — defines `DistributionV2Spec`; the motivating reason
  RFC 0063 exists.

## Out-of-scope reminders

- No new `EvaluatorOptions` knobs.
- No change to the sweep expander
  (`kayakgen/search/sweep.py::expand_candidates`).
- No support for varying `LongitudinalDistribution.kind` mid-search
  (RFC 0063 §"Non-Goals").
- No list-index syntax (`...coefficients.2`) — deferred to a
  follow-on RFC per RFC 0063 §"Open Questions".
