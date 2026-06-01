# CLI-completion handoff — RFC 0043 stage 4

The claim-integrity **core** is landed and green (commit `8e5c68e`):
`kayakgen/eval/stability/registry.py` (13-gate accepted-fit registry),
the `ANALYTICAL_EVALUATOR_VERSION` constant + evaluator call-site swap,
and `tests/test_stability_fit_registry.py` (19 tests). This doc is the
step-by-step for the remaining **CLI + web + docs** surface so a fresh
agent (or a 2-lane claude+codex build-review run) can finish it.

Spec source of truth: `../synthesis/DESIGN_SYNTHESIS.md` §A–E. Read it
first. Everything below cites it.

---

## 1. `promote-fixture` — make it write the acceptance record, not mutate the manifest

**File:** `kayakgen/cli/stability_cli.py:81-124` (existing command).

**Current behavior (WRONG for stage 4):** it loads the manifest and
*rewrites* `manifest.json` with a new `intended_use`
(`stability_cli.py:114-118`). The threat-model review established that
the manifest is **immutable after ingest** and acceptance is a
*separate hash-bound record*, not an in-place flag (§A.1, §B.1).

**Target behavior (§A.2):**
- Validate the `StabilityFixturePromotionPacket` from `--packet`.
- Load the on-disk manifest at
  `data/stability/fixtures/<fixture_id>/manifest.json`.
- Check `packet.fixture_ref.fixture_sha256 ==
  registry.fixture_canonical_sha256(manifest)`. On mismatch, refuse with
  the `fixture_sha256_mismatch` reason (see §3 refusal copy). **Reuse
  `from kayakgen.eval.stability.registry import fixture_canonical_sha256`
  — do not re-derive the hash; the registry's gate 5 compares against
  exactly this.**
- Write the packet **verbatim** to
  `data/stability/fixtures/<fixture_id>/promotion.json` (this file *is*
  the `AcceptedStabilityFixtureRecord`). Do **not** touch
  `manifest.json`.
- Refuse-on-overwrite is acceptable (mirror
  `_write_json_refusing_overwrite`), but a re-promote with identical
  bytes should be a clean no-op.

**Test (`tests/test_measured_stability_acceptance.py`):**
- `test_promote_fixture_writes_accepted_fixture_record` — packet +
  matching manifest hash → `promotion.json` lands; manifest bytes
  byte-equal to the original ingest.
- `test_promote_fixture_refuses_sha256_mismatch` — tamper the manifest
  after the packet is signed → refusal.
- `test_ingest_rig_run_does_not_mutate_intended_use` — after
  `promote-fixture`, `manifest.json` bytes are byte-equal to the
  ingest output.

---

## 2. `accept-fit` — breaking signature change

**File:** `kayakgen/cli/stability_cli.py:127-161` (existing command).

**Current signature:** positional `fit_record_path` + `--packet`.

**Target signature (§A.3):**
```
kayakgen stability accept-fit --fit-record <path> --fixture-id <id> --out <path>
```
- `--fit-record` (was positional), `--fixture-id` (NEW, required, no
  default), `--out` (NEW, required). **Remove `--packet`.**
- Resolve `data/stability/fixtures/<fixture_id>/`, validate the
  co-located `promotion.json`, hash the manifest's canonical bytes
  (`fixture_canonical_sha256`), and confirm the fit's
  `fixtures[]` cites `(fixture_id, fixture_sha256)`. Refuse with the §B
  reason token on any failure.
- Output is the `StabilityFitRecord` dump to `--out` with
  `acceptance_verdict="accepted"`, `strict=True`.
- **Typer error path:** when a caller passes the removed `--packet`,
  the error message must name it as removed and point to `--fixture-id`
  (Typer surfaces unknown options; add an explicit note in the
  command docstring + a `no_args_is_help`-style hint).
- **Sweep in-tree callers:** `tests/test_cli_stability.py` (and any
  docs) use the old `accept-fit <path> --packet`. Update them.

**Tests:** `test_accept_fit_binds_to_promoted_fixture_happy_path`,
`test_accept_fit_refuses_unpromoted_fixture`,
`test_accept_fit_refuses_missing_promotion_packet`,
`test_accept_fit_refuses_evaluator_version_mismatch`,
`test_accept_fit_refuses_disjoint_heel_range`,
`test_accept_fit_refuses_strict_check_skipped_with_accepted_verdict`,
`test_accept_fit_writes_record_byte_stable` (§D). Many of these mirror
gates already proven in `test_stability_fit_registry.py` — reuse the
in-test triple factory there (lift it into `tests/conftest.py` as
`make_stability_acceptance_triple`).

---

## 3. `claim-status <hull>` — new read-only command

**File:** add to `kayakgen/cli/stability_cli.py`.

**Signature (§A.4):**
```
kayakgen stability claim-status hull.json [--fits-root DIR] [--debug]
```
- Load the hull (`from kayakgen.io.json import load_hull`).
- `from kayakgen.eval.stability.registry import load_stability_fit_registry`
  and `from kayakgen.eval.stability.high_angle_contracts import
  resolve_analytical_claim_label`.
- `fits = load_stability_fit_registry(fits_root)`;
  `label = resolve_analytical_claim_label(hull, fits)`.
- Emit ONE JSON line with the §A.4 shape: `hull_class`, `design_hash`,
  `claim_label`, `covering_fit_id` (the first fit whose
  `hull_family_scope` covers the hull, else `null`), `fits_root`,
  `fits_loaded`, `dropped_fit_count`.
- `--debug`: call `load_stability_fit_registry(fits_root,
  with_diagnostics=True)` and add a `diagnostics` list, each entry
  `{fit_id, reason_code, detail}` from the `FitRejectionDiagnostic`
  tuple. `dropped_fit_count` = `len(diagnostics)`.

**Tests:** `test_claim_status_command_reports_resolved_label`,
`test_claim_status_debug_lists_dropped_fit_diagnostics` (§D).

**Note on `hull_class` / `design_hash`:** `resolve_analytical_claim_label`
reads `getattr(hull, "hull_class", None)` and `hull.design_hash()`
(`high_angle_contracts.py:66-79`). Confirm the `Hull` model exposes
`hull_class`; if it does not, the label cannot flip for any hull and
that is a separate gap to raise (the registry core is correct
regardless — it gates the *fits*, the resolver matches *hulls*).

---

## 4. `--help` text + refusal copy (§E.1, §E.3)

- Update `kayakgen stability --help` to the §E.1 block (add
  `claim-status`).
- Each refusal emits one structured JSON line:
  `{"ok": false, "code": "<REASON_*>", "fixture_id": ..., "details":
  {...}, "next_action": "<from REASON_NEXT_ACTION>"}`. Import
  `REASON_NEXT_ACTION` from `registry.py` — it already maps every gate
  constant to operator-facing remediation (test-enforced complete).

---

## 5. Two web call-site swaps (§C.4, sites 2/3)

The evaluator (site 1) is done. Mirror it at:
- `kayakgen/ui/web/generate_frontier_view.py:568` — replace
  `fit_registry=EMPTY_STABILITY_FIT_REGISTRY` with a lazy
  mtime-memoized `load_stability_fit_registry()` accessor (copy the
  `evaluator._loaded_fit_registry` shape). Also drop the now-unused
  `EMPTY_STABILITY_FIT_REGISTRY` import at line 31.
- `kayakgen/ui/web/generate_spec_form.py:897` — same swap; import at
  line 34.
- Each web request re-stats the fits-dir mtime (the registry memoizes),
  so an operator who runs `promote-fixture` / `accept-fit` mid-session
  sees the new state on the next request without restarting Trame.

**Tests:** `test_generate_frontier_view_color_token_flips_under_loaded_registry`,
`test_evaluator_flips_result_semantics_under_loaded_registry` (§D) —
both stage a full acceptance triple under a tmp
`KAYAKGEN_STABILITY_FITS_ROOT` and assert the flipped label / color
token. The triple factory in `test_stability_fit_registry.py` plus a
`Hull` whose `design_hash()` lands in the fit's
`hull_family_scope.design_hash_envelope` is the setup.

---

## 6. Docs (§E.2, §E.4)

- `docs/USER_GUIDE.md`: append the §E.2 "Stage 4 — accepted-fit registry
  and label flip" subsection under the existing RFC 0058 stability
  section. The three on-disk artifacts + the `claim-status` example +
  the `KAYAKGEN_STABILITY_FITS_ROOT` override.
- `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md`:
  per §E.4, remove the obsolete `kayakgen calibration
  ingest-measured-stability` / `accept-measured-stability` lines and the
  `measured_acceptance.py` reference (that module was the run-1
  over-reach, never landed); point at `registry.py` and add the
  `promotion.json` = `AcceptedStabilityFixtureRecord` role line.

---

## 7. Verification gate before declaring done

```bash
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
.venv/bin/ruff check kayakgen/ tests/
```
All green + the GZ/evaluator suite unchanged. Then run the standard
`/code-review` (or a fresh 2-lane claude+codex build-review run) over
the CLI/web diff before merge.

---

## 8. What is intentionally NOT in scope

- **Promoting a real measured fixture.** The pipeline accepts a fixture
  *when one exists*; the first real promotion stays gated on D007/D014
  physical rig data. The RFC 0043/0056 status lines already say this.
- **Per-heel labels / partial-acceptance granularity** (§B.3) — future
  RFC.
- **Desktop surfacing** — stays minimal per D014.
- **CFD-in-loop graduation to `first_class`** — needs the CFD half too
  (RFC 0058 §C.5); stage 4 lands only the analytical half.
