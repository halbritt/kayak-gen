# Role: reviewer

You verify the implementer's RFC 0062 + `HydrostaticsRowMetadata`
registry close audit batch R3 (AUD-O-005) from the 2026-05-25
release_candidate audit.

You confirm:

- **Registry shape.** `kayakgen/ui/hydrostatics_metadata.py`
  defines `HydrostaticsRowMetadata` as a frozen Pydantic model with
  `parameter`, `label`, `unit`, and `description` fields. The
  `HYDROSTATICS_ROW_METADATA` registry is keyed by row id and
  covers every key emitted by
  `analysis_view_model::hydro_rows`. Field naming mirrors
  `HullParameterMetadata` (RFC 0060).

- **`analysis_view_model` wiring.**
  `kayakgen/services/evaluation.py::analysis_view_model` consumes
  the new registry for the `label` and `unit` slots of every hydro
  row. The numeric `value` formatting is unchanged. The function
  returns the same top-level dict shape.

- **Wire-payload stability.** The new test
  `tests/test_hydrostatics_row_metadata.py` includes a regression
  assertion that constructs a known `Hull` state and asserts
  `hydro_rows_from_state(state)` returns the same `[{"label",
  "value"}]` list it did before the registry refactor. The
  expected list is committed as a frozen snapshot in the test
  file; the assertion is on the full list (not just length).

- **Registry coverage test.** The new test exercises every key
  referenced by `analysis_view_model` and asserts each is present
  in the registry, mirroring the
  `tests/test_hull_parameter_metadata.py` coverage shape.

- **RFC 0062 internal consistency.** The RFC's Status is `landed`;
  Date is `2026-05-25`; Context cites RFC 0060, RFC 0061, and
  D043; the Problem narrates the audit finding (AUD-O-005); the
  Proposal matches the actual landed code (registry shape + wiring
  point + test shape); the Acceptance section names the regression
  test as the discipline gate.

- **`docs/rfcs/README.md` row.** The new row is placed after the
  0061 row, follows the existing column shape, and accurately
  states `landed` + the one-line topic.

- **`hydro_rows_from_state` unchanged.** The function body in
  `evaluation.py` is unchanged; only its upstream
  `analysis_view_model` shifts from inline tuples to registry
  lookups.

- **`mesh_diagnostics_rows_from_state` unchanged.** That function
  body is workflow 0037's territory; the 0038 diff must not touch
  it. If 0037 has already landed, the 0038 diff merges cleanly on
  top.

- **Scope discipline.** The implementer touched ONLY:
  - `kayakgen/ui/hydrostatics_metadata.py` (new)
  - `kayakgen/services/evaluation.py` (only `analysis_view_model`)
  - `tests/test_hydrostatics_row_metadata.py` (new)
  - `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (new)
  - `docs/rfcs/README.md` (index row)
  - `docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/`

  No diffs on `CHANGELOG.md`, `docs/USER_GUIDE.md`,
  `docs/DECISION_LOG.md`, audit SYNTHESIS / REMEDIATION_PLAN /
  FINDINGS files, `docs/audits/README.md`,
  `docs/SPEC.md` / `docs/PRD.md` / `docs/ROADMAP.md` /
  `docs/ARCHITECTURE_MAP.md` / `docs/UBIQUITOUS_LANGUAGE.md`,
  `kayakgen/ui/parameter_metadata.py`,
  `kayakgen/ui/web/`,
  `kayakgen/ui/desktop.py`, or
  `kayakgen/ui/desktop_slider_ranges.py`.

- **Verification suite passes.** Run

  ```bash
  .venv/bin/pytest \
    tests/test_hydrostatics_row_metadata.py \
    tests/test_hull_parameter_metadata.py \
    tests/test_web_layout.py \
    tests/test_vocabulary_coverage.py \
    -q
  ```

  in the implementer's venv. All must pass.

You do not write code. You write a single `REVIEW.md` with a
verdict (accept | needs_revision) and per-criterion check results
(pass / fail with file:line evidence).
