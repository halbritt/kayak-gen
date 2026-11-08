# RFC 0071: Bound streamed solver command lifetime

Status: landed streamed deadlines + bounded capture
Date: 2026-11-07
Context: KAYGEN-13; D057; staged OpenFOAM command runner; system review kayakgen-system-20261107.

## Problem

The streamed helper iterated stdout until EOF before applying `wait(timeout)`.
A silent command, continuous output, or an exited leader with a descendant
holding stdout could exceed the deadline and still report success. Retaining
all output lines in memory also grew without a bound.

## Goals

- The monotonic deadline covers shell startup, output draining and process wait.
- Timeout returns 124, terminates the owned process group and reaps its leader.
- Returned output retains at most the final 64 KiB of raw stream bytes plus an
  explicit truncation notice, while the selected disk log remains complete.
- Preserve merged-output ordering, normal exit codes and raw_unvalidated claims.

## Non-Goals

No whole-CFD-job SLA, generalized cancellation service, cross-host ownership,
retention deletion policy, or physical-validation claim is introduced.

## Proposal

Launch each streamed command in a new POSIX session/process group. Use nonblocking
binary reads and selectors with the remaining monotonic deadline. Reading does
not depend on line boundaries. The bounded capture keeps the tail so OpenFOAM
summary parsers can still see final status lines; a truncation notice makes the
loss explicit, and `log_path` retains all bytes already received.

On expiry, send SIGTERM to the owned group, allow 0.5 seconds for the leader,
then SIGKILL the group (also covering descendants after leader exit) and reap the
leader with a further bounded 0.5 second wait. Drain available final bytes and
close the pipe. OS failures remain exceptions; they never become successful
command results. Cleanup also runs if output/log processing raises. Normal
completion preserves the real exit code; timeout is always 124 even when the
leader exited zero while a descendant retained the pipe.

The implementation is for local POSIX command groups. A deliberately daemonized
process escaping its session is outside this boundary; such commands are not
supported solver stages. The operating system owns reaping orphan descendants;
the helper reaps its direct child and checks termination behavior through real
process fixtures. This does not assert a universal bound for an uninterruptible
kernel task or another execution host.

## Acceptance Criteria

- A silent `sleep` and continuous output without newlines obey the deadline.
- A leader exiting zero with a background descendant retaining stdout times out,
  and the descendant is no longer executing after return.
- Large output has bounded returned capture, intact final summary and complete
  disk log. Normal merged stdout/stderr and nonzero exit are unchanged.
- Existing ordinary adapter timeout behavior remains independently covered;
  opt-in real OpenFOAM smoke remains a separate gate.

## Open Questions

A wall-clock cap for a whole multi-stage CFD job would be a different contract.
Retention of full logs needs workload/preservation evidence before any deletion.

## Implementation Path

1. Reproduce silent, continuous and descendant-held-pipe failures using bounded
   local test processes, with no real solver required.
2. Implement concurrent deadline/draining, group cleanup and bounded tail capture.
3. Run focused regressions, full pytest/Ruff and the installed OpenFOAM smoke.

## Domain Modeling

A command deadline limits one subprocess stage. It is distinct from CFD attempt
completion, job cancellation, mesh readiness and accepted scientific use. This is
an execution-boundary correction. Before rollback, stop admissions and drain
owned commands; retain full logs and use a compatible runner for active stages.
