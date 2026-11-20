# Contributing to kayakgen

Start with the [user guide](docs/USER_GUIDE.md) to run the CLI, desktop GUI
or web workspace. For changes to hull geometry, read the
[hull design constraints](docs/design/kayak_hull_design_constraints.md)
and the implementation in `kayakgen/model/hull.py` and
`kayakgen/model/geometry.py`. The root Python modules support legacy imports.

The [product requirements](docs/PRD.md) define project scope. The
[architecture map](docs/ARCHITECTURE_MAP.md) lists package boundaries, CLI
commands and durable artifacts. Check the [RFC index](docs/rfcs/README.md)
and [decision log](docs/DECISION_LOG.md) for the design behind a feature.
The [glossary](docs/UBIQUITOUS_LANGUAGE.md) defines the claim and readiness
labels shared by the UI, evaluators and saved results.

## Verification

Follow the [release discipline](docs/RELEASE_DISCIPLINE.md) before landing a
change. Run focused tests during development and the full gate before merging.

```sh
.venv/bin/python -m pytest -q tests/test_form_metrics.py
scripts/full-gate.sh
```

Where the shared host tasks are installed, `mise run test -- <paths>`,
`mise run lint`, `mise run test:fast` and `mise run test:full` provide the
same project checks. Browser setup is in [web verification](docs/WEB_VERIFICATION.md).

## Landing changes

Use separate worktrees for concurrent edits. Land verified changes on
`main` and remove the merged branch and worktree. Update the changelog for
user-facing changes and the RFC index when a design's status changes.
Use the project's Plane tracker (KAYGEN) for maintainer work items.
