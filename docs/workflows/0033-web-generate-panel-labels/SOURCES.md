# Sources for workflow 0033 — web Generate-panel labels and tooltips

> Operator: this file is the per-run context manifest. Each job reads it
> as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## RFC in scope

- [`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`](../../rfcs/0060-web-generate-panel-form-labels-and-tooltips.md)
  is the spec. §1 defines the value object, §2 the 11-row registry, §3
  the helper API, §4 the form-wiring, §5 the regression test.

## Audit finding addressed

- `AUD-O-003` — "Web Generate-panel form labels are raw JSON parameter
  names." See
  [`docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md).

## Source files touched

| Surface | Paths |
|---|---|
| New module | `kayakgen/ui/parameter_metadata.py` |
| Wired form | `kayakgen/ui/web/generate_spec_form.py` |
| New test | `tests/test_hull_parameter_metadata.py` |
| Extended test | `tests/test_vocabulary_coverage.py` |
| Docs | `docs/USER_GUIDE.md` (Generate-panel section), `docs/UBIQUITOUS_LANGUAGE.md` (`HullParameterMetadata` row) |

## Files NOT touched by this workflow

The parent agent owns these surfaces:

- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/README.md`
- `docs/rfcs/0060-*.md`

## Byte-stability invariant

RFC 0060 acceptance criterion #2: the form's submitted JSON payload
must not change. The byte-stability gate is the existing
`tests/test_generate_spec_form.py` round-trip / snapshot suite. The
`implement` job runs this suite as part of its own verification before
publishing `PATCH_SUMMARY.md`.

## Where the artifacts land

`docs/audits/2026-05-22-code-doc-audit/follow-ups/0033/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
