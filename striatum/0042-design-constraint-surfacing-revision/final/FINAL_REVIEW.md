# Final Review — workflow 0042 design constraint surfacing revision

## Scope

RFC 0031 narrows RFC 0029 into a conservative validity-metadata slice on top
of RFC 0006's existing class presets and advisory checks
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:1`,
`docs/rfcs/0031-design-constraint-surfacing-revision.md:55`,
`docs/rfcs/0006-design-constraints.md:1`). This review verifies the landed
implementation against the ledger's seven implementation-required findings and
the non-blocking preservation/deferral list
(`striatum/0042-design-constraint-surfacing-revision/ledger/FINDINGS.md:26`,
`striatum/0042-design-constraint-surfacing-revision/ledger/FINDINGS.md:162`).

## Verdict

The landed patch satisfies the ledger's seven implementation-required findings
and preserves the documented boundaries (geometry, calibration, CFD readiness,
closed-volume, optimizer ranking, enforced validation). One residual
documentation gap remains: the AGENTS.md changelog convention was not honored
for this landing.

## Implementation-required findings coverage

### F-001 — shared validity model and evaluator (Satisfied)

`kayakgen/model/validity.py:58` defines `DesignValidityFinding` with required
`code`, `level`, `severity`, `message`, `source`, `parameters` and
`extra="allow"`; `kayakgen/model/validity.py:75` defines `DesignValidityReport`
with `schema_version`, `findings`, and synchronized
`advisory_count`/`warning_count`/`unsupported_count`/`error_count` plus
`extra="allow"` for future top-level fields
(`kayakgen/model/validity.py:65`, `kayakgen/model/validity.py:78`,
`kayakgen/model/validity.py:87`). `evaluate_design_validity(...)` lives at
`kayakgen/model/validity.py:120` with explicit source pins:

- `L/B_wl` → `SOURCE_L_BWL = "...section 4"` (`kayakgen/model/validity.py:22`,
  exercised in `tests/test_design_validity.py:33`).
- Displacement → `SOURCE_DISPLACEMENT = "...section 7"`
  (`kayakgen/model/validity.py:23`, `tests/test_design_validity.py:35`).
- `Cp` → `SOURCE_CP = "...section 8"` (`kayakgen/model/validity.py:24`,
  `tests/test_design_validity.py:34`).
- Class drift → `SOURCE_CLASS = "...sections 3, 4, and 9"`
  (`kayakgen/model/validity.py:25`).
- Unsupported → `SOURCE_UNSUPPORTED = "...RFC 0031 section 3; kayakgen/model/hull.py..."` (`kayakgen/model/validity.py:26`).

Future-field tolerance is tested in
`tests/test_design_validity.py:44`–`tests/test_design_validity.py:62`. Older
strict records without `design_validity` still load via
`tests/test_design_validity.py:65`–`tests/test_design_validity.py:102`.

### F-002 — existing advisory strings preserved (Satisfied)

`design_advisory()` in `kayakgen/model/advisory.py:31` is now a wrapper that
calls `evaluate_design_validity()` (`kayakgen/model/advisory.py:51`) and
returns the same warning strings via `design_warning_messages()`
(`kayakgen/model/validity.py:230`, `kayakgen/model/advisory.py:62`). The
returned `DesignAdvisory.warnings` remains a `tuple[str, ...]`
(`kayakgen/model/advisory.py:27`). Round-trip with prior call sites is
preserved by `tests/test_classes.py:75`–`tests/test_classes.py:102`, which
also asserts shared advisory codes appear in the structured report.

### F-003 — unsupported neutral sentinels (Satisfied)

`_unsupported_findings(...)` (`kayakgen/model/validity.py:314`) emits records
only when `LCB_frac != 0.50`, `rocker_bow_m != 0.0`, or `rocker_stern_m != 0.0`
using `math.isclose(..., abs_tol=1e-12)`. Severity is `info` and level is
`unsupported`. `tests/test_design_validity.py:133`–`tests/test_design_validity.py:147`
verifies neutral defaults stay quiet and that all three non-neutral fields
emit `unsupported` records with `severity == "info"`. Reserved
`bow_rake`/`stern_rake` are correctly excluded because RFC 0028 makes them
honored geometry controls (`docs/rfcs/0006-design-constraints.md:38`,
`kayakgen/model/hull.py:43`).

### F-004 — additive serialization wiring (Satisfied)

- `EvaluationResult.design_validity` is a defaulted field
  (`kayakgen/eval/contract.py:293`).
- `kayakgen evaluate` populates it with `surface=("cli",)`
  (`kayakgen/cli/main.py:77`, `kayakgen/cli/main.py:87`); coverage at
  `tests/test_cli.py:144`, `tests/test_cli.py:148`–`tests/test_cli.py:164`.
- Web `evaluation_for_state()` populates it with `surface=("web",)`
  (`kayakgen/ui/web/controllers.py:322`); `evaluation_payload()`
  serializes it (`kayakgen/ui/web/controllers.py:962`); coverage at
  `tests/test_web.py:322`–`tests/test_web.py:331`.
- Sweep `_evaluate_candidate(...)` populates the candidate report with
  `surface=("sweep",)` (`kayakgen/search/sweep.py:238`) and carries it on
  both `CandidateRecord.design_validity` and the persisted
  `EvaluationResult` (`kayakgen/search/sweep.py:113`,
  `kayakgen/search/sweep.py:321`); coverage at
  `tests/test_sweep.py:76`–`tests/test_sweep.py:93`.
- Comparison summaries/reports carry per-candidate records and aggregate
  counts (`kayakgen/search/compare.py:44`,
  `kayakgen/search/compare.py:71`–`kayakgen/search/compare.py:91`,
  `kayakgen/search/compare.py:188`–`kayakgen/search/compare.py:198`);
  coverage at `tests/test_compare.py:193`–`tests/test_compare.py:209`.
- Pareto/objective ranking is unaffected: `_default_objectives` and
  `_normalize_objectives` read only from `summary.metrics`
  (`kayakgen/search/compare.py:313`,
  `kayakgen/search/compare.py:327`); `design_warning_count` is excluded from
  `metrics` (asserted by `tests/test_compare.py:209` and
  `tests/test_sweep.py:92`). Advisory findings do not change candidate
  status, sweep failure counts, exit behavior, or Pareto eligibility
  (`tests/test_sweep.py:87`–`tests/test_sweep.py:88`,
  `tests/test_compare.py:204`–`tests/test_compare.py:209`).

### F-005 — shared codes/messages on both UIs (Satisfied)

Desktop reads warning lines from `design_advisory(...).warnings`
(`kayakgen/ui/desktop.py:327`, `kayakgen/ui/desktop.py:364`), and that
wrapper now derives strings from the shared
`evaluate_design_validity(...)` report. Web compact metrics expose the same
`advisory.warnings` plus the structured report and code list
(`kayakgen/ui/web/controllers.py:107`,
`kayakgen/ui/web/controllers.py:126`–`kayakgen/ui/web/controllers.py:133`).
The analysis view model keeps `design_warnings` and `resistance_warnings`
distinct (`kayakgen/ui/web/controllers.py:181`–`kayakgen/ui/web/controllers.py:184`),
while a legacy combined `warnings` key is preserved for existing helper
consumers; the user-visible text rendering uses the separate fields
(`kayakgen/ui/web/controllers.py:205`–`kayakgen/ui/web/controllers.py:216`).
Coverage at `tests/test_web.py:111`–`tests/test_web.py:154`.

### F-006 — selected-class drift is explicit and optional (Satisfied)

`_selected_class_findings(...)` returns `[]` when `selected_class` is `None`,
`"custom"`, or unknown (`kayakgen/model/validity.py:261`–`kayakgen/model/validity.py:272`),
so class drift is never inferred from `Hull.name`. The desktop call site
passes `selected_class=None` when the desktop class is `custom`
(`kayakgen/ui/desktop.py:331`). Class drift coverage is explicit:
`tests/test_design_validity.py:120`–`tests/test_design_validity.py:130`
proves drift records appear only when the caller supplies the class, and
`tests/test_design_validity.py:105`–`tests/test_design_validity.py:117`
proves class defaults stay advisory-quiet for every preset.

### F-007 — enforced validation authority preserved (Satisfied)

`Hull._validate_beam_wl` still rejects `beam_wl_m > beam_oa_m`
(`kayakgen/model/hull.py:73`). The new RFC 0031 evaluator never emits an
`enforced` finding for that case, so it does not duplicate Pydantic errors as
metadata or loosen them. Coverage:

- CLI rejection: `tests/test_cli.py:166`–`tests/test_cli.py:177`.
- Sweep records the failure as `status="failed"` with an empty design
  validity report (`tests/test_sweep.py:56`–`tests/test_sweep.py:73`).
- Web `clamp_beam_wl_state(...)` remains a pre-validation UI clamp, not a
  model-level rule (`kayakgen/ui/web/controllers.py:51`,
  `tests/test_web.py:133`–`tests/test_web.py:142`,
  `tests/test_web.py:157`–`tests/test_web.py:164`).

## Compatibility and strict-schema risk

`EvaluationResult` (`kayakgen/eval/contract.py:285`), `CandidateRecord`
(`kayakgen/search/sweep.py:99`), `CandidateSummary`
(`kayakgen/search/compare.py:34`), and `ComparisonReport`
(`kayakgen/search/compare.py:61`) keep `extra="forbid"` but add
`design_validity` with a default factory. Old strict records without those
fields still round-trip
(`tests/test_design_validity.py:65`–`tests/test_design_validity.py:102`).
Forward compatibility lives at the finding/report layer where
`extra="allow"` accepts future optional fields without breaking older
consumers (`kayakgen/model/validity.py:65`, `kayakgen/model/validity.py:78`;
covered by `tests/test_design_validity.py:44`–`tests/test_design_validity.py:62`).

## Advisory boundary preservation

- Design warnings are not mixed into resistance, calibration, or CFD warning
  streams. Web analysis distinguishes `design_warnings` from
  `resistance_warnings`
  (`kayakgen/ui/web/controllers.py:181`–`kayakgen/ui/web/controllers.py:184`,
  `tests/test_web.py:123`–`tests/test_web.py:131`). Web sweep candidate
  warning strings still tag resistance entries with a `"resistance:"` prefix
  (`kayakgen/search/compare.py:248`).
- Sweep status, completion counts, exit codes, and pareto eligibility are
  unchanged by advisory or unsupported records
  (`tests/test_sweep.py:76`–`tests/test_sweep.py:93`,
  `tests/test_compare.py:193`–`tests/test_compare.py:209`).
- Pareto/objective ranking is not based on `design_warning_count` or
  `design_unsupported_count`; the comparison report's `report_kind` and
  `pareto_front_keys` still depend on resistance/design-fitness gating, not
  validity findings (`kayakgen/search/compare.py:124`,
  `kayakgen/search/compare.py:140`).
- CFD readiness, watertight semantics, and solver dispatch are not altered;
  the patch made no edits under `kayakgen/eval/cfd/`,
  `kayakgen/eval/mesh_package.py`, or `kayakgen/model/geometry*.py` (see
  `git diff 78f14d0~1..78f14d0 --stat`). CFD raw/unvalidated wording in
  `docs/USER_GUIDE.md` is preserved (`docs/USER_GUIDE.md:303`,
  `docs/USER_GUIDE.md:358`).
- Final-design-fitness and resistance claim gates remain separate streams
  (`kayakgen/search/compare.py:175`–`kayakgen/search/compare.py:178`,
  `tests/test_compare.py:274`–`tests/test_compare.py:445`).

## Unsupported wording does not claim implementation

Unsupported finding messages explicitly describe the reserved fields as
stored-but-not-honored (`kayakgen/model/validity.py:49`,
`kayakgen/model/validity.py:50`, `kayakgen/model/validity.py:53`), aligned
with RFC 0031 wording (`docs/rfcs/0031-design-constraint-surfacing-revision.md:93`).
`docs/USER_GUIDE.md:106`–`docs/USER_GUIDE.md:111` mirrors the same wording for
the CLI surface: advisories and unsupported records are not proof of
seaworthiness or final design fitness. `Hull.LCB_frac`/`rocker_bow_m`/
`rocker_stern_m` remain reserved fields (`kayakgen/model/hull.py:58`).
Neutral defaults stay quiet (`tests/test_design_validity.py:134`).

## Test execution

- `.venv/bin/python -m pytest tests/test_design_validity.py tests/test_classes.py tests/test_cli.py tests/test_sweep.py tests/test_compare.py tests/test_web.py -q` → 92 passed in 14.36s.
- `.venv/bin/python -m pytest -q` → 263 passed in 51.73s.

## Residual findings

### R-001 — CHANGELOG.md was not updated by the landing commit

The implementation commit `78f14d0` ("Land RFC 0031 design validity metadata")
modified 16 files but did not edit `CHANGELOG.md`. The `PATCH_SUMMARY.md`
proposed a changelog entry (`striatum/0042-design-constraint-surfacing-revision/implementation/PATCH_SUMMARY.md:73`–`striatum/0042-design-constraint-surfacing-revision/implementation/PATCH_SUMMARY.md:77`)
but it was never appended. The existing `## Unreleased` block only documents
RFC 0031 scaffolding/accepted-target status (`CHANGELOG.md:49`,
`CHANGELOG.md:71`), not the actual validity-metadata landing. AGENTS.md is
explicit that landing an RFC or user-facing behavior change should update
CHANGELOG.md (`AGENTS.md:73`–`AGENTS.md:75`). This is a documentation gap,
not a code defect, but it falls inside the workflow's expected closing
discipline.

## Non-blocking observations

- The wrapper `design_advisory(...)` does not forward a `surface` value to
  `evaluate_design_validity()` (`kayakgen/model/advisory.py:51`). The
  desktop and compact-web metrics paths therefore emit findings with no
  `surface` field, while CLI/sweep/web `evaluation_payload` paths do
  populate it (`kayakgen/cli/main.py:81`, `kayakgen/search/sweep.py:242`,
  `kayakgen/ui/web/controllers.py:326`). RFC 0031 marks `surface` as
  optional (`docs/rfcs/0031-design-constraint-surfacing-revision.md:79`),
  so this is consistent with the slice's optional-field tolerance, but a
  follow-up could thread `surface=("desktop",)`/`("web",)` through the
  wrapper for stronger parity diagnostics.
- The legacy combined `warnings` field is preserved in `analysis_view_model`
  (`kayakgen/ui/web/controllers.py:184`). User-visible text uses the
  separated `design_warnings` and `resistance_warnings` keys, so the visible
  parity requirement still holds, but downstream callers consuming
  `model["warnings"]` continue to see a mixed stream. This is explicitly
  noted as a compatibility shim in the patch summary and not a regression.

## Conclusion

The landed RFC 0031 slice is conservative, additive, and faithfully tracks
the ledger's seven implementation-required findings. Geometry, resistance,
CFD, closed-volume, optimizer, and stability surfaces are untouched. The full
test suite passes, including new advisory-parity, source-pin, class-default,
class-drift, unsupported, sweep, and comparison tests. The only residual gap
is the missing `CHANGELOG.md` entry for the landing — captured as R-001 for
the operator to close before workflow finalization.

Verdict intent: accept_with_findings
