# RFC 0076 — Verified candidate reuse and explicit sweep execution scope

Status: landed verified candidate reuse + explicit sweep scope
Date: 2026-11-07
Decision: D062
Work item: KAYGEN-12 / system architecture review W7

## Context and problem

A completed sweep resumed without new work changed each `complete` outcome to
`skipped`. Comparison then removed the same candidates from frontier eligibility.
Missing evaluation files bypassed artifact verification and allowed summary-only
reuse. A cancelled one-of-two sweep exposed only its processed subset, without
naming the full requested scope.

## Goals

Keep scientific outcomes stable across reuse, require recorded artifact evidence
before cached numerical admission, and persist requested versus processed work
with explicit execution status. Preserve D050 verified reads and D053 manifests.

## Non-goals

No numerical or physical claim promotion, regenerated evidence, inferred legacy
history, authenticated manifest, multi-host ownership, or universal crash and
power-loss guarantee. Active-search algorithm checkpoint redesign is separate;
this change verifies cached candidate evidence before either algorithm reuses it.

## Proposal

`CandidateRecord.status` remains the scientific outcome. Newly reused completed
candidates stay `complete`; their record bytes are unchanged. Legacy `skipped`
records remain readable and ineligible rather than being promoted to complete.

`SweepRunRecord` adds nullable legacy-compatible `execution_state`,
`requested_candidate_count`, `processed_candidate_count`, `reused_count`,
`reused_candidate_keys`, `execution_errors`, and `previous_run_artifact_hash`.
Current executions use `running`, `complete`, `cancelled`, or `incomplete`.
Counts are validated against actual outcomes. `complete` requires every requested
candidate to have been processed and no pending outcome. Failure is a resolved
scientific outcome, so a completed execution can contain failed candidates.
`skipped_count` remains a deprecated alias for the reuse action count; it no
longer describes newly persisted candidate states. Legacy absent execution fields
remain unknown, and comparison displays that uncertainty.

The writer publishes an initial running record. Individual candidate outcomes
remain durable as they are produced; full run snapshots are published at exit,
avoiding retention of every growing prefix in the content store. Cancellation
is polled after reused and new outcomes.
Required summary/failure outputs and indexing precede the final completion
record. Exceptions publish incomplete scope and error text, then
propagate to the caller and make the CLI report failure.
An uncatchable interruption can leave the initial running snapshot; it never
authorizes a completion claim. Verified candidate records support later resume.
Both job backends inspect the returned sweep execution state. Incomplete
execution remains `resumable` with an explicit scope error rather than becoming
`succeeded` merely because the function returned. Operator cancellation retains
its existing cancellation error and resumable state.
In-process sweep resume resets progress counters before replaying the requested
scope, including reused outcomes, so cancellation followed by resume cannot
double-count a prior completion. Active-search progress behavior is unchanged.

`search/candidate_reuse.py` is shared by sweep and both active-search algorithms.
It reads candidate occurrences through the existing manifest/content store,
checks occurrence kind and candidate key, verifies every named required artifact,
and checks hull/evaluation/record identity agreement. Missing canonical files are
restored only from bytes matching the recorded digest. Missing all copies,
corruption, metadata mismatch, or unknown bindings refuse reuse. A current file
cannot become invented historical evidence. `restore_artifact` returns the exact
verified bytes; consumers do not reopen an unchecked file after verification.
Comparison now also reads a missing canonical evaluation through its recorded
content reference rather than treating absence as permission for summary fallback.

Combined job/recovery verification exposed a pre-existing shared-index race:
simultaneous initializers could both observe schema version zero, then one
could drop tables and rows just committed by the other. `SqliteIndex` now holds
`BEGIN IMMEDIATE` across the version check and initialization/migration. SQLite
serializes those transactions across independent instances and processes;
the v1 backup and rollback rules remain intact. A deterministic two-process,
real-file regression forces the old stale observation and proves both rows
survive. This shared-index lock does not permit concurrent writers to a run
directory; that remains the separate ownership precondition.

## Migration and operation

Synchronous sweep/search invocation requires a single writer for each output
directory. Managed automatic resume additionally depends on RFC 0075 ownership
admission; do not run the CLI against an active managed job directory. Existing
manifest spec conflicts continue to refuse before output replacement.

Known historical hashes remain authoritative. Legacy directories with no trusted
run or candidate binding refuse automatic reuse; preserve them for inspection
and use a new output directory. There is no automatic adoption or reacceptance.
The previous run digest records the prior snapshot; its content blob remains in
the store. Reversal requires quiescent writers and preserved output backups;
older strict readers may reject the additive execution fields. Roll back into a
new namespace rather than deleting current ownership or provenance metadata.

## Acceptance criteria and evidence

- No-op sweep resume preserves outcome bytes, numeric metrics, and the frontier.
- Missing canonical candidate/hull/evaluation/mesh/STL files restore exactly
  from trusted content; missing all copies and corruption refuse reuse.
- NSGA-II and EHVI cannot rank cached results whose evaluation evidence is
  missing or corrupt, and both restore known missing canonical records.
- Cancellation, cancel-on-reuse, incomplete publication, pending outcomes,
  requested counts, legacy unknowns, and spec conflicts retain honest scope.
- In-process and subprocess runner boundaries keep incomplete pending sweeps
  resumable with explicit errors; `tests/test_sweep_job_completion.py` covers both.
- `tests/test_index_initialization.py` proves simultaneous process initialization
  preserves both runs; existing migration rollback and manager race tests remain.
- `tests/test_sweep_recovery.py`, `tests/test_search_recovery.py`, existing
  sweep/comparison/store/manifest tests, full pytest, and Ruff provide evidence.

## Open questions

An authenticated manifest and transactional multi-file completion would require
separate designs. Active-search checkpoint bytes remain algorithm-owned and
outside this candidate-evidence change.

## Implementation path

One coherent landing: shared admission/repair helper, explicit sweep execution
scope, comparison missing-file verification, CLI wording, regressions and docs.

## Domain modeling

**Scientific outcome** describes what happened to one candidate. **Reuse** is an
execution action consuming a verified prior outcome. **Execution scope** names
the requested and processed occurrences; a processed subset is not completion
of the full request. These concepts do not change evaluator claim semantics.
