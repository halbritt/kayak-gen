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
   be green, with only the documented OpenFOAM opt-in skips
   (expected: 4 when OpenFOAM opt-ins are unset). The four are env-gated behind
   `KAYAKGEN_OPENFOAM_SMOKE=1` + `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`:
   two in `tests/test_openfoam_v2512_smoke.py` and two
   real-solver-path stage tests in `tests/test_cfd_run_stages.py`.
   When the env knobs are set, the gated tests must pass instead
   of skipping. Any other skip count means the environment is
   missing extras and the run does **not** count as a gate
   (audit R4, 2026-06-06: the previous "green or skipped" wording
   let a `[dev]`-only env silently skip the desktop
   forbidden-copy regressions).
2. **`.venv/bin/python -m ruff check kayakgen tests`** — ruff must
   pass. Phase 0 of the architecture plan installed ruff to
   `[dev]`; new code must clear it.
3. **No `git push --force`** to `main`. Force-push is only
   permitted on operator-owned feature branches, never on `main`
   even via `--force-with-lease`.
4. **Co-author attribution** on any commit an agent participated
   in: `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`.

Requirements 1 and 2 have a mechanical form: `scripts/full-gate.sh`
runs the full suite, **enforces** the skip count, then runs Ruff — it
exports `KAYAKGEN_ENFORCE_SKIP_PIN=1` so `tests/conftest.py` also
enforces the count inside pytest, then parses the final pytest summary
line as a redundant script-level check. The expected count is derived
from the OpenFOAM env knobs: default gates expect 4 skips; a full
OpenFOAM smoke+local-run opt-in expects those tests to pass instead of
skip (audit G1, 2026-06-06; workflow 0067 gate-altitude follow-up).
The env knob is intentionally explicit so partial invocations such as
`pytest tests/test_x.py` are not punished for having zero skips.

RFC 0084 / D070 adds optional persistent receipts to this same canonical
runner. Use `scripts/full-gate.sh --receipt /outside/source/full-gate.json`
or `KAYAKGEN_GATE_RECEIPT`; the path must be new and outside source or in
a Git-ignored directory. `KAYAKGEN_PY` still selects a supported external
interpreter. Inherited `PYTEST_ADDOPTS` is cleared so environment-only
selectors cannot narrow the full suite; tracked pytest configuration stays
effective. No subset or arbitrary-command option is supported.

Freeze source before starting. The receipt binds actual candidate bytes and
a Git tree captured through a copied index, including staged, dirty and
nonignored untracked content. It records both snapshots, interpreter,
declared renderer settings, actual renderer observation status, command
durations/exits and expected/observed skips. `passed` requires both checks,
the skip pin and unchanged source; failures and caught interruptions are
distinct terminal outcomes. A `running` receipt is incomplete. The original
index is unchanged; committing the identical tested content afterward keeps
the recorded tree identity. Endpoint checks do not detect transient edits
restored between snapshots, so they do not replace the freeze requirement.
Renderer `unobserved` is an explicit absence, never proof of a CPU/GPU mode.
RFC 0082 adds the actual context probe and resource admission described below.
See [RFC 0084](rfcs/0084-source-bound-full-gate.md) for the receipt schema,
output ownership and interruption limits.

## Renderer admission for full and pre-push gates (RFC 0082)

Both shell entry points use the same maintained runner and renderer policy.
`--renderer software` is the default; `KAYAKGEN_GATE_RENDERER` selects the
same profile when a flag is inconvenient. The software profile fixes Mesa EGL
settings in the probe and every gate child, then renders a real context. It
requires Mesa llvmpipe/softpipe capabilities, loaded GL-library evidence and no
NVIDIA OpenGL mappings. Missing vendor support, failed/crashed probes or
contradictory observations refuse before pytest or Ruff starts. Verified software
gates may overlap; this does not establish unlimited CPU/RAM capacity.

`--renderer hardware` preserves the caller's renderer environment and holds
`~/.cache/kayakgen-release-gate.lock` across its actual probe and all check
commands. The supported hardware profile currently requires observed NVIDIA
capabilities and corresponding loaded GL libraries. Software fallback refuses.
The advisory lock coordinates participating gate processes; it does not reserve
VRAM or stop unrelated GPU workloads. Nested targeted checks should use software
mode instead of recursively requesting the hardware lock.

Receipts retain requested profile, original/effective renderer environment,
actual VTK/window/OpenGL identity and capabilities, mapped GL libraries, probe
exit/duration/stderr, and the hardware lock's policy/path/state when applicable.
A native probe failure, partial suite or stale running receipt is never a pass.
The profile is currently Linux-specific (EGL vendor files, `/proc` and `flock`);
current observations do not establish future driver/dependency compatibility.

The fast subset still runs Ruff before its fixed pytest plan; full release
verification still runs complete pytest followed by mandatory Ruff. The exact
11 ignore paths and two deselections now live in `FAST_PYTEST_ARGS` in
`kayakgen.operations.gate`; manifest tests continue to verify existing paths and
collectible node IDs, and real caller tests enforce the skip pin. Both plans
clear inherited `PYTEST_ADDOPTS`; no arbitrary-command or full-entry-point subset
option is added. Fast receipts use `gate: "fast"` and cannot satisfy a full-gate
requirement.

The opt-in OpenFOAM smoke is the recommended pre-push gate when a
change touches CFD, the OpenFOAM adapter, the case templates, or the
provenance probe. Run it locally with:

```bash
KAYAKGEN_OPENFOAM_SMOKE=1 KAYAKGEN_OPENFOAM_LOCAL_RUN=1 \
  .venv/bin/python -m pytest tests/test_openfoam_v2512_smoke.py -q
```

## Shared-input semantic preflight (RFC 0081)

For a change that combines evaluation context, numerical admission, saved results
or presentation, run the relevant semantic preflight before the expensive full
freeze. Supply all relevant changed paths or select contracts explicitly:

```bash
python -m kayakgen.operations.semantic_preflight \
  --changed-path kayakgen/eval/contract.py --out /external/new-preflight-attempt
```

The work packet names producers, consumers and shared inputs. Existing context,
method-binding, admission/interval and display regressions remain the oracles;
operating-input checks also replay the retained 34-case no-evaluator consumer
oracle. Review unmapped paths and explicitly select a group for a new consumer.
Unrelated changes do not require the whole matrix. See the user guide for the
four groups and physical-adapter routing.

This command emits partial source-bound evidence. `not_applicable` means no group
was selected. Every outcome keeps `release_acceptance=false` and
`full_release_gate_required=true`; it does not replace either pre-merge check,
change the four-skip pin, add a git hook or promote physical validation.

## Local enforcement (pre-push hook)

Audit R0 (2026-06-06) found the documented gate red on `main` for 12
days with nothing making the red visible. Enforcement is two-layered:

1. **Pre-push hook (fast subset).** Install once per clone:

   ```bash
   scripts/install-hooks.sh
   ```

   This installs `scripts/fast-gate.sh` as `.git/hooks/pre-push`. The
   fast gate runs `ruff check kayakgen tests` plus the fast pytest
   subset and refuses the push on failure — including on a green run
   whose skip count differs from the pinned 4 (audit G1). The
   canonical deselect list and the measured runtime live in the
   script header (re-measured 2026-06-06 post-workflow-0066: 3m42s —
   1087 passed / 4 skipped / 2 deselected — vs. 10:49 for the full
   suite;
   deselected: the browser/visual suite, the subprocess-lifecycle
   suite, the CFD fixture-command integration tests, and the
   measured runtime-dominant integration files).
   `git push --no-verify` bypasses the hook in emergencies; the
   bypass does not waive the full-suite pre-merge gate above.

2. **Striatum slice gates (full suite).** Striatum workflow
   review/apply jobs for this repo run `scripts/full-gate.sh` as
   their slice-completion gate — the mechanical form of the FULL
   suite requirement (`.venv/bin/python -m pytest -q` → 0 failed,
   exactly the 4 documented OpenFOAM opt-in skips, enforced by the
   script's skip-count pin) plus
   `.venv/bin/python -m ruff check kayakgen tests`. A lane agent
   cannot complete a slice on a red suite — or on a green one with
   the wrong skip count.

The fast gate is a convenience net between full-suite gates, not the
release gate; pre-merge requirement 1 above is unchanged by it.

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
- Issue tracking (the current Plane workspace and project are specified in `AGENTS.md`).
- PR review process (single-operator project; no PR template).

These items become load-bearing only if the project grows beyond
one operator + agents.

## Persistent runtime observation (RFC 0080 / D066)

Installed-release workflow acceptance does not by itself prove persistent
service lifetime. `python -I -B -m kayakgen.operations.runtime` reuses the
selected installed verification request and byte audit. Backend-only controls
retain `persistent_deployment_accepted=false`. Persistent observation requires
an explicit unit, idle interval and loopback readiness URL, effective installed
parser settings, process/invocation continuity, restart count and HTTP readiness
before and after that interval. No WebSocket or HTTP keepalive is introduced
during the interval. A healthy replacement still counts as a restart.

Keep stable release paths, timeout zero/server mode, `Restart=always`, detached
workers and `KillMode=process`. Positive timeout remains valid for intentionally
transient servers. Retain failed attempts and their reasons. The campaign's
315 seconds is one deployment observation, not a universal policy. The verifier
reads the unit; activation or configuration remains separately authorized work.
