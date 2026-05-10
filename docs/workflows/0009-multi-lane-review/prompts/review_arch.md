# Task — review architecture / package layout / RFC 0007 acceptance

Read `SOURCES.md`, `docs/rfcs/0007-architectural-revisit.md`, and the
contents of `kayakgen/`. Write your review at
`striatum/0009-multi-lane-review/gemini/REVIEW_ARCH.md`.

Use the same finding template as the other reviewers (see
`prompts/review_math.md`); IDs use the prefix `F-ARCH-NNN`.

## Specific things to verify

1. **Package layout vs. RFC 0007 §1.** Walk the directory tree. Is
   every promised module present? Are responsibilities respected
   (no math in `ui/`, no UI in `model/`, etc.)?
2. **Hull aggregate (`kayakgen/model/hull.py`).** Pydantic v2 schema,
   `extra="forbid"`, the `to_geometry` factory, the `hash` cache key.
   Does it match RFC 0007 §2 verbatim?
3. **HullGeometry ABC (`kayakgen/model/geometry.py`).** Required
   methods (`section`, `mesh`, `waterplane`, `keel_line`,
   `deck_centreline`, `section_area`). Are private helpers truly
   private — does any consumer reach across the abstraction?
   `grep -n '_get_area_fraction\\|_get_deck_height_scaling' kayakgen/ui/`
   should be empty (per RFC 0007 acceptance criterion).
4. **Evaluation contract (`kayakgen/eval/contract.py`).** Is
   `EvaluationResult` the union RFC 0007 §5 promised? Are
   `ResistanceCurve`, `GZCurve`, `CfdResult` slot-stubs ready for
   future evaluators?
5. **CLI surface (`kayakgen/cli/main.py`).** Walk every subcommand:
   `init`, `generate`, `evaluate`, `view`, `serve`. Argument shapes,
   exit codes, the `--skip-resistance` opt-out, the
   `kayakgen[desktop]` / `kayakgen[web]` extras handling.
6. **Backwards-compat shims (`generator.py`, `gui.py`,
   `pyvista_view.py`).** Do they preserve the prior API surface?
   Does `python gui.py` still work via the desktop extras?
7. **RFC-by-RFC acceptance walkthrough.** For each of RFCs 0004,
   0005, 0006, 0007, 0008, 0002/0003 audit, copy the
   "Acceptance Criteria" section into your review and tick / cross
   each item against the current code. Cite the file path that
   satisfies (or fails) the criterion.

Skip math correctness (sent to `reviewer_math`) and process / commit
hygiene (sent to `reviewer_integrity`). Forward anything you spot in
those tracks as a "see also" note rather than your own finding.
