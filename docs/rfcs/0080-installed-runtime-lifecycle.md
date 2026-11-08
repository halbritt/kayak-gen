# RFC 0080: Installed persistent runtime lifecycle acceptance

Status: landed installed runtime lifecycle acceptance
Date: 2026-11-08
Context: KAYGEN-17 / retrospective R2; D066.

## Problem

A web service can become ready, exit cleanly on its idle timer, and appear
healthy again after an automatic restart. Startup and environment declarations
therefore cannot prove continuous operation. The corrected local deployment
already uses timeout zero, server mode, stable release paths and
`KillMode=process`; verification must retain those choices.

## Goals

- Exercise the installed idle backend with positive and disabled timeouts.
- Observe effective installed parser settings and service process continuity.
- Require process-owned HTTP readiness before and after a selected idle interval.
- Preserve detached job ownership and report lifecycle failures explicitly.

## Non-goals

No service is installed, restarted, reconfigured or activated by this command.
It adds no universal observation duration, physical validation, hosted-worker
readiness or cross-host ownership guarantee. The earlier 315-second observation
belongs to that deployment's evidence.

## Proposal

Run `python -I -B -m kayakgen.operations.runtime` with the selected installed
interpreter, a source-bound `verification-request.json` from RFC 0083 and a new
external output directory. Before and after execution, reuse the release byte,
origin, wheel, resource and dependency audit. Failed attempts remain available.

The installed backend controls replay the actual Trame parser and start
`wslink.backends.aiohttp.WebAppServer` without WebSocket clients. Timeout one
must schedule and complete its idle shutdown; timeout zero must keep the same
backend process alive until explicit cleanup. Positive timeout is a valid
transient-server control, never persistent-deployment acceptance.

Optional persistent observation requires all of `--unit`, `--observe-seconds`
and `--readiness-url`. On Linux, capture systemd restart policy, invocation and
restart count, plus `/proc` PID/start/boot identity and actual argv. Replay the
installed parser through the observed stable virtual-environment interpreter.
Only the supported installed console entry point for `kayakgen serve` is
admitted; arbitrary processes containing a `serve` argument are refused.
Require effective timeout zero/server mode, `Restart=always`,
`KillMode=process`, the detached manager default and no in-process opt-out.
Backend versions and module bytes must match the exercised installed controls.

Readiness uses an explicit loopback IP HTTP URL. The observed main process
must own the listening socket; accept HTTP 200–399 without following redirects.
Do not create WebSocket clients or send HTTP traffic during the requested idle
interval. After sampled continuity and settings checks, repeat readiness so a
live process with a closed listener cannot pass. Record clean exit, failed
exit, restart and continuous same-process survival separately. Sampling proves
the recorded interval and observations, not continuous tracing of every event.

The receipt records control source, installed audits, backend identities,
requested and actual idle duration, before/after readiness, service samples,
settings and refusal reasons. A new external output directory retains terminal
failure evidence. Omitting the unit runs controls only and leaves
`persistent_deployment_accepted=false`.

## Alternatives and consequences

A fixed sleep after startup misses clean exits hidden by restart. Environment
inspection alone misses parser precedence. Active browser keepalives change the
idle condition being tested. A read-only installed replay plus owned backend
controls keeps verification separate from deployment authority. The supported
console wrapper is deliberately explicit; another installer needs demonstrated
entry-point support rather than a permissive argv fallback.

## Acceptance criteria

- Identify the actual installed interpreter, parser/backend and effective policy.
- Prove positive timeout exit and timeout-zero survival with the real backend.
- Observe explicit-duration persistent continuity, PID/invocation/restart count
  and readiness before and after a traffic-free interval.
- Retain stable paths, detached job ownership and `KillMode=process`; verify an
  owned manager child across its parent unit's lifecycle without touching the
  owner's service or unrelated jobs.
- Refuse lifecycle failures with retained diagnostics; positive-timeout
  transient controls remain valid.
- Pass the frozen full pytest suite with the documented skips, then Ruff.

## Open questions

Other service managers, backends and console-wrapper formats need separate
supported observations. None is inferred from this Linux/systemd/aiohttp path.

## Implementation path

Real backend controls, read-only service identity and readiness checks,
behavioral refusal cases, installed acceptance and owned systemd lifecycle
controls, then the frozen full gate and trunk integration.

## Domain modeling

This is an operations boundary. Runtime lifecycle acceptance describes one
observed deployment interval; it is separate from scientific accepted uses,
candidate lifecycle and the existing managed-job ownership protocol.
