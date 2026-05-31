---
author: reviewer-claude-opus-4.7-fallback
note: |
  The workflow's declared reviewer lane was gemini/single_shot. The gemini
  supervised lane attached cleanly under tmux but never claimed the queued
  review packet (no F42 turn-driver wrapping was applied to the gemini
  process despite `adapter_capabilities: {"single_shot": true}`; root cause
  is striatum 2.8.0 turn-driver dispatch config that the operator did not
  resolve mid-session). The implement artifact was concrete and complete,
  so the review was performed inline by Claude Opus 4.7 in the operator's
  session against the same acceptance criteria the workflow declares.
  Flagging the substitution explicitly per RFC 0059's "don't pretend a
  lane ran when it didn't" discipline.
---

# REVIEW — workflow 0040

## Decision

**accept**

## Required-check findings

1. **Flat-key byte-stability** — pass. Evidence:
   `tests/test_active_search_nested_keys.py::test_flat_keys_byte_identical_after_refactor`
   runs the existing `docs/examples/search_touring_sea_kayak_pareto.json`
   twice through `run_search`, strips `realized_wall_clock_seconds`, and
   asserts byte-equal `run.json`. Also asserts every candidate's
   `parameters` dict has no dotted keys on the no-dot path. Broader
   regression: 63 active-search and search-spec tests pass with no
   modifications. The implementer's PATCH_SUMMARY also confirms.
2. **Dotted-path resolver correctness** — pass. Evidence:
   `kayakgen/search/active/runner.py:167-195`. `_apply_genome` deep-copies
   `base` (so `spec.base_hull` is never mutated), short-circuits on
   no-dot keys (flat path is the original one-liner equivalent),
   segment-walks dotted keys with non-dict / missing-intermediate /
   non-dict-cursor checks at every step, and sets the leaf. Error
   messages name both the offending key and the failing segment.
   `_hull_from_genome` and `_build_pending_record` both route through it
   so candidate-record and pending-record paths stay consistent.
3. **Spec-load-time validator** — pass. Evidence:
   `kayakgen/search/active/spec.py:191-241`. `_validate_dotted_search_keys`
   short-circuits when no dotted keys are present (no Hull synthesis
   overhead — preserves load latency for existing flat-key examples).
   When dotted keys are present, it synthesizes `Hull.model_validate(base_hull)`
   and walks each key against the dumped payload, rejecting missing
   intermediates, null intermediates, and unknown leaves with messages
   that name the offending key and segment.
4. **Example config runs end-to-end** — pass. Evidence: I ran
   `kayakgen search docs/examples/search_distribution_v2_section_family.json
   --out /tmp/rfc63_smoke_out`. Result: 36 of 48 candidates complete, 0
   failed, 0 constraint_failed; termination_reason=completed.
   Family-count breakdown across the completed candidates:
   `round: 14, deep_v: 8, hard_chine: 8, shallow_v: 4, shallow_arch: 2`.
   All five declared `cross_section_family` choices appear in the run —
   confirming the dotted-path overlay actually drives the loft, not just
   the candidate record.
5. **RFC + index coherence** — pass. Evidence:
   `docs/rfcs/0063-nested-key-search-variables.md` line 3:
   `Status: landed`. Line 4: `Landed by: workflow 0040-rfc-0063-nested-key-search-variables on 2026-05-31`.
   `docs/rfcs/README.md` 0063 row updated to `landed` and references
   workflow 0040.
6. **Scope discipline** — pass. Evidence:
   `git status` shows modifications only under the workflow's declared
   `write_scope.allowed_paths`. `kayakgen/model/hull.py`,
   `kayakgen/model/distribution_v2.py`, and `kayakgen/search/sweep.py`
   are unmodified (verified `git diff` empty for those paths). The
   PATCH_SUMMARY also explicitly lists the touched paths.

## Observations

- The empty-segment edge case (`distribution_v2..cross_section_family`)
  is rejected — `_apply_genome` splits on `.` producing an empty string
  segment, which is then tested with `part not in cursor` and rejected
  cleanly with the same "missing or non-dict path" error message.
  Implicit, but it works.
- The `kind` discriminator defense suggested in RFC 0063 §"Open
  Questions" was not added. A search spec varying
  `distribution_v2.waterline_half_breadth.kind` would silently
  reshape the discriminated union, which the implementer did NOT
  guard against. Suggested follow-up.
- The pending-record builder gained the `_apply_genome` call with a
  fallback to flat merge on `ValueError`, which is a subtle behaviour
  delta from RFC 0063 §"Proposal" (which only mentioned routing
  `_hull_from_genome`). The fallback prevents pending-record creation
  from breaking when a downstream operator hand-injects an invalid
  genome between evaluator runs. Defensible, but worth a one-line note
  in RFC 0063 if the resolver path is ever revisited.

## Suggested follow-ups

- File a follow-on RFC (or extend RFC 0063 with a stage 2) to add the
  `kind`-discriminator guard the open-question recommends. The
  implementation cost is small; the silent-failure mode it prevents is
  the kind of debug-hostile bug that surfaces three sprints later.
- Investigate striatum 2.8.0 gemini single_shot dispatch — the lane
  attested cleanly but never received the F42 turn-driver wrap, so
  the review packet sat queued. Out of scope for this RFC; a
  striatum-side ticket.
