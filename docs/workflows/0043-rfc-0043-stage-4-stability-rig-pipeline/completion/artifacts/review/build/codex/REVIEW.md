author: reviewer-codex-gpt-5.5-003

# Build Review - Threat Model

Verdict: request_changes

Scope: fresh, document-only review of the packet-listed files. I did not
inspect unlisted artifacts or prior review reports.

## Trust Boundaries And Attack Surfaces

- `data/stability/fixtures/<fixture_id>/manifest.json`: untrusted fixture
  manifest until parsed, checked for smoothness, trace evidence, operator-bound
  limits, rights, and hash-bound promotion.
- `data/stability/fixtures/<fixture_id>/promotion.json`: acceptance record; must
  be present, parse as a promotion packet, hash-bind to the canonical manifest,
  target `measured_stability_fixture`, and carry accepted review state.
- `data/stability/fits/*.json`: candidate fit records; must cite the fixture by
  id and sha, match runtime evaluator version, be strict accepted, and declare a
  hull-family scope that matches the measured fixture hull class.
- `Hull.hull_class`: caller-authored hull-family tag; unset/non-string values
  must keep the analytical label unvalidated.
- Registry cache: any cache key must invalidate when evidence required by the
  gates changes or disappears, not only when fit JSON changes.

## Findings

### P2 - Missing regression for cached fit after trace evidence is deleted

`kayakgen/eval/stability/registry.py:215` gates required trace evidence on disk,
and `_dir_fingerprint()` now scans the fixture tree including non-JSON evidence
at `kayakgen/eval/stability/registry.py:442`. That code addresses the threat,
but the listed tests do not lock it down.

The current tests cover a cold-load missing-trace refusal in
`tests/test_stability_fit_registry.py:335` and cache invalidation after adding a
fit JSON in `tests/test_stability_fit_registry.py:372`. They do not cover the
specific threat path from the handoff: load a passing fit, let it enter the
non-diagnostic registry cache, delete `fixtures/<id>/cal/pre.csv` or
`post.csv`, then call `load_stability_fit_registry(root)` again without
`clear_registry_cache()` and assert the fit is dropped.

Impact: a future cache-key regression could silently reintroduce the original
claim-label bypass, where the full chain is no longer present but a previously
cached fit can still reach `resolve_analytical_claim_label()`.

Required fix: add the explicit cached-pass-then-delete regression test to
`tests/test_stability_fit_registry.py`.

## Confirmations

- The production evaluator path calls `resolve_analytical_claim_label()` with
  `_loaded_fit_registry()` in `kayakgen/eval/stability/evaluator.py:407`, so the
  label flip is backed by the loader gates.
- The loader requires manifest, promotion packet, manifest sha match, promoted
  target, fixture citation, hull-class binding, heel-range overlap, evaluator
  version match, and strict accepted fit before a record can reach the resolver
  (`kayakgen/eval/stability/registry.py:187` through `:340`).
- The new hull-class binding rejects a fit whose
  `hull_family_scope.hull_class` differs from the measured fixture's
  `hull_identity.hull_class` at `kayakgen/eval/stability/registry.py:305`, and
  the listed registry tests cover that rejection in
  `tests/test_stability_fit_registry.py:281`.
- An unset real `Hull.hull_class` keeps the label unvalidated through
  `resolve_analytical_claim_label()` at
  `kayakgen/eval/stability/high_angle_contracts.py:66`, with coverage in
  `tests/test_resolve_analytical_claim_label.py:157`.
- `promote-fixture` writes `promotion.json` and asserts that manifest bytes are
  unchanged at `kayakgen/cli/stability_cli.py:236` through `:250`.
- `accept-fit` refuses sha mismatch, unpromoted promotion packets, evaluator
  version mismatch, and strict-skipped records at
  `kayakgen/cli/stability_cli.py:345`, `:354`, `:404`, and `:412`.
- The real-Hull production flip test now stages a full acceptance triple and
  resolves through `load_stability_fit_registry()` in
  `tests/test_resolve_analytical_claim_label.py:201`, rather than only passing a
  hand-built record straight to the resolver.

## Residual Notes

`resolve_analytical_claim_label()` is intentionally a pure resolver over a
caller-supplied registry. A direct caller can still pass a hand-built accepted
record and get a validated label; the reviewed production call sites avoid that
by loading through `load_stability_fit_registry()`.
