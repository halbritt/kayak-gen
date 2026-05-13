author: operator [self-declared: operator-0029-browser-domain]

# Workflow 0029 Browser And Domain Review

Verdict intent: accept_with_findings

## Scope

This review checks the browser-visible CFD route slice for domain truthfulness:
users must be able to inspect local CFD job states without mistaking raw,
unavailable, failed, or fixture output for validated hydrodynamic prediction.

## Findings

### B-001 - Raw/unvalidated wording must be visible outside JSON internals

`CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, and `SolverRawResult` carry
`result_semantics: raw_unvalidated`, and the CLI prints "CFD results are raw
and unvalidated." The web UI currently has no CFD panel, so there is no
browser-visible equivalent.

Required action: every CFD job status, run result, log/raw-result view, and
artifact inspection entry must show a plain raw/unvalidated warning in the UI
and API payload. Do not rely on users noticing `result_semantics` in raw JSON.

### B-002 - Unavailable and failed states must not look like completed solver work

The accepted local profiles include `unavailable-open-wetted-surface`,
`unavailable-watertight-solid`, and `mock-failing-local-command`. These are
useful browser fixtures only if the UI makes their meaning explicit. A
completed HTTP request is not the same as successful CFD.

Required action: render `unavailable` and `failed` as terminal problem states
with `error_kind`, `error_message`, solver profile, and timestamps. Avoid
success colors or "complete" wording unless a run record has `status:
succeeded`, and even then keep the raw/unvalidated warning attached.

### B-003 - Mesh readiness rejection needs structured user-facing detail

RFC 0018 requires readiness rejection to be visible as a structured API error.
The CLI currently exposes readable error strings such as readiness below
solver requirement or solver profile mismatch. A browser user needs the same
facts without parsing a traceback or generic validation failure.

Required action: job creation failures must return JSON with a stable error
kind, selected solver profile, required readiness, observed readiness when
available, mesh profile mismatch details when available, and a user-facing
message. The UI should show this as a job-preparation rejection, not as a
server crash.

### B-004 - Logs and raw outputs must be presented as artifacts, not conclusions

For unavailable and failed runs there may be logs but no raw-result artifact.
For future fixture success there may be a `raw-result.json`, but that is still
solver output, not calibrated resistance. The current web analysis panel shows
analytical resistance as a raw comparative filter; CFD artifacts must remain a
separate domain boundary.

Required action: log and raw-result links must indicate missing/unavailable
artifacts cleanly and label present artifacts as raw solver artifacts. Do not
blend CFD output into the hydrostatics/resistance analysis rows or comparison
objectives as validated drag.

### B-005 - Local filesystem scope should be visible as a product limitation

RFC 0018 allows the first implementation to use local filesystem jobs only.
That is materially different from hosted workers or shared team queues.

Required action: UI copy and docs should say this web CFD slice reads and
writes local job artifacts on the server running `kayakgen serve`. Leave
hosted workers, auth, multi-user persistence, cancellation guarantees, and
live progress as explicit follow-up work.

## Browser/Domain Summary

The browser slice can be accepted if it acts as an honest local job inspector:
profiles, readiness rejection, unavailable/failed states, logs, and raw
artifacts are visible, while real CFD success and calibrated predictions remain
unclaimed.
