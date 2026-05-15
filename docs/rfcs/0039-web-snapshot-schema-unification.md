# RFC 0039: Web Snapshot Schema Unification

Status: landed shared-schema-unification
Date: 2026-05-14
Context: successor to RFC 0035 and workflow 0047 final review FR4. RFC 0035
introduced declared `STATE_SNAPSHOT_KEYS`; workflow 0047 found that the same
state/alias knowledge still overlaps with controller-side CFD status scanning.

## Problem

The web app now declares a snapshot key tuple, and tests cover optional,
missing, and populated values. The controller layer still owns a parallel alias
scan for CFD status, payload, status lines, and mesh package references. The
duplication is tested and acceptable for the RFC 0035 cleanup slice, but it
leaves two places that must remember the same compatibility aliases.

The failure mode is schema drift: app snapshot keys and controller alias
handling can diverge while public route payloads and read models still expect
legacy compatibility.

## Goals

- Move web snapshot and CFD alias ownership into one declared schema or alias
  source.
- Preserve current public REST route payload shapes and controller/read-model
  behavior.
- Preserve optional and legacy aliases unless focused tests prove a specific
  alias is unused and removable.
- Add focused tests that fail if app snapshot keys and controller alias handling
  drift.

## Non-Goals

- No REST route shape changes.
- No new route fields or payload meanings.
- No hosted CFD, worker queue, cloud storage, auth, cancellation, or solver
  behavior.
- No web-side mesh-package authoring.
- No hull geometry, class envelope, export-menu, UI copy, calibration,
  stability, or readiness changes.

## Proposal

Create one small web-state schema source, preferably in `kayakgen/ui/web/state.py`,
that owns:

- the keys copied by `_state_snapshot`;
- CFD status aliases such as `cfd_status` and `status`;
- CFD payload aliases such as `cfd_payload`, `cfd_job_payload`, and
  `cfd_last_payload`;
- CFD status-line aliases such as `cfd_status_lines`;
- mesh package references such as `mesh_package_ref` and
  `cfd_mesh_package_ref`.

The schema may be a plain tuple plus grouped alias metadata, a small typed
value object, or another equally narrow structure. The key requirement is that
the app snapshot helper and controller alias readers consume the same declared
source.

Compatibility is the default. Existing aliases should remain unless a focused
implementation review proves an alias is unreachable and updates tests and docs
accordingly. This RFC does not authorize route payload redesign.

## Acceptance Criteria

- One declared schema or alias source owns web snapshot keys and CFD
  status/payload/status-line aliases.
- `_state_snapshot` remains compatible for missing, `None`, and populated
  optional keys.
- `_cfd_status_from_state` remains compatible for status, payload, and
  status-line aliases.
- Mesh package references still feed existing read models without route payload
  changes.
- Focused tests fail if app snapshot keys and controller alias handling drift.
- Existing `/api/evaluate`, `/api/stl`, `/api/cfd/*`, and `/api/hulls/*` JSON
  shapes remain unchanged.
- Existing CFD review-tab browser acceptance continues to cover status chips,
  status lines, and artifact-panel behavior without visible behavior changes.
- Docs describe the change as maintenance/schema consolidation only, not new
  backend capability.

## Open Questions

- Should the shared source be a plain constant/tuple with alias groups, or a
  typed dataclass/value object?
- Should aliases be grouped by consumer intent: snapshot keys, CFD status,
  payload, status lines, and mesh package references?
- Are any legacy aliases ready for removal, or should compatibility remain
  unconditional until a later deprecation RFC?

## Implementation Path

1. Inventory current snapshot keys and controller aliases from the RFC 0035
   implementation.
2. Add the shared schema source and update the app snapshot helper and
   controller alias readers to consume it.
3. Preserve public route payload shapes and read-model outputs.
4. Add drift tests for missing, `None`, populated, legacy alias, and mesh
   package reference cases.
5. Run focused web layout/read-model/browser tests and forbidden-copy checks.
6. Run the existing CFD review-tab browser acceptance unchanged and record that
   status chips, status lines, artifact panels, and route payload shapes remain
   unchanged.

## Domain Modeling

Boundary clarification. The shared snapshot schema is a presentation boundary
contract for web state compatibility. It is not a new hull, CFD, mesh, or
solver domain concept.
