# Findings ledger - workflow 0034 watertight volume mesh handoff

session: sess_4eec82ce693a4358bfb887b0ee4b9007
job: job_run_ef025ef630ec470e8d138821225783a2_findings_ledger
lease: lease_3fa340b57a9840e89b3cc7dc75830b18
date: 2026-05-14
gate_result: accept_with_findings

## Gate Verdict

Proceed to implementation only under a narrow RFC 0023 evidence-contract slice.
The reviews agree that current behavior is conservative: existing generated
open-surface packages remain below `cfd_ready`, and watertight dispatch rejects
all current evidence rather than trusting a hand-edited manifest readiness
string.

The implementation may add typed manifest evidence, volume-mesh diagnostics,
hash/path validation, structured rejection reasons, and an evidence-derived
writer/dispatch path. It must not promote open surfaces, explicit synthetic
closed-volume fixtures, or closed generated surfaces without matching
volume-mesh evidence to `cfd_ready`.

Generated hull-plus-deck closed-body diagnostics and self-intersection checks
now exist as prerequisites. The remaining hard blocker for unconditional RFC
0023 completion is volume-mesh capability and the evidence binding around it.
A positive `cfd_ready` handoff is acceptable only if the implementer provides a
real or fixture-backed volume-mesh artifact derived from the matching generated
body and validates it against RFC 0023 evidence.

## Consolidation Stats

- Review artifacts read: 3.
- Read-only helper passes used: 3.
- Raw review themes: 17.
- Deduplicated accepted findings: 6.
- Downgraded or folded findings: 3.
- Gate shape: conditional implementation, no blanket `cfd_ready` promotion.

## Deduplicated Findings

### F-001 - Watertight dispatch has no positive evidence accept path

Severity: high

Source lanes: traceability F1/F8, ops positive-handoff finding, domain
profile-scoped `cfd_ready` finding.

Current `dispatch_evidence_satisfies_profile()` parses
`ClosedVolumeDiagnostics` and then returns `False` for every case, including
`required_mesh_readiness == "cfd_ready"`. This is correct for the earlier safe
slice, but it means RFC 0023 cannot land a successful
`watertight_solid_resistance_v1` handoff today.

Required action:

- Add a real typed evidence validator for the RFC 0023 handoff profile.
- Treat manifest readiness as necessary but never sufficient.
- Accept only generated kayak bodies, not `explicit_synthetic_triangle_mesh`
  bodies.
- Require generated-body diagnostics, passed self-intersection diagnostics,
  volume-mesh diagnostics, matching profile/tolerances, and matching hashes.
- Preserve conservative rejection for unknown, malformed, missing, synthetic,
  stale, or cross-body evidence.
- Return rejection reasons that callers can surface instead of a bare boolean.

### F-002 - RFC 0023 manifest evidence fields are absent

Severity: high

Source lanes: traceability F2/F5, ops manifest/evidence-shape finding, domain
volume-mesh evidence finding.

`MeshPackageManifest` currently records the RFC 0010 package shape:
`hull_hash`, solver profile, readiness, parts, hull JSON, quality reports,
surfaces, and warnings. It has no RFC 0023 fields for `body_ref`,
`closed_volume_diagnostic`, `self_intersection_diagnostic`,
`volume_mesh_artifacts`, `volume_mesh_diagnostic`, `evidence_hashes`, or
`readiness_authority`.

Required action:

- Add only the RFC 0023 traceability fields needed for the handoff.
- Keep the manifest as an evidence index, not the physical readiness authority.
- Preserve the current open-surface package shape and default behavior.
- Add round-trip tests for manifests with and without the new optional evidence
  fields.

### F-003 - Volume-mesh diagnostic and artifact evidence do not exist

Severity: high

Source lanes: ops manifest/evidence-shape finding, domain volume-mesh evidence
finding, traceability RFC 0023 matrix.

There is no `volume_mesh` model/module or package artifact path. RFC 0023
requires a diagnostic that records `body_ref`, source hull hash,
generated-body diagnostic hash, mesher identity/version/config digest,
deterministic inputs, output artifact refs and checksums, cell and boundary
metrics, invalid/inverted/zero-volume/nonfinite counts, quality summaries,
body-surface match status, readiness, reasons, and warnings.

Required action:

- Add a volume-mesh diagnostic model with explicit readiness reasons and
  warnings.
- Record deterministic mesher inputs and output artifact checksums.
- Include enough fixture data to test both positive and negative handoff
  behavior.
- If no actual volume-mesh artifact can be produced in this implementation,
  stop at schema and rejection plumbing and keep all packages below
  `cfd_ready`.

### F-004 - Manifest refs are not path-bound or hash-bound

Severity: high

Source lanes: traceability F3, ops stale/forged/outside-package finding.

Dispatch currently checks referenced artifacts by testing `(mesh_dir / ref)`.
It does not reject absolute refs or `../` refs as a class, and it does not
compare referenced diagnostic or artifact content to hashes stored in the
manifest. This is currently mitigated by blanket rejection of watertight
evidence, but it becomes load-bearing as soon as a positive accept path exists.

Required action:

- Add content hashes for every referenced diagnostic and handoff artifact.
- Reject missing, stale, swapped, absolute-path, parent-directory, and
  malformed references.
- Compare `body_ref`, `source_hull_hash`, generated-body diagnostic hash,
  profile, tolerance set, and volume-mesh artifact checksums at dispatch.
- Ensure accepted evidence hashes participate in deterministic job identity, or
  otherwise prevent stale job reuse when evidence changes.

### F-005 - Current tests prove blanket rejection, not RFC 0023 discrimination

Severity: medium

Source lanes: ops test finding, traceability residual-risk matrix, domain
fixture-boundary finding.

Existing tests cover rejection of hand-edited `cfd_ready`, forged quality
report content, synthetic closed-volume diagnostics, and generated closed-body
diagnostics used as `cfd_ready` evidence. They all pass because the current
watertight evidence path rejects everything. They do not yet prove the RFC
0023 distinction between accepted matching volume-mesh evidence and rejected
stale/cross-body/synthetic evidence.

Required action:

- Add positive and negative tests tied to the typed RFC 0023 evidence model.
- Keep existing open-surface and forged-readiness rejection tests.
- Add focused fixtures for missing volume mesh, stale hashes, cross-body,
  cross-hull, cross-profile, cross-tolerance, synthetic evidence, failed or
  inconclusive self-intersection, malformed diagnostics, and path escape refs.

### F-006 - CLI and JSON explanations are too coarse for handoff failures

Severity: medium

Source lanes: traceability F6, ops CLI finding.

`kayakgen mesh-package` currently prints only the manifest path and readiness
level. `kayakgen cfd prepare` prints broad exception text and raw/unvalidated
wording. RFC 0023 asks for CLI/JSON output that explains why a package is below
`cfd_ready` and names the rejected evidence class.

Required action:

- Print readiness reasons and evidence blocker classes for mesh package and
  dispatch failures.
- Surface distinct blocker classes such as missing volume mesh, stale checksum,
  profile mismatch, synthetic evidence, failed self-intersection, malformed
  diagnostic, and forbidden path ref.
- Keep all CFD result wording raw and unvalidated.

## Downgraded Or Folded Findings

- Traceability F8 is folded into F-001. Parsing and discarding evidence is the
  implementation detail of the unconditional rejection stub.
- Traceability F7 is an implementation note, not a standalone blocker. The
  body diagnostic profile `generated_hull_plus_deck_closed_body_v1` and the
  solver handoff profile `watertight_solid_resistance_v1` are distinct
  concepts; the implementation should encode their allowed mapping in
  constants/tests.
- Traceability F4 is accepted only as a guardrail after correction. Current
  watertight evidence gating fires from solver required readiness, solver
  required mesh profile, or manifest solver profile `requires_watertight`; it
  does not directly key off `manifest.readiness.level == "cfd_ready"`.

## Accepted Safe Implementation Slice

Implementers may:

- add optional RFC 0023 manifest traceability fields;
- add volume-mesh diagnostic models and fixture-backed artifact records;
- add a generated-body package-writer path that is separate from the current
  open-surface default path;
- derive `cfd_ready` only from in-memory or verified referenced evidence;
- consume explicit manifest fields instead of substring-discovered diagnostic
  refs for the accepted handoff path;
- add path-bound, checksum-bound dispatch validation;
- add structured evidence rejection reasons and CLI/JSON surfacing;
- add positive `cfd_ready` handoff only when a matching generated-body-derived
  volume-mesh artifact and diagnostic exist.

Implementers must keep:

- default open wetted-surface packages below `cfd_ready`;
- current watertight-profile packages without volume mesh below `cfd_ready`;
- synthetic closed-volume diagnostics permanently unable to satisfy generated
  kayak CFD handoff;
- raw/unvalidated CFD semantics on job, run, profile, and adapter records.

## Explicit Deferrals

- Production CFD solver selection or integration.
- Validated or calibrated CFD force claims.
- Boundary-layer or solver-specific quality thresholds beyond conservative
  profile gates and warnings.
- `cfd_ready` promotion from closed surfaces without volume-mesh evidence.
- `cfd_ready` promotion from explicit synthetic closed-volume fixtures.
- Replacing the open wetted-surface package profile.
- Surface-only watertight solver readiness profiles.
- Broader UI/web workflow changes beyond any small CLI/JSON explanation needed
  for RFC 0023 handoff failures.

Generated closed-body construction and self-intersection diagnostics are not
deferred as missing prerequisites in this worktree, but their outputs remain
prerequisites to be bound to the same `body_ref`, source hull hash, profile,
tolerance set, and volume-mesh evidence.

## Validation Expectations

Expected command after implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider \
  tests/test_mesh_package.py \
  tests/test_cfd_jobs.py \
  tests/test_closed_volume.py \
  tests/test_generated_closed_body.py \
  tests/test_cli.py
```

Required coverage:

- open-surface packages cannot promote to `cfd_ready`;
- generated closed body with passing self-intersection but no volume-mesh
  diagnostic remains below `cfd_ready`;
- successful generated-body plus volume-mesh handoff reaches `cfd_ready` only
  for matching body, hull hash, profile, tolerances, diagnostics, artifacts,
  and checksums;
- dispatch rejects missing, malformed, stale, cross-body, cross-hull,
  cross-profile, cross-tolerance, synthetic, failed-self-intersection,
  absolute-path, and parent-directory evidence;
- changing any referenced diagnostic or artifact hash prevents stale reuse;
- deterministic job identity or equivalent stale-run protection changes when
  accepted evidence hashes change;
- CLI/JSON names the blocker class for missing volume mesh, stale hash, profile
  mismatch, forged path, synthetic evidence, and self-intersection blocker;
- all CFD records and output wording remain raw and unvalidated.
