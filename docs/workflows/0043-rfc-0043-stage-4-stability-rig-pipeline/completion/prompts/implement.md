# Implement prompt — 0043 stage-4 CLI completion

You land the remaining RFC 0043 stage-4 surface. The claim-integrity **core**
is already landed and green on `main`; you build on it, you do not rebuild it.

Read first, in order:

1. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/CLI_COMPLETION_HANDOFF.md`
   — your **step-by-step**, sections 1-8. Follow it literally; it cites the
   synthesis for every step.
2. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
   §A-E — the authoritative design.
3. `kayakgen/eval/stability/registry.py`, `kayakgen/eval/stability/evaluator.py`,
   `kayakgen/eval/stability/high_angle_contracts.py`,
   `kayakgen/eval/stability/accepted_fit.py`,
   `kayakgen/eval/stability/measured_fixture.py`, `kayakgen/cli/stability_cli.py`.

## Deliverables (handoff sections 1-6)

Land each, exactly as the handoff specifies:

1. **`promote-fixture`** (handoff §1 / synthesis §A.2) — validate the packet,
   check `fixture_ref.fixture_sha256 == fixture_canonical_sha256(manifest)`
   (reuse the registry helper; do not re-derive), write the packet **verbatim**
   to `data/stability/fixtures/<fixture_id>/promotion.json`. Do **not** mutate
   `manifest.json`. Re-promote with identical bytes = clean no-op.
2. **`accept-fit`** (handoff §2 / synthesis §A.3) — new signature
   `--fit-record <path> --fixture-id <id> --out <path>`; **remove `--packet`**.
   Resolve the fixture dir, validate the co-located `promotion.json`, hash the
   manifest, confirm the fit cites `(fixture_id, fixture_sha256)`, refuse with
   the §B reason token on any failure. Output the `StabilityFitRecord` to
   `--out` with `acceptance_verdict="accepted"`, `strict=True`. The Typer error
   path for a passed-in `--packet` must name it as removed and point at
   `--fixture-id`. Sweep in-tree callers (`tests/test_cli_stability.py`, docs).
3. **`claim-status <hull>`** (handoff §3 / synthesis §A.4) — new read-only
   command emitting one JSON line with the §A.4 shape; `--debug` adds the
   `diagnostics` list from `load_stability_fit_registry(..., with_diagnostics=True)`.
4. **`--help` + refusal copy** (handoff §4 / synthesis §E.1,§E.3) — update
   `kayakgen stability --help`; every refusal emits one structured JSON line
   `{"ok": false, "code": ..., "fixture_id": ..., "details": {...},
   "next_action": ...}` with `next_action` taken from `REASON_NEXT_ACTION`
   (import it; do not re-author the remediation text).
5. **Two web call-site swaps** (handoff §5 / synthesis §C.4) — replace
   `EMPTY_STABILITY_FIT_REGISTRY` at `generate_frontier_view.py:568` and
   `generate_spec_form.py:897` with a lazy mtime-memoized
   `load_stability_fit_registry()` accessor (copy the
   `evaluator._loaded_fit_registry` shape). Drop the now-unused imports.
6. **Tests** (handoff §1-§5 + synthesis §D) — add
   `tests/test_measured_stability_acceptance.py`,
   `tests/test_measured_stability_ingest.py`,
   `tests/test_claim_state_measured_promotion.py`; lift the in-test triple
   factory into `tests/conftest.py` as `make_stability_acceptance_triple`;
   sweep `tests/test_cli_stability.py` to the new `accept-fit` signature. Cover
   every refusal path the handoff names.
7. **Docs** (handoff §6 / synthesis §E.2,§E.4) — append the §E.2 stage-4
   subsection to `docs/USER_GUIDE.md`; update
   `docs/workflows/0043-.../SOURCES.md` per §E.4; add a `docs/DECISION_LOG.md`
   D-series row recording stage-4 completion AND a follow-up row for the two
   synthesis §5 resistance-side findings (opaque-token bypass;
   `AcceptedFitRecord` fixture-binding) as future-RFC scope.

## ADDENDUM — plumb `hull_class` end-to-end (operator-added scope)

The handoff §3 note flags that `Hull` exposes no `hull_class`, so
`resolve_analytical_claim_label` always reads `None` and the label can never
flip for a real generated hull (today the resolver tests pass only via a
`_HullWithScope` stub). This run **closes that gap** so the flip works in
production.

- Add `hull_class` to the `Hull` aggregate (`kayakgen/model/hull.py`) reusing
  the **existing** calibration-envelope vocabulary
  (`sea_kayak` / `sprint_k1` / `kayak_general` / `pacific_canoe_like_slender` /
  …; see `kayakgen/eval/calibration/__init__.py`,
  `MeasuredStabilityFixture.hull_class`, `HullFamilyScope.hull_class`). An
  explicit optional field (`hull_class: str | None = None`) is the low-risk
  default; a geometry-derived classifier is acceptable **only** if it cannot
  over-broaden a class. State your choice + rationale in the handoff.
- **Safety invariant (the threat_model reviewer gates this):** an unset /
  `None` `hull_class` MUST keep the label `unvalidated_hydrostatic_comparison`.
  Do not default to a real class that would auto-flip hulls. The resolver
  already enforces the `None` case — preserve it; do not weaken
  `high_angle_contracts.py`.
- `Hull.design_hash()` already exists — the design-hash half of the resolver
  works; you only add `hull_class`.
- Add a **production-path integration test** (in
  `tests/test_resolve_analytical_claim_label.py` and/or
  `tests/test_claim_state_measured_promotion.py`) that builds a **real `Hull`**
  (not the `_HullWithScope` stub) carrying a `hull_class`, an accepted fit whose
  `hull_family_scope.hull_class` matches and whose `design_hash_envelope`
  contains the hull's `design_hash()`, and asserts the evaluator + the web
  frontier flip to `validated_hydrostatic_comparison`. Add the negative: a hull
  with no `hull_class`, or a mismatched class, stays unvalidated.
- The web `generate_spec_form.py:861` `_current_hull_family_scope` already reads
  `hull_class`/`design_hash` off `base_hull`; confirm it now resolves once the
  base hull carries `hull_class` (no separate fix needed if the serialized Hull
  includes the new field).

## Workflow handoff

Write `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/CLI_COMPLETION_RESULT.md`:

- Files changed (path + line counts).
- Pytest summary (collected / passed / failed / skipped) for the §7 gate +
  `ruff` result.
- Section-by-section evidence: handoff §1-§7 + the hull_class addendum — for
  each, cite `file:line` where it landed and quote one line of evidence.
- The `hull_class` mechanism you chose (explicit field vs derived) + why, and
  the test that proves the production flip.
- Any review recommendations you did NOT adopt and why (revision-history).

## Verification (handoff §7)

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

All green + the GZ/evaluator suite unchanged before you publish the handoff.

## Scope discipline

Write only to `write_scope.allowed_paths`. `forbidden_paths` bars `docs/rfcs/`,
`CHANGELOG.md`, `evaluator.py`, `high_angle_contracts.py`, and unrelated
subdomains. Do not work around these through an allowed path.
