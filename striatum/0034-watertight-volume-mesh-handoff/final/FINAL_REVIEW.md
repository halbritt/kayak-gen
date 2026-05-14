# Final Review - workflow 0034 watertight volume mesh handoff

session: sess_79f47bf1b31149b29522e8ad037dc400
job: job_run_ef025ef630ec470e8d138821225783a2_final_review
lease: lease_798233907a7e43159f269517c6786cfb
date: 2026-05-14

Verdict intent: accept

## Findings

No high-severity findings. The implementation matches the accepted safe slice
in `striatum/0034-watertight-volume-mesh-handoff/ledger/FINDINGS.md`. The
positive `cfd_ready` path is evidence-derived, profile-scoped, hash- and
path-bound; forged manifests, synthetic fixtures, open surfaces, and stale
diagnostics are all rejected. Lower-severity observations only:

### L-001 - Missing direct test coverage for several rejection codes

Severity: low

Source: ledger F-005 validation expectations.

`kayakgen/eval/cfd/jobs.py:1030-1186` defines the rejection codes
`cross_body`, `cross_hull`, `cross_tolerance`, `evidence_profile_mismatch`,
`malformed_diagnostic`, `body_surface_mismatch`, and
`artifact_checksum_mismatch`, but `tests/test_cfd_jobs.py` only exercises
`stale_checksum`, `forbidden_path_ref`, `synthetic_evidence`, and
`failed_self_intersection`. The remaining codes are reachable in principle
(e.g. corrupting `volume.body_ref` to trigger `cross_body`, replacing the
volume mesh JSON with garbage to trigger `malformed_diagnostic`) but no test
proves they fire. The ledger expected coverage explicitly named
"cross-body, cross-hull, cross-profile, cross-tolerance, ... malformed
diagnostics" rejection.

This is a coverage gap, not a behavior gap; the validator paths exist and
are deterministic. Logging it for follow-up rather than blocking, since
positive accept, stale checksum, forbidden path, synthetic, and
self-intersection-failed tests already prove the validator is wired up and
not a no-op.

### L-002 - `_expected_evidence_hash` alias resolution is permissive

Severity: low

Source: review of `kayakgen/eval/cfd/jobs.py:991-1005`.

`_expected_evidence_hash` accepts three alias forms when looking up
`manifest.evidence_hashes`: the canonical key (e.g. `volume_mesh_diagnostic`),
the literal `ref` value, and a `volume_mesh_artifact:<short>` form. Today the
writer only emits canonical keys and `volume_mesh_artifacts.<name>`, so the
alias surface is unused. It is harmless given each artifact is hash-bound to
file content, but the extra alias path widens the contract that future
manifests would have to honor and is worth narrowing or documenting if the
manifest ever evolves.

### L-003 - `MeshPackageManifest.solver_profile.profile_name` is the only signal that triggers watertight gating from a permissive solver

Severity: low

Source: review of `_solver_profile_requires_watertight_evidence` at
`kayakgen/eval/cfd/jobs.py:810-818`.

A package manifest can mark itself watertight by setting
`solver_profile.requires_watertight=True`, which is desirable for safety: any
dispatch into such a package goes through the full watertight evidence path
even if the *solver* profile is permissive. The same flag is set by the
package writer only via `watertight_solid_profile()`, so this is correct. It
does mean a forged manifest that *removes* `requires_watertight` and lowers
the solver profile to open-surface would skip watertight gating - but that
attack only succeeds if the dispatch profile also accepts open-surface
readiness, in which case nothing is being promoted to `cfd_ready` and the
attacker has gained nothing. Documenting the design choice.

## Verification Reviewed

- Patch summary `striatum/0034-watertight-volume-mesh-handoff/implementation/PATCH_SUMMARY.md`
  reports `90 passed in 42.29s` for the ledger-required suite under a
  temporary virtualenv.
- Independently re-ran
  `PYTHONDONTWRITEBYTECODE=1 /tmp/kayakgen-0034-venv/bin/pytest -q -p
  no:cacheprovider tests/test_mesh_package.py tests/test_cfd_jobs.py
  tests/test_closed_volume.py tests/test_generated_closed_body.py
  tests/test_cli.py` from the worktree as final reviewer: `90 passed`.
- F-001 accept path: `kayakgen/eval/cfd/jobs.py:840-944` derives `cfd_ready`
  only after explicit `readiness_authority`, body/closed/volume diagnostic
  reference, hash, profile, body-type, tolerance, body-surface-match, and
  artifact checksum gates. Synthetic bodies are rejected at line 1035-1039;
  forged manifests over open packages and forged quality reports are
  rejected by `tests/test_cfd_jobs.py:279-356`; passed RFC 0021 and
  generated closed-body diagnostics presented as standalone evidence are
  rejected by `tests/test_cfd_jobs.py:359-461`.
- F-002 manifest fields: `MeshPackageManifest` adds `body_ref`,
  `closed_volume_diagnostic`, `self_intersection_diagnostic`,
  `volume_mesh_artifacts`, `volume_mesh_diagnostic`, `evidence_hashes`,
  `readiness_authority` as optional fields
  (`kayakgen/eval/mesh_package.py:49-73`). Existing open-surface manifest
  shape preserved; round-trip and default behavior verified by
  `tests/test_mesh_package.py:35-130`.
- F-003 volume-mesh diagnostic: `kayakgen/eval/volume_mesh.py:1-275`
  introduces `VolumeMeshDiagnostic` with mesher identity, deterministic
  inputs, output artifact refs and SHA-256 checksums, cell/boundary
  metrics, invalid/inverted/zero/nonfinite cell counts, body-surface-match
  flag, structured readiness reasons, and warnings. The `cfd_ready`
  level is gated by `_cfd_ready_requires_clean_fixture_metrics` so a
  ready diagnostic must have positive cell counts, zero quality counts,
  positive minimum cell volume, matching body type, and at least one
  output artifact. Round-trip and structured-blocker tests live at
  `tests/test_closed_volume.py:269-343`.
- F-004 hash and path binding: `_resolve_package_ref`
  (`kayakgen/eval/cfd/jobs.py:947-966`) rejects empty, absolute,
  parent-traversal, or out-of-tree refs and missing files for both default
  surface refs and watertight evidence refs. `_verified_evidence_path`
  (lines 969-988) requires a manifest-recorded SHA-256 entry for every
  referenced diagnostic and artifact and re-hashes file content at
  dispatch. The deterministic `_job_id`
  (`kayakgen/eval/cfd/jobs.py:1271-1292`) folds `body_ref`,
  `readiness_authority`, sorted `volume_mesh_artifacts`, and sorted
  `evidence_hashes` into the identity, so changing any accepted-evidence
  hash forces a new job directory, exercised by
  `tests/test_cfd_jobs.py:650-709`.
- F-005 tests: positive matching handoff, stale checksum, forbidden path
  ref, synthetic evidence, failed self-intersection, and evidence-sensitive
  job identity tests are present in `tests/test_cfd_jobs.py:464-709`.
  Open-surface, watertight-without-volume-mesh, generated-body-without-
  volume-mesh, and forged readiness paths are also covered.
- F-006 CLI surfacing: `mesh-package` prints `readiness_blocker:` and
  `readiness_reason:` lines (`kayakgen/cli/main.py:139-166`); `cfd prepare`
  prints `blocker_class: <code>` for every `CfdDispatchError` before the
  failure message (`kayakgen/cli/main.py:206-209`). Asserted by
  `tests/test_cli.py:212-238` and `tests/test_cli.py:348-385`. Raw CFD
  result wording remains in place via
  `_echo_cfd_warnings`/`CFD_RAW_RESULTS_WARNING`.
- Raw/unvalidated CFD semantics intact: `CfdJobSpec`, `CfdRunRecord`, and
  `SolverRawResult` still pin `result_semantics: Literal["raw_unvalidated"]`
  and inherit `RawUnvalidatedClaimFields`; `tests/test_cfd_jobs.py:93-148`
  asserts `claim_state == "raw_unvalidated"` and rejects any attempt to
  promote calibrated/accepted-uses claims. The new `mesh_evidence_hashes`
  field on `CfdJobSpec` only carries the verified evidence index, not a
  validated CFD claim.
- Forged-watertight manifest over open-surface artifacts continues to be
  rejected through the same path as before
  (`tests/test_cfd_jobs.py:279-356`); the new accept path does not weaken
  that gate because it requires `readiness_authority ==
  verified_watertight_volume_mesh_evidence` plus the full evidence chain.

## Residual Risks And Deferrals

- The positive `cfd_ready` path is fixture-backed only and explicitly
  warns "fixture volume mesh handoff evidence only; CFD outputs remain raw
  and unvalidated"; a real solver mesher and validated CFD physics remain
  deferred and outside this slice.
- L-001 above: no negative tests for `cross_body`, `cross_hull`,
  `cross_tolerance`, `evidence_profile_mismatch`, `malformed_diagnostic`,
  `body_surface_mismatch`, or `artifact_checksum_mismatch` rejection
  codes. Validator paths exist; coverage is missing. Suggest a small
  follow-up workflow to add focused fixtures rather than blocking this
  slice.
- Surface-only watertight solver readiness, broader UI/web work, and
  production solver/mesher integration remain explicitly deferred per the
  ledger.
- The temporary verification virtualenv at `/tmp/kayakgen-0034-venv` is
  outside the worktree and not part of the patch; CI bootstrap of pytest
  remains a separate concern.
