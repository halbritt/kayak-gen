---
author: designer-claude-opus-4.7-001
workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
role: designer
lane: claude
---

# DESIGN — RFC 0043/0056 stage-4 promotion pipeline (claude lane)

## Reading of the problem

RFC 0058 stages 1-3 already landed most of the surface SOURCES.md asks
this workflow to design:

- `kayakgen/eval/stability/measured_fixture.py` — the
  `MeasuredStabilityFixture` schema (RFC 0056).
- `kayakgen/eval/stability/accepted_fit.py` — `FixtureRef`,
  `HullFamilyScope`, `StabilityFitMetrics`, `ReviewerSignature`,
  `StabilityFitRecord`, `StabilityFixturePromotionPacket`, and the
  strict threshold defaults.
- `kayakgen/cli/stability_cli.py` — four working subcommands:
  `ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`,
  writing into `data/stability/fixtures/` and `data/stability/fits/`.
- `kayakgen/eval/stability/high_angle_contracts.py` —
  `resolve_analytical_claim_label(hull, fit_registry)` and the
  `AnalyticalClaimLabel` literal pair already in place.
- `kayakgen/eval/stability/evaluator.py`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/generate_spec_form.py` — three call sites already
  injecting `EMPTY_STABILITY_FIT_REGISTRY`.

SOURCES.md was written against an older draft. It asks for
`kayakgen calibration ingest-measured-stability` /
`accept-measured-stability`, an `AcceptedStabilityFixtureRecord`, and a
new `kayakgen/eval/stability/measured_acceptance.py` module. Standing
those up alongside the landed `kayakgen stability ...` surface would
fork the ingest path. The defensible reading is that **stage 4 is
exclusively the registry-loading and claim-flip wiring on top of the
landed RFC 0058 stage 1-3 surface, plus the binding gate from
`StabilityFitRecord` → on-disk `MeasuredStabilityFixture`**. No new
sub-app, no parallel record schema, no new `ClaimState` literal.

The four design pieces below answer the prompt against that reading.

## A. CLI shape

### Reuse, do not duplicate

`kayakgen stability ingest-rig-run`, `promote-fixture`, `accept-fit`,
and `residual-plot` stay as the ingest/acceptance surface.
`kayakgen calibration` stays the resistance-side surface only;
RFC 0027 is the resistance parallel and the two sub-apps are
deliberately separate domains. Adding `*-measured-stability` commands
under `calibration` would force operators to remember which
calibration sub-app owns stability data — the existing split is
clearer.

### One extra acceptance flag and one new read-side command

#### `kayakgen stability accept-fit` — extend with fixture binding

Add a required `--fixture-id` option that resolves
`data/stability/fixtures/<fixture_id>/manifest.json`, hashes its
canonical JSON, and refuses the fit unless:

- a `FixtureRef` in the record points at that path,
- the recorded `fixture_sha256` matches the on-disk content,
- the manifest's `intended_use == "measured_stability_fixture"`.

The flag is required (no default) so an acceptance call never
implicitly binds to whatever happens to be on disk.

```bash
kayakgen stability accept-fit \
  --fit-record path/to/fit_record.json \
  --fixture-id alpha-2026-05 \
  --out data/stability/fits/<fit_id>.json
```

Structured refusal tokens emitted to stderr:
`fixture_manifest_missing`, `fixture_sha256_mismatch`,
`fixture_not_promoted`, `fit_record_does_not_cite_fixture`,
`fit_metrics_outside_default_thresholds` (already raised by the
schema), `accepted_at_missing_for_accepted_verdict` (schema).

#### `kayakgen stability claim-status <hull>` — new read command

Print which analytical claim label a hull resolves to under the
current on-disk registry, and which fit (if any) covers it:

```bash
kayakgen stability claim-status hull.json [--fits-root DIR]
```

Emits a single JSON line:

```json
{
  "hull_class": "sea_kayak",
  "design_hash": "abcdef…",
  "claim_label": "unvalidated_hydrostatic_comparison",
  "covering_fit_id": null,
  "fits_root": "data/stability/fits",
  "fits_loaded": 0
}
```

When the registry has an accepted fit whose `hull_family_scope`
covers the hull, `claim_label` reads `validated_hydrostatic_comparison`
and `covering_fit_id` names it. The command never writes to disk.

This is the only surface where the operator can directly inspect the
flip without invoking the full evaluator; it parallels
`kayakgen runs evidence` for CFD readiness.

## B. Acceptance-gate criteria

### Where the gates live

Keep all validator logic inside the existing
`kayakgen/eval/stability/accepted_fit.py` and a new sibling helper
`kayakgen/eval/stability/registry.py` (loader + binding check). No
`measured_acceptance.py` module — the acceptance gates are already
on `StabilityFitRecord` and `StabilityFixturePromotionPacket`. The
*on-disk* binding check is the only new logic.

### The six gates (cited)

1. **Fixture manifest exists** — `FixtureRef.fixture_path` resolves
   to a readable file (`fixture_manifest_missing`).
2. **Fixture hash matches** — SHA-256 of canonical JSON
   (`fixture_sha256`) equals the recorded value
   (`fixture_sha256_mismatch`). Mirrors RFC 0054 D035 token shape
   (`accepted_fit_unparseable` / `accepted_fit_unresolved`).
3. **Fixture is promoted** — `MeasuredStabilityFixture.intended_use
   == "measured_stability_fixture"` (RFC 0056 acceptance criteria;
   `fixture_not_promoted`).
4. **Fixture passed every review** — there must be an accepted
   `StabilityFixturePromotionPacket` co-located at
   `data/stability/fixtures/<fixture_id>/promotion.json` with all
   five reviews `accepted` and `rig_design_match: True`. The packet
   validator already enforces this when written; the registry
   re-checks on load (`promotion_packet_missing`,
   `promotion_packet_review_incomplete`).
5. **Fit metrics within strict defaults** — already enforced by
   `StabilityFitRecord._strict_thresholds`. The CLI default is
   `strict=True` and refuses below-threshold fits with the existing
   `stability_fit_metrics_outside_default_thresholds` token. A
   `strict=False` record carries `strict_check_skipped` and is
   loadable but capped at `intended_use=validation_candidate`
   semantics for label resolution (see C).
6. **Heel range overlap** — the fixture's
   `valid_heel_range_deg` must overlap the fit's
   `valid_heel_range_deg` (token `valid_heel_range_disjoint`).
   The on-disk fixture validator already checks rows are inside the
   declared range; this gate checks the fit's claimed range is
   consistent with what the fixture actually covered.

### Partial acceptance

A fit accepted on a narrower `valid_heel_range_deg` than the
fixture's full sweep is loadable; `resolve_analytical_claim_label`
treats the flip as label-wide (per hull family). A future RFC may
introduce per-heel labels; this design doesn't anticipate that.

A `strict=False` fit is loadable but **does not flip the label**.
It surfaces in `claim-status --debug` as `covering_fit_id_skipped` so
the operator can see that the fit was found but not used. This is
the only partial-acceptance state.

### `AcceptedStabilityFixtureRecord` is `StabilityFitRecord`

The on-disk artifact under `data/stability/fits/<fit_id>.json` is a
canonical `StabilityFitRecord` dump (the existing CLI writes this
shape). No second record type is introduced. The
RFC 0054 `AcceptedFitRecord` is resistance-only; the stability
parallel was always `StabilityFitRecord`.

## C. Claim-state resolution

### No new `ClaimState` literal

RFC 0025/0027/0058 already define every literal the flip needs:

- `result_semantics` on `GeneratedBodyGZCurve` is an
  `AnalyticalClaimLabel`: `unvalidated_hydrostatic_comparison`
  (default) → `validated_hydrostatic_comparison` (post-flip).
- The top-level RFC 0025 `claim_state` literal on a GZ result stays
  `raw_unvalidated` (the high-angle GZ block is uncalibrated
  comparative output by RFC 0043 design); the *RFC 0058 analytical
  comparison label* is what flips, not the RFC 0025 state.

This matches the SOURCES.md instruction to reuse the existing
acceptance grammar and the D039 disposition that defaults stay
byte-stable.

### Lookup rule

A new module `kayakgen/eval/stability/registry.py` exposes:

```python
def load_stability_fit_registry(
    root: Path | str | None = None,
) -> tuple[StabilityFitRecord, ...]:
    """Return validated, strictly-accepted fits visible at ``root``.

    ``root`` defaults to ``data/stability/fits`` resolved from
    ``KAYAKGEN_STABILITY_FITS_ROOT`` or CWD. Returns
    ``EMPTY_STABILITY_FIT_REGISTRY`` (the canonical empty constant)
    if the directory is missing — the current default.
    """
```

The loader:

- enumerates `<root>/*.json`,
- validates each file as `StabilityFitRecord`,
- runs the six gates from B against the co-located fixture/packet,
- drops a fit that fails any gate, recording the rejection reason in
  a side-channel returned via `load_stability_fit_registry(...,
  with_diagnostics=True)`,
- returns the surviving fits in deterministic order (sorted by
  `fit_id`).

The three call sites (`evaluator.py:387`,
`generate_frontier_view.py:568`, `generate_spec_form.py:897`) switch
from the literal `EMPTY_STABILITY_FIT_REGISTRY` to
`load_stability_fit_registry()` cached on a module-level lazy
singleton keyed by root path + `stat.st_mtime` of the directory. A
new env var `KAYAKGEN_STABILITY_FITS_ROOT` overrides the default for
operators staging a candidate registry without modifying the
repository root.

### Index vs scan

A separate index file is **not** introduced. Scan-on-load is
acceptable because:

- the registry is small in practice (single-digit fit count at
  stage 4 — D007/D014 still gates the first promotion);
- the directory is already gitignored, so the only writers are the
  CLI commands designed in A;
- mtime-keyed memoization eliminates repeat parses inside one
  process.

If a later RFC needs cross-run inspection, RFC 0049's
`ArtifactStore` + `SqliteIndex` is the right home (mirror the
resistance fixture pattern). That is out of scope here.

### UI propagation

`generate_frontier_view._resolve_claim_label_color_token` already
calls `resolve_analytical_claim_label(hull, fit_registry)`. Swapping
the default registry argument makes the existing
`unvalidated_hydrostatic_comparison_color` /
`validated_hydrostatic_comparison_color` token plumbing flip
automatically per row. No further frontier or chip change is needed.

`generate_spec_form.py:897` does the same for the panel's
`cfd_in_loop_evaluator_status` admonition; the RFC 0058 stage-3
`first_class` graduation rule (analytical + CFD-in-loop both
accepted) automatically opens once the analytical side flips.

Desktop stays minimal per D014.

## D. Test surface

| Test file | Function | Objective |
|---|---|---|
| `tests/test_measured_stability_acceptance.py` | `test_accept_fit_binds_to_promoted_fixture_happy_path` | Promoted fixture + matching FixtureRef + in-threshold metrics → fit lands at `data/stability/fits/<fit_id>.json`. |
| ″ | `test_accept_fit_refuses_unpromoted_fixture` | `intended_use=validation_candidate` raises `fixture_not_promoted`. |
| ″ | `test_accept_fit_refuses_sha256_mismatch` | Tamper with manifest bytes after promotion → `fixture_sha256_mismatch`. |
| ″ | `test_accept_fit_refuses_missing_manifest` | `--fixture-id` resolves to absent path → `fixture_manifest_missing`. |
| ″ | `test_accept_fit_refuses_unaccepted_promotion_packet` | Packet with `promotion_target='validation_candidate'` → `promotion_packet_review_incomplete`. |
| ″ | `test_accept_fit_refuses_disjoint_heel_range` | Fit cites `[10,30]` but fixture rows are `[0,5]` → `valid_heel_range_disjoint`. |
| ″ | `test_accept_fit_refuses_below_strict_thresholds` | Existing schema validator path; CLI surfaces token verbatim. |
| ″ | `test_accept_fit_writes_record_byte_stable` | Two invocations on identical inputs produce byte-equal JSON. |
| `tests/test_measured_stability_ingest.py` | `test_ingest_rig_run_writes_canonical_manifest` | In-test fixture JSON → canonical write at the target path. |
| ″ | `test_ingest_rig_run_refuses_constrained_trace_promotion` | Constrained free-equilibrium trace + `intended_use=measured_stability_fixture` → existing `constrained_trace_blocks_promotion`. |
| ″ | `test_ingest_rig_run_refuses_rows_outside_valid_heel_range` | Existing schema validator path; CLI surfaces token verbatim. |
| `tests/test_claim_state_measured_promotion.py` | `test_claim_label_flips_when_fit_covers_hull` | Hull with matching `hull_class` + design hash in envelope → `validated_hydrostatic_comparison`. |
| ″ | `test_claim_label_unchanged_when_no_fit_covers_hull` | Same registry, different hull class → `unvalidated_hydrostatic_comparison`. |
| ″ | `test_claim_label_unchanged_for_skipped_strict_fit` | `strict=False` fit present but not used; covered fit absent. |
| ″ | `test_registry_loader_memoizes_until_mtime_change` | Two loads return identical tuple object; touching the directory invalidates the cache. |
| ″ | `test_registry_loader_skips_invalid_fit_with_diagnostic` | Corrupt `<fit_id>.json` is skipped, diagnostic recorded, registry length unaffected. |
| ″ | `test_claim_status_command_reports_resolved_label` | CLI smoke test: `kayakgen stability claim-status hull.json --fits-root tmp/` prints the expected JSON line. |
| ″ | `test_evaluator_flips_result_semantics_under_loaded_registry` | Integration: `build_high_angle_gz_block` with a populated `KAYAKGEN_STABILITY_FITS_ROOT` emits `result_semantics='validated_hydrostatic_comparison'`. |
| ″ | `test_generate_frontier_view_color_token_flips_under_loaded_registry` | Web integration: a row whose hull is covered shows the `validated_hydrostatic_comparison_color` token. |

All tests build fixtures in-test (no physical rig data dependency,
per SOURCES). A single in-test fixture factory under
`tests/conftest.py` produces a triple
(`MeasuredStabilityFixture`, accepted `StabilityFixturePromotionPacket`,
strictly-accepted `StabilityFitRecord`) sharing fixture id + design
hash; the suite parametrises around that.

## E. Operator-facing copy

### `kayakgen stability --help` (after additions)

```
Usage: kayakgen stability [OPTIONS] COMMAND [ARGS]...

  Stability rig fixture and accepted-fit artifact writers (RFC 0058).

Commands:
  accept-fit       Validate a stability-fit record and persist canonical JSON.
  claim-status     Print the resolved analytical high-angle GZ claim label
                   for a hull under the current accepted-fit registry.
  ingest-rig-run   Validate a measured-stability fixture manifest and
                   persist canonical JSON.
  promote-fixture  Apply a validated promotion packet to a fixture manifest.
  residual-plot    Write an RFC 0058 stage-3 SVG residual placeholder.
```

### `USER_GUIDE.md` — append under the existing RFC 0058 subsection

```markdown
#### Stage 4 — accepted-fit registry and label flip

A `StabilityFitRecord` written under `data/stability/fits/` and bound to
a promoted `MeasuredStabilityFixture` flips the analytical high-angle
`GZ` claim label from `unvalidated_hydrostatic_comparison` to
`validated_hydrostatic_comparison` for hulls inside the fit's
`hull_family_scope`. The flip propagates to `kayakgen stability
--high-angle-gz` JSON output, the web Generate frontier colour token,
and the Generate panel `cfd_in_loop_evaluator_status` admonition. The
desktop chip remains minimal per D014.

Inspect the resolution without running the evaluator:

```bash
kayakgen stability claim-status hull.json --fits-root data/stability/fits
```

Override the registry root globally with
`KAYAKGEN_STABILITY_FITS_ROOT`. Fits below the strict default
thresholds are skipped at load time and do not flip the label.
```

## F. Open questions

1. **Registry root override precedence.** `--fits-root` flag vs
   `KAYAKGEN_STABILITY_FITS_ROOT` env vs CWD-relative default — I
   propose flag > env > default. Synthesizer should confirm this is
   consistent with the RFC 0046 env-knob precedence pattern.
2. **Behavior when a previously-accepted fit's fixture is
   re-promoted back to `validation_candidate`.** The
   `MeasuredStabilityFixture` validator already raises
   `constrained_trace_blocks_promotion` against
   `intended_use=measured_stability_fixture` regression. The
   registry loader should treat the regressed fixture as
   `fixture_not_promoted` and drop the fit. Worth a dedicated
   acceptance-criteria callout.
3. **Cache invalidation granularity.** Memoizing on directory
   `st_mtime` is coarse — touching an unrelated file invalidates
   the whole registry. Per-file mtime + content hash is the
   alternative. I default to directory mtime; finer-grained
   invalidation only matters at higher fit counts than stage 4
   anticipates.
4. **Whether `claim-status` should accept a hull design hash
   directly instead of requiring a hull JSON.** A hash-only mode is
   useful for sweep summary inspection but doesn't compose with
   evaluator-level callers. Defer.
5. **Whether the new `--fixture-id` flag on `accept-fit` should be
   optional with a fallback to single-`FixtureRef` autoresolve.**
   Required is safer; the synthesizer should weigh the ergonomics.
6. **Whether `claim-status` belongs under `kayakgen runs evidence`
   rather than `kayakgen stability`.** Putting it under `stability`
   keeps the registry-touching surface in one sub-app; putting it
   under `runs evidence` matches the cross-cutting-inspection
   convention. I default to `stability`.
7. **SOURCES.md mismatch.** SOURCES.md asks for
   `kayakgen calibration ingest-measured-stability` /
   `accept-measured-stability` and a new
   `kayakgen/eval/stability/measured_acceptance.py` module. This
   design declines both on the grounds that RFC 0058 stages 1-3
   already landed the equivalent surface. The synthesizer should
   pick a disposition: this lane proposes updating SOURCES.md as
   part of stage 4 implementation rather than building parallel
   commands.
