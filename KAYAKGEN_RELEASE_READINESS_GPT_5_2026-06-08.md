# Kayakgen Release Readiness - GPT-5 - 2026-06-08

## 0. Readiness Basis

Target repository: `/home/halbritt/git/kayak-gen`.
Release intent: not explicitly supplied; assumed current `HEAD` as a local-first
application / checkpoint candidate, with PyPI-style package metadata as a
secondary release vector.
Candidate: `8e0ddf780944bcf5906b567a9ca4fe4e6e2dfb6c` on `main`, matching
`origin/main` / `origin/HEAD`.
Dirty state before report write: clean (`## main...origin/main`).

Previous boundary: no tags were present (`git tag --sort=-creatordate` returned
no output), no prior changelog release heading was found, and `pyproject.toml`
still carries the initial `0.1.0` package version. Boundary therefore used the
prompt fallback rung 5: `HEAD~50..HEAD`, from `aaa64edb5758` (exclusive) to
the candidate, because the last 30 days contain 393 commits and the 50-commit
range is smaller.

Release model: `local-first-application` with a documented release gate and
install-from-repo workflow; secondary `distributed-package` evidence exists via
`pyproject.toml`, but no package artifact, registry publish process, tag, or
release archive was inspected.

Files read included `AGENTS.md`, `docs/PRD.md`,
`docs/design/kayak_hull_design_constraints.md`, `docs/rfcs/README.md`,
`kayakgen/model/geometry.py`, `kayakgen/model/hull.py`,
`docs/CONTEXT_HYGIENE.md`, `pyproject.toml`, `README.md`, `CHANGELOG.md`,
`docs/RELEASE_DISCIPLINE.md`, `docs/USER_GUIDE.md`, `Dockerfile`,
`scripts/full-gate.sh`, `scripts/fast-gate.sh`, current touched CFD/web files,
and recent operator reports / workflow summaries.

Commands run were read-only: `git status`, `git rev-parse`, `git tag`,
`git log`, `git diff --stat`, `git show`, `git ls-files`, `find`, `rg`,
`sed`, and `nl`. Not run because not authorized by the prompt defaults:
`scripts/full-gate.sh`, `.venv/bin/python -m pytest -q`,
`.venv/bin/python -m ruff check kayakgen tests`, OpenFOAM smoke tests,
package builds, Docker builds, publishing, tagging, and deployment.

Inherited artifacts: workflow 0067 draft records
`KAYAKGEN_PY=/home/halbritt/git/kayak-gen/.venv/bin/python scripts/full-gate.sh`
with `1359 passed, 4 skipped` and `[full-gate] OK`, but that evidence is not
SHA-matching for current `HEAD`; the current commit modifies CFD claim wording,
web presentation copy, one test, and docs after that gate. Workflow 0066
summary records an earlier full gate (`1348 passed, 4 skipped`) and ruff clean,
also stale for the candidate.

## 1. Verdict

Verdict: `READY_WITH_CONDITIONS`.
Confidence: medium.
Finding counts: 0 blockers, 4 conditions, 2 residual risks.

The candidate is not immediately shippable as a release artifact because the
project-defined release gate has not been run or inherited for exact SHA
`8e0ddf7`, and the repository has no release tag / released changelog heading
for the package version. I found no open-form blocker in the inspected release
paths: the worktree was clean before this report, the recent high-risk changes
are represented in `CHANGELOG.md`, release discipline defines a mechanical gate,
and the latest OpenFOAM wording preserves `raw_unvalidated` claim boundaries.
The remaining work is closed-form and mechanically checkable.

## 2. Release Story

`pyproject.toml` declares package name `kayakgen`, version `0.1.0`, Python
`>=3.11`, setuptools build backend, optional extras for desktop, web, browser,
builder, calibration, report, and dev, and a `kayakgen` console script. The
README points users to `docs/USER_GUIDE.md`; the user guide documents editable
install from this repo and optional extras.

The changelog is still headed `## Unreleased`. Current entries cover the
2026-06-08 docs-drift remediation, workflow 0067 gate hardening, workflow 0066
artifact-read fixes, and the June 6 test-protection series. This matches the
recent commit story, but it is not yet a release note for `0.1.0` or a tagged
public release.

No Git tags exist. The repo therefore has a usable local checkpoint story, but
not a complete public package/tag release story.

## 3. Change Inventory Since Boundary

The fallback range contains 50 commits, all dated 2026-06-06 through
2026-06-08. Risk-prioritized themes:

- Gate hardening: `scripts/full-gate.sh`, `scripts/fast-gate.sh`, and
  `tests/conftest.py` now enforce the OpenFOAM skip-count pin. Release
  discipline names `scripts/full-gate.sh` as the mechanical release gate.
- Durable artifact integrity: `kayakgen/services/artifact_store.py`,
  `kayakgen/io/json.py`, and `kayakgen/cli/runs_cli.py` add atomic writes,
  verified reads, corruption refusal/repair behavior, and index/schema
  hardening.
- Public CLI / claim behavior: `kayakgen/search/compare.py` and CLI tests pin
  claim-inadmissible objective refusal and explicit exploratory opt-in.
- Durable schemas: `StabilityFitRecord.kind`, `SqliteIndex` `PRAGMA
  user_version`, and artifact refs are touched in the range.
- Current HEAD: `kayakgen/eval/cfd/adapters/openfoam_v2512.py`,
  `kayakgen/eval/cfd/profiles.py`, `kayakgen/ui/web/presentation.py`,
  `tests/test_web_inline_help.py`, and current-state docs. The OpenFOAM
  changes are wording/claim-state corrections: `CfdOpenFoamRawResult` remains
  `raw_unvalidated`, the skeleton README says real succeeded records require
  explicit opt-in, and profile limitations say ordinary generated packages
  still need matching volume-mesh evidence.

## 4. Gates And Verification

Project-defined gate: `docs/RELEASE_DISCIPLINE.md` requires, in order,
`.venv/bin/python -m pytest -q` with exactly the documented OpenFOAM opt-in
skips, then `.venv/bin/python -m ruff check kayakgen tests`. The mechanical
form is `scripts/full-gate.sh`.

Gate status:

- `scripts/full-gate.sh`: not run - not authorized. Required before shipping
  this SHA. Static inspection confirms it runs ruff, then full pytest, exports
  `KAYAKGEN_ENFORCE_SKIP_PIN=1`, derives expected skips from OpenFOAM env
  knobs, and fails if the summary skip count differs.
- Workflow 0067 full gate: inherited but stale. It reports `1359 passed,
  4 skipped` for the workflow draft, not for `8e0ddf7`.
- Focused and ruff evidence in workflow 0067: inherited but stale.
- OpenFOAM smoke: not run - not authorized. Release discipline recommends it
  when touching CFD/OpenFOAM paths; current HEAD touches OpenFOAM adapter and
  profile wording.
- CI: not run - unavailable. No `.github` workflow directory was present.
- Package / Docker build: not run - not authorized.

## 5. Packaging Or Deployment Readiness

Package metadata is present and coherent for an editable/local Python package:
`pyproject.toml` names `kayakgen`, version `0.1.0`, setuptools backend, runtime
dependencies, optional extras, and the console script. `docs/USER_GUIDE.md`
documents source checkout installation and quick-start CLI commands.

No `dist/` artifact, wheel, sdist, checksum manifest, PyPI publishing config,
or release archive was present or built. `Dockerfile` exists for the Trame web
surface, but no image build or runtime smoke was authorized. Git tracks only
golden STL fixtures under `tests/golden/`; no release-path generated artifacts
or root STL outputs are tracked.

## 6. Upgrade, Migration, And Rollback

The recent range touches rebuildable local state (`SqliteIndex`) and durable
artifact formats. `CHANGELOG.md` records the SQLite read-model versioning as
rebuild-not-migrate and the artifact-store behavior as verified/atomic. No
application database migrations, live services, cloud resources, or deployment
state were found.

Rollback for local-first use is Git-based: return to the prior commit or the
previous known-good gate artifact. Because there are no tags or release
artifacts, rollback is not yet an operator-friendly public release path.

## 7. Blockers And Conditions

`CONDITION 1 - Run the release gate for exact candidate SHA.`
Evidence: `docs/RELEASE_DISCIPLINE.md` requires the full suite and ruff;
`scripts/full-gate.sh` is the mechanical form. Scenario: shipping without a
SHA-matching gate would rely on stale workflow 0067 evidence. Fix direction:
from a clean checkout of `8e0ddf7`, run
`KAYAKGEN_PY=/home/halbritt/git/kayak-gen/.venv/bin/python scripts/full-gate.sh`
or the repo-standard equivalent; expect ruff clean, pytest 0 failures, and
exactly 4 skips by default (or 0 skips when both OpenFOAM opt-ins are set).

`CONDITION 2 - Run the OpenFOAM opt-in smoke if this release includes the
current OpenFOAM wording/profile changes.`
Evidence: current HEAD touches `kayakgen/eval/cfd/adapters/openfoam_v2512.py`
and `kayakgen/eval/cfd/profiles.py`; release discipline recommends the opt-in
OpenFOAM smoke for CFD/OpenFOAM changes. Fix direction: on a machine with
OpenFOAM-v2512 available, run
`KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 .venv/bin/python -m pytest tests/test_openfoam_v2512_smoke.py -q`
and expect the env-gated smoke tests to pass rather than skip.

`CONDITION 3 - Establish a release baseline before a public tag/package.`
Evidence: no Git tags exist, `CHANGELOG.md` is still `## Unreleased`, and
`pyproject.toml` declares `version = "0.1.0"`. Fix direction for a `0.1.0`
release: promote the changelog heading to a dated `0.1.0` release heading,
tag the gated candidate as `v0.1.0`, and verify
`git describe --tags --exact-match 8e0ddf7` returns that tag.

`CONDITION 4 - Build and smoke the artifact if the intended release vector is
package or Docker distribution.`
Evidence: package and Docker metadata exist, but no build artifact or image was
built or inspected. Fix direction: run the chosen package/image build in a
clean checkout, install/run the produced artifact, verify `kayakgen --help`,
and preserve artifact hashes or image digest with the release notes.

## 8. Residual Risks And Follow-Ups

`RISK - Confidence is capped by fallback boundary.`
No prior tag or release heading exists, so the previous boundary is the
prompt fallback range rather than a real release baseline.

`RISK - Stale but useful inherited gates.`
Workflow 0067's full gate is recent and strong, but current HEAD changed
release-critical CFD claim wording and a test after that gate. It supports
confidence in nearby code, not readiness for this exact SHA.

Open question for the maintainer: is the desired ship vector a local checkpoint
on `main`, a `v0.1.0` tag, a PyPI-style package, or a Docker/web artifact? The
conditions above are closed-form for each path, but the release intent controls
which subset is mandatory.
