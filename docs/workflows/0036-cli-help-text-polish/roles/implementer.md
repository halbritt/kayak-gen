# Role: implementer

You land two help-text polish items from the 2026-05-23
release_candidate audit in a single change set:

- **AUD-O-011 (R5).** Update `kayakgen/cli/runs_cli.py`
  `runs_list_command`'s `--kind` Typer option `help=` string to
  enumerate the valid kinds (`sweep | search | cfd | comparison`) in
  the same style that `runs_jobs_command` enumerates `--state` and
  `--kind`. Behavior unchanged; help string only.

- **AUD-O-012 (R3).** Append the on-disk RFC path
  `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md` to
  the `hull_from_gui_params` `DeprecationWarning` in
  `kayakgen/ui/gui_params.py`. The phrase `RFC 0061` stays in the
  warning text so the existing test's `pytest.warns(match="RFC 0061")`
  continues to match.

- Update the `tests/test_gui_params.py` `pytest.warns(...)` match
  assertion to also assert the on-disk path substring.

You do not touch `CHANGELOG.md`, audit `FINDINGS.md` files, the
remediation plan, RFC source, `docs/rfcs/README.md`,
`docs/DECISION_LOG.md`, `kayakgen/ui/web/`, or `kayakgen/ui/desktop.py`
— those are the parent agent's job or owned by sibling workflows
(workflow 0035 owns the web and desktop slider test surfaces).

The work is tiny (one Typer help string + one warning string + one
test match string + a PATCH_SUMMARY.md artifact). No sub-agents
needed; do it in-process.
