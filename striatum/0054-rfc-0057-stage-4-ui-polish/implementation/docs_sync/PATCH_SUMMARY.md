author: implementer-codex-gpt-5.5-002

# Patch Summary

## Scope

Synchronized documentation for RFC 0057 stage 4 without changing runtime
behavior or implementation files.

## Updated

- `docs/USER_GUIDE.md`: added `kayakgen runs jobs` usage and the default
  generative-job storage root / env override.
- `docs/ROADMAP.md`: refreshed the roadmap update date.
- `docs/rfcs/0057-generative-search-jobs-and-web-workspace.md`: marked the RFC
  landed, aligned route names to `/api/generative-jobs/*`, recorded the
  subprocess-by-default serve posture, and added the stage-4 implementation
  note.
- `docs/workflows/0054-rfc-0057-stage-4-ui-polish/OPERATOR_REPORT.md`: added
  the docs-sync receipt.
- `CHANGELOG.md`: added a docs-sync changed entry.

## Notes

`docs/DECISION_LOG.md` already contained D037 with the 12 stage-4 decisions,
and `docs/rfcs/README.md` already listed RFC 0057 as landed with the stage-4
surface. Those files were verified but did not require additional edits in this
pass.
