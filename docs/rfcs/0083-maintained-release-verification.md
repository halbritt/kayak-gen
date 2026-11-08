# RFC 0083 — Maintain source-bound installed release verification

Status: landed maintained installed release verification.
Date: 2026-11-08.

## Context and problem

The exercised deployment scripts proved a particular release, but their fixed
resource list, private owner path and script copies are unsuitable as a reusable
release contract. Checkout tests alone cannot establish installed package identity
or execute the installed resource and report paths.

## Goals

One command binds immutable Git source, wheel bytes, a new noneditable environment
and actual installed workflows. Expected Python modules and declared setuptools
package data come from that source tree. Every resolved runtime dependency must
match an explicit supplied version pin and installs from a hash-locked requirement.

## Non-goals

Live service deployment and current-link changes, PDF installation, owner-hull CFD,
physical validation, remote workers and universal descendant cleanup guarantees
are outside this release acceptance command.

## Proposal

D069 promotes the prior `stage_release.py` and `verify_installed_release.py` recipes
into `kayakgen.operations.release*`. `python -m kayakgen.operations.release` accepts
`--repo`, `--source`, `--constraints`, and a new external `--out`. Optional `--hull`
and `--context` must be paired. Supplied inputs are copied and both original and
snapshot bytes checked; their exact physical and numerical settings are evaluated.
Without them, an explicitly labelled generated analytical smoke control is used.

The source reference resolves once to a Git tree. Export excludes historical
`build/` and egg-info outputs. Wheel RECORD and all package bytes must match the
source-derived manifest. A fresh environment installs desktop/web/builder extras
and pinned Jinja2; HTML rendering does not require WeasyPrint. The isolated worker
runs installed modules with `-I -B`, with no checkout import overrides. Namespace
file membership, content, resource API bytes, wheel metadata, direct wheel hash,
exact dependency set and loaded module origins are checked before and after work.

The actual interFoam help wrapper captures and shifts its bashrc argument before
sourcing. Its real version banner and the typed provenance probe must pass before
the longer workflows. Both case resource stages render, the selected evaluation
is persisted/reloaded, and HTML rendering runs under evaluator-call guards. Actual
CLI STL and builder exports are read back for identity, geometry, units and frames.
A prepared immutable profile executes real bounded meshing and interFoam on the
separate legacy fixture. It retains `raw_unvalidated`, empty accepted uses and
terminal replay invariance. Failed attempts remain in their new output directory.

`release_audit.audit_installed(manifest, wheel, dependencies)` and
`module_audit(manifest)` are the small read-only seam for separate runtime lifecycle
probes. They require the target isolated interpreter and perform no service action.

## Acceptance criteria

Behavioral refusal tests cover omitted/altered resources, unexpected installed and
wheel files, checkout imports, missing dependency pins, owner input pairing,
retained failed commands and corrected shell argument handling. The maintained
entry point must also complete a real installed HTML/export/CFD workflow outside
the checkout. Full pytest with four default skips precedes Ruff; opt-in real
toolchain checks run separately. Counts are evidence, never fixed acceptance totals.

## Open questions and limits

Dependency pins are supplied by the operator; this command verifies the selected
set rather than choosing an update policy. A tree hash may identify a staged
candidate before its final commit exists. Receipt integrity is local and
unauthenticated. The external toolchain and build backend are prerequisites;
successful execution makes no claim about analytical physical accuracy or CFD
convergence beyond this bounded smoke.

## Implementation path

Land manifest/build/stage/audit/workflow modules and the public module entry point
together with tests and documentation. Deployment remains a separate authorized
operation consuming the retained release and verification receipts.

## Domain modeling

The source manifest is an immutable value describing release identity. Runtime
and CFD records retain existing domain ownership and claim ceilings; the release
receipt is operational evidence, not a new scientific result or readiness state.
