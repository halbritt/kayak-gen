Verdict intent: accept_with_findings

# REVIEW_TRACEABILITY — workflow 0037 first real CFD fixture adapter

Role: reviewer_traceability (Claude / Claude Opus 4.7).

Scope: trace RFC 0026 (fixture-local-command adapter) against the contracts it
inherits (RFC 0010 mesh package, RFC 0015 job dispatch, RFC 0025 claim gates),
the RFC it revises (RFC 0017), and the implementation/test surface it must
extend (`kayakgen/eval/cfd/jobs.py`, `kayakgen/cli/main.py`,
`tests/test_cfd_jobs.py`).

## Sub-agent help used

Performed the traceability review directly. Source set is bounded — five RFCs,
one dispatch module, one CLI module, one test file — so a single linear pass
with `Read`/`Grep` is sufficient to map every RFC 0026 acceptance line. No
parallel sub-agents were spawned; the assigned role is preserved.

## RFC 0026 acceptance map

| RFC 0026 acceptance line | Reused contract | Current state | Implementation obligation |
|---|---|---|---|
| Built-in fixture/local-command profile documented and listed by the CLI | RFC 0015 `SolverProfile` + `cfd profiles` (`jobs.py:41-52`, `cli/main.py:233-237`) | Not present. `CfdAdapterName` is `Literal["unavailable", "mock_local_command"]` and `_solver_profiles()` returns only `unavailable-open-wetted-surface`, `unavailable-watertight-solid`, `mock-failing-local-command` (`jobs.py:25`, `jobs.py:643-649`). RFC 0026 names `fixture-local-command` / `fixture_local_command`. | Extend `CfdAdapterName` literal, add `fixture_local_command_profile()` builder with `required_mesh_readiness="cfd_surface_candidate"` and `required_mesh_profile="open_wetted_surface_resistance_v1"`, register it in `_solver_profiles()` and (optionally) `_solver_profile_by_name` aliases. |
| `cfd prepare` writes deterministic profile, job, run, and adapter case files | RFC 0015 `prepare_local_job` (`jobs.py:254-312`) | Job, profile, run JSON already written. No adapter-case files. | Adapter must render its own deterministic case directory (e.g. `case/`) during `prepare`, parameterised by `CfdJobSpec.speed_mps`, `seawater_density_kg_m3`, `kinematic_viscosity_m2_s`, and mesh manifest metadata. |
| `cfd run` succeeds only when fixture command exits cleanly and required raw output is present and schema-valid | RFC 0015 `SolverAdapter` protocol and `MockFailingLocalCommandAdapter` (`jobs.py:145-156`, `jobs.py:375-427`) | Existing mock adapter only encodes the *failure* branch. There is no success-with-output-parsing path in any adapter. | New `FixtureLocalCommandAdapter` that (a) invokes a checked-in fixture command, (b) requires a normalized raw record on disk, (c) parses it into a pydantic model along the lines of `CfdFixtureRawResult`, and (d) maps each failure mode to `unavailable` / `failed` with stable `error_kind`. |
| Missing command, nonzero command, missing output, malformed output → `unavailable` or `failed` with `error_kind`/`error_message` | RFC 0015 `SolverRawResult` (`jobs.py:131-142`) | Returncode-based `command_failed` exists in the mock adapter. Missing-binary, missing-output, and malformed-output branches do not exist. | Adapter must distinguish: `FileNotFoundError`/`PermissionError` on the executable → `unavailable` (`solver_unavailable`); nonzero exit → `failed` (`command_failed`); missing expected output file → `failed` (e.g. `missing_output`); malformed JSON/schema → `failed` (e.g. `malformed_output`). Document the chosen `error_kind` strings in the RFC if they are not already pinned. |
| Successful runs still say `raw_unvalidated` and include a warning that fixture output is not calibrated, validated, or final design fitness | RFC 0025 `RawUnvalidatedClaimFields` (`SolverProfile`, `CfdJobSpec`, `CfdRunRecord`, `SolverRawResult` all inherit it; `jobs.py:41`, `:55`, `:75`, `:131`), and `CFD_RAW_RESULTS_WARNING` echoed by `cfd prepare/status/run` (`cli/main.py:182,207,230`) | Claim-state inheritance is already enforced; existing tests (`test_cfd_records_reject_validated_or_calibrated_promotion`, `test_reserved_cfd_drag_result_serializes_raw_claim_state`) confirm refusal of `calibrated_model` / accepted-use promotion. | New `CfdFixtureRawResult` must inherit `RawUnvalidatedClaimFields` (or its `claim_state` Literal must be pinned to `raw_unvalidated`). A new warning string ("fixture output is not calibrated, validated, or final design fitness") should be attached to `SolverRawResult.warnings` / `CfdRunRecord` so CLI can surface it next to `CFD_RAW_RESULTS_WARNING`. |
| Tests require no external solver and cover prepare, success, unavailable, command failure, missing output, malformed output, and run-record round-trip | RFC 0015 test patterns in `tests/test_cfd_jobs.py` | Existing tests cover: round-trip (`test_job_spec_and_run_record_round_trip`), prepare deterministic dir (`test_prepare_local_job_writes_deterministic_job_directory`), readiness rejection / forged-watertight (`test_prepare_rejects_*`), solver-profile mismatch, non-positive inputs, unavailable adapter, mock command failure. There are **no** tests for fixture success, missing executable, missing output, or malformed output. | Add: `test_fixture_adapter_succeeds_with_raw_unvalidated_warning`, `test_fixture_adapter_reports_unavailable_for_missing_command`, `test_fixture_adapter_reports_failed_for_missing_output`, `test_fixture_adapter_reports_failed_for_malformed_output`, and a fixture-flavored round-trip test. All must invoke only the checked-in Python fixture (`sys.executable`-based) — no OpenFOAM/SU2. |
| RFC 0017 treated as revised: OpenFOAM/SU2 selection remains deferred | RFC 0017 `RealSolverProfile`/`CfdRawResistanceResult` (proposed only) | RFC 0017 status is still `proposed`; the first real adapter remains unselected. RFC 0026 explicitly supersedes the open "which solver?" decision with a fixture slice. | Add a status note to RFC 0017 indicating RFC 0026 supersedes its first-adapter slot, and update `docs/rfcs/README.md` if an index entry needs the revision link. RFC 0026 itself should move from `proposed` to whatever next status the project conventions use once the workflow lands. |

## RFC 0015 reuse — what should not change

The RFC 0026 slice is additive, not a contract change. The traceability
expectation is that all of the following remain untouched:

- `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, `SolverAdapter` (`jobs.py:55-156`).
- Mesh readiness gating: `_validate_mesh_package`, `READINESS_ORDER`, and the
  watertight-evidence path (`jobs.py:440-588`). The fixture profile must opt in
  via `required_mesh_readiness="cfd_surface_candidate"` and the existing
  `open_wetted_surface_resistance_v1` mesh profile so it does not exercise the
  watertight path at all.
- Deterministic job-id hashing (`_job_id`, `jobs.py:669-686`). The fixture
  profile name will participate in the hash by virtue of `solver_profile.name`,
  so existing determinism tests should still hold once the new profile is
  registered.
- `cfd prepare/status/run/profiles` CLI surface (`cli/main.py:140-237`). The
  fixture profile should be reachable through the *existing* CLI flags; no new
  Typer commands are needed for RFC 0026.

If any of the above must change to accept the slice, that is a scope expansion
beyond RFC 0026 and should be called out before implementation.

## RFC 0025 claim-gate map

RFC 0025 (`raw_unvalidated`, `uncalibrated_comparative`, ..., `validated_design_fitness`)
is already wired in through `RawUnvalidatedClaimFields`. The fixture adapter
inherits the gate automatically as long as new record models extend that mixin.
Two RFC 0025 forbidden-promotion lines that the fixture work must continue to
honour:

- "Validation fixtures do not change resistance calibration status." → fixture
  adapter success must not flip any analytical resistance record to
  `calibrated_model`. The current code path has no edges from CFD to
  `kayakgen.eval.resistance`, so this is preserved by construction; the
  forbidden-promotion test (`test_cfd_records_reject_validated_or_calibrated_promotion`)
  remains the regression guard.
- "Current CFD job records still emit raw/unvalidated semantics even on command
  success." → the *new* success branch in the fixture adapter is the first
  place this is genuinely tested; the suggested
  `test_fixture_adapter_succeeds_with_raw_unvalidated_warning` is the
  acceptance-criterion mate for that line.

## RFC 0017 revision / deferral

RFC 0026 §Proposal explicitly supersedes RFC 0017's undecided
first-adapter target. Traceability obligations:

- RFC 0017 acceptance criterion "One real adapter profile is named and
  documented with installation prerequisites" is *not* delivered by RFC 0026 —
  the fixture command is not a real CFD solver. The fixture slice satisfies
  only the deterministic-success fixture half of RFC 0017's last acceptance
  bullet ("a tiny deterministic success fixture that does not require
  validated physics").
- A status note on RFC 0017 ("revised by RFC 0026 — fixture adapter first;
  OpenFOAM/SU2 selection deferred") is the minimum documentation gate.
- RFC 0017 Open Questions Q1 (watertight vs open-surface first) is now
  pre-answered for the fixture slice ("open wetted surface only"); the same
  question for the eventual OpenFOAM/SU2 slice stays open.

## Required-test coverage gap summary

Acceptance criterion → test name → status:

- prepare → `test_prepare_local_job_writes_deterministic_job_directory` /
  `test_public_prepare_api_returns_job_paths` → ✅ already present (will need an
  added assertion that the fixture profile also prepares deterministically).
- success → none today → ❌ must add.
- unavailable → `test_unavailable_adapter_writes_unavailable_run_record` → ✅
  present, but covers the *existing* `unavailable` profile only. A
  fixture-flavored variant (missing executable) is still required.
- command failure → `test_mock_local_command_adapter_writes_failed_record_and_logs`
  → ✅ pattern exists; fixture-flavored variant required to confirm
  `command_failed` → fixture path.
- missing output → none today → ❌ must add.
- malformed output → none today → ❌ must add.
- run-record round trip → `test_job_spec_and_run_record_round_trip` → ✅
  generic, will keep working; a fixture-success round-trip is nice-to-have.

## Open questions that traceability cannot resolve

These map directly to RFC 0026 §Open Questions and need a planner/operator
decision before implementation, not a reviewer call:

1. Whether the fixture command is shipped as a `python -m` module (testable in
   isolation, hashable as a checked-in file) or rendered as a per-job script
   (mirrors a future OpenFOAM case more closely). Either is RFC-compatible;
   pick one and add a one-line note to RFC 0026.
2. Whether normalized raw output is `raw-result.json` (current `MockFailing…`
   adapter convention, `jobs.py:407`) or a directory like `outputs/`. Reuse of
   the existing path keeps the schema flat; a directory parallels a future
   solver adapter. Document the decision in the RFC and reuse it in the
   `output_manifest` field of `CfdRunRecord`.
3. Whether a second watertight fixture profile is added later. Out of scope
   for this workflow; the closed-volume work (workflows 0033/0038) must land a
   real `cfd_ready` package before this is meaningful.

## Findings

1. **F1 — Missing implementation** (severity: high, blocking for workflow
   advance to implementation). No `fixture_local_command` adapter or
   `fixture-local-command` `SolverProfile` exists. RFC 0026 cannot be marked
   landed until both are present and registered in `solver_profile_names()`.
2. **F2 — Test gap for the success path** (severity: high). The repository has
   no test that exercises a CFD adapter success branch end to end. The
   fixture adapter is the first opportunity to add one; without it, the
   `status="succeeded"` branch in `_run_record_from_result` and
   `SolverRawResult.status` are uncovered.
3. **F3 — Error-kind taxonomy is informal** (severity: medium). Current code
   uses `solver_unavailable` and `command_failed` as ad-hoc strings. RFC 0026
   adds at least two more (missing output, malformed output). The taxonomy
   should be either (a) pinned to a `Literal` on `SolverRawResult` /
   `CfdRunRecord`, or (b) at minimum documented in RFC 0026 so CLI / web
   wording can stabilise.
4. **F4 — Fixture warning text not yet routed** (severity: medium). The CLI
   prints `CFD_RAW_RESULTS_WARNING` on every prepare/status/run, which covers
   the generic case. RFC 0026 calls for an *additional* warning specific to
   fixture output ("not calibrated, validated, or final design fitness"). Decide
   whether this lives in `SolverRawResult.warnings` (per-run, persisted in
   `run.json`) or in CLI copy. Per-run persistence is preferred so web and
   sweep callers see the same string.
5. **F5 — RFC 0017 documentation has not been updated** (severity: low). RFC
   0017 is still `Status: proposed` with no pointer to RFC 0026; a workflow
   that touches RFC 0017's scope should leave a status note even if no code
   change lands there.
6. **F6 — RFC 0026 §Open Questions are unresolved** (severity: low). Q1 and
   Q2 above need to be answered before implementation begins so adapter
   structure does not drift from RFC text.

## Required actions for the workflow to land

In order:

1. Resolve RFC 0026 Open Questions Q1 and Q2 in the RFC text (operator/planner).
2. Update RFC 0017 with a "revised by RFC 0026" status note.
3. Add `fixture_local_command` to `CfdAdapterName` and a
   `fixture_local_command_profile()` builder; register in `_solver_profiles()`
   and the alias map.
4. Add `FixtureLocalCommandAdapter` covering the four failure modes
   (missing command / nonzero / missing output / malformed output) plus the
   success path producing a `CfdFixtureRawResult` (or equivalent normalized raw
   record) that inherits `RawUnvalidatedClaimFields`.
5. Wire the new fixture warning into `SolverRawResult.warnings` so it is
   persisted into `run.json` and shown by `cfd status`.
6. Extend `tests/test_cfd_jobs.py` with the five tests called out in §Required
   test coverage gap; ensure none import or shell out to a real CFD solver.
7. After implementation, confirm `cfd profiles` lists the new profile and the
   CLI run path produces a `succeeded` `CfdRunRecord` with `claim_state ==
   "raw_unvalidated"` and the fixture warning string visible.

## Verdict rationale

The proposed slice is fully traceable: every RFC 0026 acceptance line maps to
either an already-landed RFC 0015 contract (reused) or a clearly bounded
addition to `jobs.py` and `tests/test_cfd_jobs.py`. The RFC 0025 claim-gate
inheritance is already in place via `RawUnvalidatedClaimFields`, and the
RFC 0017 revision is documented inside RFC 0026 itself. The workflow can
proceed with the findings above recorded; nothing requires re-scoping. Hence
`accept_with_findings` rather than `accept` (F1–F4 are real, implementation-time
obligations) and not `needs_revision` (no contract incompatibility was found).
