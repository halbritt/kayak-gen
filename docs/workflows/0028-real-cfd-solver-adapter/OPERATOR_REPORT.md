# Operator report - workflow 0028

Updated: 2026-05-13

## Current state

- Queue item 0028 is `0028-real-cfd-solver-adapter`.
- Target scope is RFC 0015 and proposed RFC 0017.
- Workflow 0025 landed only local CFD dispatch and job artifacts. Real solver
  adapters, normalized physical outputs, web job routes, container execution,
  hosted workers, watertight geometry, and validated CFD claims remain
  deferred.
- Proposed RFC 0017 must be accepted or amended before implementation.
- Workflow 0027 closed-volume geometry is a dependency if the selected solver
  requires watertight solid input.
- This scaffold owns only
  `docs/workflows/0028-real-cfd-solver-adapter/**`.

## Intended review lanes

- Traceability: map RFC 0015 deferrals and accepted RFC 0017 criteria to
  landed behavior, missing work, or explicit future slices.
- Domain/CFD: verify solver setup, boundary conditions, raw/unvalidated result
  wording, speed/fluid inputs, and artifact provenance.
- Ops/test: verify dependency detection, local execution isolation,
  reproducible job directories, failure capture, and tests that do not require
  unavailable solver binaries.

## Next action

- Validate the workflow scaffold, then start the Striatum workflow after RFC
  0017 is accepted or amended.
