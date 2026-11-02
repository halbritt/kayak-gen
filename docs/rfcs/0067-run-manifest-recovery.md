# RFC 0067: Durable run identity and provenance recovery

Status: landed run manifests + honest index reconstruction
Date: 2026-11-01
Context: RFC 0049 / D030, RFC 0066 / D052, D050, D051; F03 / KAYGEN-3.

## Problem

Sweep/search IDs combined a spec digest and directory basename, so separate
campaigns with the same basename replaced one index row. Reindex invented a
new ID, substituted spec_hash for run_hash, and restored no artifact bindings.
The index was therefore the only surviving expected-hash source for many reads.
Deleting it disabled verification even for newly produced runs.

## Goals

- Preserve original run identity, semantic hashes and recorded artifact hashes
  after SQLite loss for manifest-backed sweep, search and CFD outputs.
- Keep canonical domain records and numerical behavior compatible.
- Distinguish unknown legacy provenance from verified modern reconstruction.
- Reject copied-instance collisions and ambiguous relocation without publishing
  changed location metadata.

## Non-Goals

No remote storage, clone/adopt CLI, lossless reconstruction of unknown history,
scheduler rewrite, new search-comparison capability, or scientific claim change.
Reindex restores run/candidate/metric/content/occurrence projections; it does
not reconstruct the separate generative-jobs or events tables. Existing optional
job-index publication links to the output manifest when one exists.

## Proposal

`FilesystemArtifactStore.open_run` establishes a run instance, and the store
owns versioned `_store/manifest.json`. `RunManifest` contains run_id, kind,
spec_hash, semantic run_hash, original creation time, last location,
`provenance_complete`, and current path-to-ArtifactRef bindings. A new instance
gets an opaque ID once. Resume preserves it; equal directory basenames do not
collide. `run_hash` retains its producer's semantic definition; it is not the
instance ID. CFD job_id remains the deterministic domain identifier while its
index instance ID is separate. Existing canonical record schemas are unchanged.

`provenance_complete` describes expected-hash coverage, not whether a job or
candidate has finished. A manifest-backed path reader uses recorded hashes even
when SQLite is missing. Missing bindings in a complete manifest, malformed
manifests, mismatched kind/candidate metadata, or corrupt content fail explicitly;
none can silently fall back to an unverified canonical read.

### Publication and failures

Each acknowledged store write preserves its content-addressed bytes, publishes
the current occurrence in an atomically replaced manifest, then updates SQLite.
A projection failure propagates; the manifest remains available for recovery.
A manifest publication failure leaves the prior published expected hashes in
force. Source writers use atomic text replacement, or detach existing STL
canonical hardlinks before rewriting, so a failed update cannot destroy the
previous committed content inode. CSV retains its no-newline-translation contract.
These are local atomic-replacement guarantees, not a new power-loss/fsync or
multiple-writers-to-one-run guarantee.

CFD operational updates use the same publication rule. For manifest-backed CFD
runs, arbitrary external edits to run.json are no longer automatically reanchored:
there is no reliable way to distinguish an intentional edit from an uncommitted
failed write. Legacy index-backed CFD records retain their established reanchor
behavior. This is an explicit narrowing of that operational compatibility rule;
D050 verification and raw_unvalidated claim semantics remain unchanged.

### Legacy and movement

An unambiguous old index row can supply its original ID/hash/time and surviving
bindings. Migration copies those hashes without reading current bytes as proof.
Its provenance remains incomplete because previously overwritten associations
cannot be recovered. Without old metadata, legacy import records an unavailable
run_hash as null; it never computes a historical hash using today's version.
Matching kind/spec may reopen that incomplete run without manufacturing a hash.
Unknown legacy paths retain D051's direct-read behavior, honestly unverified.

The last location is checked against both the manifest and the index. Resolved
aliases of the same physical directory are equivalent. Relocation is allowed
only if the previous directory is absent, or its valid manifest names another
instance (the path was reused). An existing directory with no manifest, a
malformed old manifest, or another live copy of the same instance is ambiguous
and refused. A preflight checks before publication; index replacement repeats
the location invariant transactionally. No clone command is added.

### Reconstruction interface

`reindex_run` validates all surviving expected hashes, parses candidate records
from run.json, and replaces that run's SQLite projection transactionally. Removed
candidate/metric/occurrence rows do not survive as stale entries. Repeating the
operation is idempotent. The CLI reports artifact count and
`provenance=complete|incomplete`; incomplete legacy imports emit a warning.
`--run-id` may name an unindexed legacy import, or match an established identity;
it cannot silently overwrite one. Invalid candidate records refuse reconstruction
rather than silently disappearing from its success count.

## Acceptance Criteria

- Real sweep, search and unavailable-profile CFD outputs retain ID/kind/spec/hash/
  creation time, candidate metrics and occurrence bindings after deleting an
  isolated DB and reindexing twice.
- When no verified copy survives, modified content causes public comparison/
  reindex refusal. Malformed manifests, missing modern bindings and mismatched
  run-record kinds also refuse; unknown legacy CLI imports remain visibly incomplete.
- Separate same-basename runs have distinct instances; resume preserves identity.
- Relocation/copy cases obey the stated policy; refused copies leave manifest
  bytes and existing projection unchanged.
- Manifest and SQLite failure injection preserve the stated publication behavior;
  a failed real CFD update leaves the previous trusted run record readable.
- Preserve canonical JSON and CSV behavior, including simulated Windows newline
  translation, and existing algorithm determinism tests. Run the full release
  gate and installed OpenFOAM opt-in smoke/stage checks before integration.

## Open Questions

None for this slice. Authentication of maliciously rewritten valid manifests,
multiple concurrent writers to the same output directory, event replay and
subprocess job-index synchronization remain outside this local recovery contract.

## Implementation Path

1. Prove identity, known/unknown legacy trust, relocation and publication failures
   using small real SQLite/filesystem fixtures.
2. Migrate sweep/search/CFD producer registration and protect canonical prewrites.
3. Route CLI reconstruction and path readers through the durable metadata; remove
   duplicated basename/reindex ID recipes and obsolete CLI parsing.
4. Validate real producers, failures, bytes and full release checks.

## Domain Modeling

Per `DDD.md` § "Adding to the model", **RunManifest** is a persistence-owned
record. **Run instance** identifies a particular output history, while run_hash
identifies semantic inputs. **Provenance completeness** describes surviving
expected-hash coverage and does not promote a scientific claim or job state.
