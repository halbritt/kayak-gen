# Task — synthesize the remediation plan

Read `striatum/0009-multi-lane-review/ledger/FINDINGS.md`. Write
`striatum/0009-multi-lane-review/synthesis/REMEDIATION.md`.

Structure:

```markdown
# Remediation plan — 0009 multi-lane review

Date: <YYYY-MM-DD>
Source ledger: striatum/0009-multi-lane-review/ledger/FINDINGS.md

## Executive summary

3-5 sentences. What's the most important thing the user should do?
What can wait? Were there genuine blockers, or only major/minor items?

## Plan

### P-001 — <short title>
- Addresses: F-NNN [, F-NNN, ...]
- Scope: <files / functions / RFCs touched>
- Sketch: <concrete fix in 3-6 lines, including any new test required>
- Effort: S | M | L
- Risk: low | medium | high
- Depends on: P-NNN (or "none")

### P-002 — ...

## Deferred / rejected findings

Findings the synthesizer chose not to act on now. Each row carries an
explicit reason (out of scope, defer to follow-on RFC NNNN, false
positive, etc.).

## Integrity-track resolution

For each `accept` / `accept-with-remediation` / `reject` finding from
the integrity track, record the chosen action. If
"accept-with-remediation" is chosen, name the remediation as a P-row.

## Dependency graph

Optional Mermaid diagram showing which P-rows block which.
```

Rules:

1. Every `blocker` and `major` finding must be addressed by at least
   one P-row OR appear in `Deferred / rejected` with a reason.
2. Bundle `minor` and `nit` findings into one or two polish-pass
   P-rows unless one is on a blocker's critical path.
3. If reviewers dissented (per the ledger's `(dissent)` tag), pick
   one position and document the trade-off in 1-2 sentences. Do not
   bundle the dissent away silently.
4. The `final_review` job will verify your plan against the ledger.
   A `needs_revision` verdict cycles you back here once with notes.
