author: synthesizer-claude-opus-4.7-001

workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
role: synthesizer
lane: claude

# DESIGN_SYNTHESIS — RFC 0043 stage 4 stability-rig pipeline

The agy lane was removed before the design phase (commits
a4dee37 → 7a64011); this synthesis converges the two surviving
panel designs (`artifacts/design/claude/DESIGN.md`,
`artifacts/design/codex/DESIGN.md`).

## 1. Where the panel converged

- **1.1 RFC 0058 stage-1/2/3 surface is canonical.** Both
  panels build on the landed `kayakgen stability` ingest /
  promote / accept-fit / residual-plot commands. Claude §A;
  codex §Position.
- **1.2 No new `ClaimState` literal.** Flip is on
  `GeneratedBodyGZCurve.result_semantics`
  (`unvalidated_hydrostatic_comparison` →
  `validated_hydrostatic_comparison`); top-level `claim_state`
  stays `raw_unvalidated`. Claude §C; codex §C.
- **1.3 Strict threshold defaults.** Both panels adopt
  `accepted_fit.py::_strict_thresholds` verbatim
  (`rmse_m ≤ 0.005`, `mape_fraction ≤ 0.05`,
  `max_error_m ≤ 0.01`, `coverage_fraction ≥ 0.9`). Claude §B
  gate 5; codex §B.
- **1.4 Three call sites swap from constant to loaded
  registry.** `evaluator.py:387`,
  `generate_frontier_view.py:568`,
  `generate_spec_form.py:897`. Claude §C; codex §C.
- **1.5 SHA-256 hash binding.** SHA-256 of the canonical
  `MeasuredStabilityFixture` manifest is the binding token;
  refusal is `fixture_sha256_mismatch`. Claude §B gate 2;
  codex §B.
- **1.6 No physical-rig data dependency.** Deterministic
  in-test factories; D007/D014 stays independent.
- **1.7 Desktop chip stays minimal.** Per D014.
- **1.8 Generate-panel `first_class` graduation.** Opens only
  when both analytical AND CFD-in-loop accepted fits cover the
  hull; stage 4 lands the analytical half.
- **1.9 USER_GUIDE.md** gains a measured-stability subsection.

## 2. Where the panel diverged

### OQ-1. CLI sub-app naming and SOURCES.md mismatch

**Issue.** SOURCES.md prescribes `kayakgen calibration
ingest-measured-stability` / `accept-measured-stability`; the
landed RFC 0058 stages 1-3 surface is `kayakgen stability ...`.

**Panel.** claude: reuse stability-only, update SOURCES.md.
codex: stability + calibration aliases.

**Chosen.** Claude's stability-only surface.

**Rejected.** Codex aliases create split vocabulary: same write
path under two command names. SOURCES.md verbatim would fork
the ingest path and violate SOURCES.md's own "no new vocabulary"
line.

### OQ-2. Promotion-packet on-disk location

**Panel.** claude: co-locate at
`data/stability/fixtures/<fixture_id>/promotion.json`. codex:
pass via `--packet` flag.

**Chosen.** Claude's on-disk co-location.

**Rejected.** Flag-only leaves no recoverable on-disk
acceptance state; loader cannot verify provenance without
re-presenting the packet every call. Structural defect:
non-recoverable acceptance state.

### OQ-3. Registry shape

**Panel.** claude: scan `<root>/*.json` + mtime memoize. codex:
`index.json` + operator `rebuild-fit-index`.

**Chosen.** Claude's scan-on-load.

**Rejected.** Index file is a second source of truth that
drifts against the directory at single-digit fit counts.

### OQ-4. `claim-status` introspection command

**Panel.** claude: add it. codex: omit.

**Chosen.** Add it.

**Rejected.** Without `claim-status`, registry state is
observable only as an evaluator side-effect — registry health
has no direct read surface.

### OQ-5. `--fixture-id` required vs autoresolve

**Panel.** claude: required. codex: implicit via fit record's
`fixtures[]` list.

**Chosen.** Required.

**Rejected.** Autoresolve invites a record whose `fixtures[0]`
cites a drifted path; acceptance binding loses its provenance
guarantee.

### OQ-6. `analytical_evaluator_version` gate

**Panel.** claude: no gate. codex:
`evaluator_version_mismatch`.

**Chosen.** Codex's gate.

**Rejected.** A fit accepted against evaluator v1 silently
keeps flipping when evaluator graduates to v2 with different
`(θ, GZ)` shape — silent stale-fit reuse across generations.

### OQ-7. Accepted-fixture artifact (load-bearing)

**Issue.** The synthesis prompt encodes a load-bearing
threat-model boundary: the accepted fixture must be a separate,
hash-bound artifact, not a flag-flip in place.

**Panel.** claude: `StabilityFitRecord` is the acceptance
artifact; `intended_use` flips on the manifest. codex:
`StabilityFitRecord` + `kind`; packet not necessarily
persisted.

**Chosen.** Neither panel position satisfies the threat model.
Synthesis adopts a third disposition: persist the
`StabilityFixturePromotionPacket` at
`data/stability/fixtures/<fixture_id>/promotion.json` as the
canonical `AcceptedStabilityFixtureRecord`. The
`MeasuredStabilityFixture.intended_use` field becomes a hint;
the registry loader uses `promotion.json` as the source of
truth for acceptance.

**Rejected.** Claude in-place flag flip breaks the audit
trail — reading `intended_use` from a mutable manifest cannot
prove provenance. Codex flag-only packet has no persisted
record, so acceptance is asserted by the fit record rather than
proved by an independent reviewed artifact.

**Open question carry-forward.** Reviewers may require a thin
pydantic wrapper (packet + manifest hash + `accepted_at`) as a
distinct sibling type. Synthesizer: no wrapper.

### OQ-8. `strict=False` + `accepted` combination

**Panel.** claude: loadable but never flips. codex: allow
`strict=False` only on `acceptance_verdict="rejected"`.

**Chosen.** Claude's non-flipping semantics, narrowed by
codex's rule: `strict=False` + `accepted` is refused at
acceptance time with
`strict_check_skipped_blocks_acceptance`. Any `strict=False`
fit on disk is loaded for inspection but does not flip.

**Rejected.** Claude flip-blind loadable would let "accepted"
lose its threshold guarantee.

## 3. Final accepted design

The implementer reads this section linearly and turns it into
code. The five surfaces A-E below specify exactly what the
implementer builds. Illustrative fenced blocks are sketches, not
finished modules; the implementer authors the real code under
their own write_scope.

### A. CLI shape

The canonical sub-app is `kayakgen stability`; no aliases under
`kayakgen calibration` (which remains resistance-only).

#### A.1 `ingest-rig-run` (already landed)

Validates an RFC 0056 `MeasuredStabilityFixture` JSON and
writes `data/stability/fixtures/<fixture_id>/manifest.json`.
Implementer makes no behavior change. The manifest is
**immutable on disk after first write**: subsequent
`promote-fixture` calls do NOT mutate `intended_use` in place.

#### A.2 `promote-fixture` (extended)

```bash
kayakgen stability promote-fixture <fixture_id> \
  --packet <promotion_packet.json>
```

Validates the `StabilityFixturePromotionPacket`, checks
`fixture_ref.fixture_sha256` matches the on-disk manifest, and
writes the packet **as-is** to
`data/stability/fixtures/<fixture_id>/promotion.json`. Does NOT
mutate the manifest. This file is the
`AcceptedStabilityFixtureRecord` per §B.

#### A.3 `accept-fit` (extended)

```bash
kayakgen stability accept-fit \
  --fit-record path/to/fit_record.json \
  --fixture-id alpha-2026-05 \
  --out data/stability/fits/<fit_id>.json
```

The `--fixture-id` flag is **required, no default**. The
command resolves `data/stability/fixtures/<fixture_id>/`,
validates the co-located accepted promotion packet, hashes the
manifest's canonical bytes, and refuses with a §B token. Output
is a `StabilityFitRecord` dump with
`acceptance_verdict="accepted"` and `strict=True`.

**Breaking-flag note.** This replaces the RFC 0058 stages 1-3
`accept-fit <path> --packet <p>` signature (positional → flag;
`--packet` removed; `--fixture-id` and `--out` required). The
implementer's PR sweeps in-tree callsites and the Typer error
path names `--packet` as removed with a pointer to
`--fixture-id`.

#### A.4 `claim-status <hull>` (new)

```bash
kayakgen stability claim-status hull.json [--fits-root DIR] [--debug]
```

Read-only. Emits one JSON line:

```json
{
  "hull_class": "sea_kayak",
  "design_hash": "abcdef...",
  "claim_label": "validated_hydrostatic_comparison",
  "covering_fit_id": "stability-fit-001",
  "covering_fit_id_skipped": null,
  "fits_root": "data/stability/fits",
  "fits_loaded": 1,
  "dropped_fit_count": 0
}
```

`dropped_fit_count > 0` signals the operator to re-run with
`--debug`, which adds a `diagnostics` list naming each dropped
fit and its `REASON_*` code.

#### A.5 `kayakgen stability residual-plot` (already landed)

Implementer makes no behavior change.

### B. Acceptance-gate criteria

The acceptance gates are the **load-bearing safety surface** for
the claim-state flip. The implementer encodes them in
`kayakgen/eval/stability/registry.py` (new module) and reuses
existing validators in `accepted_fit.py` and `measured_fixture.py`.

#### B.1 The `AcceptedStabilityFixtureRecord` boundary

The threat-model review established that the accepted
measured-stability fixture is a **separate, hash-bound
acceptance artifact** — sibling to RFC 0054's
`AcceptedFitRecord`. It is NOT a flag flipped in place on the
manifest.

The canonical on-disk form is the persisted
`StabilityFixturePromotionPacket` at
`data/stability/fixtures/<fixture_id>/promotion.json`, whose
`fixture_ref.fixture_sha256` hash-binds it to the manifest at
`data/stability/fixtures/<fixture_id>/manifest.json`. The
on-disk role is `AcceptedStabilityFixtureRecord`; the type is
the existing `StabilityFixturePromotionPacket`. The
`MeasuredStabilityFixture.intended_use` field is a hint only;
the loader uses `promotion.json` as the source of truth.

If a reviewer requires a distinct pydantic class, the
implementer adds a thin wrapper in
`kayakgen/eval/stability/accepted_fixture.py` carrying
`promotion_packet`, `manifest_path`, `manifest_sha256`,
`accepted_at`. Default: no wrapper.

#### B.2 The thirteen gates (in order)

The implementer encodes the following gates in
`kayakgen/eval/stability/registry.py::load_stability_fit_registry`.
Each gate names a structured rejection-code constant defined as
a module-level `Final[str]`. A failing gate drops the fit from
the registry and records the constant in the loader's diagnostic
side-channel.

```python
REASON_FIXTURE_MANIFEST_MISSING: Final[str] = "fixture_manifest_missing"
REASON_FIXTURE_SMOOTHNESS_FAILURES: Final[str] = "fixture_smoothness_failures_nonempty"
REASON_FIXTURE_TRACE_PATH_UNRESOLVED: Final[str] = "fixture_trace_path_unresolved"
REASON_FIXTURE_BOUNDS_TOO_LOOSE: Final[str] = "fixture_declared_bounds_exceed_operator_maxima"
REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE: Final[str] = "fixture_rights_redistribution_not_authorized"
REASON_PROMOTION_PACKET_MISSING: Final[str] = "promotion_packet_missing"
REASON_FIXTURE_SHA256_MISMATCH: Final[str] = "fixture_sha256_mismatch"
REASON_FIXTURE_NOT_PROMOTED: Final[str] = "fixture_not_promoted"
REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE: Final[str] = "promotion_packet_review_incomplete"
REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE: Final[str] = "fit_record_does_not_cite_fixture"
REASON_VALID_HEEL_RANGE_DISJOINT: Final[str] = "valid_heel_range_disjoint"
REASON_EVALUATOR_VERSION_MISMATCH: Final[str] = "evaluator_version_mismatch"
REASON_STRICT_CHECK_SKIPPED: Final[str] = "strict_check_skipped_blocks_acceptance"
REASON_FIT_METRICS_OUT_OF_THRESHOLDS: Final[str] = "stability_fit_metrics_outside_default_thresholds"

# Operator-controlled maxima — outside the manifest under review.
OPERATOR_MAX_CALIBRATION_DRIFT_BOUND_FRACTION: Final[float] = 0.005
OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION: Final[float] = 0.03
```

Gate order (short-circuit on first failure):

1. **Manifest exists.**
   `data/stability/fixtures/<fixture_id>/manifest.json` resolves
   and parses as `MeasuredStabilityFixture`.
   → `REASON_FIXTURE_MANIFEST_MISSING`.
2. **Smoothness-failures empty.** Schema accepts
   `MeasuredStabilityFixture` with non-empty
   `free_equilibrium_trace.smoothness_failures`; the loader
   hardens this.
   → `REASON_FIXTURE_SMOOTHNESS_FAILURES`.
3. **Trace paths resolvable.** `calibration_trace.{pre,post}_run_trace_path`
   and `runs_dir` (when set) resolve to existing files /
   directory. Schema treats them as strings; the loader treats
   them as evidence. → `REASON_FIXTURE_TRACE_PATH_UNRESOLVED`.
3a. **Operator-maxima bounds check.** Manifest's
    `calibration_trace.drift_bound_fraction` and
    `hysteresis_bound.bound_fraction` are AUTHORED on the
    manifest under review (`measured_fixture.py:126,185`); a
    self-authored manifest could widen its own bounds and pass
    schema validation. The loader rejects the fit unless both
    fields are ≤ the operator-controlled constants above.
    → `REASON_FIXTURE_BOUNDS_TOO_LOOSE`.
3b. **Rights redistribution authorized.** The schema requires
    a `RightsChecklist` but does not block downstream
    comparison when `redistribution_authorized=False`. The
    loader rejects the fit unless
    `manifest.rights.redistribution_authorized=True`.
    → `REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE`.
4. **Promotion packet exists.**
   `data/stability/fixtures/<fixture_id>/promotion.json` resolves
   and parses as `StabilityFixturePromotionPacket`.
   → `REASON_PROMOTION_PACKET_MISSING`.
5. **Packet hash-binds the manifest.**
   `fixture_ref.fixture_sha256` equals SHA-256 of the on-disk
   manifest's canonical JSON bytes.
   → `REASON_FIXTURE_SHA256_MISMATCH`.
6. **`promotion_target == "measured_stability_fixture"`.**
   → `REASON_FIXTURE_NOT_PROMOTED`.
7. **Five reviews all accepted + `rig_design_match=True` +
   `rejection_reasons=[]`.** Schema enforces this at packet
   construction; loader re-checks because on-disk bytes may
   have been edited post-sign.
   → `REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE`.
8. **Fit cites this fixture.** Some `FixtureRef` in
   `StabilityFitRecord.fixtures` matches both
   `fixture_id` and `fixture_sha256`.
   → `REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE`.
9. **Heel-range overlap.** Fit's `valid_heel_range_deg`
   intersects fixture's. → `REASON_VALID_HEEL_RANGE_DISJOINT`.
10. **Evaluator-version match.**
    `analytical_evaluator_version` equals
    `kayakgen.eval.stability.evaluator.ANALYTICAL_EVALUATOR_VERSION`
    (implementer adds the constant).
    → `REASON_EVALUATOR_VERSION_MISMATCH`.
11. **Strict acceptance.** `acceptance_verdict="accepted"` AND
    `strict=True`. `strict=False`+`accepted` drops with
    `REASON_STRICT_CHECK_SKIPPED`. Below-threshold metrics on a
    `strict=True` record are blocked at construction by
    `_strict_thresholds`; the loader surfaces
    `REASON_FIT_METRICS_OUT_OF_THRESHOLDS` only when bytes were
    tampered post-acceptance.

Gates 2, 3, 3a, and 3b are threat-model hardenings: the
`MeasuredStabilityFixture` schema validators are necessary but
not load-bearing for acceptance — the loader cross-checks
evidence (smoothness, trace path resolution, declared bounds,
rights) using operator-controlled inputs the schema does not
gate. Hull-family envelope mismatch is a **hard non-flip** (not
a refusal): the fit stays loaded; the resolver simply does not
flip outside `hull_family_scope`. This is the existing
`resolve_analytical_claim_label` behavior
(`high_angle_contracts.py:60-79`).

**Fixture presence does not flip the label.** A
`promotion.json` alone never flips `result_semantics`. The
flip requires the full chain: manifest + accepted promotion
packet + strict-accepted `StabilityFitRecord` whose
`analytical_evaluator_version` matches the runtime, with
`hull_family_scope` covering the hull. §D encodes this.

Diagnostic shape:

```python
@dataclass(frozen=True, slots=True)
class FitRejectionDiagnostic:
    fit_id: str
    fit_path: Path
    reason_code: str
    detail: str
```

A `with_diagnostics=True` mode on the loader returns
`(records, diagnostics)`; default mode returns `records` only.

#### B.3 Partial acceptance

A fit accepted on a narrower `valid_heel_range_deg` than the
fixture's full sweep is loadable; the flip is label-wide per
hull family (no per-heel labels in stage 4 — that is future
RFC scope).

### C. Claim-state resolution

#### C.1 The flip semantics

The flip is on `GeneratedBodyGZCurve.result_semantics` from
`unvalidated_hydrostatic_comparison` to
`validated_hydrostatic_comparison`, as already defined in
`kayakgen/eval/stability/high_angle_contracts.py:24-79`. The
RFC 0025 top-level `claim_state` stays `raw_unvalidated`. No
new literals.

#### C.2 The registry loader

New module `kayakgen/eval/stability/registry.py` exposes
`load_stability_fit_registry(root=None, *,
with_diagnostics=False)` returning a tuple of gate-passing
accepted fits (sorted by `fit_id`), optionally paired with a
diagnostic tuple. `root` resolution order: explicit argument >
`KAYAKGEN_STABILITY_FITS_ROOT` env > CWD-relative
`data/stability/fits` default. Missing root → empty registry.
Memoized by `(root_path, directory_stat_mtime)`.

#### C.3 Provenance verification

A flipped label can be traced back through
`fit → accepted_fixture_record (promotion.json) → manifest`
without trusting any mutable flag. The §B.2 gate sequence is
the RFC 0027/0025 audit trail.

#### C.4 The three call-site swaps

```python
# kayakgen/eval/stability/evaluator.py:387 — was:
#   resolve_analytical_claim_label(hull, fit_registry=EMPTY_STABILITY_FIT_REGISTRY)
# becomes:
result_semantics = resolve_analytical_claim_label(
    hull, fit_registry=load_stability_fit_registry()
)

# kayakgen/ui/web/generate_frontier_view.py:568 — same swap.
# kayakgen/ui/web/generate_spec_form.py:897 — same swap.
```

The implementer threads the loaded registry through one
module-level lazy accessor per call site rather than calling
`load_stability_fit_registry()` per hull. Each web request
(`generate_frontier_view`, `generate_spec_form`) re-stats the
fits-directory mtime; only when the mtime advances is the
registry rebuilt. Operators who run `promote-fixture` or
`accept-fit` mid-session see the new state on the next web
request without restarting the Trame process.

#### C.5 UI propagation

The frontier color tokens
`unvalidated_hydrostatic_comparison_color` /
`validated_hydrostatic_comparison_color` already exist; no new
tokens. Generate-panel `cfd_in_loop_evaluator_status` graduates
to `first_class` only when both analytical and CFD-in-loop
accepted fits cover the hull; stage 4 lands the analytical
half. Desktop stays minimal per D014.

### D. Test surface

Three new test files. All tests build deterministic in-test
fixtures; no physical rig data dependency. A single shared
factory in `tests/conftest.py` named
`make_stability_acceptance_triple(*, fixture_id="fxt-001",
hull_class="sea_kayak", design_hash="aa...", scan_hash="ab...",
evaluator_version="rfc-0043-generated-body-v1", strict=True)`
produces a triple `(MeasuredStabilityFixture,
StabilityFixturePromotionPacket, StabilityFitRecord)` sharing
fixture id + design hash + scan hash + evaluator version. The
tamper / mismatch / version-gate tests override one keyword
argument to produce the failing variant.

| File | Function | Objective |
|---|---|---|
| `tests/test_measured_stability_ingest.py` | `test_ingest_rig_run_writes_canonical_manifest` | Valid in-test fixture JSON → canonical manifest at `data/stability/fixtures/<id>/manifest.json`. |
| ″ | `test_ingest_rig_run_does_not_mutate_intended_use` | After `promote-fixture`, manifest bytes are byte-equal to the original ingest. |
| ″ | `test_ingest_rig_run_refuses_constrained_trace_promotion` | Constrained free-equilibrium trace + `intended_use=measured_stability_fixture` → `constrained_trace_blocks_promotion`. |
| ″ | `test_ingest_rig_run_refuses_rows_outside_valid_heel_range` | Schema-validator path; CLI surfaces token verbatim. |
| `tests/test_measured_stability_acceptance.py` | `test_promote_fixture_writes_accepted_fixture_record` | Valid packet + matching manifest hash → `promotion.json` lands; manifest unchanged on disk. |
| ″ | `test_promote_fixture_refuses_sha256_mismatch` | Tampered manifest bytes after packet sign → `fixture_sha256_mismatch`. |
| ″ | `test_promote_fixture_refuses_unaccepted_reviews` | Parametrised over rights, hull identity, calibration drift, hysteresis, free equilibrium → schema validator raises. |
| ″ | `test_promote_fixture_refuses_rig_design_mismatch` | `rig_design_match=False` → schema validator raises. |
| ″ | `test_accept_fit_binds_to_promoted_fixture_happy_path` | Promoted fixture + matching FixtureRef + strict in-threshold metrics → fit lands at `data/stability/fits/<fit_id>.json`. |
| ″ | `test_accept_fit_refuses_unpromoted_fixture` | Promotion-target=`validation_candidate` → `fixture_not_promoted`. |
| ″ | `test_accept_fit_refuses_missing_promotion_packet` | Manifest exists but `promotion.json` absent → `promotion_packet_missing`. |
| ″ | `test_accept_fit_refuses_evaluator_version_mismatch` | Fit's `analytical_evaluator_version` differs from runtime constant → `evaluator_version_mismatch`. |
| ″ | `test_accept_fit_refuses_disjoint_heel_range` | Fit `[10,30]` vs fixture rows `[0,5]` → `valid_heel_range_disjoint`. |
| ″ | `test_accept_fit_refuses_below_strict_thresholds` | RMSE/MAPE/max_error/coverage parametrised → schema validator raises. |
| ″ | `test_accept_fit_refuses_strict_check_skipped_with_accepted_verdict` | `strict=False` + `accepted` → `strict_check_skipped_blocks_acceptance`. |
| ″ | `test_accept_fit_writes_record_byte_stable` | Two invocations on identical inputs produce byte-equal JSON. |
| `tests/test_claim_state_measured_promotion.py` | `test_claim_label_flips_when_fit_covers_hull` | Hull matching hull_class + design hash in envelope → `validated_hydrostatic_comparison`. |
| ″ | `test_claim_label_unchanged_when_no_fit_covers_hull` | Different hull class → `unvalidated_hydrostatic_comparison`. |
| ″ | `test_claim_label_unchanged_for_strict_skipped_fit` | `strict=False` fit present but dropped; covering accepted fit absent. |
| ″ | `test_registry_loader_memoizes_until_mtime_change` | Two loads return identical tuple object; `Path(root).touch()` invalidates. |
| ″ | `test_registry_loader_skips_invalid_fit_with_diagnostic` | Corrupt fit JSON skipped; diagnostic carries the reason code. |
| ″ | `test_registry_loader_uses_env_var_then_default` | `KAYAKGEN_STABILITY_FITS_ROOT` overrides default; explicit arg overrides env. |
| ″ | `test_claim_status_command_reports_resolved_label` | CLI smoke test: `kayakgen stability claim-status hull.json --fits-root tmp/` prints expected JSON. |
| ″ | `test_evaluator_flips_result_semantics_under_loaded_registry` | Integration: `build_high_angle_gz_block` with populated `KAYAKGEN_STABILITY_FITS_ROOT` emits `result_semantics='validated_hydrostatic_comparison'`. |
| ″ | `test_generate_frontier_view_color_token_flips_under_loaded_registry` | Web integration: covered hull row shows the validated color token. |
| ″ | `test_provenance_chain_holds_under_manifest_tamper` | After promotion, tampering with manifest bytes drops the fit from the registry on next load (mtime change forces re-scan). |
| ″ | `test_claim_status_debug_lists_dropped_fit_diagnostics` | `claim-status --debug` JSON includes `diagnostics` list naming each dropped fit and its `REASON_*` code. |
| ″ | `test_registry_drops_fit_with_nonempty_smoothness_failures` | Manifest with `free_equilibrium_trace.smoothness_failures=["wobble"]` → `fixture_smoothness_failures_nonempty`. |
| ″ | `test_registry_drops_fit_with_unresolved_trace_path` | Manifest's `calibration_trace.pre_run_trace_path` points to a missing file → `fixture_trace_path_unresolved`. |
| ″ | `test_registry_drops_fit_with_loose_self_declared_bounds` | Manifest declares `drift_bound_fraction=0.05` (10× the operator max) → `fixture_declared_bounds_exceed_operator_maxima`. |
| ″ | `test_registry_drops_fit_when_redistribution_not_authorized` | Manifest's `rights.redistribution_authorized=False` → `fixture_rights_redistribution_not_authorized`. |
| ″ | `test_accepted_fixture_alone_does_not_flip_label` | A valid `promotion.json` exists but no `StabilityFitRecord` covers the hull → `result_semantics` stays `unvalidated_hydrostatic_comparison`. |
| ″ | `test_full_chain_required_for_flip` | Drop any one of {manifest, promotion.json, fit record, strict acceptance, evaluator-version match, hull-family coverage} → label does not flip. Parametrised over each link. |

### E. Operator-facing copy

#### E.1 `kayakgen stability --help` (after additions)

```
Usage: kayakgen stability [OPTIONS] COMMAND [ARGS]...

  RFC 0043 stage 4 / RFC 0058 stability-rig pipeline: ingest,
  promote, accept, inspect measured-stability fixtures and the
  accepted-fit registry that flips the high-angle GZ claim label.

Commands:
  accept-fit       Validate a stability-fit record and persist
                   canonical JSON.
  claim-status     Print the resolved analytical high-angle GZ
                   claim label for a hull under the current
                   accepted-fit registry.
  ingest-rig-run   Validate a measured-stability fixture
                   manifest and persist canonical JSON.
  promote-fixture  Persist a validated promotion packet alongside
                   a fixture manifest.
  residual-plot    Write an RFC 0058 stage-3 SVG residual
                   placeholder.
```

#### E.2 `USER_GUIDE.md` — append under the existing RFC 0058 subsection

````markdown
#### Stage 4 — accepted-fit registry and label flip

A `StabilityFitRecord` written under `data/stability/fits/` and
bound to an accepted `MeasuredStabilityFixture` flips the
analytical high-angle GZ claim label from
`unvalidated_hydrostatic_comparison` to
`validated_hydrostatic_comparison` for hulls inside the fit's
`hull_family_scope`. The flip propagates to the high-angle GZ
JSON output, the web Generate frontier colour token, and the
Generate panel `cfd_in_loop_evaluator_status` admonition.

Acceptance produces three on-disk artifacts:

1. `data/stability/fixtures/<fixture_id>/manifest.json` — the
   immutable `MeasuredStabilityFixture` JSON.
2. `data/stability/fixtures/<fixture_id>/promotion.json` — the
   `AcceptedStabilityFixtureRecord` (the persisted
   `StabilityFixturePromotionPacket` whose
   `fixture_ref.fixture_sha256` hash-binds it to the manifest).
   **The manifest's `intended_use` field is a hint only; the
   canonical acceptance signal is `promotion.json` with
   `promotion_target = "measured_stability_fixture"`.**
3. `data/stability/fits/<fit_id>.json` — the
   `StabilityFitRecord` whose `fixtures[].fixture_sha256`
   re-binds to the same manifest bytes.

Inspect the resolution without running the evaluator:

```bash
kayakgen stability claim-status hull.json --fits-root data/stability/fits
```

Override the registry root with `KAYAKGEN_STABILITY_FITS_ROOT`.
Fits failing any §B gate (below threshold, `strict=False`,
tampered, evaluator-version mismatch, rights not authorized, …)
are dropped at load time and do not flip the label.
````

#### E.3 Refusal copy

The CLI emits one structured JSON line per refusal:

```json
{
  "ok": false,
  "code": "fixture_sha256_mismatch",
  "fixture_id": "msf-2026-001",
  "details": {
    "expected_sha256": "abcdef...",
    "actual_sha256": "012345..."
  },
  "next_action": "re-run `kayakgen stability ingest-rig-run` if the manifest changed intentionally, or re-sign the promotion packet against the new bytes."
}
```

Every `REASON_*` constant has a fixed `next_action` template
encoded as a module-level
`REASON_NEXT_ACTION: Final[Mapping[str, str]]` dict in
`registry.py`:

| Reason | `next_action` |
|---|---|
| `fixture_manifest_missing` | run `ingest-rig-run` first. |
| `fixture_smoothness_failures_nonempty` | re-run the sweep with smoother heel actuation. |
| `fixture_trace_path_unresolved` | correct the manifest's trace paths or stage the files. |
| `fixture_declared_bounds_exceed_operator_maxima` | tighten the bound or escalate the operator threshold via RFC. |
| `fixture_rights_redistribution_not_authorized` | resolve rights with the source author. |
| `promotion_packet_missing` | run `promote-fixture --packet` first. |
| `fixture_sha256_mismatch` | re-ingest if manifest changed intentionally, else re-sign the packet. |
| `fixture_not_promoted` | packet's `promotion_target` ≠ `measured_stability_fixture`; revise and re-sign. |
| `promotion_packet_review_incomplete` | one of the five required reviews is not accepted; re-sign. |
| `fit_record_does_not_cite_fixture` | pass `--fixture-id` matching a `fixtures[].fixture_id`. |
| `valid_heel_range_disjoint` | re-fit on a heel range covering both fixture and fit. |
| `evaluator_version_mismatch` | runtime evaluator changed; re-run `accept-fit` to record the new version. |
| `strict_check_skipped_blocks_acceptance` | re-fit with `strict=True`. |
| `stability_fit_metrics_outside_default_thresholds` | tighten the fit, or accept with `strict=False` for inspection only. |

#### E.4 SOURCES.md update

The implementer's PR includes an edit to
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md`
that:

- Removes the obsolete `kayakgen calibration ingest-measured-stability`
  / `accept-measured-stability` lines and the
  `kayakgen/eval/stability/measured_acceptance.py` reference.
- Replaces them with the canonical `kayakgen stability` surface and
  the new `kayakgen/eval/stability/registry.py` module reference.
- Adds the `AcceptedStabilityFixtureRecord` role line for
  `data/stability/fixtures/<fixture_id>/promotion.json`.
- Moves the USER_GUIDE placement line from "under the existing
  `## Calibration` heading" to "under the existing RFC 0058
  stability subsection".

#### E.5 Upgrade note

Fixtures whose `manifest.json` was written under the RFC 0058
stages 1-3 `promote-fixture` (which mutated `intended_use` in
place) are silently honored: the new loader does not read
`intended_use` from the manifest. Operators should treat the
field as a hint; `promotion.json` is canonical. The
implementer's PR does NOT mass-rewrite existing manifests.

## 4. Open Questions

OQ-1 through OQ-8 are the divergence carry-forwards from §2;
each carries the synthesizer's chosen disposition above.

**Revision-cycle status (attempt 3).** Attempt 2 addressed
ergonomics_dx findings + first-round threat-model gates
(smoothness, trace-path resolution, `intended_use`-as-hint).
Attempt 3 adds gate 3a (operator-controlled drift/hysteresis
maxima outside the manifest), gate 3b (rights-redistribution
authorization), the §B.2 "fixture presence does not flip the
label" callout with two parametrised tests, and a §5
out-of-scope callout for codex's resistance-side findings
(opaque-token bypass + `AcceptedFitRecord` fixture-binding).

Non-divergence open questions:

- **OQ-A. Registry growth path.** Synthesizer disposes: defer
  RFC 0049 `ArtifactStore` + `SqliteIndex` migration to a
  future RFC; stage 4 stays scan-based.
- **OQ-B. Cache-invalidation granularity.** Synthesizer
  disposes: directory `st_mtime` is adequate at the expected
  fit count; per-file mtime + content hash is overkill.
- **OQ-C. `claim-status` hash-only input.** Synthesizer
  disposes: defer to a future RFC; hull JSON only for now.

## 5. What this synthesis explicitly does NOT do

- **No physical rig acquisition.** D006/D007/D014 stays
  operator-driven.
- **No flip of RFC 0043 / RFC 0056 Status.** Doc-only flip is
  a parent-agent commit after workflow convergence.
- **No CFD or resistance touches.** Stability subdomain only.
- **No new `ClaimState` literal or `SourceUse` vocabulary.**
- **No `kayakgen calibration` aliases.** SOURCES.md is updated.
- **No mutation of `intended_use` in place.** Manifest is
  immutable after ingest; acceptance is a separate record.
- **No per-heel claim labels.** Partial heel-range acceptance
  flips hull-family-wide; per-heel is future RFC scope.
- **No `kind` discriminator on `StabilityFitRecord`.** Schema
  stays as landed; CFD-in-loop adds its own record type later.
- **No index file or CFD-in-loop fit-record schema** in stage 4.
- **No resistance-side fixes.** Two threat-model findings from
  the codex review concern resistance-only paths and are out of
  scope for stage 4: (a)
  `kayakgen/eval/calibration/__init__.py:416`'s
  `_validate_accepted_fit_ref_on_disk()` admits opaque tokens
  for resistance `calibration_fixture` reviews;
  (b) `AcceptedFitRecord` (RFC 0054) carries no `fixture_id`,
  so a resistance accepted-fit could be filed under the wrong
  fixture's directory. The implementer adds a DECISION_LOG.md
  follow-up row flagging both as future RFC scope; the stage-4
  PR does not patch them.
