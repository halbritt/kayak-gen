# RFC 0075: Local subprocess attempt ownership

Status: landed local subprocess ownership and fenced state publication
Date: 2026-11-07
Context: KAYGEN-10; RFC 0057/D037; system review kayakgen-system-20261107.

## Problem

A fresh subprocess manager treated an empty in-memory process map as proof that
an existing worker was dead. It could write `resumable` while that worker was
still running, then authorize another writer. A PID alone cannot distinguish
reuse, and legacy job records do not carry sufficient ownership evidence.

## Goals

- Retain one manager-owned writer across manager restarts and concurrent resumes.
- Distinguish a live owner, a proven dead owner and missing/unknown evidence.
- Preserve attempt identity, history, diagnostics, spec and checkpoints.
- Fence stale job-state publications and reject unsafe mixed-backend operation.

## Non-Goals

No distributed scheduler, cross-host execution, hostile same-user protection,
force-unlock operation, power-loss claim or whole-evaluation cancellation SLA.
Raw CLI writes into an actively managed output directory remain unsupported.

## Proposal

New subprocess jobs have `ownership-protocol.json`. `GenerativeJob.attempt_id`
is nullable for legacy/in-process records; managed attempts carry a 32-hex token.
`services/generative_job_ownership.py` owns the local protocol.

The admitting manager acquires `ownership.lock` using nonblocking POSIX flock,
records a new attempt and inherits the open lock descriptor into the actual
runner. The manager closes only its descriptor reference. It never calls
`LOCK_UN`, which would release the shared open-file-description lock. The child
retains its descriptor through all algorithm effects, final state and cleanup.
Concurrent admission fails while either holder remains.

`owner.json` binds the current token to machine ID, boot UUID, PID, process start
ticks and lifecycle phase. The parent records worker identity before the child
starts writes; the child handshake is bounded at five seconds. History lives in
`attempts/<token>/{admitting,starting,running,launch_failed}.json`; final/reconciled job state is
retained as `attempts/<token>/job.json`. Existing bounded `log.txt`, spec and
algorithm output/checkpoints remain. Logs name their attempt.

A manager lacking a Popen handle can observe and request cooperative cancellation
of the actual owner. Observation cannot infer death from its process map.
With an unlocked namespace, a matching-host owner is proven dead only when its
process is absent/zombie or its boot/start identity differs. Missing, malformed,
foreign-host or inconsistent evidence remains unknown; automatic resume refuses.
A failed process launch is recorded as an ended admission with no surviving
worker, so a later corrected launch can safely acquire a successor. The admission
lock is held during reconciliation and successor creation. The
persisted spec must still hash to the admitted request before execution.

Every managed `job.json` write requires the active local lease context and the
current attempt token. Cached old snapshots and unmanaged publishers cannot
replace state. In-process resume refuses a managed subprocess namespace or an unknown prior
thread; same-manager thread resume checks the old thread under its admission lock. Its
cancel operation delegates to the existing cooperative flag path. Parents do
not race worker state updates when cancelling: the durable flag records the
request time, the response acknowledges it, and the worker persists it.

### Ownership invariants

1. A live protocol worker holds the same lock inherited at admission. No second
   compliant manager can acquire a successor lease while it can write output.
2. Each successor receives a new token. Job-state publication needs both its
   token and a current lease context; a stale snapshot fails before replacement.
3. Reconciliation writes `resumable` only under the lock after full process
   evidence establishes death. Unknown evidence does not change on-disk state.
4. A direct runner invocation may start only a newly marked queued job with no
   existing attempt. Existing attempts require manager admission.
5. Completed attempts retain their own metadata snapshot; new attempts preserve
   prior directories and algorithm checkpoints. Indexing remains derived.

This is a same-host local-Linux protocol: `/proc` process/boot identity,
`/etc/machine-id`, POSIX descriptor inheritance and flock are required. Unsupported
hosts refuse this subprocess backend explicitly; in-process operation remains
available. Network-mounted job directories and direct foreign writers are not
accepted ownership guarantees. File hashes do not replace the lock.

## Acceptance Criteria

- A real live sweep survives a fresh manager observer and can be cancelled by it.
- A killed owned child is proven dead; one successor with a new token is admitted.
- A worker keeps its lease after its actual manager process dies and remains
  observable/cancellable through a fresh manager.
- Concurrent resume from two managers admits exactly one successor.
- A cached old job cannot publish success over the successor.
- Reused PID with a different start identity is not treated as the old process.
- Missing, malformed and foreign-host evidence blocks automatic replacement and
  leaves persisted state unchanged when the operator is absent.
- Legacy namespaces without the new protocol remain readable but quarantined
  from automatic execution. No in-process takeover of a managed job occurs.
- A changed persisted spec is refused before creating another attempt.
- Existing deterministic cancellation checks and real subprocess/search/web
  regressions pass without new skips or weakened assertions.

## Open Questions

Additional operating systems need a separately proven process/lock capability.
Cross-host successor admission requires a different authority protocol; changing
host identity is not evidence that the original host's worker died.

## Implementation Path

Reproduce the real live-child failure; add runner-held lease and process evidence;
verify each recovery/negative scenario; document namespace migration; run full
pytest then Ruff under the shared gate lock; land one coherent RFC.

## Domain Modeling

A job is the admitted request; an attempt is an execution owner. Scientific result
status, job execution state, artifact provenance and process liveness remain
separate. Unknown ownership is a refusal condition, not successful recovery.

## Migration and reversal

Drain existing workers before deployment. Read legacy job records for inspection;
do not infer ownership or silently resume an unmarked namespace. If ownership
cannot be established, retain it for diagnosis and start a separately identified
new job only through an explicit operator decision after reconciling old work.
Do not delete/unlink a live ownership lock or run old and new managers against
one active job namespace. Older strict readers reject the new attempt field.

Before new managed writes, rollback is a code reversal. Afterwards stop admission,
drain only owned work, retain attempt history and use compatible readers or
forward repair. Never strip attempt IDs, restore stale job files, or remove lock
files to simulate legacy state. Cancellation remains cooperative between candidate
emissions; no fixed latency is claimed for a currently running evaluator.
