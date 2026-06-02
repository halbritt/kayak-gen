# Kayakgen User Guide

Kayakgen is a parametric kayak hull generator with scriptable evaluation
tools. Current output is useful for geometry iteration, hydrostatic checks,
exploratory sweeps, mesh diagnostics, and local CFD job-record plumbing. It is
not yet a validated performance-prediction or production CFD system.

## Install From This Repo

Use Python 3.11 or newer.

```bash
cd /home/halbritt/git/kayak-gen
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Optional extras:

```bash
python -m pip install -e '.[desktop]'      # PyQt/PyVista desktop GUI
python -m pip install -e '.[web]'          # Trame web frontend
python -m pip install -e '.[browser]'      # Playwright (browser acceptance)
python -m pip install -e '.[builder]'      # ezdxf (kayakgen build-export)
python -m pip install -e '.[calibration]'  # openpyxl (calibration ingest)
python -m pip install -e '.[report]'       # jinja2 + weasyprint (design-report)
python -m pip install -e '.[dev]'          # tests, linting, type checking
```

After install, `kayakgen --help` should show the command list.

## Quick Start

Create a default hull, generate STL surfaces, evaluate hydrostatics plus raw
analytical resistance, and inspect mesh quality:

```bash
kayakgen init hull.json
kayakgen generate hull.json --stl-out build/default
kayakgen evaluate hull.json --out build/default.eval.json
kayakgen stability hull.json --out build/default.stability.json
kayakgen mesh-check hull.json --out build/default.mesh.json
```

The generated STL command writes `build/default_hull.stl` and
`build/default_deck.stl`. JSON inputs and outputs use SI units; hull parameters
use names such as `length_m`, `beam_oa_m`, `beam_wl_m`, and `draft_m`.

## Editing Hull Inputs

`kayakgen init` writes a Pydantic `Hull` JSON record. Edit that file directly
for repeatable command-line work. Important fields include:

- `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`
- `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`
- `bow_rake` and `stern_rake`, where `0.0` is exact plumb and `1.0` is the
  legacy raked taper
- `rocker_bow_m` and `rocker_stern_m`

Coordinate convention: X increases from bow to stern. The bow endpoint is
`x = -length_m / 2`; the stern endpoint is `x = +length_m / 2`. Z increases
upward from the design waterline, and Y spans half-beam in generated sections
before being mirrored port/starboard.

`bow_rake` is retained as the legacy compatibility field. Older hull JSON that
only supplies `bow_rake` uses that value symmetrically for bow and stern,
matching historical behavior. New hull JSON may supply `stern_rake` to make the
stern independent. Rake fields are dimensionless fullness controls, not angles;
reverse rake and values outside `[0, 1]` are invalid.

The current loft honors only the implemented parameter set. Some fields exist
for RFC compatibility and are not complete shape controls yet; for example,
`LCB_frac` is reserved and not yet honored by the loft.

Hull JSON may set `geometry_kind`. The default `"lofted"` runs the
existing implicit loft and is byte-stable for every existing hull.
`"distribution_v2"` (RFC 0048) opts into an explicit distribution
model: the hull's `distribution_v2` block carries five
`LongitudinalDistribution` records (waterline half-breadth, draft
profile, section-area, deck-freeboard, rocker), a
`cross_section_family` choice from `round` / `shallow_arch` /
`shallow_v` / `deep_v` / `hard_chine` / `multi_chine` (2-4 chines),
plus deadrise / chine-radius / bow-flare controls and a target
LCB fraction. The canonical closed body is the source of truth in
v2; open hull/deck STLs are derived from it. Hydrostatics is
cross-checked by both section-integration and triangle-integration
methods (advisory-only on >1% displaced volume / Aw / LCB drift, or
>0.5% GM0). `bow_rake` / `stern_rake` are refused at non-default
values on a v2 hull. Use `kayakgen migrate-geometry` to produce a
v2 sibling from an existing lofted hull.

## CLI Commands

### `init`

Write a default hull JSON:

```bash
kayakgen init hull.json
```

### `generate`

Write open hull and deck STL inspection surfaces from a hull JSON:

```bash
kayakgen generate hull.json --stl-out build/example
```

Without `--stl-out`, the prefix is the hull path without `.json`.

### `evaluate`

Write hydrostatics and, by default, a raw ITTC plus Michell resistance curve:

```bash
kayakgen evaluate hull.json --out build/eval.json
kayakgen evaluate hull.json --skip-resistance --out build/hydro-only.json
```

Resistance output is an analytical screening estimate. It is explicitly
uncalibrated, has no accepted final-prediction validity envelope, and is meant
for comparative filtering across nearby candidates.

The evaluation JSON also includes additive `design_validity` metadata for
valid hulls. These records separate non-blocking design advisories, such as
`L/B_wl`, `Cp`, and displacement guidance, from unsupported reserved controls
such as non-neutral `LCB_frac`, `rocker_bow_m`, or `rocker_stern_m`. Advisory
and unsupported records do not make the hull invalid, do not change sweep or
comparison ranking, and are not proof of seaworthiness or final design fitness.

The result also gains a `convergence: list[ConvergenceFlag]` block
(RFC 0052) summarising each evaluator's convergence: `(stage, status
∈ {converged, not_converged, iteration_cap}, residual)`. Default
hulls evaluate to a fully-converged block; values are populated
automatically by an additive model validator on `EvaluationResult`.

Pass `--turning` (RFC 0053) to emit a `turning_metrics` block
(`heel_deg`, `edged_waterline_length_m`, `upright_waterline_length_m`,
`lateral_plane_shift_m`, `rocker_weighted_maneuverability_signal`,
`method="geometric_proxy_v1"`). Default heel is 8 deg; override via
`--turning-heel-deg <float>`. The metrics are a geometric proxy, not
a turning prediction. All four are registered as `display_only` in
the metric registry and refused as Pareto/search objectives.

### `stability`

> The bare-form `kayakgen stability <hull>` invocation is preserved via a
> hidden `legacy` subcommand and a Typer parse shim (D040). Running
> `kayakgen stability --help` intentionally hides the legacy form so the
> new RFC 0058 sub-app commands (`ingest-rig-run`, `promote-fixture`,
> `accept-fit`, `residual-plot`) surface; the bare-form invocation
> documented below continues to work unchanged.

Write initial-stability results for a load case:

```bash
kayakgen stability hull.json --out build/stability.json
```

Use `--load-case` to pass a JSON load case. A compact example:

```json
{
  "name": "day-trip",
  "paddler_mass_kg": 85,
  "hull_mass_kg": 18,
  "cargo_mass_kg": 8,
  "kg_above_keel_m": 0.28
}
```

Use `--equilibrium` to solve upright sinkage, and for explicit longitudinal
components the command attempts the current bounded fixed-body trim slice:

```bash
kayakgen stability hull.json --load-case load.json --equilibrium --out build/equilibrium.json
```

High-angle `GZ` curves and secondary-stability peak metrics are unavailable as
real kayak claims. They require real heeled integration over the generated
closed-body evidence; the current handoff records unavailable results or
explicitly labeled fixture-only synthetic math instead of real kayak stability
claims. Fixture records now carry grid-bounded summary semantics and
`unvalidated_hydrostatic_comparison` result semantics so they stay readable
without being mistaken for a real kayak stability claim.

Pass `--high-angle-gz` to emit an opt-in `high_angle_gz` block alongside the
default stability JSON. Without the flag, the JSON output is byte-identical to
the existing behavior. With the flag, the block records a fixed-trim
generated-body v1 heel sweep (default `0..90` deg by `5` deg; override with
`--heel-grid-deg "0,5,15,30,45,60,75,90"`) under
`body_profile=generated_hull_plus_deck_closed_body_v1` and
`result_semantics=unvalidated_hydrostatic_comparison`. Surface warnings
(`deck_immersion_assumption`, `flooding_not_modeled`,
`not_safety_or_seaworthiness_claim`, `active_paddler_not_modeled`,
`sealed_body_assumption`) are always included. Synthetic bodies record
`available: false` with `unavailable_reason.code = synthetic_body_not_allowed_for_real_gz`.
Defaults, sweep ranking, and frontier behavior remain unchanged.

#### Stability fixtures (RFC 0058)

The `kayakgen stability` group exposes four RFC 0058 stage-3 subcommands
that write schema-only artifacts for a future measured-stability
acceptance workflow. None of them ingest physical sensor data, run a real
fit, or promote a fixture today; they pin the on-disk data contract so the
first measured rig run can land cleanly. Stage 4 first promotion remains
gated on D007 / D014 physical rig data.

```bash
# 1. Schema-only ingest of a candidate measured-stability rig run.
kayakgen stability ingest-rig-run \
  --fixture-id alpha-2026-05 \
  --rig-run path/to/rig_run.json \
  --out data/stability/fixtures/alpha-2026-05/manifest.json

# 2. Schema-only StabilityFixturePromotionPacket writer. The five review
#    verdicts (rights, hull-identity, calibration-drift, hysteresis,
#    free-equilibrium) plus rig_design_match are required for the
#    measured_stability_fixture promotion target.
kayakgen stability promote-fixture \
  --fixture-id alpha-2026-05 \
  --packet path/to/promotion_packet.json \
  --out data/stability/fixtures/alpha-2026-05/promotion.json

# 3. Schema-only StabilityFitRecord acceptance. Default strict thresholds
#    (rmse_m <= 0.005, mape_fraction <= 0.05, max_error_m <= 0.01,
#    coverage_fraction >= 0.9) refuse out-of-band fits unless
#    `strict=false` is set (which adds the `strict_check_skipped`
#    warning).
kayakgen stability accept-fit \
  --fit-record path/to/fit_record.json \
  --out data/stability/fits/<fit_id>.json

# 4. Placeholder SVG residual plot for an accepted fit; the renderer is a
#    stub today and is replaced when stage 4 lands.
kayakgen stability residual-plot \
  --fit-record data/stability/fits/<fit_id>.json \
  --out data/stability/fits/<fit_id>.svg
```

The four subcommands write canonical fixture/fit manifests; the validators
refuse missing review verdicts, ill-ordered heel ranges, non-hex SHA-256
strings, and empty design-hash envelopes. A fit accepted today does not
upgrade RFC 0043's `unvalidated_hydrostatic_comparison` label — the
upgrade contract (`resolve_analytical_claim_label`) wires through but
defaults to an empty fit registry until stage 4 promotes the first
fixture.

#### Stage 4 — accepted-fit registry and label flip

A `StabilityFitRecord` written under `data/stability/fits/` and
bound to an accepted `MeasuredStabilityFixture` flips the analytical
high-angle GZ claim label from `unvalidated_hydrostatic_comparison` to
`validated_hydrostatic_comparison` for hulls inside the fit's
`hull_family_scope`. The flip propagates to the high-angle GZ JSON
output, the web Generate frontier colour token, and the Generate panel
`cfd_in_loop_evaluator_status` admonition.

Acceptance produces three on-disk artifacts:

1. `data/stability/fixtures/<fixture_id>/manifest.json` — the
   immutable `MeasuredStabilityFixture` JSON. After `ingest-rig-run`
   writes it, no later command (including `promote-fixture`) mutates
   its bytes.
2. `data/stability/fixtures/<fixture_id>/promotion.json` — the
   `AcceptedStabilityFixtureRecord` (the persisted
   `StabilityFixturePromotionPacket` whose `fixture_ref.fixture_sha256`
   hash-binds it to the manifest). **The manifest's `intended_use`
   field is a hint only; the canonical acceptance signal is
   `promotion.json` with `promotion_target =
   "measured_stability_fixture"`.**
3. `data/stability/fits/<fit_id>.json` — the `StabilityFitRecord`
   whose `fixtures[].fixture_sha256` re-binds to the same manifest
   bytes.

The stage-4 CLI signature for `accept-fit` requires `--fit-record`,
`--fixture-id`, and `--out` (the prior `--packet` flag is REMOVED;
acceptance is anchored on the fixture directory's `promotion.json`):

```bash
kayakgen stability accept-fit \
  --fit-record path/to/fit_record.json \
  --fixture-id alpha-2026-05 \
  --out data/stability/fits/<fit_id>.json
```

Inspect the resolved claim label for a hull without running the
evaluator:

```bash
kayakgen stability claim-status hull.json --fits-root data/stability/fits
```

`claim-status` prints a single JSON line carrying `hull_class`,
`design_hash`, `claim_label`, `covering_fit_id`, `fits_root`,
`fits_loaded`, and `dropped_fit_count`. Add `--debug` to receive a
`diagnostics` list naming each dropped fit and the gate it failed.

Override the registry root with `KAYAKGEN_STABILITY_FITS_ROOT`
(explicit `--fits-root` wins over the env, env wins over the default
`data/stability/fits`). Fits failing any §B gate (sha256 mismatch,
below threshold, `strict=false`, tampered, evaluator-version mismatch,
rights not authorized, …) are dropped at load time and do not flip the
label.

Every CLI refusal emits one structured JSON line with the shape:

```json
{
  "ok": false,
  "code": "fixture_sha256_mismatch",
  "fixture_id": "msf-2026-001",
  "details": {"expected_sha256": "abcdef…", "actual_sha256": "012345…"},
  "next_action": "re-ingest if the manifest changed intentionally, else re-sign the packet against the new bytes."
}
```

The `next_action` text comes from
`kayakgen.eval.stability.registry.REASON_NEXT_ACTION` — that mapping is
the single source of truth for operator-facing remediation copy. The
high-angle GZ claim-state flip only happens when the full provenance
chain holds: an immutable fixture manifest, a strict-accepted
`promotion.json`, and a `StabilityFitRecord` whose
`analytical_evaluator_version` matches the runtime and whose
`hull_family_scope` covers the hull. The hull itself must carry a
`hull_class` value (e.g. `sea_kayak`); a `hull_class=null` hull stays
`unvalidated_hydrostatic_comparison` regardless of registry contents.

### `sweep`

Run a deterministic JSON sweep and write candidate records:

```bash
kayakgen sweep sweep.json --out runs/demo
kayakgen sweep sweep.json --out runs/demo --resume
```

Minimal sweep spec:

```json
{
  "schema_version": "1",
  "name": "beam-scan",
  "base_hull": {"length_m": 5.2, "beam_oa_m": 0.55, "draft_m": 0.12},
  "variables": {
    "beam_wl_m": {"kind": "values", "values": [0.45, 0.50, 0.55]},
    "Cp": {"kind": "linspace", "min": 0.50, "max": 0.58, "count": 3}
  },
  "evaluators": {
    "hydrostatics": true,
    "resistance": true,
    "stability": true,
    "mesh_diagnostics": true,
    "stl": false
  },
  "limits": {"max_candidates": 100}
}
```

The run directory contains `run.json`, `summary.csv`, `failures.jsonl`, the
copied `spec.json`, and per-candidate artifacts under `candidates/`.
Current sweep record statuses are `complete`, `failed`, `pending`, and
`skipped` on resume. The `pending` state remains visible across resume; the
CLI reports a pending count; pending and failed candidates remain in the
comparison report but are frontier-ineligible.

Set `evaluators.stl: true` in a sweep spec to emit per-candidate open inspection
surfaces. Each `complete` candidate gets `candidates/<key>/hull.stl` and
`candidates/<key>/deck.stl`, with the candidate record's `stl_artifacts` block
recording `{path, bytes, sha256}` for each file. Failed and pending candidates
skip artifact emission; resume preserves existing STL files byte-for-byte
without regeneration. Sweep STLs are open hull/deck inspection surfaces and do
not prepare mesh packages or promote any candidate to watertight readiness;
run `kayakgen mesh-package` separately when a package is needed.

Set `evaluators.high_angle_gz: true` (and optionally
`evaluators.high_angle_gz_heel_grid_deg: [0, 5, 15, ...]`) to emit a per-candidate
opt-in `candidates/<key>/high_angle_gz.json` artifact alongside the standard
record. Each `complete` candidate's record gains a `high_angle_gz_artifact`
block with `{path, bytes, sha256}`. Failed and pending candidates skip emission;
resume preserves existing artifacts byte-for-byte. The block content is the same
shape that `kayakgen stability --high-angle-gz` emits and remains
`unvalidated_hydrostatic_comparison`. High-angle GZ metrics do NOT enter
`summary.csv` columns and are NOT selectable as Pareto objectives — they are
display-only.

Set `evaluators.turning_metrics: true` (RFC 0053; optionally
`evaluators.turning_metrics_heel_deg: 8.0`) to emit four numeric
`turning.*` metrics on each candidate's `summary`. They appear as
columns in `summary.csv`. All four are registered as `display_only`
and refused as Pareto/search objectives, matching the CLI `--turning`
flag's contract.

### `compare`

Build a Pareto-style comparison report from a sweep run:

```bash
kayakgen compare runs/demo --out runs/demo/compare.json
kayakgen compare runs/demo --out runs/demo/compare.json \
  -o GM0_m:max -o displacement_error_kg:min -o mesh_problem_count:min
```

Resistance metrics can be named as objectives, but reports that include them
remain exploratory because resistance is a raw comparative filter.
The default objective set is built only from conservative metrics that are
present in the current records: `GM0_m`, `displacement_error_kg`, and
`mesh_problem_count`. Comparison reports are for candidate review; pending
candidates remain visible in the report but are not eligible for the Pareto
frontier. Objective metadata for optimizer/search workflows remains roadmap
work.

When per-candidate `high_angle_gz.json` artifacts are present (see the sweep
`high_angle_gz` evaluator above), the comparison report adds a top-level
`high_angle_gz_columns: true` flag and attaches a `high_angle_gz_display` block
to each row with body/load/trim provenance, the summary metrics (`max_gz_m`,
`heel_at_max_gz_deg`, `range_positive_stability_deg` — null unless every
heeled point converged), warnings, assumptions, and any `unavailable_reason`.
This is display-only: high-angle GZ metrics are refused as Pareto objectives
(token `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`), so passing `-o max_gz_m:max`
errors. Frontier eligibility is unchanged.

### `search`

Run an active multi-objective hull-design search (RFC 0044 v1, NSGA-II):

```bash
kayakgen search search.json --out runs/touring-pareto
kayakgen search search.json --out runs/touring-pareto --resume
```

Minimal search spec:

```json
{
  "schema_version": "1",
  "name": "touring-sea-kayak-pareto",
  "base_hull": {"length_m": 5.2, "beam_oa_m": 0.55, "draft_m": 0.12},
  "search_space": {
    "length_m":  {"kind": "uniform", "min": 4.4, "max": 5.6},
    "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.58},
    "Cp":        {"kind": "uniform", "min": 0.50, "max": 0.62}
  },
  "algorithm": {
    "kind": "nsga2",
    "population_size": 24,
    "generations": 8,
    "seed": 1234
  },
  "evaluators": {"hydrostatics": true, "mesh_diagnostics": true, "stability": true},
  "budget": {"max_evaluations": 192, "wall_clock_seconds": 600}
}
```

When the spec omits `objectives`, the conservative defaults
(`GM0_m:max`, `displacement_error_kg:min`, `mesh_problem_count:min`)
are resolved automatically. Optional `constraints` (each with a `metric`
plus `min` and/or `max`) hard-reject candidates that fail any bound;
those rows are recorded with `status="constraint_failed"` and stay
frontier-ineligible.

Active search is additive on top of `kayakgen sweep` and reuses the
same run directory layout: `run.json`, `summary.csv`,
`failures.jsonl`, the copied `spec.json`, and per-candidate artifacts
under `candidates/`. The `run.json` adds a `search_metadata` block with
the resolved algorithm, seed, objectives, constraints, realized budget,
termination reason, and a per-generation history trail (population
size, frontier size, best/median/worst on each objective).

Determinism is seed-preserving. A spec with a fixed `algorithm.seed`
produces byte-identical `candidates/<key>/record.json` across
independent invocations and across resume.

Objective admissibility is strictly gated. Active search refuses any
metric whose claim state is `raw_unvalidated` (raw OpenFOAM forces) or
`uncalibrated_comparative` (the analytical resistance filter) unless the
spec sets `"objectives_explicit_exploratory": true`. Even then the
high-angle-GZ display-only token from RFC 0043 still refuses
`max_gz_m`, `heel_at_max_gz_deg`, and `range_positive_stability_deg`
as objectives. Exploratory runs tag the run record with
`search_class: "exploratory"` and print a banner; the resulting
frontier is still frontier-ineligible under the conservative
comparison view.

`kayakgen search` does not run real CFD by itself. To use the
OpenFOAM-v2512 succeeded path inside the loop, set the env knobs
documented under `cfd run` above.

### `target-draft`

Solve upright sinkage for a load case (RFC 0050), or report the
mismatch between a given draft and that load:

```bash
kayakgen target-draft hull.json --load day-trip.json --out target-draft.json
kayakgen target-draft hull.json --load day-trip.json --draft 0.12 --report-only \
    --out target-draft-mismatch.json
```

The default mode writes the equilibrium `StabilityResult`. With
`--report-only` and `--draft`, the command writes a
`TargetDraftMismatchReport` (`hull_record_hash`, `assumed_draft_m`,
`expected_displaced_mass_kg`, `actual_displaced_mass_kg`, `mismatch_kg`,
`mismatch_percent`, `notes`). Loads that exceed 2× the hull's max
displaced mass are refused with a structured `load_unphysical` error.

### `target-trim`

Solve draft + trim for a load case with a non-zero longitudinal CG
(RFC 0050):

```bash
kayakgen target-trim hull.json --load offset-paddler.json --out target-trim.json
```

Wraps the existing bounded fixed-body trim solver via
`kayakgen.services.evaluation.solve_target_trim`. Same load-physics
guard as `target-draft`.

### `migrate-geometry`

Convert a v1 lofted `Hull` JSON to a best-effort v2 distribution
record (RFC 0048):

```bash
kayakgen migrate-geometry hull.json --out hull.v2.json --tolerance-percent 1.0
```

Without `--out`, the migration writes a sibling `<name>.v2.json`. If
the round-trip discrepancy exceeds the configured tolerance, the
command writes the v2 file but exits with a non-zero status and a
structured warning. The v1 `geometry_kind="lofted"` hull and STL
output remain byte-stable; v2 is additive, not a replacement.

### `build-export`

Write builder-oriented artifacts (RFC 0051; requires
`kayakgen[builder]` extras for the DXF writer):

```bash
kayakgen build-export hull.json --out build/builder
kayakgen build-export hull.json --out build/builder --n-stations 48
```

Produces seven artifacts under `--out`: `offsets.csv`, `sections.dxf`,
`sheer.svg`, `keel.svg`, `waterline.svg`, `deck_centreline.svg`,
`station_molds.dxf`, plus a `manifest.json` enumerating each with
`sha256` and `bytes`. Each artifact carries a header comment with the
hull SHA-256 and the kayakgen version pin. Output is deterministic
modulo CAD-library save timestamps (the DXF determinism check
compares parsed entities, not raw bytes).

### `sensitivity`

Local finite-difference Jacobian over hull parameters (RFC 0052):

```bash
kayakgen sensitivity hull.json \
    --metric GM0_m --metric displaced_mass_kg \
    --param length_m --param beam_oa_m \
    --out hull.sensitivity.json
kayakgen sensitivity hull.json --metric GM0_m --param beam_oa_m --step 0.005
```

Auto-step is `1e-4 * baseline_value` per parameter, clamped to
`[1e-9, 1e-2]`. The output JSON is a `SensitivityResult` with the hull
record hash, the chosen step per parameter, the metric baselines, the
`metric → param` partial-derivative table, and any `(metric, param,
reason)` triples that produced non-finite partials. The result is
explicitly local-sensitivity, not a calibrated reliability claim.

The comparison report (`kayakgen compare`) also gains a
`pairwise_notes` block flagging Pareto-front pairs whose default-
objective metrics differ by less than the registry's per-metric
`within_evaluator_noise_threshold` (defaults: `GM0_m=0.001 m`,
`displacement_error_kg=0.5 kg`, `mesh_problem_count=1`). The advisory
does not change frontier eligibility; it tells the operator that two
"different" candidates are within evaluator noise.

### `design-report`

Render a self-contained HTML (and optionally PDF) design report
(RFC 0055; requires `kayakgen[report]` extras):

```bash
kayakgen design-report hull.json --out report.html
kayakgen design-report hull.json --out report.html --pdf
kayakgen design-report hull.json --out report.html --from-run runs/demo
```

The report assembles ten sections: header, parameters, rendered
views (embedded base64 PNG preview), hydrostatics, stability
(including opt-in high-angle GZ when present), resistance, mesh /
readiness, optional comparison position (when `--from-run` is set),
artifact refs + SHA-256, and claim-state explanations. The
renderer scans the assembled text against
`FORBIDDEN_COPY_TOKENS` after scrubbing the explicit negated forms;
forbidden copy raises `ReportForbiddenCopyError` instead of writing
the file. The optional PDF path uses weasyprint; without weasyprint
the command emits a structured error pointing at the `report` extras.

### `runs`

Cross-run inspection over the RFC 0049 artifact store:

```bash
kayakgen runs list [--kind sweep|search|cfd|comparison] [--limit N] [--header]
kayakgen runs query <run_id> [--metric NAME ...] [--filter key:value ...]
kayakgen runs reindex <run_dir> [--run-id ID]
kayakgen runs jobs [--state queued|running|succeeded|failed|cancelled|resumable] \
    [--kind sweep|search] [--limit N] [--header]
```

`runs list` and `runs jobs` default to `--no-header` for back-compat
with existing scripts that parse the tab-separated output. Pass
`--header` to prefix the rows with a `#`-prefixed header line naming
the columns. `runs query --filter key:value` honors two keys today —
`status` (e.g. `accepted`, `rejected`) and `hull_design_hash` (full
hex). Unknown keys parse cleanly but match no rows, silently
dropping the candidate; the filter is applied client-side after the
SQLite query. Example:

```bash
kayakgen runs list --header --limit 5
kayakgen runs query <run_id> --filter status:accepted --metric GM0_m
kayakgen runs jobs --header --state succeeded
```

The SQLite index lives at `~/.local/share/kayakgen/index.sqlite` by
default; override via `KAYAKGEN_INDEX_DB`. Each sweep, search, and
CFD run that writes through `FilesystemArtifactStore` registers
itself in `runs`, `candidates`, `metrics`, `artifacts`, and `events`
tables on completion. Legacy run directories produced before RFC
0049 still load; `kayakgen runs reindex <run_dir>` re-derives index
rows from disk.

RFC 0057 generative jobs also register in the index. `kayakgen runs jobs`
lists durable sweep/search job records created by the web Generate tab or the
service layer, including their kind, state, output directory, counters, and
timestamps. The job artifacts live under
`~/.local/share/kayakgen/generative_jobs/` by default; override that root for
the web app with `KAYAKGEN_GENERATIVE_JOBS_ROOT`.

### `calibration`

Calibration-campaign ingest, acceptance, and artifact tooling
(RFC 0054). The campaign itself is operator action; this surface is
the on-disk plumbing that makes a future campaign reproducible.

```bash
kayakgen calibration ingest-tank-test <csv> \
    --hull hull.json --rights rights.json --out fixtures/tank-test/<source>/ \
    --source-id <source> [--uncertainty-method documented_caveat]
kayakgen calibration ingest-inclining-test <csv> \
    --hull hull.json --out fixtures/inclining/<source>/ --source-id <source>
kayakgen calibration accept-fit <fixture-id> \
    --fit fit.json --rmse-threshold 5.0 --out fixtures/calibration/<fixture>/
kayakgen calibration residual-plot accepted_fit.json --out residuals.svg
```

`accept-fit` refuses below-threshold fits with structured tokens
(`fit_above_rmse_threshold`, `fit_above_mape_threshold`,
`fit_below_r2_threshold`). The validator on
`ResistanceSourceReviewPacket` resolves `accepted_fit_ref` on disk
when it points at a `.json` file and refuses promotion to
`calibration_fixture` if the fit is missing, unparseable, or
below threshold (`accepted_fit_unresolved`,
`accepted_fit_unparseable`). Edinburgh stays at `validation_fixture`
per D013; no current source resolves the calibration gate.

### `mesh-check`

Diagnose the generated surface mesh for one part:

```bash
kayakgen mesh-check hull.json --part hull --out build/hull.mesh.json
kayakgen mesh-check hull.json --part deck --out build/deck.mesh.json
```

Diagnostics report boundary edges, non-manifold edges, degenerate faces,
readiness level, and warnings. This command does not promote a mesh to CFD
readiness.

### `mesh-package`

Write a deterministic mesh package with manifest, hull JSON, quality reports,
and STL surfaces:

```bash
kayakgen mesh-package hull.json --out build/mesh-package
kayakgen mesh-package hull.json --out build/watertight-package --solver-profile watertight-solid
```

The default `open-wetted-surface` profile currently produces an open-surface
candidate with readiness `cfd_surface_candidate`, not `cfd_ready`. The
`watertight-solid` profile can report `cfd_ready` only for matching
generated-body fixture volume-mesh evidence with bound diagnostics, hashes, and
paths. Ordinary generated packages still emit separate open surfaces and remain
below solver-ready status.

Changing `bow_rake` or `stern_rake` to `0.0` does not by itself make those
inspection STLs watertight; closed-body readiness must come from the explicit
generated closed-body path and diagnostics.

### `mesh-evidence` (RFC 0045)

`kayakgen mesh-evidence <hull>` runs the snappyHexMesh-evidence harness
against an installed OpenFOAM-v2512 toolchain and writes the resulting
`SnappyHexMeshEvidence` (case-template version, dictionary hashes,
patch metadata, `CheckMeshSummary`, polyMesh artifact checksums,
`OpenFoamProvenanceProbe`) into the package directory. The default
output binds back into `mesh-package --bind-evidence` to promote an
ordinary generated package to `cfd_ready` without copying fixture
artifacts.

```bash
export KAYAKGEN_OPENFOAM_LOCAL_RUN=1
export KAYAKGEN_OPENFOAM_BASHRC=/usr/lib/openfoam/openfoam2512/etc/bashrc
kayakgen mesh-evidence hull.json --out build/mesh-evidence
kayakgen mesh-package hull.json --out build/watertight-package \
  --solver-profile watertight-solid \
  --bind-evidence build/mesh-evidence/evidence.json
```

The command refuses to run without `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and an
OpenFOAM-v2512 toolchain reachable via `KAYAKGEN_OPENFOAM_BASHRC`. The
refusal emits a structured `binding_code` token
(`openfoam_local_run_env_required` or
`openfoam_toolchain_unavailable`). See the env-knob list under
`### cfd run` for the three RFC 0046 opt-in mechanisms; `mesh-evidence`
currently honors only the env-knob mechanism.

## Synthetic Closed-Volume Diagnostics

Workflow 0027 introduced a narrow diagnostic contract for explicit synthetic
triangle meshes. Workflow 0032 adds self-intersection evidence for the
RFC 0021 synthetic profile. These diagnostics are serializable and can
distinguish valid closed synthetic bodies from open, nonmanifold, or
self-intersecting synthetic fixtures.

The contract requires zero body-level boundary edges, zero body-level
nonmanifold edges, and positive signed volume with outward normals before a
synthetic body can report `closed_volume`. The compatibility profile
`explicit_synthetic_closed_volume_v1` records
`self_intersection_status: not_checked`; the RFC 0021 profile
`explicit_synthetic_closed_volume_self_intersection_v1` requires
`self_intersection_status: passed`.

Self-intersection diagnostics are body-level checks on the assembled explicit
body, not per-part readiness claims. The serialized result records
`self_intersection_status`, `self_intersection_algorithm`,
`self_intersection_tolerance_m`, `self_intersection_pair_count`, and up to
eight example triangle pairs. Status values are `not_checked`, `passed`,
`failed`, and `inconclusive`. Both `failed` and `inconclusive` block the
RFC 0021 closed-volume diagnostic profile.

The first algorithm,
`assembled_welded_aabb_triangle_pairs_v1`, uses deterministic expanded
axis-aligned bounding boxes as a broad phase, then checks non-adjacent triangle
pairs. Adjacency is derived from the assembled body after the vertex-weld
tolerance is applied: shared-edge neighbors are skipped, and vertex-only pairs
are skipped only when the welded topology proves they belong to the same local
vertex fan. Coplanar overlap, coplanar touch, edge/point touch, and crossing
between non-adjacent triangles are `failed`; non-adjacent pairs closer than
`self_intersection_tolerance_m` without a detected crossing are
`inconclusive`.

The diagnostic artifact always keeps `cfd_ready` false. Synthetic diagnostics
do not repair geometry, create a volume mesh, or make a watertight solver
handoff. Generated closed-body construction is a separate evaluation-side path;
it must still pass closed-volume diagnostics before it can be treated as a
closed body. By itself it does not make a CFD-ready solver handoff; the narrow
RFC 0023 handoff also requires matching fixture volume-mesh evidence.

Generated mesh packages remain open-surface artifacts. Treat their hull and
deck STLs as inspection and packaging surfaces, not as a closed volume for
high-angle stability or watertight CFD.

### `cfd profiles`

List built-in local dispatch profiles:

```bash
kayakgen cfd profiles
```

Current profiles are placeholders for deterministic job-state behavior:
`unavailable-open-wetted-surface`, `unavailable-watertight-solid`, and
`mock-failing-local-command`. The `fixture-local-command` profile is also
available as a checked-in deterministic test adapter; it writes a
`raw-result.json` fixture artifact for route and CLI plumbing tests, but it is
not a real CFD solver and does not produce validated or calibrated output.

### `cfd prepare`

Prepare a local CFD job record from a mesh package:

```bash
kayakgen cfd prepare \
  --mesh-package build/mesh-package \
  --out runs/cfd \
  --solver-profile unavailable-open-wetted-surface \
  --speed-mps 2.5
```

This writes a job directory containing `profile.json`, `job.json`, and
`run.json`. Mesh profile and readiness are checked before the job is written.

### `cfd status`

Show current state for a prepared local job:

```bash
kayakgen cfd status runs/cfd/cfd-xxxxxxxxxxxxxxxx
```

### `cfd run`

Run the selected local adapter state:

```bash
kayakgen cfd run runs/cfd/cfd-xxxxxxxxxxxxxxxx
```

No real SU2, hosted worker, Docker solver, or calibrated CFD result is
available in the current CLI. The unavailable profiles report
`solver_unavailable`; the mock local-command profile deliberately fails for
dispatch testing. The fixture local-command profile can produce a deterministic
successful raw fixture record for tests.

The `openfoam-v2512-interfoam-local` profile has a real local-execution path
behind RFC 0046's three opt-in mechanisms. The CLI accepts any one of the
three; an installed OpenFOAM-v2512 toolchain must still be sourceable via
`KAYAKGEN_OPENFOAM_BASHRC`. The three mechanisms, ranked by precedence:

1. **Profile flag** (highest precedence). `kayakgen cfd prepare
   --allow-real-solver-execution` writes the opt-in into the job's
   `profile.json` (`allow_real_solver_execution=true`); the value
   travels with the job and is the most auditable mechanism because it
   appears in every artifact derived from that profile.
2. **Persistent setting** (middle precedence).
   `~/.config/kayakgen/cfd.json` may carry an
   `allow_real_solver_execution_profiles: ["openfoam-v2512-interfoam-local"]`
   list. Use this for long-lived operator setups; the persistent setting
   is not embedded in any artifact, so prefer the profile flag when
   provenance matters.
3. **Env knob** (lowest precedence). `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`
   admits the real succeeded path in `kayakgen cfd run`. Convenient for
   shell-local runs; not recommended for CI or unattended jobs because
   the env var is not visible in the run artifacts.

The full env-knob list, including the test-only smoke gate and the
toolchain source, has distinct roles:

- `KAYAKGEN_OPENFOAM_LOCAL_RUN`: operational opt-in (RFC 0046 env-knob
  mechanism #3 above); without it and without the other two mechanisms,
  the adapter falls back to `error_kind="solver_success_blocked"`.
- `KAYAKGEN_OPENFOAM_SMOKE`: test-only smoke gate. Gates the integration test
  surface (`tests/test_openfoam_v2512_smoke.py` and the env-gated stage tests
  in `tests/test_cfd_run_stages.py`) only; the CLI does not consult it.
- `KAYAKGEN_OPENFOAM_BASHRC`: environment source. Path to the OpenFOAM bashrc
  the runner sources to acquire the WM/FOAM environment; defaults to
  `/usr/lib/openfoam/openfoam2512/etc/bashrc`.

```bash
# Mechanism 1: per-job profile flag (preferred for CI / auditable runs).
kayakgen cfd prepare ... --allow-real-solver-execution --out runs/cfd

# Mechanism 2: persistent setting (long-lived operator setup).
mkdir -p ~/.config/kayakgen
cat > ~/.config/kayakgen/cfd.json <<'JSON'
{"allow_real_solver_execution_profiles": ["openfoam-v2512-interfoam-local"]}
JSON

# Mechanism 3: env knob (shell-local convenience).
export KAYAKGEN_OPENFOAM_LOCAL_RUN=1
export KAYAKGEN_OPENFOAM_BASHRC=/usr/lib/openfoam/openfoam2512/etc/bashrc
export KAYAKGEN_OPENFOAM_SMOKE=1   # only needed for the integration test suite
```

With both opt-ins set, `kayakgen cfd run` against an
`openfoam-v2512-interfoam-local` job calls
`kayakgen.eval.cfd.openfoam_v2512_interfoam.render_case`, runs
`blockMesh + surfaceFeatureExtract + snappyHexMesh -overwrite + checkMesh`
(meshing stage) and `setFields + interFoam` (solve stage) under the sourced
OpenFOAM environment, parses the resulting `postProcessing/forces/0/force.dat`,
and writes a `CfdRunRecord` with `status="succeeded"` and a `CfdOpenFoamRawResult`
payload. The payload preserves
`case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
`claim_state="raw_unvalidated"`, and empty `accepted_uses`. Without the env
knobs the adapter still reports `error_kind="solver_success_blocked"`.

The `CfdRunRecord` schema carries an additive `stages: list[CfdRunStage]`
field that models the local CFD execution pipeline as explicit, named stages
(`mesh_readiness_evidence`, `case_render`, `meshing`, `mesh_evidence_binding`,
`solver_execution`, `parser_post_processing`, `raw_result`, `validation_gate`).
A `succeeded` record records per-stage wall-clock under
`stages[*].wall_clock_seconds` so consumers can see which stage produced the
record without parsing logs. Skipped stages (`mesh_evidence_binding` and
`validation_gate` in the current slice) carry `state="skipped"` and a `notes`
entry that explains why. The blocked path and the unavailable/mock/fixture
adapters keep `stages=[]`.

Real-binary smoke wall-clock on a default `kayakgen init` hull: ~7 s meshing
plus ~2 s solve. All output remains raw and unvalidated: it is not a
calibration result, a validated CFD result, a final prediction, a
design-fitness signal, or a safety/seaworthiness claim.

All other CFD run records (unavailable, mock, fixture, or OpenFOAM without the
env knobs) remain raw and unvalidated.

### `view`

Open the desktop GUI:

```bash
kayakgen view
kayakgen view hull.json
```

Install `kayakgen[desktop]` first. The legacy `python gui.py` entry point is
still present, but `kayakgen view` is the package CLI path.

The desktop GUI exposes sliders for the implemented hull fields, including
`Cp`, `Cm`, beam-at-waterline, deck flatness, parallel mid-body, bow rake, and
stern rake. The target-speed slider only changes the live resistance readout;
it is not written into the `Hull` JSON model.

Use **Export STLs** to write the current open inspection surfaces. The button
label changed from the older "Generate STLs" wording, but the filenames are
unchanged: choosing a stem such as `kayak` writes `kayak_hull.stl` and
`kayak_deck.stl`.

The desktop review text now keeps the same four status categories used by the
workspace RFC: package, readiness, resistance, and CFD. RFC 0043 stage 4 adds
a fifth segment, `high_angle_gz`, which always reads
`cli_only_unvalidated_hydrostatic_comparison` on the desktop. The desktop
intentionally does not render a high-angle GZ curve (per D021); the staged
opt-in surfaces are `kayakgen stability --high-angle-gz`, the sweep
`evaluators.high_angle_gz` artifact, the comparison report's
`high_angle_gz_display` block, and the Trame web workspace. In the current
desktop slice these are status labels only; the GUI does not prepare mesh
packages, start CFD jobs, or promote raw resistance output to a final
prediction. The 3D preview still opens as a separate PyVista window.

### `serve`

Run the local Trame web frontend:

```bash
kayakgen serve
kayakgen serve hull.json --host 127.0.0.1 --port 8080
kayakgen serve --jobs-in-process   # opt out of the subprocess runner
```

Install `kayakgen[web]` first, then open the printed local URL. The web shell
supports interactive hull inspection, compact analysis views, comparison report
loading, a local CFD job panel, and the **Generate** tab for parametric
sweep / NSGA-II / EHVI runs (RFC 0057). Generative jobs run as detached
subprocesses by default (RFC 0057 stage 3); pass `--jobs-in-process` to run
them as background threads instead. Required local browser acceptance and
hosted-demo documentation are covered by the web verification runbook; public
hosting, full dashboard parity, hosted CFD workers, cancellation guarantees,
authentication, and real solver adapters are not complete.

The workspace is organised as a parameter rail on the left plus a tabbed
detail area on the right: **Hydro**, **Mesh**, **Comparison**, and
**Generate**. The 2026-05-22 second-pass redesign (`b82b544`) restructured
the previous monolithic layout into these four tabs; the wire payload of
`build_spec_from_form_state` is unchanged across the redesign, so saved
specs and shared URLs from before the rework continue to load correctly.
The RFC 0065 polish pass applies the shared theme tokens across the same
workspace: denser section rhythm, token-sourced focus rings, consistent
control states, explicit empty/loading/error states, and the same
first-viewport / under-960px collapse behavior. This is presentation-only;
it does not add routes, evaluators, solver capability, or new claim/readiness
states.

**Param rail.** Sliders for the canonical hull-shape inputs. The class
selector reseeds `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, and `Cp`
for the touring, performance, intermediate-surfski, and elite-surfski
presets, and narrows those slider ranges to the selected class envelope.
Class presets seed and narrow only those five fields; editing any
hull-shaping slider returns the selector to `custom`, while target speed
stays view state, does not switch the preset, and is not written to `Hull`
JSON. Every parameter exposes a friendly label (e.g. "Beam WL (m)",
"Prismatic coefficient (Cp)") and a hover-for-description tooltip; the
labels and descriptions come from
`kayakgen.ui.parameter_metadata.HULL_PARAMETER_METADATA` (RFC 0060), so
the submitted JSON continues to use the raw parameter names (`beam_wl_m`,
`Cp`, ...).

**Validity badge.** A chip-styled header sits above the param rail and
reports one of `In <class> envelope`, `Custom — sub-touring`,
`Custom — beyond elite`, or `Custom (L/B_wl=X.X)` for the current hull
against the canonical web class envelopes (before custom fallback). The
badge is advisory: it is not proof of seaworthiness, calibrated
performance, design fitness, or solver readiness. Screen-reader users
get the same statement via `aria-label` (the chip carries
`role="status"` + `aria-live="polite"`). Sighted users may need to
hover for full text in narrow viewports; the chip colour mirrors the
state ("In envelope" reads as success-soft, "Custom" reads as
warn-soft) but the textual claim is the authoritative signal.

**Hydro tab.** Renders the current hydrostatics as a key/value table
(displacement, wetted surface, waterplane area, GM0, Cp/Cm actuals,
L/B at WL) sourced from `evaluate_hydrostatics(hull)`. Row labels and
units come from the RFC 0062 `HYDROSTATICS_ROW_METADATA` registry in
`kayakgen.ui.hydrostatics_metadata`, which also carries one-sentence
operator-facing `description` fields per row. The current Hydro tab
renders only label and value; the description fields are written and
covered by the regression test in
`tests/test_hydrostatics_row_metadata.py`, but no UI surface renders
them today — to read a row's description, consult
`kayakgen/ui/hydrostatics_metadata.py` directly. Hover-tooltip
rendering of descriptions is tracked as audit finding AUD-O-003 from
the 2026-05-25 full_repo audit; the follow-up workflow lands the
tooltip surface. The previous monospace `<pre>` dump is gone. High-angle GZ visualisation is still
deferred per D021; when applicable, the tab surfaces a tonal warning
saying high-angle GZ is unavailable in the workspace and pointing the
operator at the comparison-report import or `kayakgen stability
--high-angle-gz` for that data. The Hydro labels are currently
human-curated rather than registry-sourced; the audit follow-up tracks
moving them to a sibling registry of `HULL_PARAMETER_METADATA`.

**Mesh tab.** Renders hull and deck diagnostics as key/value tables
(boundary edges, non-manifold edges, open faces, thin triangles,
welded-primary counts, etc.) plus the package/readiness/profile state
when available. The readiness chip now renders as a pair when no
package is built: a neutral `No package built` chip alongside the live
`status_readiness` value. The pair resolves the previous
"unavailable" copy by showing both the package state and the underlying
hull/deck geometry readiness — they answer two different questions and
the operator sees both. `watertight-solid` remains unavailable in the
browser for authoring or promotion; use the CLI package/dispatch path
for the narrow fixture-backed RFC 0023 handoff. Mesh diagnostic labels
are currently raw diagnostic keys (e.g. `boundary_edges`,
`nonmanifold_edges`); a follow-up batch will rewrite them with
operator-facing copy and threshold guidance (non-manifold edges must
be 0, etc.).

**Comparison tab.** The 2D Pareto frontier scatter + sortable table
lives here, not on the Generate tab. A `live_frontier / imported_report`
toggle at the top of the tab chooses the source: **Live frontier** shows
candidates from the in-session jobs index (with `claim_state` colouring
and `ConvergenceFlag` marker shape per RFC 0057 D-6 / D-7);
**Imported report** reveals a JSON textarea that accepts a design-report
payload (the output of `kayakgen report export`) so a saved frontier
from another run can be inspected alongside the current session. Both
sources render with the same scatter/table widget; selecting a row
loads the candidate into the single-hull view with a one-click undo
toast.

**Generate tab.** A two-column form-builder primary input. The left
column carries variables (now rendered as a `VDataTable`, one row per
variable name + kind + bounds) plus the algorithm radio. The right
column carries the claim-admissibility-filtered objective picklist
(with a `VAlert` refusal block per refused objective that names the
admissibility cause), the RFC 0046 CFD-in-loop opt-in row with explicit
acknowledgement, and the soft 4-job in-flight advisory. CFD-in-loop is
orders of magnitude slower than the default hydrostatics-only sweep
because each candidate runs an OpenFOAM job through the local adapter;
leave the box unchecked unless calibrated CFD evidence is needed. Below
the form sits a single kind-aware Submit button that adapts its label to
"Submit Search" or "Submit Sweep" depending on the selected algorithm
(both share `data-testid="generative-submit"` for tests). A collapsible
**Raw JSON (advanced)** panel below the form-builder accepts a direct
SearchSpec / SweepSpec JSON payload for power-user cases (custom
evaluator configurations, non-standard variable distributions,
machine-generated specs); the form-builder is the primary path for
everyone else. The jobs index renders as a `VDataTable` with columns
for job ID, kind, state, elapsed time, and acceptance summary; rows
hand off to the single-hull view, expose a "Fork with new seed" button
on succeeded rows, and render bounded log tails with home-dir /
`<jobs_root>` redaction (RFC 0057).

**Responsive behavior.** On wide screens the param rail and the active
tab sit side-by-side and the Generate form uses its two-column layout.
On narrow viewports (under ~960px) Vuetify's grid stacks the columns
vertically; the validity badge remains pinned at the top of the rail
section.

**Browser verification.** The required browser-acceptance profile now includes
hard masked visual-regression screenshots at `1440x900`, `1024x768`, and
`960x720`, plus focus-order, visible focus-ring, hit-target, contrast, Share
URL reload, STL API, nonblank-3D, and browser-cleanliness checks. Baseline
regeneration and tolerance details live in `docs/WEB_VERIFICATION.md`.

**Export menu.** Lists Hull STL, Deck STL, Hydro JSON, Stability JSON,
and Mesh package. Hull and Deck STL use the existing local STL
behavior. Hydro JSON uses current local evaluation data. Stability
JSON and Mesh package remain unavailable in the browser; use
`kayakgen stability` and `kayakgen mesh-package` for those artifacts
today. The menu does not create hosted storage, hosted solver jobs,
high-angle `GZ` exports, or watertight `cfd_ready` packages.

Browser share or reload links seed the current hull state from the
query string, so a saved URL restores the same design inputs that
were open when the link was copied. The web shell's `data-testid`
attributes (`validity-badge`, `generative-submit`,
`comparison-source-toggle`, `mesh-no-package-chip`, etc.) are an
internal test contract documented in `docs/WEB_VERIFICATION.md`; they
are not a public API and may change without notice.

The web CFD panel and `/api/cfd/*` routes use the same local filesystem job
records as `kayakgen cfd`. They accept an explicit server-local
`mesh_package_ref`, prepare jobs under the web server's local CFD jobs root,
run the current local adapter synchronously, and expose status, logs, and raw
artifacts when present. All CFD route and panel output is raw and unvalidated;
unavailable and failed states are terminal problem states, not completed solver
work.

Current local routes:

```text
GET  /api/cfd/profiles
POST /api/cfd/jobs
GET  /api/cfd/jobs/{job_id}
POST /api/cfd/jobs/{job_id}/run
GET  /api/cfd/jobs/{job_id}/logs
GET  /api/cfd/jobs/{job_id}/raw-result
```

Set `KAYAKGEN_WEB_CFD_JOBS_ROOT` before `kayakgen serve` to choose the local
job-artifact root. Web-side mesh-package creation remains a separate follow-up
work item; create a mesh package with `kayakgen mesh-package` first.

## Mesh And CFD Readiness Caveats

Generated hull and deck meshes are useful STL surfaces for inspection and
packaging. They are not currently a closed watertight solid suitable for a
watertight CFD solver. Treat `cfd_surface_candidate` as a diagnostic staging
state, not proof that a solver can produce meaningful drag numbers.

The current local CFD layer is job plumbing: deterministic profile selection,
mesh-package gating, local job directories, status records, and adapter error
capture. It does not run a real solver unless a future adapter is added, and it
does not normalize, validate, or calibrate external solver output.

## Troubleshooting

- `kayakgen: command not found`: activate the virtual environment and reinstall
  with `python -m pip install -e .`.
- `desktop GUI extras not installed`: install `python -m pip install -e '.[desktop]'`.
- `web extras not installed`: install `python -m pip install -e '.[web]'`.
- `mesh-package solver profile mismatch`: prepare CFD jobs with a solver
  profile that matches the package profile. The default package matches
  `unavailable-open-wetted-surface`.
- `mesh package readiness below solver requirement`: the selected solver
  requires a higher readiness level than the package provides. Current
  generated packages do not satisfy watertight-solid readiness.
- `unknown solver profile`: run `kayakgen cfd profiles` and use one of the
  listed names.
- `candidate failed` in a sweep: inspect `failures.jsonl` and the candidate
  record under `candidates/`; invalid parameter combinations are recorded
  rather than stopping the whole sweep.
- Resistance or CFD values look surprising: check metadata and warnings in the
  output JSON. Resistance is raw analytical screening output; CFD dispatch
  records are raw and unvalidated.

## Current Limits

- Analytical resistance is uncalibrated and accepted only as a comparative
  filter.
- CFD dispatch is local job-state plumbing with unavailable or test adapters,
  not real solver execution.
- Mesh packages are open-surface candidates by default. Only the narrow
  fixture-backed RFC 0023 evidence path can produce watertight `cfd_ready`;
  production solver-ready meshing remains roadmap work.
- High-angle `GZ`, secondary-stability peak, and full capsize-range stability
  are unavailable as real kayak claims; fixture-only comparison records use
  bounded, unvalidated hydrostatic semantics instead.
- Some class/shape parameters are reserved or partially surfaced in frontends
  while the RFC backlog lands.
