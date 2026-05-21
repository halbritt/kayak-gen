# Implement `cfd_in_loop_evaluator_status` — RFC 0058 stage 2

Read RFC 0058 (section "CFD-in-loop graduation contract"),
`STAGE_2_3_DECISIONS.md` rows D-5 through D-8 and D-15, and the
top of `kayakgen/services/generative_jobs.py`.

Land:

- `cfd_in_loop_evaluator_status(*, registry, hull_scope, persistent_opt_in=None) -> Literal["opt_in_only", "first_class"]`
  in `kayakgen/services/generative_jobs.py`. `registry` is an
  iterable of `StabilityFitRecord`-shaped values; `hull_scope` is a
  `HullFamilyScope` (from `kayakgen.eval.stability.accepted_fit`);
  `persistent_opt_in` is an `Optional[bool]`.
- The helper inspects each record's `hull_family_scope` and the
  `kind` attribute (a structural protocol — `"analytical"` or
  `"cfd_in_loop"`). It returns `"first_class"` only when:
  1. at least one `kind == "analytical"`, `acceptance_verdict == "accepted"`
     record covers `hull_scope`; AND
  2. at least one `kind == "cfd_in_loop"`, `acceptance_verdict == "accepted"`
     record covers `hull_scope`; AND
  3. `persistent_opt_in is not False`.
  Otherwise `"opt_in_only"`.
- A scope-coverage helper is fine to extract privately. Do **not**
  introduce a new field on `StabilityFitRecord` itself.

Tests in `tests/test_cfd_in_loop_evaluator_status.py` (new) must cover:

- empty registry → `"opt_in_only"`;
- analytical-only registry → `"opt_in_only"`;
- CFD-in-loop-only registry → `"opt_in_only"`;
- both present + matching → `"first_class"`;
- both present but persistent_opt_in=False → `"opt_in_only"`;
- both present + persistent_opt_in=True → `"first_class"`;
- both present + persistent_opt_in=None → `"first_class"`;
- non-matching scope on the CFD-in-loop record → `"opt_in_only"`.

Use a small `SimpleNamespace`-style fake record with `kind`,
`hull_family_scope`, and `acceptance_verdict` fields in the tests;
do not add a real `kind` field to `StabilityFitRecord`.

Requirements:

- The helper is additive. Do not touch any existing function in
  `generative_jobs.py`.
- Run focused tests + ruff before publishing.

Write scope:
- `kayakgen/services/generative_jobs.py` (additive)
- `tests/test_cfd_in_loop_evaluator_status.py`

Publish the required patch summary artifact under
`striatum/0056-.../implementation/cfd_in_loop_status/PATCH_SUMMARY.md`.
