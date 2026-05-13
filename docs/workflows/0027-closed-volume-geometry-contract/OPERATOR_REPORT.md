# Operator report - workflow 0027

Updated: 2026-05-13

## Current state

- Scaffold landed on `main` as `76c33e6`.
- Prepared and started Striatum run `run_6a701b70b294436ba529dce7bb705b9b` on
  branch `striatum/0027-closed-volume-geometry-contract`.
- Claimed and acked the three review jobs:
  - `review_traceability` as `sess_36f6e40dd26c4cd496acb07f481d12f6`;
  - `review_domain_geometry` as `sess_64eea9ef66f94d29a758cc95f48fd380`;
  - `review_ops_test` as `sess_73ce13d09321454aafe7478b4e841654`.
- Published the three review artifacts:
  - traceability `art_24649ce62405405cafe8f24666733001`
    (`accept_with_findings`);
  - domain/geometry `art_4dd7dd6d57bf455f88265da470024b22`
    (reviewer intent `needs_revision`, operator-overridden to
    `accept_with_findings` for ledger gating);
  - ops/test `art_5a7daadb9c354eabaa8a0e33a8b387b2`
    (reviewer intent `needs_revision`, operator-overridden to
    `accept_with_findings` for ledger gating).
- Claimed and acked `findings_ledger` as
  `sess_e0e0c612b9aa46d2be941e835c512ef3`.
- Queue item 0027 is `0027-closed-volume-geometry-contract`: define and
  implement the first explicit closed-volume hull-plus-deck geometry contract
  after RFC 0016 is accepted or amended.
- Scope targets RFCs 0004, 0006, 0010, 0015, and proposed RFC 0016.
- This scaffold uses three review lanes before implementation:
  traceability, domain/geometry, and ops/test.
- Implementation is assigned to Codex by default.
- Current generated mesh packages must remain honestly classified as open
  surfaces unless the accepted RFC and tests prove closed-volume readiness.
- Implementation is complete locally. It landed only the ledger-constrained
  safe slice: explicit synthetic closed-volume contract models/diagnostics,
  body-level open/nonmanifold/signed-volume checks, forged watertight dispatch
  rejection, RFC/docs/user-guide/changelog updates, and no generated
  hull-plus-deck closure or `cfd_ready` promotion.
- Targeted verification passed:
  `.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_cfd_jobs.py tests/test_mesh_package.py -q`
  -> 21 passed.
- Full verification passed: `.venv/bin/python -m pytest -q` -> 167 passed;
  `git diff --check` -> clean.
- Final review accepted with findings as
  `art_3d03d49d6c814726aa9c59e7e99bde8f`; Striatum run
  `run_6a701b70b294436ba529dce7bb705b9b` is complete.

## Findings recorded

- Ledger written to
  `striatum/0027-closed-volume-geometry-contract/ledger/FINDINGS.md`
  by `operator-0027-ledger`.
- Published ledger as `art_882d828a0f3f428798fc7a8ccbaf623f` and completed
  `findings_ledger`.
- Claimed and acked `implement_findings` as
  `sess_3dd3513def214f58b8b5909e8b9aacbc`.
- Gate result: `needs_revision` for generated closed-volume implementation and
  any `cfd_ready` handoff. The operator override to `accept_with_findings` was
  used only to consolidate the domain/geometry and ops/test blockers; it does
  not water them down.
- Safe-now implementation scope is limited to RFC 0016 contract scaffolding,
  serializable closed-body metadata/manifest boundaries, closed-body
  diagnostics, synthetic valid/open/nonmanifold fixtures, evidence-based
  watertight dispatch rejection, profile-scoped diagnostics, RFC 0006
  validity/advisory metadata, and broader CLI failure-mode wording/tests.
- Required RFC 0016 policy amendments before generated-body implementation:
  name the first closed body and waterline semantics; define bow/stern cap
  construction and plumb endpoint handling; define sheerline/deck-join behavior
  including `beam_wl_m != beam_oa_m`; define outward normals, signed-volume
  acceptance, body-level manifold authority, and serialized closure tolerances.
- Explicitly deferred until those policy amendments and tests land: valid
  default generated hull-plus-deck closed-body success, any generated-geometry
  `cfd_ready` handoff, high-angle `GZ`, real CFD adapters, calibrated drag,
  final design fitness, volume meshing, and validated solver-output claims.

## Next action

- Commit and push the accepted workflow branch, then fast-forward and push
  `main`.
