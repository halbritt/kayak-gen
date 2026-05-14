# RFC 0037: Export Row Schema Consolidation

Status: proposed
Date: 2026-05-14
Context: successor to RFC 0035 and workflow 0047 final review FR2. RFC 0035
made `EXPORT_MENU_ROWS` the source for export-menu labels, availability,
disabled states, row classes, actions, and guidance copy. Workflow 0047 found
that the row schema still carries duplicate guidance fields.

## Problem

The export menu row schema currently has both `subtitle` and `description`.
`subtitle` is the compact visible copy rendered in the menu. `description` is a
longer read-model field. On most rows they say nearly the same thing, which
keeps the UI conservative but leaves a drift path in the exact area RFC 0035
tried to make single-source.

The failure mode is maintenance drift: visible guidance, tests, and read-model
copy can diverge even though they describe the same export row.

## Goals

- Collapse export-row guidance copy to one canonical field.
- Preserve currently shipped visible export subtitles byte-for-byte.
- Keep `EXPORT_MENU_ROWS` as the single source for row labels, availability,
  disabled state, row class, action key, and guidance copy.
- Update tests so drift between rendered menu rows and the row schema fails
  early.

## Non-Goals

- No runtime export behavior changes.
- No new enabled exports. Enabled browser rows remain Hull STL, Deck STL, and
  Hydro JSON.
- No change to Stability JSON or Mesh package availability.
- No `Mesh package...` label polish; that is RFC 0038 scope.
- No REST route shape changes, hosted storage, solver behavior, web-side
  mesh-package authoring, or watertight-readiness promotion.
- No user-visible copy changes unless a later implementation explicitly records
  them as UI cleanup.

## Proposal

Make `subtitle` the canonical export-row guidance field and remove
`description` from `EXPORT_MENU_ROWS`. Rendering and read-model tests should
consume the same `subtitle` value rather than maintaining a parallel
description sentence.

The visible subtitle strings should remain byte-identical to the shipped UI.
If an external or internal read model still needs a `description` property, that
property should be derived at the read-model boundary from the canonical row
field rather than stored as a second row-schema field.

## Acceptance Criteria

- `EXPORT_MENU_ROWS` has exactly one guidance-copy field for each row, named
  `subtitle`.
- No export row carries both `subtitle` and `description`.
- Rendered export-menu subtitles remain byte-identical to the current shipped
  visible UI.
- Read-model tests consume the same canonical subtitle field instead of a
  separate description field.
- Static tests fail if rendered labels, disabled states, row classes, action
  keys, availability, or guidance copy drift from `EXPORT_MENU_ROWS`.
- The existing rendered export-menu subtitle fixture is treated as the
  byte-identical reference for shipped visible subtitles before any later RFC
  0038 label polish is applied.
- Browser acceptance still observes the same honest enabled and unavailable
  rows.
- If any visible copy changes despite the preferred zero-copy-change path,
  docs or changelog record that as UI cleanup only.

## Open Questions

- Should any compatibility read model expose a derived `description` property
  for outside consumers, or can all current consumers use `subtitle` directly?
- Are there downstream tests or artifacts that depend on the longer description
  sentences and need an explicit migration note?

## Implementation Path

1. Audit current row consumers and identify whether any require a derived
   compatibility property.
2. Remove `description` from `EXPORT_MENU_ROWS` and route rendering/read-model
   assertions through `subtitle`.
3. Preserve current visible subtitle strings and enabled/unavailable row state.
4. Run focused export menu, browser, and forbidden-copy tests.
5. Land this consolidation before RFC 0038, or bundle both RFCs with separate
   acceptance gates so the RFC 0038 mesh-package label polish is intentional
   visible-copy cleanup rather than schema drift.

## Domain Modeling

Boundary clarification. Export rows are presentation read-model data, not hull
domain concepts. This RFC consolidates UI schema ownership without changing
artifact generation, solver readiness, or persistence.
