# Sources for workflow 0010

This workflow revisits every non-template RFC currently listed in
`docs/rfcs/README.md`. As of 2026-05-12, the latest project RFC is
RFC 0008, so the review scope is RFCs 0002 through 0008.

## Required RFC sources

- `docs/rfcs/0002-gui-usability.md`
- `docs/rfcs/0003-layout-and-station-view.md`
- `docs/rfcs/0004-plumb-bow.md`
- `docs/rfcs/0005-cfd-resistance.md`
- `docs/rfcs/0006-design-constraints.md`
- `docs/rfcs/0007-architectural-revisit.md`
- `docs/rfcs/0008-web-frontend.md`

`docs/rfcs/0001-template.md` is the template and is out of scope except
when checking whether new RFCs followed the template. `docs/rfcs/0002-0003-audit.md`
is supporting evidence for the early GUI/layout work and should be read when
reviewing RFCs 0002 and 0003.

## Implementation surface

Reviewers should inspect the current repo rather than trusting prior
workflow artifacts. The important authored surface is:

- Compatibility shims: `generator.py`, `gui.py`, `pyvista_view.py`.
- Package code: `kayakgen/model/`, `kayakgen/eval/`, `kayakgen/io/`,
  `kayakgen/ui/`, `kayakgen/cli/`.
- Frontends: `kayakgen/ui/desktop.py`, `kayakgen/ui/pv_window.py`,
  `kayakgen/ui/web/`, `Dockerfile`.
- Tests and fixtures: `tests/`, `tests/golden/`, `requirements-dev.txt`,
  `pyproject.toml`.
- Project guidance: `AGENTS.md`, `docs/PRD.md`,
  `docs/design/kayak_hull_design_constraints.md`, `docs/CONTEXT_HYGIENE.md`.

Generated STL files at the repo root are build artifacts. Do not treat them
as authored evidence unless a finding is specifically about checked-in
generated output.

## Review posture

The job is not to prove the previous work was good. The job is to find the
gap between the RFC commitments and the current repo, then leave Codex with a
small, actionable remediation set.
