author: implementer-codex-gpt-5.5-003

# RFC 0058 Stage 1 Docs Sync Patch Summary

Updated the documentation surfaces for the schema-only RFC 0058 stage 1
landing:

- `CHANGELOG.md`: added an Unreleased entry for the accepted stability-fit
  schemas and explicitly retained the deferred claim/CLI/CFD work.
- `docs/DECISION_LOG.md`: added D038 for the stage 1 schema landing.
- `docs/ROADMAP.md`: added a "Stability calibration acceptance" dependency
  track between calibration-campaign tooling and the existing following rows.
- `docs/rfcs/0058-stability-calibration-acceptance.md`: changed status to
  `landed (schemas only)` and added a Stage 1 implementation note.
- `docs/rfcs/README.md`: updated RFC 0058 status and narrowed the shipped
  description to schemas only.
- `docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/OPERATOR_REPORT.md`:
  recorded the docs synchronization.

No runtime behavior changed. No fixture or fit was promoted. RFC 0043 high-angle
GZ remains `unvalidated_hydrostatic_comparison`; the analytical claim resolver,
CFD-in-loop graduation helper, and `kayakgen stability` CLI are still deferred.
