---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Traceability review — workflow 0035 high-angle GZ generated-body handoff

Maps RFC 0014, RFC 0016, RFC 0020, and RFC 0024 acceptance requirements to the
current repository state on
`striatum/0035-high-angle-gz-generated-body-handoff` and identifies surfaces
that could display synthetic GZ as real kayak stability.

## Verdict rationale

Under the clarified workflow verdict contract, this slice is
`accept_with_findings`. The RFC 0024 scaffold is internally coherent:

- RFC 0024 (`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md`) defines
  the `evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)` signature,
  the gating diagnostics, the extended result contract, the `fixture_only`
  labeling rule, the assumptions/warnings surface, the summary metrics, and a
  Step 1–5 implementation path.
- The workflow scaffold (`workflow.json`, `SOURCES.md`, role prompts, write
  scopes) is complete and consistent with the RFCs it cites.
- All dependencies that RFC 0024 declares (RFC 0014 trim + reserved `GZCurve`
  boundary, RFC 0016 generated closed-body builder + diagnostics) are already
  landed in the codebase.
- The four §Open Questions in RFC 0024 are flagged for the ledger; none of
  them block deciding the safe Step 1–3 slice (each can be pinned or
  explicitly deferred without further RFC revision).

The remaining gaps are all "not implemented yet" code, contract, test, and
labeling gaps that the ledger and implementer can address inside this
workflow. None of them require an RFC or workflow correction before the
ledger runs. They are recorded as findings below for the ledger to triage.

## Findings

### F1 — `evaluate_gz_curve` does not accept the RFC 0024 signature or body_ref handoff (severity: high)

RFC 0024 §Proposal requires
`evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)` and states that
real GZ values may be emitted only when `body_ref` resolves to a generated
closed body that passes diagnostics, otherwise the result must be unavailable
with warnings. The current implementation at
`kayakgen/eval/stability.py:501-504` is:

```
def evaluate_gz_curve(*_args: object, **_kwargs: object) -> None:
    raise GZNotImplementedError(
        "high-angle GZ is reserved until closed_volume_body_not_defined is resolved"
    )
```

There is no `body_ref` argument, no heel grid, no result returned, and no
diagnostic dispatch against `diagnose_closed_volume_body`. This violates RFC
0024 acceptance items "Open display meshes, open CFD packages, and synthetic
closed-volume fixtures cannot produce real kayak GZ curves" and "Generated
bodies with failed closure or self-intersection diagnostics return unavailable
status and warnings" by absence — the evaluator cannot return any structured
unavailable result. The test
`tests/test_stability.py:131-133` only proves the blanket raise, not the RFC
0024 contract.

### F2 — Canonical unavailable warning still uses RFC 0014's `closed_volume_body_not_defined` (severity: high)

RFC 0024 §Proposal designates `generated_closed_body_not_available` (or a
more specific diagnostic-derived reason) as the canonical warning. Six
references still carry the older strings:

- `kayakgen/eval/stability.py:186` (trim path emits `high_angle_gz_not_implemented`),
- `kayakgen/eval/stability.py:354` (initial-stability path emits same),
- `kayakgen/eval/stability.py:440` (sinkage path emits same),
- `kayakgen/eval/stability.py:503` (exception message names `closed_volume_body_not_defined`),
- `tests/test_stability.py:132` (asserts the exception still names that boundary),
- `tests/test_stability.py:169` (asserts the warning text still says `high_angle_gz_not_implemented`).

This is the compatibility shim from RFC 0014 that RFC 0024 now supersedes.
Without renaming, JSON consumers cannot distinguish "evaluator not yet built"
from "generated body diagnostics failed for this hull."

### F3 — Result `GZCurve` model lacks RFC 0024 traceability fields (severity: high)

RFC 0024 §Result Contract requires the result to extend RFC 0014/0020 with
`body_ref`, `body_type`, `body_diagnostic_ref`, `heel_grid_deg`, `heel_deg`,
`gz_m`, `righting_moment_nm`, `max_gz_m`, `heel_at_max_gz_deg`,
`range_positive_stability_deg`, `area_under_positive_gz_m_deg`, `assumptions`,
and `warnings`. The current model in `kayakgen/eval/contract.py:109-115` only
has:

```
class GZCurve(BaseModel):
    angles_deg: list[float]
    gz_m: list[float]
```

`StabilityResult.gz_curve: GZCurve | None` (`kayakgen/eval/contract.py:269`)
therefore cannot carry body provenance, fixture labeling, summary metrics, or
warnings even if a future evaluator populated it. Any caller that
synthetically constructs a `GZCurve` and assigns it to `StabilityResult`
would round-trip through `EvaluationResult` JSON with no way for consumers to
tell synthetic from real.

### F4 — No `fixture_only` labeling exists for synthetic body outputs (severity: medium)

RFC 0024 §Proposal says "Synthetic explicit bodies may be used only in tests
and internal math fixtures. Their outputs must be labeled `fixture_only`."
A grep for `fixture_only` across `kayakgen/` and `tests/` returns matches
only in the RFC, this review, and the sibling ops review — no production
code, contract, or test surface carries the label. The `ClosedVolumeBody`
and `ClosedVolumeDiagnostics` already distinguish
`explicit_synthetic_triangle_mesh` from `generated_hull_plus_deck_closed_body`
at the body-type level
(`kayakgen/eval/closed_volume.py:16-19,46`), and `diagnose_closed_volume_body`
emits a `closed-volume synthetic diagnostic only; not cfd_ready` warning for
the synthetic case (`kayakgen/eval/closed_volume.py:399-404`), but neither
flag is propagated into a GZ result, sweep summary, or UI surface. Step 3 of
the RFC 0024 implementation path explicitly calls for math fixtures that
prove heel-grid and summary-metric derivation without claiming real kayak
stability — that work is not yet present.

### F5 — Hydrostatics carries a residual untyped `gz_curve` field that could leak synthetic data (severity: medium)

`kayakgen/eval/hydrostatics.py:31` declares
`gz_curve: list[tuple[float, float]] | None = None` on `Hydrostatics`. Nothing
in `evaluate()` writes it, but the field is part of the JSON schema for every
hydrostatics result (CLI `evaluate`, sweep records, web app, desktop app). A
future or third-party caller could populate it with synthetic righting arms
and it would round-trip through `EvaluationResult` with no body_ref, no
warning, no fixture label. RFC 0024 §Acceptance Criteria item 6 ("CLI/sweep/UI
surfaces do not display secondary-stability metrics when the generated-body
handoff is unavailable") requires this surface to be removed or replaced with
the typed RFC 0024 read model on `StabilityResult` only.

### F6 — RFC 0020 acceptance test coverage is missing for the cases RFC 0024 narrows (severity: medium)

RFC 0020 §Acceptance Criteria requires tests covering "unavailable body
behavior, synthetic symmetric-body behavior, non-convergence warnings, and
summary-metric derivation." Only the first cell is covered, by
`tests/test_stability.py:131-133`, and it only checks that
`GZNotImplementedError` is raised. Synthetic-fixture math, non-convergence
warnings, and summary-metric derivation will all need to land alongside the
RFC 0024 implementation.

### F7 — RFC 0024 result JSON shape is not yet observable in sweep or CLI output (severity: low/medium)

RFC 0024 §Acceptance Criteria requires "Result JSON includes `body_ref`, body
type, diagnostic ref, heel grid, assumptions, warnings, and summary metrics."
The CLI `stability` command (`kayakgen/cli/main.py:256-306`) and sweep
(`kayakgen/search/sweep.py:285-302,335-348`) currently surface only initial
GM0 and the upright trim fields. No GZ JSON shape exists for them to emit;
this is consistent with current absence of a real evaluator, but the
acceptance contract for the JSON envelope still needs to be locked in once the
evaluator lands so that downstream consumers don't fork their schemas.

### F8 — Open RFC 0024 questions are not yet resolved or recorded as deferrals (severity: low)

RFC 0024 §Open Questions lists four decisions that the implementation needs
before Step 4 (trim policy per heel vs upright fixed, deck inclusion in the
first generated stability body, deck-immersion warning string, and whether
`range_positive_stability_deg` interpolates between grid points). RFC 0014
§Open Questions has matching items, and RFC 0016 §Open Questions has the
deck-inclusion decision. None of these are pinned in code, tests, or
configuration. The implementer needs the ledger to either resolve them or
record them as explicit deferrals with `deck_immersion_warning_pending` /
`range_positive_stability_grid_bounded_only` etc. so the first slice can ship
without claiming kayak stability beyond what is decided. This is a ledger
input, not a scaffold defect — RFC 0024 itself flags these as deliberately
open.

## Surfaces that could currently display synthetic GZ as real kayak stability

- `Hydrostatics.gz_curve` (F5) — typed `list[tuple[float, float]] | None`, no
  provenance, lives on every evaluation result. Highest exposure surface.
- `StabilityResult.gz_curve` typed as the minimal `GZCurve` from
  `contract.py` (F3) — currently always `None`, but the schema permits a
  synthetic populated curve to round-trip with no `body_ref` or
  `fixture_only` flag.
- Sweep CSV/JSON (`kayakgen/search/sweep.py:285-348`) does not emit GZ today,
  but its summary contract is built from `StabilityResult` and would
  silently pick up an unlabeled `gz_curve` if F3 is not fixed before any
  populating code lands.
- Web UI (`kayakgen/ui/web/app.py:205-1112`) currently renders a single
  `HIGH_ANGLE_GZ_HEADING = "High-angle GZ unavailable"` card. That copy is
  correct today, but the UI has no contract test guaranteeing it hides a
  populated `StabilityResult.gz_curve` — if F3/F5 ship without rewiring, the
  card could be replaced by a synthetic curve render.
- Desktop GUI (`kayakgen/ui/desktop.py`) reads from the same result models
  and currently does not render GZ, but inherits the same schema risk as the
  web frontend.

## RFC requirement mapping

### RFC 0014 — Generalized Trim and GZ Stability

- `LongitudinalLoadComponent` and trim residual fields landed in workflow
  0022; verified at `kayakgen/eval/contract.py:118-138,241-269` and
  `tests/test_stability.py:34-296`.
- Upright trim solver and bow-down/stern-down sign convention
  (`+x` aft → `trim_angle_deg > 0` stern-down) implemented at
  `kayakgen/eval/stability.py:80-327`; verified by
  `tests/test_stability.py:235-296`.
- CLI/JSON exposure of trim fields:
  `kayakgen/cli/main.py:256-306`, `kayakgen/search/sweep.py:294-302`.
- Deferred high-angle `GZCurve`: RFC 0014 §Acceptance Criteria "evaluate_gz_curve
  emits real GZ values only when a named closed-volume model is used" — still
  deferred; the warning text and exception message reference the now-obsolete
  `closed_volume_body_not_defined` boundary (see F2).

### RFC 0016 — Closed-Volume Geometry

- Synthetic explicit body, policy, diagnostics: landed
  (`kayakgen/eval/closed_volume.py:55-471`,
  `tests/test_closed_volume.py:70-413`).
- `never_claim_cfd_ready`, `not_applicable_explicit_mesh` cap/deck-join,
  outward-positive signed volume, body-level manifold authority all enforced
  (`kayakgen/eval/closed_volume.py:74-103,366-450,1410-1444`).
- Generated hull-plus-deck closed body builder and policy:
  `kayakgen/eval/closed_volume.py:114-364,474-661` plus the compatibility
  shim at `kayakgen/eval/generated_closed_body.py:1-30`. Diagnostics
  consumption is verified in `tests/test_generated_closed_body.py` and
  `tests/test_cfd_jobs.py:409-435`.
- Dispatch rejection of forged watertight readiness:
  `kayakgen/eval/closed_volume.py:453-471` returns `False` for any
  `cfd_ready` request, satisfying RFC 0016 §Acceptance "Dispatch preparation
  rejects forged or hand-edited watertight manifests."

### RFC 0020 — High-Angle GZ and Secondary Stability (narrowed by RFC 0024)

- Goal "Define when a real `GZCurve` may be emitted": handled by RFC 0024.
- Acceptance "Unsupported hulls return an explicit
  `closed_volume_body_not_available` warning and no synthetic GZ values":
  current code raises `GZNotImplementedError` rather than returning a
  structured unavailable result — see F1 and F2.
- Remaining RFC 0020 acceptance items (deterministic GZ arrays, per-point
  convergence reporting, summary-metric derivation from the curve, CLI/JSON
  inclusion of assumptions/warnings/body reference/heel-grid metadata,
  test coverage of unavailable/synthetic/non-convergence/summary cases) are
  all still pending — see F1, F3, F6, F7.

### RFC 0024 — High-Angle GZ Generated-Body Handoff

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Open display meshes, CFD packages, synthetic fixtures cannot produce real kayak GZ | Partially met by absence (evaluator raises; nothing else can populate GZ) | F1, F2, F5 |
| Generated bodies with failed closure or self-intersection diagnostics return unavailable status and warnings | Not met (no evaluator dispatch on diagnostics) | F1 |
| Passing generated-body fixtures produce deterministic curves over a declared heel grid | Not met | F1 |
| Result JSON includes `body_ref`, body type, diagnostic ref, heel grid, assumptions, warnings, summary metrics | Not met (`GZCurve` lacks fields) | F3 |
| Synthetic fixture tests verify righting-arm math marked `fixture_only` and excluded from user-facing kayak stability | Not met (no `fixture_only` label exists) | F3, F4, F6 |
| CLI/sweep/UI surfaces do not display secondary-stability metrics when the generated-body handoff is unavailable | Currently met by absence; not enforced contractually | F5 (residual `Hydrostatics.gz_curve`), F7 |

Closure policy decisions called out by RFC 0024 §Open Questions and RFC 0014/0016
§Open Questions are not pinned anywhere; see F8.

## Evidence reviewed

- `docs/rfcs/0014-generalized-trim-and-gz-stability.md`
- `docs/rfcs/0016-closed-volume-geometry.md`
- `docs/rfcs/0020-high-angle-gz-secondary-stability.md`
- `docs/rfcs/0024-high-angle-gz-generated-body-handoff.md`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/SOURCES.md`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/prompts/review_traceability.md`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json`
- `kayakgen/eval/stability.py`
- `kayakgen/eval/closed_volume.py`
- `kayakgen/eval/generated_closed_body.py`
- `kayakgen/eval/hydrostatics.py`
- `kayakgen/eval/contract.py`
- `kayakgen/cli/main.py`
- `kayakgen/search/sweep.py`
- `kayakgen/ui/web/app.py` (high-angle-GZ heading and copy)
- `kayakgen/ui/theme.py` (`high_angle_unavailable` chip)
- `tests/test_stability.py`
- `tests/test_closed_volume.py`
- (cross-check) `tests/test_generated_closed_body.py`, `tests/test_cfd_jobs.py`

## Validation / read-only commands run

- `Grep` over `kayakgen/` and `tests/` for
  `gz_curve|GZCurve|gz_m|high_angle|secondary_stability|max_gz|heel_at_max|range_positive|fixture_only|body_ref|generated_closed_body_not_available|closed_volume_body_not_defined`
  (multiple narrowed passes) — confirmed F1, F2, F3, F4, F5.
- `Grep` over `kayakgen/search/sweep.py` for `gz|stability|GZ|trim|gm0|GM0` —
  confirmed sweep does not emit GZ today (relevant to F5, F7).
- `Grep` over `kayakgen/ui/` for `gz_curve|HIGH_ANGLE_GZ` — confirmed only
  the "High-angle GZ unavailable" heading and chip exist today.
- `Glob`/`Bash ls` over `docs/rfcs/` and
  `striatum/0035-high-angle-gz-generated-body-handoff/` to confirm RFC and
  workflow inventory.
- Read full source of `stability.py`, `closed_volume.py`,
  `generated_closed_body.py`, `hydrostatics.py`, `contract.py` (relevant
  lines), `cli/main.py`, `tests/test_stability.py`, `tests/test_closed_volume.py`.

No build, test, or write commands were executed.

## Residual risks

- **Schema drift via `Hydrostatics.gz_curve`.** Even after RFC 0024 lands on
  `StabilityResult`, the untyped legacy field on `Hydrostatics` remains a
  separate JSON surface in CLI `evaluate` output, sweep records, and web
  state. Implementer should delete it or migrate it explicitly; otherwise a
  divergent populator can re-introduce unlabeled GZ data downstream.
- **Warning-string churn breaking existing JSON consumers.** Renaming
  `closed_volume_body_not_defined` → `generated_closed_body_not_available`
  and `high_angle_gz_not_implemented` → diagnostic-derived strings will alter
  every cached `StabilityResult` JSON. The ledger should decide whether to
  keep both strings for one release or hard-cut.
- **`fixture_only` labeling boundary.** RFC 0024 demands the label appear on
  any result produced from a synthetic body. Without a single chokepoint
  (likely inside `evaluate_gz_curve`), a future helper that constructs a
  `GZCurve` directly from `ClosedVolumeDiagnostics` could bypass the label.
  The implementation should enforce the label at the result-construction
  boundary, not as an opt-in caller responsibility.
- **Heel-grid contract drift.** RFC 0024 requires the result to echo the
  requested grid exactly and to flag missing heel points. Bisection-style
  trim solvers used at each heel can silently drop points if non-convergence
  is handled by skipping; the implementer must record `heel_grid_deg` and
  `heel_deg` separately with per-point warnings.
- **Open questions left unresolved.** Trim policy per heel, deck inclusion,
  deck-immersion warning, and `range_positive_stability_deg` interpolation
  must be pinned or explicitly deferred by the ledger before implementation.
  Choosing silently risks producing numbers that look like real kayak
  secondary stability but represent unstated modeling assumptions.
