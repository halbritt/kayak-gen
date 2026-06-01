# Build review prompt — 0043 stage-4 CLI completion (2-lane)

You review the implementation landed by the `implement` job under your assigned
posture. The step-by-step spec is
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/CLI_COMPLETION_HANDOFF.md`;
the authoritative design is
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`;
the implementer's handoff is
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/CLI_COMPLETION_RESULT.md`.

Write to
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/completion/artifacts/review/build/<lane>/REVIEW.md`.

## Postures

- **ergonomics_dx** (claude lane) — operator + developer experience of the
  landed code. Run `kayakgen stability --help` and confirm `claim-status`
  surfaces. Run `promote-fixture` / `accept-fit` / `claim-status` against an
  in-test triple and confirm each works end-to-end. Trigger a structured
  refusal and confirm the JSON line's `next_action` names the operator's
  remediation. Confirm the `accept-fit` Typer error path names `--packet` as
  removed and points at `--fixture-id`. Read the USER_GUIDE stage-4 subsection
  and confirm an operator who reads only it can run the pipeline.
- **threat_model** (codex lane) — surfaces of attack on the acceptance gate and
  the claim-label flip chain as landed. Find any path where the label flips
  without the full hash-bound chain (manifest + accepted `promotion.json` +
  strict-accepted fit + evaluator-version match + `hull_family_scope`
  coverage). **Scrutinize the new `hull_class` plumbing**: can a wrong,
  over-broad, default, or attacker-controlled `hull_class` flip a hull it
  should not cover? Confirm an unset `hull_class` keeps the unvalidated label
  and that `high_angle_contracts.py` was not weakened. Confirm `promote-fixture`
  does not mutate `manifest.json` and that `accept-fit` refuses
  unpromoted / sha256-mismatch / evaluator-version-mismatch / strict-skipped
  inputs. Verify the tests cover the threat surface — and that the
  production-flip test exercises the real resolver, not a stub.

## Required content

### Decision

Exactly one of: `accept` · `accept_with_findings` · `needs_revision`.

**Do NOT use `reject`.** In this workflow `reject` is terminal and
non-recoverable: it fails the review job permanently, cannot be re-cycled,
retried, or overridden, and wedges the run. If the implementer could revise to
address your findings, return `needs_revision`. The cycle allows two revisions
before escalation.

### Required checks

For each, mark `pass` / `fail` / `n/a` and cite `file:line`:

1. **`promote-fixture`** writes `promotion.json` verbatim and does NOT mutate
   `manifest.json` (manifest bytes byte-equal to ingest output).
2. **`accept-fit`** uses `--fit-record/--fixture-id/--out`, `--packet` removed,
   refuses on the §B gate failures, writes a byte-stable record.
3. **`claim-status`** emits the §A.4 JSON shape; `--debug` lists dropped-fit
   diagnostics with `REASON_*` codes.
4. **`--help` + refusals** — `claim-status` listed; refusals are one structured
   JSON line with `next_action` from `REASON_NEXT_ACTION`.
5. **Web swaps** — both `generate_frontier_view.py` and `generate_spec_form.py`
   load a real mtime-memoized registry (no `EMPTY_STABILITY_FIT_REGISTRY`);
   imports cleaned.
6. **Tests** — the three new files + `conftest` triple factory exist; the
   §7 gate passes; `test_cli_stability.py` swept to the new signature.
7. **hull_class** — `Hull` carries `hull_class`; unset keeps the unvalidated
   label; a real-`Hull` production-flip test exists and passes.
8. **Docs** — USER_GUIDE / SOURCES / DECISION_LOG updates land in the right
   sections; the two resistance-side findings recorded as follow-ups.

### Posture-scoped findings

- Surface (1-8). Issue (one sentence). Evidence (`file:line`). Impact.
  Suggested remediation.

### Out-of-posture observations

Mark each `out-of-posture: <one line>`.

## Operating discipline

- You do NOT write or modify implementation files. Your write_scope is your own
  `REVIEW.md`.
- You do NOT coordinate with the other reviewer.
- You MAY run `.venv/bin/pytest` and `kayakgen stability --help`; both are
  read-only on the landed code.

## Output

One file: `.../completion/artifacts/review/build/<lane>/REVIEW.md`. Under 1500
words. Cite `file:line` for every finding.
