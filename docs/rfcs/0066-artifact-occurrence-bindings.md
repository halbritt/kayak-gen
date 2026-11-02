# RFC 0066: Artifact occurrence bindings

Status: landed occurrence bindings + transactional v1 migration
Date: 2026-11-01
Context: RFC 0049 / D030, D050, D051; architecture finding F02 / KAYGEN-2.

## Problem

The v1 SQLite `artifacts` row combined content identity with a single run,
path and candidate association. Equal bytes in another run replaced that
association. A duplicate deterministic sweep therefore removed the first
run's expected-hash lookup; comparison then used its legacy unverified
fallback and accepted a modified `run.json`.

## Goals

- Preserve each current run/path occurrence of shared content.
- Keep known expected hashes across index upgrades without trusting today's
  canonical bytes as historical evidence.
- Keep canonical JSON, `_store/` content paths and `ArtifactRef` unchanged.

## Non-Goals

Global blob storage, remote backends, scientific claim changes and run-identity
reconstruction are outside this change. KAYGEN-3 tracks durable manifest recovery (planned RFC 0067).

## Proposal

SQLite schema v2 retains `artifacts` for content hash, byte count and creation
time. `artifact_occurrences` owns the current expected hash, kind and candidate
for each `(run_id, relative_path)`. Path replacement changes that occurrence
only. `SqliteIndex.upsert_artifact` writes content and occurrence in one
transaction. Path readers resolve the occurrence and keep D050 verification.

Opening a v1 index first writes `<index-path>.v1.bak` if absent, then migrates
under `BEGIN IMMEDIATE`. Every surviving content hash is copied. When multiple
old hashes describe one path, the previous lookup order (creation time, then
row ID) selects its current occurrence. No canonical files are read during
migration. DDL uses individual statements, because `executescript` would commit
before migration completes. Any exception rolls the migration back; retry on
the same index object remains possible. A concurrent opener rechecks the stamp
after obtaining the write lock.

The migration removes obsolete association columns from the content table.
Pre-versioned incomplete indexes retain the existing rebuild behavior. Newer
stamps are not downgraded. Older code must not be run against a migrated index:
restore its v1 backup when rolling code back, accepting that the backup excludes
later writes. Preserve the migrated database before rollback. This is one
explicit schema transition, not a new general migration framework.

Previously overwritten associations are unrecoverable without independent
expected hashes. They remain unverified legacy reads under D051; this change
does not certify them by hashing their current files.

## Acceptance Criteria

- Comparison rejects a modified run after an identical sweep is written to a
  second directory, as well as for an isolated run.
- Equal bytes at different paths/kinds/candidates retain both occurrences;
  replacing one path does not replace the other.
- A real v1 database migrates its expected hash even if its canonical file was
  changed; verification refuses the mismatch.
- SQLite write and migration failure injection roll back partial changes;
  retry succeeds without losing known bindings.
- Existing artifact corruption/repair tests and the full release gate pass.

## Open Questions

None for this slice. Same-basename run-ID collisions and reconstruction after
index loss remain explicitly assigned to KAYGEN-3 (planned RFC 0067).

## Implementation Path

1. Reproduce duplicate-sweep verification bypass through comparison.
2. Split content from occurrences and migrate known v1 bindings transactionally.
3. Verify preservation, replacement, rollback and public comparison behavior.

## Domain Modeling

Per `DDD.md` § "Adding to the model", this is a persistence responsibility
clarification. **Artifact occurrence** means a current run/path binding to
content; it is distinct from **artifact_hash**, the identity of bytes. The
`ArtifactStore` retains persistence ownership and its existing caller interface.
