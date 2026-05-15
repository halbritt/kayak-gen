# RFC 0038: Export Menu Disabled Copy Polish

Status: landed disabled-copy-polish
Date: 2026-05-14
Context: successor to RFC 0035 and workflow 0047 final review FR3. This RFC
addresses only the disabled Mesh package export-row label left as optional
copy polish by the RFC 0035 cleanup workflow.

## Problem

The web export menu still labels the disabled mesh package row
`Mesh package...`. A trailing ellipsis commonly implies that selecting the row
opens a dialog or follow-up flow. In the current web UI, the row is unavailable
and mesh-package authoring remains a CLI/local workflow.

The current behavior is honest because the row is disabled, but the label copy
is a weak signal for a permanently unavailable browser action.

## Goals

- Remove the misleading ellipsis from the disabled mesh-package row.
- Keep the row disabled and explicitly unavailable in the browser.
- Record the visible copy change in tests and user-facing docs/changelog if the
  implementation workflow changes shipped copy.
- Preserve all existing export behavior and no-claims boundaries.

## Non-Goals

- No browser-side mesh-package authoring.
- No new export route, artifact storage, hosted job, worker queue, or solver
  behavior.
- No new enabled export rows.
- No promotion to watertight-solid, `cfd_ready`, final prediction, or design
  fitness.
- No restructuring of the export-row schema beyond the label/copy polish needed
  here.

## Proposal

Normalize the disabled mesh-package label from `Mesh package...` to
`Mesh package (CLI only)`.

The row remains disabled/unavailable in the browser. Its subtitle or disabled
help may continue to point users to `kayakgen mesh-package`, but it must not
imply that the web UI can create mesh packages, hosted artifacts, or
watertight solver-ready packages.

If the implementation chooses the shorter label `Mesh package`, it must keep
the CLI-only limitation in adjacent visible guidance and update tests to pin
the accepted copy. The default proposal is the more explicit
`Mesh package (CLI only)`.

This RFC depends on RFC 0037's canonical export-row `subtitle` ownership.
Implementation must review the final mesh-package label and adjacent subtitle
together, avoid duplicating the same CLI-only guidance in both fields, and
record the exact accepted label/subtitle pair in the workflow patch summary.
RFC 0037 should land first, or both RFCs should land in one workflow with
separate schema-consolidation and visible-copy acceptance gates.

## Acceptance Criteria

- The export menu renders `Mesh package (CLI only)` instead of
  `Mesh package...`, unless implementation review records an explicit alternate
  accepted label.
- The mesh package export row remains disabled/unavailable in the browser.
- Static export-menu tests fail if the rendered label drifts from
  `EXPORT_MENU_ROWS`.
- Browser acceptance still observes the same enabled Hull STL, Deck STL, and
  Hydro JSON rows and the same unavailable Stability JSON and Mesh package
  rows.
- The final label/subtitle pair avoids repetitive CLI-only guidance while still
  making the browser row disabled, unavailable, and CLI/local-only.
- The implementation lands after RFC 0037 or in the same workflow with separate
  acceptance gates for schema consolidation and visible label polish.
- User guide and changelog updates describe visible label polish only.
- Existing forbidden-copy/no-claims tests continue to pass.

## Open Questions

- Is `Mesh package (CLI only)` preferable to `Mesh package` plus unchanged
  disabled-row guidance?
- Which exact subtitle should be pinned beside the accepted label after RFC
  0037 makes `subtitle` the canonical guidance field?

## Implementation Path

1. Choose the final disabled-row label during first-pass review.
2. Update only export-menu copy and focused tests for that label.
3. Update user-facing docs/changelog if visible copy changes.
4. Run focused export menu, browser, and forbidden-copy tests.

## Domain Modeling

Boundary clarification. This RFC changes only presentation copy for an
unavailable export row. It does not introduce a mesh-package authoring domain
operation or change readiness semantics.
