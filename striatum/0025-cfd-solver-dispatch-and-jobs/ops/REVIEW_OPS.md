author: operator [self-declared: operator-ops-review]

# Ops review - workflow 0025

Verdict intent: accept_with_findings

## Findings

### O-001 - Local job directories should be deterministic and inspectable

RFC 0015 needs artifacts that can be compared in tests. The job directory
should have a stable ID and small JSON records so status can be read without
external services.

Required action: derive the job ID from stable mesh manifest/profile/fluid
inputs; write `job.json`, `run.json`, and a manifest reference file or field in
one job directory; cover JSON round-trip tests.

### O-002 - CLI ergonomics need explicit prepare, status, and run errors

Users need to see whether a job is queued, unavailable, failed, or succeeded
without inspecting raw files. Missing mesh packages and malformed records should
fail clearly.

Required action: add `kayakgen cfd prepare --mesh-package ... --solver-profile
... --speed-mps ... --out ...`, `kayakgen cfd status JOB_DIR`, and `kayakgen cfd
run JOB_DIR`. Return non-zero for prepare/readiness failures and successful
exit for status reads.

### O-003 - Baseline tests must not depend on solver binaries

The project cannot require OpenFOAM, SU2, Docker, or hosted credentials for the
dispatch contract tests.

Required action: implement an unavailable adapter that needs no binary and a
mock local-command adapter that deliberately fails through the Python
interpreter. Assert unavailable and failed states without installing external
software.

### O-004 - Failure capture must write durable run records

A failed command should leave a run record that captures the command failure
instead of throwing away the job state.

Required action: when a local command exits non-zero, write `status: failed`,
`error_kind: command_failed`, an `error_message`, and a log path/reference.

### O-005 - Test coverage should be focused but end-to-end

The safe slice touches models, filesystem IO, CLI parsing, mesh readiness, and
failure semantics.

Required action: add focused tests for job/run model round-trips, prepare
success, readiness rejection, unavailable run behavior, failed command
behavior, and at least one CLI prepare/status/run path.
