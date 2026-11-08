# RFC 0070: Preserve CFD preparation and execution attempts

Status: landed idempotent preparation + explicit retained attempts
Date: 2026-11-07
Context: KAYGEN-11; RFC 0067; D056; system review kayakgen-system-20261107.

## Problem

Identical preparation reopened a deterministic directory and reset a completed
run to queued. Its identity included a profile name, not the whole execution
profile. Repeating run overwrote logs and results in that same directory.

## Goals

- Repeated preparation preserves compatible prepared/completed bytes.
- Profile, mesh metadata or mesh-file changes conflict before existing writes.
- An explicit new attempt has its own directory, input snapshot and history.
- One local writer can prepare/run a request at a time; incomplete publication
  never appears as a committed executable attempt.

## Non-Goals

No distributed runner, retry scheduler, power-loss durability guarantee or
physical-validation promotion is introduced. Completed history is never purged.

## Proposal

Keep the legacy deterministic first directory name. `preparation.json` records
schema version, full normalized input fingerprint (`request_id`), unique attempt
identity, actual job specification, profile, mesh manifest and SHA-256 of all
referenced mesh files. Repeated prepare compares these inputs and returns the
existing run; conflicts and unverified legacy directories refuse unchanged.

`prepare(..., new_attempt=True)`, CLI `cfd prepare --new-attempt`, and the web
create body's `new_attempt` field allocate a distinct `-attempt-<random>` sibling.
Equal full inputs retain request identity; changed inputs receive another
fingerprint even if the legacy directory prefix is equal. Previous output stays
at its previous path. Calling run on a terminal attempt returns its committed
record without executing again. Running state is unresolved and cannot be reused
as permission to launch another process in the same attempt.

A nonblocking OS advisory lock held across the operation serializes preparation
and execution under the same legacy request prefix. Kernel release after process
death does not manufacture completion. Old children may retain partial files only
in their own immutable attempt namespace. All writers in an active namespace must
use this protocol; drain legacy writers before deployment or rollback.

Preparation writes into a hidden provisional sibling and publishes it by directory
rename after the input marker and content/occurrence records are complete. A failure
retains its provisional diagnostics. Run refuses a provisional/moved directory whose
name differs from its committed job identity. The existing content store protects
snapshot and result bytes; it remains distinct from ownership/completion.

Prepared job, profile and mesh inputs are immutable. Immediately before execution,
`execution-inputs.json` binds the unchanged full prepared inputs to that attempt.
Profile or job drift refuses before process launch. Custom command profiles must
be supplied to `prepare_local_job`, and any later change requires explicit new
preparation/attempts. A missing durable manifest or missing preparation occurrence never grants new-write
authority from raw snapshot bytes or legacy index reanchoring. Legacy records remain readable but require explicit new
preparation to execute under this protocol.

## Acceptance Criteria

- Prepare/run/prepare returns succeeded and leaves completed bytes unchanged.
- Full-profile changes (including timeout) conflict despite equal legacy ID.
- Explicit rerun creates another path and preserves old results/logs.
- Actual concurrent local prepare/run attempts have one writer or structured busy
  refusal. Partial preparation and failed terminal publication never report success.
- Mesh mutation refuses before execution. CLI/web expose the same new-attempt
  behavior and keep raw_unvalidated claim semantics.

## Open Questions

A coordinated multi-host protocol and power-loss/fsync guarantees would require a
separate decision. No such guarantee is implied by an advisory local lock.

## Implementation Path

1. Characterize replay/input conflicts and explicit rerun through public APIs.
2. Add retained snapshots, stage publication and one-writer local admission.
3. Exercise concurrent fixture children, failure publication, CLI/web and full
   release gates; retain the opt-in OpenFOAM checks independently.

## Domain Modeling

A CFD request fingerprint is the normalized immutable input value. An attempt is
one retained execution history. Preparation and execution snapshots are durable
artifacts; their existence alone is not completed solver work (DDD boundary
clarification). Reversal after new attempts requires compatible readers and
stopping admissions/draining owned work; never reuse an old manager on new active
attempts or rewrite history for rollback.
