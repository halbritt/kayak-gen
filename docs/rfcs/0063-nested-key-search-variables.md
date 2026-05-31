# RFC 0063: Nested-key search variables for active-search runner

Status: landed
Landed by: workflow 0040-rfc-0063-nested-key-search-variables on 2026-05-31
Date: 2026-05-31
Context: RFC 0044 (NSGA-II active search), RFC 0047 (EHVI v2), RFC 0048
(distribution_v2 geometry), `kayakgen/search/active/runner.py::_hull_from_genome`.

## Problem

Today the active-search runner constructs each candidate by flat-overlaying
the search `genome` onto `base_hull`:

```python
def _hull_from_genome(spec: SearchSpec, genome: dict[str, Any]) -> tuple[Hull, dict[str, Any]]:
    attempted = dict(spec.base_hull) | dict(genome)
    hull = Hull.model_validate(attempted)
    return hull, attempted
```

This works fine for top-level `Hull` fields (`length_m`, `beam_oa_m`,
`Cp`, ...) but it cannot reach into nested values:

- `Hull.distribution_v2.cross_section_family` — a categorical knob with
  six legal values; cannot be varied by a `ChoiceVariable`.
- `Hull.distribution_v2.waterline_half_breadth.value` (or
  `.coefficients`, `.knots`) — the actual shape distribution; cannot be
  varied at all without supplying a whole replacement spec dict.
- Same story for `draft_profile`, `section_area_curve`,
  `deck_freeboard`, `rocker`, `deadrise_deg`, `chine_radius_m`,
  `bow_flare_deg`, `multi_chine_count`.

Empirically observed during the 2026-05-30 Epic 18X Sport search
exercise: the only way to sweep cross-section family today is to
hand-author N hull JSONs (one per family, identical otherwise) and
invoke `kayakgen evaluate` on each. That sidesteps the search loop
entirely — no NSGA-II / EHVI direction signal, no Pareto frontier across
the categorical axis.

## Goals

- Allow `SearchSpec.search_space` keys to use a dotted-path syntax
  (e.g. `"distribution_v2.cross_section_family"`,
  `"distribution_v2.deadrise_deg"`) that the runner resolves into
  nested writes on the constructed Hull.
- Preserve flat keys verbatim (no breaking change for existing top-level
  search specs — the example
  `docs/examples/search_touring_sea_kayak_pareto.json` keeps working).
- Make `ChoiceVariable` usable for `cross_section_family` and any
  Literal-typed Pydantic field — the discriminated-union validators in
  `kayakgen.model.distribution_v2` should accept the genome values
  unchanged.
- Surface a structured rejection (with a documented error code) when a
  dotted path either resolves to a non-existent field or violates the
  Pydantic validator after merge, so failures are debuggable.

## Non-Goals

- This RFC does **not** propose a search-side mechanism for varying
  whole `LongitudinalDistribution` records as a unit (e.g. swapping a
  `UniformDistribution` for a `PolynomialDistribution` mid-search). The
  dotted-path mechanism only touches fields within a fixed shape.
- No change to the v1 NSGA-II crossover/mutation operators: continuous
  dotted-path variables still use SBX/polynomial, categorical
  dotted-path variables go through the existing `ChoiceVariable` path.
- No change to `SweepSpec.expand_candidates` — the deterministic sweep
  expander already has a different code path and is not affected.

## Proposal

1. **Genome key syntax.** Allow keys in `search_space` to contain
   dots. A key `a.b.c` means "set `hull.a.b.c = value`" on the
   constructed Hull. Keys without dots retain today's behaviour
   (top-level overlay).

2. **Genome-to-Hull resolution.** Replace the current `dict(spec.base_hull) | dict(genome)`
   one-liner in `_hull_from_genome` with:

   ```python
   def _apply_genome(base: dict, genome: dict) -> dict:
       attempted = copy.deepcopy(base)
       for key, value in genome.items():
           if "." not in key:
               attempted[key] = value
               continue
           parts = key.split(".")
           cursor = attempted
           for part in parts[:-1]:
               if part not in cursor or not isinstance(cursor[part], dict):
                   raise ValueError(f"search variable {key!r} traverses missing or non-dict path at {part!r}")
           cursor[parts[-1]] = value
       return attempted
   ```

   The Pydantic validators on `Hull` (and recursively
   `DistributionV2Spec`, the discriminated `LongitudinalDistribution`,
   the `LoadCase` shapes) catch any post-merge invariant violations and
   bubble them up as today's `ValueError` failures.

3. **Spec validator.** Add a `model_validator` on `SearchSpec` that, for
   each dotted-path key, walks the corresponding path on a synthesized
   `Hull.model_validate(spec.base_hull)` and confirms the traversal
   reaches a writable leaf. This catches typos at spec-load time
   instead of at first-candidate evaluation time.

4. **Reporting.** When a dotted-path variable is involved, the
   `CandidateRecord.parameters` block records the dotted key verbatim
   (no flattening into a nested dict) so comparison tooling stays
   stable on string keys.

5. **EvaluatorOptions stays unchanged.** This RFC only widens the
   search-genome → Hull conversion, not the evaluator-options layer.

## Acceptance Criteria

- A search spec like:

  ```json
  {
    "base_hull": {
      "geometry_kind": "distribution_v2",
      "length_m": 5.49,
      "distribution_v2": {
        "waterline_half_breadth": {"kind": "uniform", "value": 0.25},
        "draft_profile":          {"kind": "uniform", "value": 0.087},
        "section_area_curve":     {"kind": "uniform", "value": 0.012},
        "deck_freeboard":         {"kind": "uniform", "value": 0.15},
        "rocker":                 {"kind": "uniform", "value": 0.0},
        "cross_section_family":   "round",
        "deadrise_deg":           0.0
      }
    },
    "search_space": {
      "length_m": {"kind": "uniform", "min": 5.30, "max": 5.60},
      "distribution_v2.cross_section_family": {
        "kind": "choice",
        "values": ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine"]
      },
      "distribution_v2.deadrise_deg": {"kind": "uniform", "min": 0.0, "max": 15.0}
    },
    ...
  }
  ```

  runs end-to-end without errors and produces candidates whose
  `parameters` dicts carry the dotted keys.

- An invalid dotted-path key (`distribution_v2.no_such_field`) is
  rejected at spec-load time with a clear error.

- An existing spec with only flat keys (e.g.
  `docs/examples/search_touring_sea_kayak_pareto.json`) produces
  byte-identical `run.json` to today — no regression.

- New tests:
  - `tests/test_active_search_nested_keys.py::test_dotted_path_overlays_distribution_v2`
  - `tests/test_active_search_nested_keys.py::test_missing_dotted_path_rejected_at_spec_load`
  - `tests/test_active_search_nested_keys.py::test_flat_keys_byte_identical_after_refactor`

## Open Questions

- Should the dotted-path syntax also support list indexing
  (e.g. `distribution_v2.waterline_half_breadth.coefficients.2` to
  sweep the cubic term of a polynomial distribution)? My
  recommendation: out of scope here, deferred to a follow-on RFC — the
  Pydantic discriminated-union round-tripping is fiddly enough for
  scalar leaves alone.
- Should the spec validator also enforce that any varied
  Pydantic-discriminator field (e.g. `kind` on a distribution) is held
  fixed within a single search run? Probably yes — varying `kind`
  changes the legal sibling fields and would silently break the
  overlay. Recommend rejecting at spec-load time.

## Implementation Path

- Step 1 — Add dotted-path resolver `_apply_genome` in
  `kayakgen/search/active/runner.py`; route `_hull_from_genome` through
  it. Behaviour for flat keys must be byte-identical.
- Step 2 — Add `SearchSpec` model-validator that walks the
  dotted-path keys against a synthesized hull from `base_hull`.
- Step 3 — Add the new tests above plus an end-to-end smoke test that
  runs a tiny NSGA-II budget over `distribution_v2.cross_section_family`
  + `distribution_v2.deadrise_deg` and asserts the resulting Pareto
  frontier contains at least one row per cross-section family that
  passed validation.
- Step 4 — Update `docs/examples/` with a new
  `search_distribution_v2_section_family.json` example.
- Step 5 — Update RFC 0048 cross-references (no schema changes there;
  just a note that nested-key search is now supported).

## Domain Modeling

This RFC does **not** introduce a new aggregate root or value object;
the change is purely in the **search-genome → Hull** adapter. The
`SearchSpec` aggregate gains a derived constraint (dotted-key validity),
but its schema additions are zero (the dotted-path syntax lives in the
existing `search_space: dict[str, SearchVariable]` keys).

Per `DDD.md § "Adding to the model"` this is a **boundary
clarification** between the active-search subdomain and the geometry
aggregate (`Hull` + `DistributionV2Spec`) — it does not change either
domain, only how genomes are translated across the boundary.
