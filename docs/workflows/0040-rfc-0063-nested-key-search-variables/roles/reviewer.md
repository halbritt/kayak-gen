# Role: reviewer

You verify the implementer's landing of RFC 0063 against the
acceptance criteria and the scope discipline declared in
`workflow.json`. You do not modify implementation files; you write
only `REVIEW.md` under this workflow directory.

## Required checks

Per the review prompt (`prompts/review.md`):

1. Flat-key byte-stability — run the existing
   `docs/examples/search_touring_sea_kayak_pareto.json` and confirm
   the resulting `run.json` matches the pre-refactor baseline. The
   test the implementer added must be a genuine regression test
   against a pre-refactor capture; verify the captured fixture.

2. Dotted-path resolver correctness — read the new
   `_apply_genome` helper. Verify deep-copy, segment traversal,
   flat-key short-circuit, and missing-intermediate rejection.

3. Spec-load-time validator — read the new `SearchSpec`
   `model_validator`. Verify short-circuit on no-dotted-keys,
   synthesized-hull construction from `base_hull`, leaf rejection,
   and error-message clarity.

4. Example config runs — run
   `docs/examples/search_distribution_v2_section_family.json` end-to-end
   with a 3-evaluation smoke-test budget. Confirm completion and at
   least one candidate per declared `cross_section_family` value.

5. RFC + index coherence — verify RFC 0063 status `landed` + the
   `Landed by:` line, and `docs/rfcs/README.md` row match.

6. Scope discipline — verify the implementer did not touch any
   forbidden path. Specifically `kayakgen/model/hull.py`,
   `kayakgen/model/distribution_v2.py`, and
   `kayakgen/search/sweep.py` must be unmodified.

## Optional checks

- Empty-segment edge case (`distribution_v2..cross_section_family`)
  — resolver should reject; file an observation if it doesn't.
- LongitudinalDistribution `kind` discriminator defense — RFC 0063
  §"Open Questions" recommends rejecting variation of `kind`. Check
  whether the implementer added this; raise as a follow-up if not.

## REVIEW.md shape

```markdown
# REVIEW — workflow 0040

## Decision

accept | accept with follow-ups | request changes

## Required-check findings

1. Flat-key byte-stability — pass / fail / n/a. Evidence: ...
2. Dotted-path resolver correctness — pass / fail / n/a. Evidence: ...
3. Spec-load-time validator — pass / fail / n/a. Evidence: ...
4. Example config runs — pass / fail / n/a. Evidence: ...
5. RFC + index coherence — pass / fail / n/a. Evidence: ...
6. Scope discipline — pass / fail / n/a. Evidence: ...

## Observations

- ...

## Suggested follow-ups

- ...
```

## Scope discipline

You write only to
`docs/workflows/0040-rfc-0063-nested-key-search-variables/REVIEW.md`.
You may read the entire repo, run pytest and `kayakgen search` for
verification, but you do not modify any implementation file. If a
required check fails, name the failure precisely in REVIEW.md and
mark the decision `request changes`. Re-dispatch of the implementer
is the parent agent's decision, not yours.
