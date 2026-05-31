---
author: implementer-claude-opus-4.7-001
---

# PATCH_SUMMARY — workflow 0040 (RFC 0063)

Lands RFC 0063 "Nested-key search variables for active-search runner":
dotted-path keys in `SearchSpec.search_space` (e.g.
`distribution_v2.cross_section_family`) now overlay onto nested records of
the synthesized Hull, and typos are rejected at spec-load time instead of
at first-candidate evaluation.

## Files changed

| File | Lines | Kind |
| --- | --- | --- |
| `kayakgen/search/active/runner.py` | +37 / −2 | modify |
| `kayakgen/search/active/spec.py` | +47 / −0 | modify |
| `tests/test_active_search_nested_keys.py` | +407 / −0 | new |
| `docs/examples/search_distribution_v2_section_family.json` | +40 / −0 | new |
| `docs/rfcs/0063-nested-key-search-variables.md` | +2 / −1 | modify (status flip) |
| `docs/rfcs/README.md` | +1 / −1 | modify (index row) |
| `docs/workflows/0040-rfc-0063-nested-key-search-variables/PATCH_SUMMARY.md` | new | artifact |

## Pytest summary

Verification command:

```bash
.venv/bin/pytest \
  tests/test_active_search_nested_keys.py \
  tests/test_active_search_spec.py \
  tests/test_active_search_runner.py \
  -q
```

Result: **28 passed in 36.59s, 0 failed, 0 skipped**. The implement prompt
asks for `tests/test_active_search.py` and `tests/test_search_spec.py`;
neither exists. Substituted `tests/test_active_search_runner.py` (closest
runner integration coverage) and `tests/test_active_search_spec.py`
(closest schema/validator coverage).

Broader regression scope (every active-search and search-spec test in the
repo):

```bash
.venv/bin/pytest tests/ -k "active_search or search_spec" -q
```

Result: **63 passed, 1159 deselected in 49.70s** — no regressions in the
existing NSGA-II runner, EHVI runner, GP / Pareto / pareto-gate, or the
CLI surface.

## Dotted-path resolver

`_apply_genome(base, genome)` lives above `_hull_from_genome` in
`kayakgen/search/active/runner.py`. It deep-copies the base dict so
mutations never alias back into `spec.base_hull`, then iterates the
genome:

- Flat keys (`"length_m"`) overlay at the top level — byte-identical to
  the pre-RFC-0063 `dict(base) | dict(genome)` behaviour.
- Dotted keys (`"distribution_v2.cross_section_family"`) split on `.`,
  walk every intermediate part, and set the leaf value at the final
  cursor. Missing or non-dict intermediates raise `ValueError` with a
  message naming both the offending dotted key and the failing
  intermediate part, so any failure that slips past the spec-load
  validator (e.g. dynamic genome mutation by a future operator) is still
  debuggable.

`_hull_from_genome` now routes through `_apply_genome` and otherwise
preserves its tuple `(hull, attempted)` shape, so the runner's
candidate-record / failure-path / EHVI surfaces stay byte-stable for
flat-key specs. The pending-record builder also routes through
`_apply_genome` so queued candidates carry the resolved nested-hull
snapshot, with a safe fallback to flat merge if the overlay would have
raised.

## Spec-load validator

`SearchSpec._validate_dotted_search_keys` (in
`kayakgen/search/active/spec.py`) runs as a `model_validator(mode="after")`.
It is a fast no-op when the spec uses only flat keys (so the existing
`docs/examples/search_touring_sea_kayak_pareto.json` shape continues to
load identically — see the byte-stability test below). When at least one
dotted key is declared, the validator synthesizes a full Hull from
`base_hull` via `Hull.model_validate(self.base_hull)` (which fills in
defaults and instantiates every nested `DistributionV2Spec` /
`LongitudinalDistribution` record), dumps it to a payload dict, and walks
every dotted key against the payload. Any missing intermediate, null
intermediate, or unknown leaf raises a `ValueError` (surfaced as
`ValidationError` by Pydantic) whose message names both the offending
search-space key and the failing path component.

A spec that names `distribution_v2.no_such_field` therefore fails at
`SearchSpec.model_validate` time rather than only at evaluation time —
the operator sees the typo on `load_search_spec` instead of waiting for
the first failed candidate.

## Flat-key byte-stability proof

`tests/test_active_search_nested_keys.py::test_flat_keys_byte_identical_after_refactor`
loads `docs/examples/search_touring_sea_kayak_pareto.json` and runs it
twice with `run_search`, into two separate temp dirs. After stripping the
single nondeterministic field (`realized_wall_clock_seconds`), both
`run.json` payloads must compare byte-equal. The test additionally
asserts every candidate's `parameters` dict contains only flat
(no-`.`) keys, ruling out any accidental dotted-key leakage on the
no-dot path. Combined with the broader 63-test sweep above (which
re-exercises all existing seed-and-record byte-stability assertions in
`test_active_search_runner.py`, `test_active_search_v2_runner.py`, and
the NSGA-II / EHVI / GP / Pareto coverage), this establishes that
routing `_hull_from_genome` through `_apply_genome` does not perturb the
no-dot path. Flat-key specs are byte-stable across the refactor.

## Scope discipline

Only paths under the work-packet `write_scope.allowed_paths` were touched:

- `kayakgen/search/active/runner.py`
- `kayakgen/search/active/spec.py`
- `tests/test_active_search_nested_keys.py`
- `docs/examples/search_distribution_v2_section_family.json`
- `docs/rfcs/0063-nested-key-search-variables.md`
- `docs/rfcs/README.md`
- `docs/workflows/0040-rfc-0063-nested-key-search-variables/PATCH_SUMMARY.md`

`kayakgen/model/hull.py`, `kayakgen/model/distribution_v2.py`, and
`kayakgen/search/sweep.py` are untouched per RFC 0063 §"Non-Goals" and
the workflow's `forbidden_paths` list.
