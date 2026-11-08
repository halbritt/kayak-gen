# RFC 0079: Audit and receipt admission for completion actions

Status: landed terminal audit and declared receipt admission
Date: 2026-11-08
Context: KAYGEN-16 / retrospective R1; D065; `kayakgen/operations/completion.py`.

## Problem

The R1 incident advanced completion after an audit command returned nonzero.
The later session-local correction checked specific receipts but left no
maintained caller for future completion, publication or tracker actions.
A tool returning normally also does not establish that its asynchronous audit
has finished. The maintained boundary must check results before invoking an action.

## Goals

- Refuse nonzero, nonterminal and contradictory audit results before any action.
- Require every task-declared receipt, its exact bytes, source identities and
  selected predicates, retaining useful refusal reasons.
- Provide both a Python callback API and a real argv caller.
- Permit an admitted action once per invocation, without retrying side effects.

## Non-Goals

Hosted tool protocol changes, distributed exactly-once execution, automatic
authorization, evidence authentication, action rollback and universal service
idle checks are outside this change. This gate changes no scientific claim,
readiness, calibration or candidate lifecycle state.

## Proposal

`guarded_completion(audit_result, requirements_path, action)` validates before
calling `action(CompletionEvidence)`. Audit `exit_code` must be integer zero,
excluding booleans. Every `session_id` or `cell_id` must be absent or null.
An optional `status`, when present, must be `passed`, `succeeded` or `success`.
Omitted status accommodates normal terminal subprocess/tool results; unknown,
malformed or explicitly failed status refuses even with exit zero.

The version-1 **Completion requirements** JSON names nonempty `expected_source`
hash identities and mandatory `receipts`. Each receipt declares a path,
SHA-256 of its bytes, JSON pointers binding every expected source dimension,
and nonempty `equals` predicates. Selectors support object keys and array indexes,
including JSON pointer escapes. Equality preserves JSON types and structures;
`true`, `1` and `1.0` differ. Paths are absolute or relative to the requirements
file. All JSON ingress is strict UTF-8 and rejects duplicate keys and non-finite
numbers. Immutable **Completion evidence** records the consumed requirements
hash, source expectations, receipt hashes and checked selectors.

`python -m kayakgen.operations.completion --audit-result RESULT --requirements
POLICY -- ACTION ARGV...` is the maintained orchestration caller. It executes
the actual argv without a shell or retry only after admission. Structured JSON
on stdout records `refused`, `action_succeeded` or `action_failed`; action output
goes to stderr. Refusal exits 2; the action's exit status propagates (signals use
128 plus the signal). Launch failures return 127 for missing executable, otherwise
126. `action_succeeded` means that process exited zero; it does not certify the
whole task or create permission to perform the action.

Inputs are trusted operator declarations. A matching hash establishes the bytes
consumed, not their truth or authenticity. Source identity is explicit, so an
intentionally historical snapshot may pass; the helper does not infer HEAD.
Receipt bytes are read once and returned evidence is immutable. No filesystem
lock spans validation and execution: callers own changes after validation,
action deadlines, atomicity and resulting state. Each invocation admits at most
one action call. A later invocation can execute it again.

## Alternatives and consequences

Leaving session-local scripts alone retains the reproduced unconditional-action
failure. Editing hosted tool protocols assumes unavailable authority. A durable
distributed workflow engine adds a larger state and recovery contract than the
accepted single-invocation requirement. A small local admission module plus a
real subprocess caller is the selected boundary. Explicit pointer policies
allow different receipt schemas without hiding domain-specific requirements in
generic code. Operators remain responsible for declaring all necessary checks.

## Acceptance Criteria

- Real caller tests prove failed and still-running audits cannot create an action
  marker, including falsey non-null handles and contradictory status.
- Missing, malformed, changed-byte or source-mismatched receipts and false
  predicates refuse with a reason; JSON type confusion cannot admit an action.
- A successful terminal result with matching evidence runs the action once;
  action errors propagate without retries.
- Alternate receipt layouts, explicit historical source and transient previews
  work with their declared requirements and no inherited idle interval.

## Open Questions

None within this admission scope. Authenticated evidence, concurrent mutation,
cross-host execution or idempotent external transitions require a separately
accepted contract before stronger guarantees can be claimed.

## Implementation Path

One coherent landing: behavioral red/green tests, the shared validator and real
module caller, operator documentation, then frozen-source full pytest and Ruff.
Root orchestration consumes the caller for the authorized final action.

## Domain Modeling

This is an operations boundary clarification under `DDD.md`'s “Adding to the
model” guidance. Completion requirements and completion evidence are immutable
operational value descriptions, not new hull-domain aggregates or scientific
acceptance states. Admission and the resulting external action remain distinct.
