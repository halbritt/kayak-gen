# Implement prompt — workflow 0040

You are landing RFC 0063 (nested-key search variables): extending
`_hull_from_genome` in the active-search runner to support dotted
genome keys like `distribution_v2.cross_section_family`, plus the
matching spec-load-time validator and tests.

Read first:

- `docs/rfcs/0063-nested-key-search-variables.md` — the design.
- `docs/workflows/0040-rfc-0063-nested-key-search-variables/SOURCES.md`
  — per-run context manifest with the exact source lines to edit.
- `kayakgen/search/active/runner.py` — `_hull_from_genome` and
  `_apply_genome` (your new helper).
- `kayakgen/search/active/spec.py` — `SearchSpec` (add the
  model_validator here).
- `kayakgen/model/hull.py`, `kayakgen/model/distribution_v2.py` —
  read-only; the geometry aggregate stays as-is.
- `docs/examples/search_touring_sea_kayak_pareto.json` — the flat-key
  example that must continue to behave byte-identically.

## Deliverables

### 1. `kayakgen/search/active/runner.py` — dotted-path resolver

Add an `_apply_genome` helper above `_hull_from_genome`:

```python
import copy
from typing import Any

def _apply_genome(base: dict[str, Any], genome: dict[str, Any]) -> dict[str, Any]:
    """Overlay genome values onto base, honoring dotted-path keys.

    Flat keys ("length_m") overlay at top level — byte-identical to
    the pre-RFC-0063 ``dict(base) | dict(genome)`` behaviour. Dotted
    keys ("distribution_v2.cross_section_family") traverse into nested
    dicts and set the leaf, raising ValueError if the traversal hits a
    missing or non-dict node.
    """
    attempted = copy.deepcopy(base)
    for key, value in genome.items():
        if "." not in key:
            attempted[key] = value
            continue
        parts = key.split(".")
        cursor = attempted
        for part in parts[:-1]:
            if part not in cursor or not isinstance(cursor[part], dict):
                raise ValueError(
                    f"search variable {key!r} traverses missing or non-dict path "
                    f"at {part!r} (genome must target an existing nested record)"
                )
            cursor = cursor[part]
        cursor[parts[-1]] = value
    return attempted
```

Route `_hull_from_genome` through it:

```python
def _hull_from_genome(spec: SearchSpec, genome: dict[str, Any]) -> tuple[Hull, dict[str, Any]]:
    attempted = _apply_genome(spec.base_hull, genome)
    hull = Hull.model_validate(attempted)
    return hull, attempted
```

The Pydantic validators on `Hull` and recursively
`DistributionV2Spec` catch any post-merge invariant violations and
bubble them up as today's `ValueError` failures.

### 2. `kayakgen/search/active/spec.py` — spec-load validator

Add a `model_validator(mode="after")` on `SearchSpec` that walks each
dotted-path key against a synthesized hull built from `base_hull`:

```python
from kayakgen.model.hull import Hull

@model_validator(mode="after")
def _validate_dotted_search_keys(self) -> "SearchSpec":
    if not any("." in key for key in self.search_space):
        return self
    try:
        synthesized = Hull.model_validate(self.base_hull)
    except Exception as exc:
        raise ValueError(
            f"cannot validate dotted-path search keys: base_hull does not validate as a Hull ({exc})"
        ) from exc
    payload = synthesized.model_dump()
    for key in self.search_space:
        if "." not in key:
            continue
        parts = key.split(".")
        cursor: Any = payload
        for part in parts[:-1]:
            if not isinstance(cursor, dict) or part not in cursor:
                raise ValueError(
                    f"search variable {key!r} traverses missing field at {part!r} "
                    f"(synthesized hull from base_hull has no such nested record)"
                )
            cursor = cursor[part]
        if not isinstance(cursor, dict) or parts[-1] not in cursor:
            raise ValueError(
                f"search variable {key!r} terminates at unknown leaf {parts[-1]!r}"
            )
    return self
```

### 3. `tests/test_active_search_nested_keys.py` (new)

Required tests (function names verbatim per RFC 0063 §"Acceptance
Criteria"):

- `test_dotted_path_overlays_distribution_v2` — build a SearchSpec
  with `base_hull.geometry_kind="distribution_v2"`, a populated
  `distribution_v2` block, and a search variable
  `distribution_v2.cross_section_family` as a `ChoiceVariable`
  values `["round", "shallow_arch", "shallow_v"]`. Run a minimal
  NSGA-II budget (population_size 6, generations 1) with
  evaluators `hydrostatics=True` only. Assert: the final run.json
  contains at least one candidate per family declared in the
  choices that did not get marked `constraint_failed`.

- `test_missing_dotted_path_rejected_at_spec_load` — build a
  SearchSpec with a search variable
  `distribution_v2.no_such_field`. Assert `SearchSpec.model_validate`
  raises `ValidationError` (or `ValueError` wrapped) with a message
  that mentions the offending key and the missing leaf.

- `test_flat_keys_byte_identical_after_refactor` — load
  `docs/examples/search_touring_sea_kayak_pareto.json`, run it with a
  fixed seed against `/tmp/<tmpdir>/before` (using a checked-in
  baseline `run.json` snapshot built before this refactor) and
  against `/tmp/<tmpdir>/after` (the current code). Assert the two
  `run.json` documents are byte-identical after stripping nondeterministic
  fields (`realized_wall_clock_seconds` if present).

Optionally also add:

- `test_dotted_path_handles_top_level_fields_too` — a sanity test
  that a `top_level_field` key without dots produces the same
  hull as before.

Mirror the regression-net shape of `tests/test_hull_parameter_metadata.py`
where applicable.

### 4. `docs/examples/search_distribution_v2_section_family.json` (new)

Exactly the spec body shown in RFC 0063 §"Acceptance Criteria",
filled in with a realistic budget (population_size 12, generations
3, max_evaluations 48). Use the conservative default objectives
(no exploratory opt-in, no resistance evaluator) so the example
runs in under 5 minutes.

### 5. Status flip on RFC 0063 + index row

In `docs/rfcs/0063-nested-key-search-variables.md`:

- Change `Status: proposed` → `Status: landed`.
- Append a "Landed by" line under the status:
  `Landed by: workflow 0040-rfc-0063-nested-key-search-variables on 2026-05-31`.

In `docs/rfcs/README.md`:

- Update the 0063 row's status column from `proposed` to `landed`.
- Append `Landed via workflow 0040.` to the row's summary.

### 6. `docs/workflows/0040-rfc-0063-nested-key-search-variables/PATCH_SUMMARY.md`

Required artifact. Use the standard patch-summary shape:

- Files changed (with line counts)
- Pytest output summary (test count, pass/fail/skip)
- One paragraph describing the dotted-path resolver behaviour
- One paragraph describing the spec-load validator behaviour
- One paragraph confirming flat-key byte-stability proof

## Verification

Before closing, run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_active_search_nested_keys.py \
  tests/test_active_search.py \
  tests/test_search_spec.py \
  -q
```

If `tests/test_active_search.py` or `tests/test_search_spec.py` do
not exist in the repo, substitute the closest existing active-search
test files and document the substitution in PATCH_SUMMARY.md.

## Scope discipline

You may write only to the paths listed in
`workflow.json::jobs[0].write_scope.allowed_paths`. In particular,
you must NOT touch `kayakgen/model/hull.py`,
`kayakgen/model/distribution_v2.py`, or
`kayakgen/search/sweep.py`. The geometry aggregate and sweep
expander are out of scope per RFC 0063 §"Non-Goals".
