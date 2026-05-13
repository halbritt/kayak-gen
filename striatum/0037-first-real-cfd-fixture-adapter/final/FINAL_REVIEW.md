Verdict intent: accept

# Final Review — workflow 0037 first real CFD fixture adapter

Role: `final_reviewer` (claude / Opus 4.7), session `sess_fbcd5632acf34ce39e3ed336d6848ca9`, job `job_run_f0ce0eddffee4622a10d02a842cd84ea_final_review`, worktree `/tmp/kayak-gen-ledger-worktrees/0037`.

This artifact is being written by the assigned final reviewer. It does not call `striatum`, does not publish, does not complete the job, does not mutate project code, does not commit or push, and does not edit `OPERATOR_REPORT.md`.

## Sub-agent / parallel worker usage

This final review was performed directly without spawning sub-agents. The Agent tool was available, but the upstream artifacts (`REVIEW_DOMAIN_SOURCE.md`, `REVIEW_OPS.md`, `REVIEW_TRACEABILITY.md`, `FINDINGS.md`, `PATCH_SUMMARY.md`) already partition the review surface into disjoint scopes, and the implementation diff is small enough (≈1.4k added lines across 16 files, one production module net-new) for a single linear pass with `Read` / `Grep` / `git diff` to map every RFC 0026 acceptance line to its delivered code. The remaining cost was running the targeted and full test suites, which `Bash` handles directly. Spawning sub-agents would have duplicated work already produced by the three first-pass reviewers and the ledger.

## Verification

Ran in the workflow's worktree using the same `.venv` interpreter the implementer used.

- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q tests/test_cfd_jobs.py tests/test_cli.py` → `36 passed in 8.48s`.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q` (full suite) → `201 passed in 29.56s`.
- `git diff --stat main` reviewed; production change set is confined to `kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/cfd/fixture_command.py` (new), `kayakgen/eval/cfd/__init__.py`, and `kayakgen/cli/main.py`; everything else is tests, RFC text, README index, CHANGELOG, and Striatum artifacts. No new dependency, no solver binary, no Docker/container.
- Read full diff of `kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/cfd/fixture_command.py`, `kayakgen/cli/main.py`, `tests/test_cfd_jobs.py`, `tests/test_cli.py`, and the RFC/CHANGELOG/README changes. Cross-checked field inheritance for `warnings` on `CfdRunRecord` against `kayakgen/eval/claims.py:63` (inherited from `RawUnvalidatedClaimFields`).
- Inspected each ledger finding (L-F1…L-F8) against the implementation; mapped each RFC 0026 acceptance line against the patch.

## Acceptance-criteria check (per `prompts/final_review.md`)

The four gating conditions from the role prompt and `objective`:

1. **Deterministic adapter behavior, success and failure tests.**
   - Prepare-side determinism: `tests/test_cfd_jobs.py::test_fixture_prepare_writes_deterministic_case_files` re-prepares the same job and asserts `_case_file_texts(second.job_dir) == first_case_files`, covering `case/fixture-case.json`, `case/mesh-summary.json`, and `case/command.json`. The `case_template_version` literal and sorted serialization of mesh maps anchor the byte-level contract.
   - Success path: `test_fixture_adapter_succeeds_with_schema_valid_raw_unvalidated_output` asserts `record.status == "succeeded"`, `output_manifest == "raw-result.json"`, `result_semantics == "raw_unvalidated"`, `claim_state == "raw_unvalidated"`, fixture warning string present, and run-record round-trip.
   - Failure paths covered with disjoint expected `error_kind` values:
     - missing command → `unavailable`/`failed`, message names the missing path (`test_fixture_missing_command_persists_unavailable_or_failed_record`).
     - nonzero command → `command_failed`, logs round-tripped (`test_fixture_nonzero_command_persists_failed_record_and_logs`).
     - clean exit, missing output → `missing_output`, no `output_manifest` (`test_fixture_clean_command_with_missing_raw_output_persists_failed_record`).
     - malformed output → `malformed_output` (`test_fixture_malformed_raw_output_persists_failed_record`).
   - CLI surface: `test_cfd_profiles_lists_fixture_local_command` and `test_cfd_fixture_run_and_status_keep_raw_warning_visible` cover profile listing plus `cfd run` / `cfd status` raw + fixture warning visibility.
   - Each test substitutes the command template via `_set_fixture_command` (or relies on the built-in `python -m kayakgen.eval.cfd.fixture_command`), and `subprocess.run` is wrapped in `try / except (FileNotFoundError, PermissionError)` so a missing executable cannot leave a stale `running` record.

2. **No real solver dependency in CI.**
   - Only `sys.executable` and the checked-in `kayakgen.eval.cfd.fixture_command` module are invoked. No OpenFOAM, SU2, RANS, panel-method, Docker, or external binary appears in the changed code or tests. `_fixture_command_env()` prepends the repo root to `PYTHONPATH` so the checked-in module resolves under any cwd; no installer step is introduced.

3. **Reuses existing job records.**
   - `CfdAdapterName` literal is extended in place; no new dispatch surface is introduced. The fixture profile reuses `CfdJobSpec`, `SolverProfile`, `PreparedSolverCase`, `SolverRawResult`, `CfdRunRecord`, `LocalCfdJob`, `_run_record_from_result`, `_write_command_logs`, `_validate_mesh_package`, the deterministic job-id hash, and the existing CLI Typer commands. The fixture adapter is wired through `_adapter_for()` and `_solver_profiles()` (with alias `fixture_local_command_v1`) without changing any prior contract.
   - Mesh gating remains pinned to `required_mesh_readiness="cfd_surface_candidate"` and `required_mesh_profile="open_wetted_surface_resistance_v1"`, matching RFC 0026 §Proposal and the §Workflow 0037 Pinned Choices block.

4. **All output raw/unvalidated.**
   - `CfdFixtureRawResult` inherits `RawUnvalidatedClaimFields`, pinning `claim_state="raw_unvalidated"`, and adds `result_semantics: Literal["raw_unvalidated"] = "raw_unvalidated"`. The forbidden-promotion validator in `RawUnvalidatedClaimFields._raw_claim_must_not_promote` (`kayakgen/eval/claims.py:78`) continues to block any accepted use / calibration fixture / model version / validity envelope from being attached to fixture output.
   - Every fixture-side `SolverRawResult` constructor path passes `warnings=_fixture_warnings()`, which is `[WARNING_RAW_CFD_UNVALIDATED, CFD_FIXTURE_RESULTS_WARNING]`. `_run_record_from_result` now propagates those into `CfdRunRecord.warnings` (inherited from `RawUnvalidatedClaimFields`), so the fixture-specific “not calibrated, validated, or final design fitness” string lands in `run.json` and is visible to web and sweep callers, not only CLI copy. `_echo_cfd_warnings` shows both warnings on `cfd run` / `cfd status` when the fixture warning is persisted.
   - The existing forbidden-promotion regression tests (`tests/test_cfd_jobs.py::test_cfd_records_reject_validated_or_calibrated_promotion`, `test_reserved_cfd_drag_result_serializes_raw_claim_state`) are untouched and still pass under the new profile.

## Ledger findings → implementation

- **L-F1** (high) — fixture profile and adapter present, registered in `solver_profile_names()` and alias map, listed by `cfd profiles`. ✅
- **L-F2** (high) — `FixtureLocalCommandAdapter.prepare` renders `case/fixture-case.json`, `case/mesh-summary.json`, `case/command.json` deterministically from `CfdJobSpec` + `MeshPackageManifest` and is covered by the deterministic-prepare test. ✅
- **L-F3** (high) — `CfdFixtureCommandOutput` is parsed with pydantic, normalized into `CfdFixtureRawResult`, written to `raw-result.json`; `status="succeeded"` is gated on schema-valid output and a `job_id` match against the prepared `CfdJobSpec`. ✅
- **L-F4** (high) — `subprocess.run` is wrapped for `FileNotFoundError` / `PermissionError`; the four failure modes map to `solver_unavailable`, `command_failed`, `missing_output`, `malformed_output`, all persisted into `run.json`. `error_message` includes the missing path, the nonzero return code, and the expected raw-output filename respectively, so call sites have stable evidence. ✅
- **L-F5** (high) — Test matrix delivered: profile listing, deterministic prepare, success with raw-unvalidated warning, missing command, nonzero command, missing output, malformed output, run-record round trip, CLI fixture run/status warning visibility. ✅
- **L-F6** (medium) — Fixture warning string is now persisted on `CfdRunRecord.warnings` (via `SolverRawResult.warnings` → `_run_record_from_result`), not only printed by the CLI. The CLI also prints it via `_echo_cfd_warnings`. ✅
- **L-F7** (low) — RFC 0026 §Workflow 0037 Pinned Choices block records `python -m kayakgen.eval.cfd.fixture_command`, `raw-result.json`, and `open_wetted_surface_resistance_v1` as the locked decisions, replacing the prior §Open Questions block. ✅
- **L-F8** (low) — RFC 0017 has a “Workflow 0037 Revision Note” section pointing to RFC 0026; `docs/rfcs/README.md` flips RFC 0026 to “landed fixture-local-command” and references the pinned choices. ✅

## Minor observations (non-blocking)

These do not change the verdict; recording them for the record.

- `CfdRunRecord` still has no top-level `warnings` field declared on the subclass body. Reading the diff in isolation it looks like the `warnings=list(result.warnings)` kwarg might violate `extra="forbid"`, but `warnings` is inherited from `RawUnvalidatedClaimFields` (`kayakgen/eval/claims.py:76`), so the construction is valid and confirmed by the passing CLI/run-record tests that read `run_record["raw_records"]["warnings"]` and CLI stdout. A future cleanup could promote `warnings` to a first-class field on `CfdRunRecord` for readability, but that is outside this slice.
- `started_at` and `finished_at` use `_utc_now()`, so two successive `cfd run` invocations produce non-byte-identical `run.json` files. This is RFC 0015 behavior and not regressed here; the workflow’s determinism requirement (RFC 0026 “deterministic profile, job, run, and adapter case files”) is satisfied at the prepare stage and by stable payload contents inside `raw_records`. The test surface correctly asserts payload determinism rather than timestamp determinism.
- The fixture warning is emitted both by the CLI and persisted into `run.json`. CLI logic gates the fixture-specific line on `CFD_FIXTURE_RESULTS_WARNING in run.warnings`, which means web/sweep callers see the same string from the record without needing CLI-only copy. Good.
- The `PATCH_SUMMARY.md` notes `ruff` was not run because the referenced venv lacks the module. That is a tooling gap rather than a code issue; `pytest` and `compileall` both passed, and the new modules are small and follow surrounding style. Not a blocker.
- `OPERATOR_REPORT.md` shows a `-12` line delta in the diff against `main`; that is the operator’s own bookkeeping outside this role’s write scope and is not part of the final review verdict.

## Verdict rationale

All four explicit acceptance bars from `prompts/final_review.md` are satisfied:

- Deterministic adapter behavior and disjoint success / failure tests are present and the full suite passes (201/201).
- No external solver is invoked in code or tests; the fixture command is a checked-in module run via `sys.executable`.
- The fixture slice extends `CfdAdapterName`, `_solver_profiles()`, and the alias map without changing `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, or the CLI surface — it reuses existing job records.
- Every fixture record path inherits `RawUnvalidatedClaimFields`, sets `result_semantics="raw_unvalidated"`, and persists the fixture-specific not-calibrated / not-validated / not-design-fitness warning into the run record.

All eight ledger findings (L-F1 through L-F8) are addressed. The deferred out-of-scope list (OpenFOAM, SU2, hosted/Docker execution, real solver validation, calibration, watertight `cfd_ready` bypass, final design-fitness claims) remains deferred and is reaffirmed in RFC 0026 §Non-Goals and the §Workflow 0037 Pinned Choices block.

Therefore `accept` — not `accept_with_findings`, because the prior ledger findings are now satisfied by code/tests/docs, and the minor observations above are below the threshold for new findings; and not `needs_revision`, because no contract incompatibility or missing acceptance line was found.
