# Review prompt — workflow 0040

You are reviewing the implementer's landing of RFC 0063 (nested-key
search variables). Verify that:

## Required checks

1. **Flat-key byte-stability.** Load
   `docs/examples/search_touring_sea_kayak_pareto.json` and run it
   end-to-end. The resulting `run.json` should match the
   pre-refactor behaviour byte-for-byte after stripping
   nondeterministic fields. The new
   `tests/test_active_search_nested_keys.py::test_flat_keys_byte_identical_after_refactor`
   should enforce this; verify the snapshot it compares against is a
   genuine pre-refactor capture (not a regenerated post-refactor
   snapshot that would silently mask drift).

2. **Dotted-path resolver correctness.** Read the
   `_apply_genome` helper. It must:
   - Deep-copy `base` (no mutation of the spec's stored
     `base_hull` dict).
   - Traverse dotted keys segment-by-segment, raising on any
     missing or non-dict intermediate.
   - Leave flat keys completely untouched (no string-split or
     traversal cost in the no-dot case).

3. **Spec-load-time validator.** Read the new `SearchSpec`
   `model_validator`. It must:
   - Short-circuit when no dotted keys are present (no Hull
     synthesis overhead for the existing flat-key examples).
   - Construct a synthesized hull from `base_hull` using
     `Hull.model_validate` (failure here surfaces as a clear
     error about base_hull not validating).
   - Walk each dotted-path key against the synthesized
     `hull.model_dump()` payload and reject missing-leaf paths
     with a message naming the offending key and the missing
     part.

4. **Example config runs.** Run
   `docs/examples/search_distribution_v2_section_family.json`
   end-to-end with a 3-evaluation smoke-test budget override
   (if the file's declared budget is too large, suggest the
   implementer trim it):

   ```bash
   .venv/bin/kayakgen search \
     docs/examples/search_distribution_v2_section_family.json \
     --out /tmp/rfc63_smoke_out
   ```

   Assert the run completes and the resulting candidates include
   at least one per declared `cross_section_family` value.

5. **RFC + index coherence.** Verify
   `docs/rfcs/0063-nested-key-search-variables.md` status is
   flipped to `landed` and carries a `Landed by:` line pointing at
   this workflow. Verify the `docs/rfcs/README.md` row mirrors.

6. **Scope discipline.** Verify the implementer did not touch any
   path under `forbidden_paths` in `workflow.json`. Specifically:
   `kayakgen/model/hull.py`, `kayakgen/model/distribution_v2.py`,
   `kayakgen/search/sweep.py` should all be unmodified relative to
   the workflow branch's base.

## Optional checks (worth raising, not blocking)

- Does the dotted-path syntax cleanly handle an empty-segment edge
  case (`distribution_v2..cross_section_family`)? The resolver
  should reject it; if it silently accepts an empty intermediate
  segment, file an observation.

- Does the spec-load validator reject varying the
  `kind` discriminator on a `LongitudinalDistribution`? RFC 0063
  §"Open Questions" recommends rejection; check whether the
  implementer added this defense and, if not, raise it as a
  follow-up.

## REVIEW.md

Write your findings to
`docs/workflows/0040-rfc-0063-nested-key-search-variables/REVIEW.md`
with sections:

- `## Decision` — `accept` / `accept with follow-ups` / `request changes`.
- `## Required-check findings` — one bullet per numbered check
  above, marked `pass` / `fail` / `n/a`.
- `## Observations` — anything notable but not blocking.
- `## Suggested follow-ups` — if any.

## Scope

You write only to
`docs/workflows/0040-rfc-0063-nested-key-search-variables/REVIEW.md`.
You may not modify implementation files. If a check fails, document
the failure in REVIEW.md and let the parent agent decide whether to
re-dispatch the implementer.
