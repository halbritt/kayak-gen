# FINAL_REVIEW - workflow 0035 high-angle GZ generated-body handoff

Verdict intent: accept

## Summary

The implementation lands the conservative RFC 0024 handoff slice the ledger
authorised. `evaluate_gz_curve` now returns a structured `GZCurve` envelope,
generated closed bodies are gated against the existing
`ClosedVolumeBody`/`ClosedVolumeDiagnostics` evidence chain, synthetic explicit
bodies are barred from real kayak claims, and fixture math is reachable only
when `fixture_only=True` is set explicitly. CLI, sweep, and web surfaces stay
in the documented unavailable/warning posture, and the legacy
`hydrostatics.gz_curve: null` JSON path still round-trips. The full pytest
suite passes (272 passed, 3 skipped for unrelated web/browser extras).

Every ledger rejection criterion is satisfied: open/CFD/synthetic/legacy bodies
cannot produce real kayak GZ; unavailable payloads are forbidden by the model
from carrying numeric curve or summary values; result JSON carries body
provenance, diagnostic reference, requested heel grid, assumptions, warnings,
and an availability status; generated-body diagnostics never claim CFD-ready.

## Findings

### F-A - Medium - Comparison-objective gating and crafted-record negative test absent

`kayakgen/search/compare.py:213` still promotes every finite numeric
`record.summary[*]` into objective metrics and `parse_objective`
(`kayakgen/search/compare.py:94`) still accepts arbitrary metric names. The
ledger F-004 required both a comparison gate and a "negative tests with
crafted records containing GZ-like numeric fields" check.

The implementer correctly notes that `kayakgen/search/` was outside this
packet's write scope (see `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json`
implementer.write_scope.allowed_paths) so the compare.py edit had to defer.
This is legitimate scope containment.

However, `tests/` was in write scope. A crafted-record test that injects
`summary={"max_gz_m": ..., "heel_at_max_gz_deg": ...}` into a
`CandidateRecord` and asserts that compare.py either drops or warns on the
metric would have closed F-005's negative-test bullet without touching
search code, and would catch any regression the day comparison gating lands.

Severity is medium rather than high because no current evaluator or sweep
path writes GZ-named keys into `record.summary` — the only producer of those
keys is `GZCurve`, which never reaches `record.summary`. The defensive
forbidden-set checks added in `tests/test_sweep.py:144-155` and the
CLI/web tests guard the present production paths well; the gap is in
future regression coverage.

Required follow-up (track as a deferral, not a blocker):
- Add comparison gating in `kayakgen/search/compare.py` so GZ-like metrics
  require accepted generated-body provenance.
- Add a negative test in `tests/test_compare.py` that constructs a
  `CandidateRecord` with GZ-named numeric summary keys and asserts they do
  not become objective metrics, or that they carry a provenance warning.

### F-B - Low - `Hydrostatics.gz_curve` legacy field still permits non-null payloads

`kayakgen/eval/hydrostatics.py:31` keeps the legacy field
`gz_curve: list[tuple[float, float]] | None = None` unchanged. The ledger
F-002 asked for the field to be "quarantine[d], remove[d], or migrate[d]
deliberately. Old JSON with `hydrostatics.gz_curve: null` should remain
compatible if possible, but non-null legacy curves must not be promoted to
real GZ."

The implementation preserves the null-compatibility path
(`tests/test_stability.py::test_legacy_hydrostatics_null_gz_curve_still_round_trips`)
but does not actively forbid a non-null legacy payload from validating
through `Hydrostatics.model_validate`. In practice no production code path
populates this field today, and the new strict `StabilityResult.gz_curve`
type (`kayakgen/eval/contract.py:353`) is the only surface that consumes a
`GZCurve` — but the latent loophole would allow a malicious or mistaken
upstream caller to round-trip a tuple-of-pairs GZ curve through hydrostatics
without provenance.

Suggested follow-up: either change the type to `None` only (with a
deprecation shim accepting legacy null), or add a validator that rejects
non-null legacy values. Either change is small; both can be deferred since
nothing presently emits the field.

### F-C - Low/Info - Diagnostic warnings embed raw exception text

`kayakgen/eval/stability.py:669,673` produce warning strings of the form
`f"closed_volume_diagnostic_unavailable: {exc}"` and
`f"closed_volume_diagnostic_invalid: {exc}"`. Embedding `repr(exc)` makes
the warning code unstable for downstream consumers that pattern-match
warning prefixes (RFC 0024 contract values, sweep-side gating). The
canonical-prefix portion is still pattern-matchable, but a stricter contract
would emit a fixed sentinel and place free-form detail in a separate
diagnostic field. Not a blocker.

### F-D - Info - Synthetic-fixture warnings include the canonical `fixture_only` token

`_fixture_gz_curve` emits `warnings=["fixture_only",
"synthetic_closed_body_not_generated_kayak",
"not_user_facing_secondary_stability"]` and the GZCurve validator requires
`fixture_only=True` for synthetic bodies. The web layout test
(`tests/test_web_layout.py:139-148`) explicitly forbids the literal token
`fixture_only` in render-source copy. This pair is correct and provides
defense in depth, but readers should not confuse the warning token with a
user-facing string — adding a code comment on the `_fixture_gz_curve`
warning list (or a constant) would make this less brittle if either side
changes wording. Optional.

## Verification reviewed

The implementer ran the relevant suites in `/tmp/kayakgen-0035-venv`:

- `tests/test_stability.py` (31 passed)
- `tests/test_closed_volume.py` + `tests/test_generated_closed_body.py` (31
  passed)
- `tests/test_cli.py`, `tests/test_sweep.py`, `tests/test_web_layout.py`
  (27 passed, 1 skipped for `kayakgen[web]` extras)
- `tests/test_compare.py` (22 passed)

I re-ran the same set plus the full suite in the same venv during this
review:

- Targeted run: `tests/test_stability.py tests/test_cli.py tests/test_sweep.py
  tests/test_web_layout.py tests/test_compare.py tests/test_closed_volume.py
  tests/test_generated_closed_body.py` — 111 passed, 1 skipped.
- Full suite: 272 passed, 3 skipped (`tests/test_web.py`,
  `tests/test_web_layout.py`, `tests/test_web_browser.py` skips are
  pre-existing and unrelated to this packet).

Surface spot-checks confirmed:

- CLI: `kayakgen/cli/main.py:303` only ever invokes initial/equilibrium
  evaluators; both set `StabilityResult.gz_curve=None`
  (`kayakgen/eval/stability.py:230,292,350,394,521`). CLI never calls
  `evaluate_gz_curve`. The CLI JSON test asserts `gz_curve is None` and
  forbids the GZ summary keys (`tests/test_cli.py:385-399`).
- Sweep: `kayakgen/search/sweep.py:96` exposes an arbitrary `summary` dict,
  but no GZ keys are ever written; the new sweep test asserts both the CSV
  header and `record.summary` are GZ-free
  (`tests/test_sweep.py:144-155`).
- Web: `kayakgen/ui/web/app.py:205-1110` keeps the "High-angle GZ
  unavailable" copy and routes via the `RFC 0020 / RFC 0024` references; the
  forbidden-render-token test now covers the RFC 0024 vocabulary
  (`tests/test_web_layout.py:136-152`).
- Model boundary: `GZCurve` rejects legacy `angles_deg/gz_m`
  (`kayakgen/eval/contract.py:139-146`), enforces finite values, requires
  array-length alignment, forbids numeric values in unavailable payloads,
  and forces `fixture_only=True` on synthetic body types
  (`kayakgen/eval/contract.py:176-199`).
- Generated-body gate: the warnings list in
  `_generated_body_gz_gate_warnings` checks body type, profile, cap,
  deck-join, self-intersection, normal-orientation and waterline policies,
  part identity, source hull hash match, diagnostics readiness, all
  topology zero-counts, positive signed volume above tolerance,
  self-intersection-status `passed`, and `cfd_ready` strictly `False`
  (`kayakgen/eval/stability.py:718-814`). When all gates pass the result
  remains unavailable with
  `high_angle_gz_generated_body_solver_not_implemented`, never numeric
  values.

## Residual risks and deferrals

1. Real generated-kayak high-angle GZ physics remains deferred. Even with a
   passing generated body, the result is unavailable with
   `high_angle_gz_generated_body_solver_not_implemented`. Unblocking
   requires the heeled-volume solver and CG/trim policy decisions enumerated
   in the ledger "Explicit deferrals" section.
2. Comparison-source hardening (F-A) is deferred until a future workflow
   widens write scope to `kayakgen/search/`. No current path emits GZ-named
   metrics into sweep summaries, so the gap is regression coverage rather
   than an active leak.
3. `Hydrostatics.gz_curve` (F-B) remains a passive legacy field. No code
   path populates it; tightening it is small but out of scope here.
4. CLI/UI copy continues to surface "High-angle GZ unavailable" with the
   RFC 0020/0024 reference. Once a verified GZ slice lands this copy must be
   revisited together with the cockpit/flooding and CG policy decisions
   listed in the ledger.
5. The root `CHANGELOG.md` was not edited (workflow write scope). The
   patch summary contains the proposed wording for the operator to apply.
