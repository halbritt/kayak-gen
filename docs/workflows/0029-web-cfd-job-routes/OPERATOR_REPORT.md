# Operator report - workflow 0029

Updated: 2026-05-13

Run: `run_9126a2d7dd7a4fa3b9cbf6815a8e0c98`
Current job: `findings_ledger`

## Current state

- Queue item 0029 is `0029-web-cfd-job-routes`.
- Scope targets RFC 0008, RFC 0015, and proposed RFC 0018.
- Three review lanes completed: traceability, browser/domain, and ops/test.
- The findings ledger has been consolidated at
  `striatum/0029-web-cfd-job-routes/ledger/FINDINGS.md`.
- Gate result: `accept_with_findings`.
- No runtime code, source docs outside this workflow report, workflow JSON, or
  Striatum state files were changed by this ledger job.

## Ledger summary

The accepted implementation slice is local filesystem web CFD job routes over
the existing RFC 0015 dispatch contract. The implementation should add
`/api/cfd/*` routes for profiles, job creation, status, synchronous local run,
logs, and raw-result lookup; add a compact browser panel for those states; and
keep raw/unvalidated warnings visible in API payloads and UI copy.

The ledger explicitly rejects scope expansion into hosted workers, auth,
billing, quotas, cancellation guarantees, real solver success, watertight
promotion, validated CFD, calibrated resistance, or final design fitness
claims.

## Next action

- Hand `FINDINGS.md` to the implementation lane.
- Implement only the ledger-approved safe slice over `CfdJobSpec`,
  `CfdRunRecord`, solver profiles, mesh readiness gates, and local job
  artifacts.
- Keep docs and tests factual when implementation lands: local filesystem only,
  unavailable/failed states visible, and all CFD outputs raw/unvalidated.
