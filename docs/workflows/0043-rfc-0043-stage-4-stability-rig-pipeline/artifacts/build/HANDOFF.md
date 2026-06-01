---
author: implementer-claude-opus-4.7 (hand-driven, daemon run wedged)
---

# HANDOFF — workflow 0043 implement (RFC 0043 stage 4)

## Context

The striatum daemon run wedged three times (synthesizer over-reach;
then codex `reject` verdicts which are terminal in striatum with no
operator recovery path — see striatum#118/#139 and the run arc in the
repo's recent commits). The operator chose to **hand-drive** the
implementation off the twice-revised, claim-integrity-converged design
(`../synthesis/DESIGN_SYNTHESIS.md`). This file is the build record.

## What landed (commit on `main`)

The **load-bearing claim-integrity core** — the part three rounds of
threat-model review converged on, including codex's final P1 (the GZ
claim-state flip is gated on the *full provenance chain*, never on
"accepted fixture exists" alone):

| Surface | File | Status |
|---|---|---|
| 13-gate accepted-fit registry | `kayakgen/eval/stability/registry.py` (new) | ✅ landed + tested |
| Evaluator version constant (gate 10) | `kayakgen/eval/stability/evaluator.py::ANALYTICAL_EVALUATOR_VERSION` | ✅ landed |
| Evaluator call-site swap (§C.4, site 1/3) | `evaluator.py::_loaded_fit_registry` | ✅ landed |
| Registry gate tests | `tests/test_stability_fit_registry.py` (new, 19 tests) | ✅ green |

Verification: 19/19 new tests pass; 112 GZ/evaluator/high-angle + 31
existing stability tests pass (call-site swap non-breaking); `ruff`
clean. Registry is empty by default (D039) so the label stays
`unvalidated_hydrostatic_comparison` until a real fixture is promoted —
defaults byte-stable.

### Self-review of the landed core (3 postures)

- **ergonomics_dx**: every `REASON_*` constant has a `REASON_NEXT_ACTION`
  entry (test-enforced); the loader's `with_diagnostics` mode names the
  dropped fit + reason for `claim-status --debug` to surface.
- **threat_model**: gates 2/3/3a/3b re-check evidence the pydantic schema
  does NOT gate (smoothness, on-disk trace resolution, self-declared
  bounds vs `OPERATOR_MAX_*` constants that live outside the manifest,
  rights). Gate 5 hash-binds the packet to the on-disk manifest bytes;
  gate 8 re-binds the fit's `FixtureRef` to the same bytes. A tampered
  manifest or packet drops the fit (tests
  `test_gate_sha256_mismatch`, `test_post_sign_review_tamper_drops_fit`,
  `test_provenance` family). **Known finding:** gate 7 (review-incomplete)
  is *schema-shadowed* — a measured-target packet with a non-accepted
  review cannot parse, so gate 4's parse-failure catches the tamper first.
  Gate 7 is retained as defense-in-depth; the security property (fit
  dropped) holds either way. Documented in the test.
- **devils_advocate**: the cache key folds the fixtures-tree mtime, not
  just the fits dir, so a `promote-fixture` write into a *fixture* dir
  still invalidates (test `test_registry_memoizes_until_mtime_change`
  covers the fits-side; the fixtures-side mtime is in `_dir_mtime_ns`).
  Weakest remaining spot: `_dir_mtime_ns` rglob's every fixtures `*.json`
  on each *cache-miss* load — acceptable for the expected handful of
  fixtures, would want an index at scale (future RFC).

## Remaining surface (not yet landed)

Spec references are to `../synthesis/DESIGN_SYNTHESIS.md`.

1. **CLI — `kayakgen stability` sub-app** (§A.2–A.4). The existing
   sub-app has `ingest-rig-run` / `promote-fixture` / `accept-fit` /
   `residual-plot` (RFC 0058). Stage 4 needs:
   - `promote-fixture <fixture_id> --packet <p>`: validate the packet,
     check `fixture_ref.fixture_sha256` == `fixture_canonical_sha256` of
     the on-disk manifest (reuse `registry.fixture_canonical_sha256`),
     write the packet verbatim to
     `data/stability/fixtures/<fixture_id>/promotion.json`. Do NOT mutate
     the manifest.
   - `accept-fit` **breaking change** (§A.3): `--fit-record <path>`
     `--fixture-id <id>` (required) `--out <path>`; remove `--packet`;
     Typer error path names `--packet` as removed → `--fixture-id`. Sweep
     in-tree callsites (`tests/test_cli_stability.py`).
   - `claim-status <hull> [--fits-root DIR] [--debug]` (§A.4, new):
     read-only, calls `resolve_analytical_claim_label(hull,
     load_stability_fit_registry(root))`, emits the one-line JSON in §A.4;
     `--debug` adds the `diagnostics` list from
     `load_stability_fit_registry(..., with_diagnostics=True)`.
   - Refusal copy: one JSON line per refusal using `REASON_NEXT_ACTION`
     (§E.3).
2. **Web call-site swaps** (§C.4, sites 2/3): replace
   `EMPTY_STABILITY_FIT_REGISTRY` with a lazy mtime-memoized loader at
   `kayakgen/ui/web/generate_frontier_view.py:~568` and
   `kayakgen/ui/web/generate_spec_form.py:~897` (mirror
   `evaluator._loaded_fit_registry`).
3. **Tests** (§D): the CLI-surface tests
   (`tests/test_measured_stability_ingest.py`,
   `tests/test_measured_stability_acceptance.py`) for promote/accept-fit/
   claim-status, plus the web-integration colour-token test and the
   evaluator-flip integration test
   (`test_evaluator_flips_result_semantics_under_loaded_registry`). The
   registry-gate half of §D is done in `test_stability_fit_registry.py`.
   A shared `tests/conftest.py` factory
   `make_stability_acceptance_triple` can wrap the in-test triple builder
   already written in `test_stability_fit_registry.py`.
4. **Docs**: USER_GUIDE.md stage-4 subsection (§E.2); SOURCES.md update
   (§E.4) — remove the obsolete `kayakgen calibration
   ingest-measured-stability` lines, point at `registry.py`.
5. **RFC status flips** (parent-agent, after build review converges):
   RFC 0043 + RFC 0056 `Status:` → landed in their `.md` files +
   `docs/rfcs/README.md` rows + CHANGELOG row. **Note:** RFC 0056 stage-4
   *promotion of a real fixture* stays blocked on D007/D014 physical rig
   data — this pipeline lands the machinery, not a promoted fixture, so
   the RFC status should read "stage-4 pipeline landed; first promotion
   still gated on rig data."

## Build-review note

The 3-lane daemon build review did not run (the run was wedged at the
design phase). The landed core carries my own 3-posture self-review
above. A follow-up build review of the CLI/web surface — once landed —
is recommended via a fresh 2-lane (claude+codex) build-review run, or
the standard `/code-review`.
