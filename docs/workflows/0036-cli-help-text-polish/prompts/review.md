# Review prompt — workflow 0036

You are reviewing the implementer's landing of two help-text polish
findings from the 2026-05-23 release_candidate audit:

- **AUD-O-011 (R5)** — `runs list --kind` enumeration symmetry with
  `runs jobs`.
- **AUD-O-012 (R3)** — `hull_from_gui_params` DeprecationWarning gets
  the on-disk RFC path.

Read in order:

1. `docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md`
   batches R3 / R5 and the `operator-adoption/FINDINGS.md` rows for
   AUD-O-011 / AUD-O-012 — the spec.
2. `docs/audits/2026-05-23-code-doc-audit/follow-ups/0036/PATCH_SUMMARY.md`
   — the implementer's report.
3. The actual touched files (`kayakgen/cli/runs_cli.py`,
   `kayakgen/ui/gui_params.py`, `tests/test_gui_params.py`).

## Acceptance criteria (verify each)

1. **AUD-O-011 (R5) — `runs list --kind` enumeration symmetry.**
   - `kayakgen/cli/runs_cli.py` `runs_list_command` `--kind` Typer
     option `help=...` string enumerates the valid kinds
     (`sweep | search | cfd | comparison` is the established set; the
     implementer should have confirmed against source).
   - The enumeration style matches `runs_jobs_command`'s `--state` and
     `--kind` help (parenthesized list, optional note naming the
     SQLite column the filter is matched against).
   - No behavioral change to the command — `help=` edit only.

2. **AUD-O-012 (R3) — DeprecationWarning has on-disk RFC path.**
   - `kayakgen/ui/gui_params.py` `hull_from_gui_params`
     `DeprecationWarning` text mentions both `RFC 0061` and the
     on-disk path `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`.
   - The rest of the warning text is intact (mentions the canonical
     Hull field name migration and the `Hull(**params)` filter
     guidance).

3. **`tests/test_gui_params.py` retargeted.**
   - `test_hull_from_gui_params_emits_rfc_0061_deprecation_warning`
     asserts both the `RFC 0061` substring and the on-disk path
     substring `0061-desktop-sliders-on-hull-parameter-metadata.md`.
   - The existing
     `test_gui_params_preserve_new_hull_fields` continues to pass
     (no change required; the test catches and ignores the warning).

## Tests to confirm

```bash
.venv/bin/pytest \
  tests/test_gui_params.py \
  tests/test_desktop_sliders_use_registry.py \
  tests/test_cfd_jobs.py \
  tests/test_cfd_jobs_openfoam.py \
  -q
```

All must pass. If `tests/test_runs_cli.py` was created during the run,
confirm it passes too.

## Scope check

The implementer MUST NOT have touched `CHANGELOG.md`,
`docs/audits/2026-05-23-code-doc-audit/*/FINDINGS.md`,
`docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md`,
`docs/rfcs/`, `docs/DECISION_LOG.md`, `kayakgen/ui/web/`, or
`kayakgen/ui/desktop.py`. Flag any drift.

## Artifact

Write
`docs/audits/2026-05-23-code-doc-audit/follow-ups/0036/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check results
(pass / fail with file:line evidence), and any deferrals.
