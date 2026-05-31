# Role: implementer

You land RFC 0063 (nested-key search variables) by extending the
active-search runner's genome→hull adapter to support dotted-path
keys and by adding a matching spec-load-time validator and test net.

You add:

- A helper `_apply_genome(base, genome)` in
  `kayakgen/search/active/runner.py` that deep-copies `base`,
  overlays each genome entry, and supports dotted keys via
  segment-by-segment traversal. Flat keys retain the pre-RFC-0063
  one-liner semantics. Missing or non-dict intermediates raise
  `ValueError` with a message naming the offending key and the
  missing path segment.

- A `model_validator(mode="after")` on `SearchSpec` in
  `kayakgen/search/active/spec.py` that walks each dotted-path key
  against a synthesized `Hull.model_validate(spec.base_hull)` at
  spec-load time. Short-circuits when no dotted keys are present.
  Surfaces missing-leaf paths as a clear error.

- `tests/test_active_search_nested_keys.py` with the three required
  tests named in RFC 0063 §"Acceptance Criteria":
  - `test_dotted_path_overlays_distribution_v2`
  - `test_missing_dotted_path_rejected_at_spec_load`
  - `test_flat_keys_byte_identical_after_refactor`
  Plus the optional sanity check
  `test_dotted_path_handles_top_level_fields_too`.

- `docs/examples/search_distribution_v2_section_family.json` —
  exactly the spec body shown in RFC 0063 §"Acceptance Criteria",
  filled in with a runnable conservative-default-objective budget
  (population_size 12, generations 3, max_evaluations 48,
  hydrostatics-only evaluators so the example runs in under 5
  minutes).

You edit:

- `kayakgen/search/active/runner.py::_hull_from_genome` — replace
  the `dict(spec.base_hull) | dict(genome)` one-liner with a call
  to `_apply_genome(spec.base_hull, genome)`.

- `docs/rfcs/0063-nested-key-search-variables.md` — flip status from
  `proposed` to `landed`; append a `Landed by:` line under the
  status pointing at workflow 0040 and the 2026-05-31 land date.

- `docs/rfcs/README.md` — flip the 0063 row's status column and
  append `Landed via workflow 0040.` to the summary cell.

You produce:

- `docs/workflows/0040-rfc-0063-nested-key-search-variables/PATCH_SUMMARY.md`
  with the patch-summary shape described in the implement prompt.

You do not touch:

- `kayakgen/model/hull.py`, `kayakgen/model/distribution_v2.py` —
  the geometry aggregate is read-only. The change is purely in the
  search→hull adapter.
- `kayakgen/search/sweep.py`, `kayakgen/search/objectives.py`,
  `kayakgen/search/pareto.py` — sweep / objective / Pareto code is
  not in scope.
- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md` — parent
  agent territory.

## Operator-facing failure shape

Error messages from the resolver and validator are operator-facing
(they show up in `kayakgen search` stderr and in active-search test
failures). Voice should match existing search errors:

- Resolver miss: `"search variable 'distribution_v2.no_such_field'
  traverses missing or non-dict path at 'no_such_field' (genome must
  target an existing nested record)"`.
- Spec-load miss: `"search variable 'distribution_v2.no_such_field'
  traverses missing field at 'no_such_field' (synthesized hull from
  base_hull has no such nested record)"`.
- Leaf miss: `"search variable 'distribution_v2.no_leaf' terminates
  at unknown leaf 'no_leaf'"`.

Concise, names the offending key and the offending segment. No
emojis, no apologies.

## Test-net shape

Tests must use the project's existing test fixtures and helpers.
Read `tests/conftest.py` and any other tests under `tests/` whose
names contain `active_search` or `search_spec` for the existing
patterns. Mirror them rather than reinventing.

The flat-key byte-stability test is the most important one: it is
the explicit RFC 0063 §"Non-Goals" / §"Acceptance Criteria"
guarantee that no existing search spec regresses. Build the
expected snapshot from a freshly-checked-out `main`-branch capture
of `run.json` (run the example before your changes; commit the JSON
as a fixture under `tests/fixtures/` if no such fixture exists).
Stripping nondeterministic fields (realized wall clock, candidate
hashes that include wall-clock provenance, etc.) is fine — document
which fields you strip in the test docstring.
