# Traceability review - 0015 mesh package and profile

author: operator [self-declared: operator-traceability-review]
run: run_4c00d3da5e7a4420ad44067406bdc27e
job: review_traceability
verdict_intent: accept_with_findings
date: 2026-05-13

## Findings

### T-001 - `mesh-package` acceptance is unimplemented

- Severity: high
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`,
  `kayakgen/cli/main.py`
- Statement: RFC 0010 acceptance requires `kayakgen mesh-package hull.json --out
  mesh-package/`, but the CLI currently has only `mesh-check`.
- Required action: Add a `mesh-package` command that writes a deterministic
  package directory with manifest, hull JSON, quality reports, and STL surfaces.

### T-002 - Mesh manifest model/writer is absent

- Severity: high
- File(s): future package/manifest code
- Statement: RFC 0010 names `MeshPackageManifest`, coordinate metadata,
  readiness, parts, and quality report paths, but current code has diagnostics
  only.
- Required action: Add a manifest model and writer with relative artifact paths,
  hull hash, units, stern-positive coordinates, waterline metadata, parts, and
  package warnings.

### T-003 - First solver profile is not exposed as a package contract

- Severity: high
- File(s): `kayakgen/eval/mesh_diagnostics.py`, future package code
- Statement: Human decisions selected an open wetted-surface resistance profile,
  but current diagnostics always return `solver_profile=None`.
- Required action: Add or expose a named open wetted-surface solver profile for
  packaging while keeping watertight solid readiness deferred.

### T-004 - RFC status should become a partial/package landing

- Severity: medium
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`, `docs/rfcs/README.md`
- Statement: RFC 0010 is `proposed`. If this workflow lands mesh package and
  profile work, status should clarify that solver dispatch and watertight solid
  readiness remain future work.
- Required action: Update RFC 0010 and the RFC index after implementation.

## Recommendation

Proceed. Existing `mesh-check` coverage is a useful base; the missing work is
manifest/package writing and honest profile metadata.
