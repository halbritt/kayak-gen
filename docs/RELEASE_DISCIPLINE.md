# Release Discipline

Date: 2026-05-16. Lives at the same level as `docs/PRD.md` /
`docs/ROADMAP.md` / `docs/SPEC.md`; cited from `AGENTS.md` as a
load-bearing process doc. Phase 9 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`.

This file consolidates the lightweight release-engineering practices
the project already follows. It exists so a new contributor (human or
agent) sees the rules in one place rather than discovering them via
CI failures.

## One phase / one RFC per landing

Land architectural changes in single coherent units. A phase or step
from a roadmap document becomes one RFC (or a small set of focused
RFCs if the phase has independent sub-scopes — e.g. Phase 3 split
into A/B/C/D). Each RFC follows the
`docs/rfcs/0001-template.md` template:

- Status, Date, Context up top.
- Problem → Goals → Non-Goals → Proposal → Acceptance Criteria →
  Open Questions → Implementation Path → Domain Modeling.
- Status header literally matches the entry in
  `docs/rfcs/README.md`.

A landed RFC's status reads `landed <short qualifier>` (e.g.
`landed v1 NSGA-II + kayakgen search CLI`). Partial landings use
`partial landed <slice description>`. Proposed RFCs use `proposed`.

## Public-behavior-change checklist

When a commit changes any of:

- a CLI command surface,
- a public JSON schema (`schema_version`, field name/type/default),
- a durable artifact name or location,
- a claim state, accepted-use, or readiness literal,
- a `docs/PRD.md` scope/status assertion,
- a `docs/SPEC.md` invariant,

then the same commit (or the next commit in a tight sequence)
updates **every** affected file in this list:

1. `docs/USER_GUIDE.md` — surface description.
2. `docs/PRD.md` — if scope or status changes.
3. `docs/ROADMAP.md` — track row and Future-Striatum-Batches
   disposition.
4. `docs/rfcs/README.md` — RFC status header.
5. `docs/DECISION_LOG.md` — new row when a decision changes; cite
   the RFC.
6. `CHANGELOG.md` — `### Added` / `### Changed` / `### Fixed` entry.
7. `docs/ARCHITECTURE_MAP.md` — when the package layout, CLI list,
   or durable-artifact table changes.
8. `docs/UBIQUITOUS_LANGUAGE.md` — when a new term is introduced;
   the `tests/test_vocabulary_coverage.py` regression catches drift.
9. `OPERATOR_REPORT.md` — checkpoint when an operator session lands
   an externally-relevant change (network access, real-solver run,
   external acquisition).

The checklist exists because the cowboy 2026-05-15/16 sessions
repeatedly discovered the same drift: code lands, the user guide
forgets it; a decision lands, the changelog forgets it. The
forbidden-copy regressions and the vocabulary-coverage test catch
the most damaging drifts, but they do not catch every wording
change.

## Pre-merge requirements

Every commit must pass, in this order:

1. **`.venv/bin/python -m pytest -q`** — the full test suite must
   stay green or skipped. The env-gated OpenFOAM smoke
   (`tests/test_openfoam_v2512_smoke.py`) is permitted to skip
   unless `KAYAKGEN_OPENFOAM_SMOKE=1` and
   `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` are set, in which case it must
   pass.
2. **`.venv/bin/python -m ruff check kayakgen tests`** — ruff must
   pass. Phase 0 of the architecture plan installed ruff to
   `[dev]`; new code must clear it.
3. **No `git push --force`** to `main`. Force-push is only
   permitted on operator-owned feature branches, never on `main`
   even via `--force-with-lease`.
4. **Co-author attribution** on any commit an agent participated
   in: `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`.

The opt-in OpenFOAM smoke is the recommended pre-push gate when a
change touches CFD, the OpenFOAM adapter, the case templates, or the
provenance probe. Run it locally with:

```bash
KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 \
  .venv/bin/python -m pytest tests/test_openfoam_v2512_smoke.py -q
```

## No-claim invariants (load-bearing)

The following claim boundaries MUST stay closed until their named
evidence gates pass. Every regression test in the project that
checks forbidden copy enforces a subset of these; the list below is
the canonical statement.

- **Calibrated prediction** — refused for resistance output until
  RFC 0042 promotes an in-envelope kayak/surfski measured source AND
  RFC 0054 records an `AcceptedFitRecord` per D006.
- **Final design fitness** — refused everywhere; no accepted
  evaluator exists.
- **Seaworthiness / safety / capsize-range** — refused everywhere;
  no measured comparator exists.
- **Validated CFD** — refused everywhere; `raw_unvalidated` is the
  ceiling under D012 / D022 / D027.
- **Production CFD hosted-worker** — refused; D023 defers public
  hosted demo indefinitely.
- **High-angle GZ as Pareto/search objective** — refused via
  `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`.
- **`raw_unvalidated` / `uncalibrated_comparative` as default
  search/Pareto objective** — refused via
  `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY` unless
  `objectives_explicit_exploratory: true`.

Any commit that proposes to widen one of the above must:

1. Cite the new RFC + DECISION_LOG row that justifies the widening.
2. Update the `tests/test_desktop_layout.py::test_desktop_status_
   segments_carry_*` and the `tests/test_web_read_models.py::
   test_web_high_angle_section_forbidden_claim_copy_absent`
   forbidden-copy regressions to reflect the new admitted wording.
3. Update `docs/SPEC.md` invariants list and `docs/PRD.md` "Roadmap
   And Deferrals" / "What is *not* on this list" sections.
4. Update `docs/ARCHITECTURE_MAP.md` claim-state vocabulary table.

## What this file does NOT prescribe

- Branch naming (the project uses `striatum/<slug>` and
  `claude/<slug>` and `feature/<slug>` historically; no rule).
- Merge strategy (`main` accepts fast-forwards and merge commits;
  no rebasing rule).
- Issue tracking (no issue tracker in this repo today).
- PR review process (single-operator project; no PR template).

These items become load-bearing only if the project grows beyond
one operator + agents.
