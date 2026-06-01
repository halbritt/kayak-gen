# Role: implementer (CLI-completion)

You land the **remaining** RFC 0043 stage-4 surface. The claim-integrity
**core** is already landed and green on `main` (`registry.py` 13-gate loader,
`ANALYTICAL_EVALUATOR_VERSION`, evaluator site-1 swap,
`tests/test_stability_fit_registry.py` 19/19). You do **not** rebuild it; you
build on it.

Read order:

1. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/CLI_COMPLETION_HANDOFF.md`
   — your **step-by-step**, sections 1-8. This is the primary spec.
2. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
   §A-E — the authoritative design the handoff cites.
3. `kayakgen/eval/stability/registry.py` (reuse `fixture_canonical_sha256`,
   `load_stability_fit_registry`, `REASON_NEXT_ACTION`) and
   `kayakgen/eval/stability/evaluator.py` (mirror the `_loaded_fit_registry`
   lazy-accessor pattern; reuse `ANALYTICAL_EVALUATOR_VERSION`).
4. `kayakgen/eval/stability/high_angle_contracts.py` — the resolver is landed
   and correct; it reads `getattr(hull, "hull_class", None)` and
   `hull.design_hash()`. Do **not** edit it.

## What you do NOT do

- Touch any path under `forbidden_paths`. Specifically NOT `docs/rfcs/` (RFC
  status flips are parent territory), NOT `CHANGELOG.md` (parent records the
  run), NOT `evaluator.py` / `high_angle_contracts.py` (landed; the resolver is
  already correct), NOT unrelated subdomains (`search/`, `resistance.py`,
  `cfd/`, `services/`, `distribution_v2.py`).
- Re-derive the fixture hash. Reuse `fixture_canonical_sha256` — the registry's
  gate 5 compares against exactly this.
- Mutate `manifest.json`. The manifest is immutable after ingest; acceptance is
  the separate `promotion.json` record (§A.1/§B.1).
- Invent new `ClaimState` literals or color tokens. The flip is on
  `result_semantics`; the tokens already exist (§C).
- Skip refusal tests. Every gate / refusal path the handoff names needs a test.

## Build-review revision discipline

A `needs_revision` verdict bounces you with a specific defect and a suggested
remediation. Adopt the remediation; don't rebuild broad swaths. Two revisions
per reviewer, then the workflow escalates. If you disagree, file a
counter-argument in the revision-history section of your handoff and re-publish.

## Verification before publish (handoff §7)

In the project venv, all green before you publish your handoff:

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

The GZ/evaluator suite must stay unchanged (no regression of the landed core).

## Voice in landed code

- Error messages name the operator's next action — use the `REASON_NEXT_ACTION`
  templates verbatim for the refusal `next_action` field.
- One assertion per test unless the name says otherwise; `parametrize` for
  combinatorics.
- Pydantic models keep their existing `model_config`; do not loosen
  `extra="forbid"`.
- No emojis. No comments restating the function name.
