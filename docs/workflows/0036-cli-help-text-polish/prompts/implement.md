# Implement prompt — workflow 0036

You are landing two low-severity help-text polish findings from the
2026-05-23 release_candidate audit:

- **AUD-O-011 (R5)** — `runs list --kind` help-text symmetry with
  `runs jobs`.
- **AUD-O-012 (R3)** — `hull_from_gui_params` deprecation warning
  should include the on-disk RFC path.

Read `SOURCES.md` for the per-run context manifest and the audit
remediation plan batches R3 / R5 for the rationale. Mirror the shape
of workflow 0034.

## Deliverables

1. **`kayakgen/cli/runs_cli.py`** — AUD-O-011 (R5):
   - Locate the `runs_list_command` Typer definition. Its `--kind`
     option help currently reads: `"Filter by run kind: sweep | search
     | cfd | comparison."` — confirm the valid set from source (the
     `SqliteIndex.list_runs(kind=...)` signature / call site).
   - Update the `--kind` Typer option `help=...` string to enumerate
     the valid kinds in the same style that `runs_jobs_command`
     enumerates its `--state` and `--kind` options. Match the
     formatting (the existing `runs_jobs_command` wraps the
     enumeration prose in a parenthesized list and notes which
     SQLite column the filter is matched against — apply the same
     convention to `runs_list_command --kind`).
   - Do not change the underlying command behavior — this is a
     help-string edit only.

2. **`kayakgen/ui/gui_params.py`** — AUD-O-012 (R3):
   - In `hull_from_gui_params`, append the on-disk RFC path to the
     existing `DeprecationWarning` text. New text reads (roughly):
     `"kayakgen.ui.gui_params.hull_from_gui_params is deprecated by
     RFC 0061; the desktop GUI now uses canonical Hull field names
     directly. Pass `params` straight to `Hull(**params)` after
     filtering view-only keys. See
     `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`."`
   - Keep the rest of the warning text intact. The `RFC 0061`
     substring must remain so the existing test's
     `pytest.warns(match="RFC 0061")` continues to match.

3. **`tests/test_gui_params.py`** —
   - Update
     `test_hull_from_gui_params_emits_rfc_0061_deprecation_warning`
     so its `pytest.warns(...)` `match=` argument also asserts the
     on-disk path is mentioned (substring assertion on
     `"0061-desktop-sliders-on-hull-parameter-metadata.md"` is
     sufficient). Keep the existing `"RFC 0061"` substring assertion
     as a separate `pytest.warns` block or fold both into a single
     regex with both substrings.

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_gui_params.py \
  tests/test_desktop_sliders_use_registry.py \
  tests/test_cfd_jobs.py \
  tests/test_cfd_jobs_openfoam.py \
  -q
```

All must pass. If `tests/test_runs_cli.py` exists at the time of the
run, run it too.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/audits/2026-05-23-code-doc-audit/*/FINDINGS.md`
- `docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md`
- `docs/rfcs/`
- `docs/DECISION_LOG.md`
- `kayakgen/ui/web/` (workflow 0035 owns the web side)
- `kayakgen/ui/desktop.py` (workflow 0035 owns the desktop slider test
  surface)

Those are the parent agent's job or owned by sibling workflows. The
workflow's `forbidden_paths` encodes this contract; do not work around
it.

## Artifact

Write
`docs/audits/2026-05-23-code-doc-audit/follow-ups/0036/PATCH_SUMMARY.md`
with: files changed, test counts per affected file, the exact new
`runs list --kind` Typer help string, the exact new DeprecationWarning
text, and confirmation that the `pytest.warns(match=...)` update covers
both the `RFC 0061` substring and the on-disk path substring.
