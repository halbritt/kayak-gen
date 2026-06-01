author: implementer-claude-opus-4.7-001

workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
role: implementer
lane: claude
run_id: run_f34bef1ca501bbe0fcad68ab893f0b04
session_id: sess_b5b468daa1915f5ccd896c4a8b42a1b3

# CLI completion result — RFC 0043 stage 4

The remaining stage-4 surface lands on
`striatum/0043-rfc-0043-stage-4-stability-rig-pipeline-cli-completion`.
Target gate green (89/89); `ruff check kayakgen/ tests/` clean.

## Revision 2 — re-verification under this run's byline

A prior implement attempt under run `run_7263118c661a23d7b278f2676a8ac3b3`
(byline `-003`) re-verified the codex threat_model fixes after the original
fixer session was killed by a daemon restart, but that attempt was itself
unable to `work.complete` and the run was re-emitted as
`run_f34bef1ca501bbe0fcad68ab893f0b04`. The fixes remain on disk inside this
run's `write_scope`. This session re-verifies them under the
`implementer-claude-opus-4.7-001` byline assigned to this packet and completes
the work packet. **No new code authored.**

On-disk evidence re-verified this attempt at the documented file:line
anchors:

- `kayakgen/eval/stability/registry.py:397-398` — cache key extended to
  `(resolved_root, mtime_ns, entry_count, version)`.
- `kayakgen/eval/stability/registry.py:442-475` — `_dir_fingerprint` walks
  EVERY entry under fixtures + fits trees (rglob/glob), not only `*.json`.
- `tests/test_claim_state_measured_promotion.py:474` —
  `test_registry_cache_invalidates_when_trace_evidence_disappears`
  (Finding 1 P1 regression).
- `tests/test_resolve_analytical_claim_label.py:201` —
  `test_real_hull_flips_through_load_stability_fit_registry`
  (Finding 2 P2 production-path positive).
- `tests/test_resolve_analytical_claim_label.py:227` —
  `test_real_hull_stays_unvalidated_when_registry_drops_fit`
  (Finding 2 P2 production-path negative).
- `tests/test_stability_fit_registry.py:281` —
  `test_gate_fit_hull_class_fixture_mismatch` (Finding 3 P2 registry-gate
  test).
- `tests/test_stability_fit_registry.py:413` —
  `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` in the emitted-reason
  completeness set.

§7 verification gate run by this attempt:

```
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
```

Result: **89 passed in 0.69 s**.

```
.venv/bin/ruff check kayakgen/ tests/
```

Result: **All checks passed!**

The Revision 1 narrative authored by `implementer-claude-opus-4.7-003` is
preserved verbatim below.

---

## Revision 1 — re-verification under attempt-3 byline

The attempt-2 Claude session that adopted the codex `threat_model` reviewer's
three findings (1 P1, 2 P2) was killed by a daemon restart before it could
`work.complete` the packet. The fixes had already landed on disk inside this
run's `write_scope`. This attempt-3 session re-verifies them, takes the
attempt-3 byline, and completes the packet. **No new code was authored in this
attempt.**

On-disk evidence (re-verified this attempt):

- `kayakgen/eval/stability/registry.py:442-478` — `_dir_fingerprint` walks
  EVERY entry under the fixtures + fits trees (`rglob("*")` / `glob("*")`),
  not only `*.json`, and returns `(max_mtime_ns, entry_count)`.
- `kayakgen/eval/stability/registry.py:397-398` — cache key extended to
  `(resolved_root, mtime_ns, entry_count, version)`.
- `tests/test_claim_state_measured_promotion.py:474` —
  `test_registry_cache_invalidates_when_trace_evidence_disappears` (Finding 1
  regression).
- `tests/test_resolve_analytical_claim_label.py:201` —
  `test_real_hull_flips_through_load_stability_fit_registry` (Finding 2
  positive production-path).
- `tests/test_resolve_analytical_claim_label.py:227` —
  `test_real_hull_stays_unvalidated_when_registry_drops_fit` (Finding 2
  negative production-path).
- `tests/test_stability_fit_registry.py:281` —
  `test_gate_fit_hull_class_fixture_mismatch` (Finding 3 registry-gate test).
- `tests/test_stability_fit_registry.py:413` —
  `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` in the emitted-reason completeness
  set.

§7 verification gate run by this attempt:

```
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
```

Result: **89 passed in 0.67 s**.

```
.venv/bin/ruff check kayakgen/ tests/
```

Result: **All checks passed!**

The original Revision 1 narrative authored by `implementer-claude-opus-4.7-002`
is preserved verbatim below.

---

## Revision 1 — codex build-review threat_model findings (addressed)

The codex `threat_model` reviewer's attempt-1 verdict was **needs_revision** with
three findings (1 P1, 2 P2). All three are adopted; the patches landed on top
of the attempt-1 surface inside this run's `write_scope`. The claude
`ergonomics_dx` reviewer's `accept_with_findings` verdict required no additional
work.

### [P1] Finding 1 — registry cache could keep a fit loaded after trace evidence disappeared

`load_stability_fit_registry()` gates calibration-trace evidence on disk
(`registry.py:215-223`), but the attempt-1 cache key
(`registry.py:439-460`) only walked the fits dir, fixtures root, and `*.json`
files. Non-JSON trace evidence (`fixtures/<id>/cal/pre.csv`, `post.csv`) was
NOT in the cache key. A passing fit could stay cached after its evidence was
deleted, violating the "current full chain required for flip" invariant.

**Fix** (`kayakgen/eval/stability/registry.py:439-471`):
- Renamed `_dir_mtime_ns` → `_dir_fingerprint`, returning
  `(max_mtime_ns, entry_count)`.
- Walk EVERY entry under the fixtures + fits trees (`rglob("*")` /
  `glob("*")`), not only `*.json`. Trace evidence files and their parent
  directories are now in the fingerprint.
- Added `entry_count` to the cache key
  (`registry.py:356-358`, `registry.py:395-396`) as a defence against the
  sub-mtime-granularity race observed on tmpfs-backed pytest `tmp_path`
  trees: deleting any tracked file drops the count regardless of whether the
  parent dir's mtime advanced within the same tick.

**Regression test** (`tests/test_claim_state_measured_promotion.py:474-495`,
`test_registry_cache_invalidates_when_trace_evidence_disappears`):
loads a passing fit, deletes `cal/pre.csv`, asserts the next non-diagnostic
load drops the fit **without** manually clearing the cache. Confirmed
non-flaky over 5 successive runs.

### [P2] Finding 2 — the "production" resolver test did not exercise the production chain

`tests/test_resolve_analytical_claim_label.py::test_real_hull_with_hull_class_flips_under_covering_fit`
handed a hand-built `StabilityFitRecord` straight to the resolver — no
manifest, no `promotion.json`, no on-disk hash binding, no registry gates.
The test would still pass if the loader or a call-site swap regressed.

**Fix** (`tests/test_resolve_analytical_claim_label.py:187-256`): the original
resolver unit tests are kept and clearly framed as resolver-matching coverage;
**two new production-path tests** stage the full acceptance triple under a
`tmp_path` fits/fixtures root and assert the flip / non-flip THROUGH
`load_stability_fit_registry()` — the same loader the evaluator
(`evaluator.py:408`), the CLI (`stability_cli.py:476-477`), and the web
surfaces (`generate_frontier_view.py:582`, `generate_spec_form.py:909`)
consume:

- `test_real_hull_flips_through_load_stability_fit_registry` — happy path:
  staged triple + real `Hull(hull_class="sea_kayak")` → loader returns 1 fit
  → resolver returns `validated_hydrostatic_comparison`.
- `test_real_hull_stays_unvalidated_when_registry_drops_fit` — negative:
  staged triple but with a stale evaluator version → loader drops the fit at
  gate 10 → resolver stays `unvalidated_hydrostatic_comparison`. Proves the
  safety invariant holds when the loader's gates run, not just when the
  resolver matches.

### [P2] Finding 3 — new hull-class fixture-binding gate lacked threat-surface coverage

The build added gate 8a (`registry.py:297-311`): the fit's
`hull_family_scope.hull_class` must equal the fixture's
`hull_identity.hull_class`, refused with `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH`.
The listed registry tests covered hull-class mismatch at *resolver* scope
but not at the *fixture-binding* trust boundary, and the reason was missing
from the emitted-reason completeness set.

**Fix**:
- Added `tests/test_stability_fit_registry.py:281-298,
  test_gate_fit_hull_class_fixture_mismatch`: stages a promoted `sea_kayak`
  fixture with a strict accepted fit declaring
  `hull_family_scope.hull_class="sprint_k1"` and asserts the loader drops it
  with `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH`.
- Added `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` to the emitted-reason
  completeness set at `tests/test_stability_fit_registry.py:392-411`
  (`test_every_reason_has_a_next_action`). The mapping was already populated
  in attempt 1 (`registry.py:86`); this binds the completeness invariant so
  a future removal would now break the test.

### Counter-arguments

None. Every finding adopted as-written.

### Revision 1 verification

```
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
```

Result: **89 passed, 0 failed, 0 skipped in 0.69 s** (+4 over attempt 1: one
new trace-evidence cache test, one new hull-class fixture-binding registry
test, two new production-path resolver tests).

```
.venv/bin/ruff check kayakgen/ tests/
```

Result: **All checks passed.**

The GZ/evaluator suite is unchanged.

---

## 1. Files changed

| Path | Change | Lines after |
| --- | --- | --- |
| `kayakgen/cli/stability_cli.py` | rewrite (promote-fixture / accept-fit / claim-status / structured-JSON refusals) | 574 |
| `kayakgen/eval/stability/registry.py` | 13-gate loader + gate 8a hull-class fixture binding + Revision 1 `_dir_fingerprint` (mtime, count) | 522 |
| `kayakgen/model/hull.py` | add `hull_class: str \| None = None` | 153 |
| `kayakgen/ui/web/generate_frontier_view.py` | swap `EMPTY_STABILITY_FIT_REGISTRY` for `_loaded_fit_registry()` accessor | 755 |
| `kayakgen/ui/web/generate_spec_form.py` | swap `EMPTY_STABILITY_FIT_REGISTRY` for `_loaded_fit_registry()` accessor; drop unused imports | 1452 |
| `tests/conftest.py` | lift `make_stability_acceptance_triple` + `stage_acceptance_triple` triple factory | 294 |
| `tests/test_cli_stability.py` | sweep to new `accept-fit` signature + structured-JSON refusal shape | 358 |
| `tests/test_measured_stability_acceptance.py` | NEW — gate refusals for promote-fixture + accept-fit | 633 |
| `tests/test_measured_stability_ingest.py` | NEW — canonical-manifest writer + immutability-after-promotion | 115 |
| `tests/test_claim_state_measured_promotion.py` | NEW — end-to-end flip, memoization, env-var, `claim-status` CLI, **Revision 1 trace-evidence cache regression** | 520 |
| `tests/test_resolve_analytical_claim_label.py` | three real-`Hull` resolver-unit tests + **Revision 1 two production-path tests through `load_stability_fit_registry()`** | 256 |
| `tests/test_stability_fit_registry.py` | 19 gate tests + **Revision 1 hull-class fixture-binding gate + completeness-set entry** | 420 |
| `docs/USER_GUIDE.md` | append §E.2 "Stage 4 — accepted-fit registry and label flip" subsection | +80 |
| `docs/workflows/0043-…/SOURCES.md` | rewrite to canonical `kayakgen stability` surface | full rewrite |
| `docs/DECISION_LOG.md` | append D045 (stage-4 completion) + D046 (resistance-side follow-ups) | +2 rows |

`git diff --stat` against `main`: 13 files changed, +1396 / -349 lines.
`OPERATOR_REPORT.md` carries one parent-supervisor annotation made before
the lane started; left untouched (outside `write_scope`).

## 2. Pytest summary + ruff

Verification gate from `prompts/implement.md`:

```
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
```

Result: **89 passed, 0 failed, 0 skipped in 0.69 s**.

```
.venv/bin/ruff check kayakgen/ tests/
```

Result: **All checks passed.**

Full repo suite (`.venv/bin/pytest -q`): the two pre-existing failures
called out in attempt 1's CLI_COMPLETION_RESULT remain (`test_services_boundaries.py`
services-imports-UI cycle; `test_web_browser.py` Playwright timeout) — both
reproduce against `main` and sit outside this run's `write_scope`. No new
regressions introduced.

## 3. Section-by-section evidence

(Attempt 1 evidence stands unchanged for sections that were not revisited.
Revision 1 additions cited above.)

### §1 — `promote-fixture` writes `promotion.json` without mutating the manifest

- `kayakgen/cli/stability_cli.py:167-251` is the rewritten command.
- Manifest immutability is asserted on every successful write at
  `stability_cli.py:250`: `assert manifest_path.read_text(encoding="utf-8") == manifest_bytes`.
- SHA-256 binding reuses the registry helper at `stability_cli.py:227`:
  `manifest_sha = fixture_canonical_sha256(manifest)`.
- Re-promote-with-identical-bytes no-op at `stability_cli.py:236-239`.
- Refusal on sha mismatch emits the structured JSON line at `stability_cli.py:228-234`.

### §2 — `accept-fit` breaking signature change

- `kayakgen/cli/stability_cli.py:254-431` is the rewritten command.
- New signature `--fit-record <path> --fixture-id <id> --out <path>` at
  `stability_cli.py:256-283`.
- Removed-`--packet` refusal path at `stability_cli.py:295-302` emits exit 2
  + an explicit pointer to `--fixture-id`.
- Hull-class fixture binding (Revision 1's gate 8a CLI mirror) at
  `stability_cli.py:383-392`: refuses with
  `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` when the fit's scope diverges from
  the manifest's measured `hull_identity.hull_class`.

### §3 — `claim-status` read-only command

- `kayakgen/cli/stability_cli.py:434-508` is the new command.
- Emits one JSON line with `hull_class`, `design_hash`, `claim_label`,
  `covering_fit_id`, `fits_root`, `fits_loaded`, `dropped_fit_count`
  (`stability_cli.py:489-497`).
- `--debug` adds a `diagnostics` list keyed by
  `{fit_id, fit_path, reason_code, detail}` at `stability_cli.py:498-507`.

### §4 — `--help` text + structured refusal copy

- Sub-app help string at `kayakgen/cli/stability_cli.py:81-86` matches §E.1.
- `_refuse` helper at `stability_cli.py:103-124` emits
  `{ok, code, fixture_id, details, next_action}` with
  `next_action = REASON_NEXT_ACTION[reason]`. Imported from `registry`;
  no remediation text re-authored locally.

### §5 — Two web call-site swaps

- `kayakgen/ui/web/generate_frontier_view.py:38-46` adds the lazy
  `_loaded_fit_registry()` accessor; use site at
  `generate_frontier_view.py:582`: `fit_registry=_loaded_fit_registry()`.
- `kayakgen/ui/web/generate_spec_form.py:881-893` adds the same accessor;
  use site at `generate_spec_form.py:909`: `registry=_loaded_fit_registry()`.
- Both `EMPTY_STABILITY_FIT_REGISTRY` imports dropped.

### §6 — Tests + conftest triple factory + `test_cli_stability.py` sweep

- `tests/conftest.py:55-217` lifts the in-test triple factory +
  `stage_acceptance_triple` helper.
- Three new test files + revision-1 hardening: `test_measured_stability_ingest.py`
  (4 tests), `test_measured_stability_acceptance.py` (18 tests covering every
  §D refusal path + byte-stability + legacy-`--packet` pointer),
  `test_claim_state_measured_promotion.py` (17 tests — attempt 1's 16 plus
  the Revision 1 trace-evidence cache regression).
- `tests/test_cli_stability.py` swept to the new `accept-fit` signature.

### §7 — Docs (USER_GUIDE, SOURCES, DECISION_LOG)

- `docs/USER_GUIDE.md` — §E.2 stage-4 subsection appended.
- `docs/workflows/0043-…/SOURCES.md` — rewritten per §E.4.
- `docs/DECISION_LOG.md` — D045 + D046 rows added.

### ADDENDUM — `hull_class` end-to-end

- **Mechanism chosen: explicit optional field**.
  `kayakgen/model/hull.py:67-79` adds
  `hull_class: str | None = Field(default=None, …)`.
- **Why explicit, not derived**: a geometry-derived classifier risks
  over-broadening — e.g. a sea-kayak-ish prototype that classifies into
  `sprint_k1` would auto-flip into a stricter envelope's accepted fit. The
  threat-model invariant is "`None` keeps the label unvalidated, no
  exceptions"; the explicit field is the lowest-risk way to satisfy that.
  Operators set `hull_class` consciously when they intend to claim coverage.
- **`design_hash()` preserved**: `kayakgen/services/identity.py::_DESIGN_FIELDS`
  (forbidden path for this run) does NOT include `hull_class`, so the
  design hash is unchanged.
- **Production-path test proving the flip**:
  `tests/test_resolve_analytical_claim_label.py::test_real_hull_flips_through_load_stability_fit_registry`
  (Revision 1) builds a real `Hull(hull_class="sea_kayak")`, stages the
  triple on disk, calls `reg.load_stability_fit_registry(root)`, and asserts
  `resolve_analytical_claim_label(hull, fits) == VALIDATED`.

## 4. Revision history

### Attempt 3 (Revision 1, this revision)

The codex `threat_model` build-reviewer's attempt-2 verdict was
**needs_revision** with three findings (1 P1, 2 P2). All three are adopted;
the patches landed inside this run's `write_scope` on top of the attempt-2
surface. See the **Revision 1** section at the top of this document for the
detailed evidence.

### Attempt 2

The codex build-reviewer's attempt-1 verdict was **changes requested** with
four findings (2 P1 + 2 P2). All four were adopted in attempt 2; details
preserved below.

- **[P1] Finding 1 — fit `hull_family_scope.hull_class` was trusted without
  being bound to the measured fixture identity.** Gate 8a added to
  `registry.py`; same check at the CLI level. Regression tests:
  `test_registry_drops_fit_when_scope_hull_class_diverges_from_fixture`,
  `test_accept_fit_refuses_hull_class_fixture_mismatch`.
- **[P1] Finding 2 — evaluator-version gate bypassable through the registry
  cache.** Cache key extended from `(resolved_root, directory_mtime_ns)` to
  `(resolved_root, directory_mtime_ns, version)`. Regression test:
  `test_registry_cache_invalidates_on_evaluator_version_change`. (Revision 1
  has since extended the key further to
  `(resolved_root, directory_mtime_ns, entry_count, version)` — see top.)
- **[P2] Finding 3 — the real-Hull flip test did not exercise the production
  loaded-registry path.** Added
  `test_evaluator_version_mismatch_real_hull_through_loaded_registry`.
  (Revision 1 finding 2 strengthens this further with the two `_through_load_stability_fit_registry`
  tests directly in the resolver test file.)
- **[P2] Finding 4 — `promote-fixture` was canonicalizing the submitted
  promotion-packet bytes.** CLI now reads the packet text once, validates
  from that text, and writes the original text unchanged. Regression test:
  `test_promote_fixture_persists_submitted_bytes_verbatim`.

### Attempt 1

First attempt; the listed surface §1-§7 + the `hull_class` addendum all
landed.

## 5. Review recommendations NOT adopted

None — every codex finding across attempts 2 and 3 adopted without
counter-argument.

## 6. Operational notes

- **Branch**: changes land on the records-only run branch
  `striatum/0043-rfc-0043-stage-4-stability-rig-pipeline-cli-completion`.
- **Stage 4 first real promotion** stays gated on D007 / D014 physical
  rig data; no production fixture lands in this PR.
- **CHANGELOG.md** untouched (forbidden path).
- **RFC status flips** untouched (`docs/rfcs/` forbidden).
- **Resistance-side findings (D046)** are recorded but NOT patched — they
  belong to a separate calibration / resistance-subdomain workflow.
