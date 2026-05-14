# Patch Summary - Workflow 0035

## Findings addressed

- F-001: `evaluate_gz_curve(...)` now returns an RFC 0024 `GZCurve` envelope
  instead of raising the old closed-volume-not-defined exception. Missing,
  unresolved, unsupported, synthetic-as-real, failed-diagnostic, mismatched, and
  pass-but-unsolved generated bodies return structured unavailable results.
- F-002: `GZCurve` now carries availability, body provenance, diagnostic
  reference, requested heel grid, computed arrays, summary metrics,
  assumptions, warnings, and a `fixture_only` label. Legacy minimal
  `angles_deg/gz_m` payloads are rejected rather than promoted.
- F-003: the GZ boundary validates generated closed bodies against
  `ClosedVolumeBody` and `ClosedVolumeDiagnostics`, including generated profile,
  source hull hash, coordinate/unit/policy metadata, topology counts, positive
  signed volume, and passed self-intersection diagnostics. Synthetic explicit
  bodies can compute only with `fixture_only=True`.
- F-004: in-scope public surfaces remain guarded. CLI stability JSON keeps
  `gz_curve: null`; web render-source tests forbid secondary-stability numeric
  tokens; generated sweep summaries and CSV headers remain free of GZ metrics.
- F-005: added focused tests for unavailable output, heel-grid validation,
  synthetic fixture-only math, generated-body diagnostic success/failure
  boundaries, JSON round trips, legacy minimal curve rejection, and public
  surface hiding.

## Files changed

- `kayakgen/eval/contract.py`
- `kayakgen/eval/stability.py`
- `tests/test_stability.py`
- `tests/test_cli.py`
- `tests/test_sweep.py`
- `tests/test_web_layout.py`
- `striatum/0035-high-angle-gz-generated-body-handoff/implementation/PATCH_SUMMARY.md`

## Verification

Used a temporary virtualenv at `/tmp/kayakgen-0035-venv` because the system
Python had no project dependencies or pytest installed.

- `python3 -m compileall kayakgen/eval kayakgen/cli kayakgen/ui tests/test_stability.py tests/test_cli.py tests/test_sweep.py tests/test_web_layout.py`
  - Result: passed.
- `/tmp/kayakgen-0035-venv/bin/python -m pytest tests/test_stability.py -q`
  - Result: 31 passed.
- `/tmp/kayakgen-0035-venv/bin/python -m pytest tests/test_closed_volume.py tests/test_generated_closed_body.py -q`
  - Result: 31 passed.
- `/tmp/kayakgen-0035-venv/bin/python -m pytest tests/test_cli.py tests/test_sweep.py tests/test_web_layout.py -q`
  - Result: 27 passed, 1 skipped (`kayakgen[web]` not installed).
- `/tmp/kayakgen-0035-venv/bin/python -m pytest tests/test_compare.py -q`
  - Result: 22 passed.

## Residual risks and deferrals

- Real generated-kayak high-angle GZ physics remains deferred. Even when a
  generated body passes diagnostics, the result is unavailable with
  `high_angle_gz_generated_body_solver_not_implemented` and no numeric GZ
  values.
- Comparison-source hardening for crafted GZ-like numeric summary fields is
  still deferred because the enforcing files are under `kayakgen/search/`,
  which is outside this packet's allowed write scope. The current generated
  sweep path does not emit GZ metrics, and existing comparison tests still pass,
  but crafted records can only be fully guarded by changing
  `kayakgen/search/compare.py`.
- No root `CHANGELOG.md` edit was made due to the workflow write scope.

## Proposed root CHANGELOG.md wording

```markdown
- Added the RFC 0024 high-angle GZ handoff envelope: generated closed-body
  diagnostic validation, structured unavailable results, fixture-only synthetic
  math, provenance-safe GZ fields, and tests that keep unavailable or fixture
  curves out of CLI, web, and generated sweep secondary-stability claims.
```
