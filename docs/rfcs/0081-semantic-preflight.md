# RFC 0081: Shared-input semantic preflight

Status: landed selected semantic preflight
Date: 2026-11-08
Context: KAYGEN-18 / retrospective R3; D067.

## Problem

The evaluation context, numerical admission, persistence and presentation slices
share load/CG, fluid, exact-speed, recorded-method and uncertainty contracts.
Their component suites previously reached expensive freezes before the combined
consumer behavior was exercised. The repaired regressions now exist; operators
need an executable handoff that selects and records them before the full gate.

## Goals

- Identify the producer, consumer and shared inputs for each selected contract.
- Reuse the landed regressions and retained independent operating-input oracle.
- Select checks from changed repository paths or explicit contract names.
- Bind the partial result to the actual candidate source and refuse source drift.
- Preserve historical, unassessed and unresolved cases under their current rules.

## Non-goals

This adds no evaluator, numerical method, git hook, automatic work assignment or
scientific acceptance policy. It cannot replace the full pytest-then-Ruff gate,
promote physical validation, or prove that an operator supplied every relevant
changed path. Unknown paths remain visible for review.

## Proposal

`python -m kayakgen.operations.semantic_preflight --changed-path PATH --out NEW_DIR`
selects fixed contract groups. Repeat `--changed-path` or `--contract` to combine
inputs. The source checkout must provide the invoked module; outputs use a new
external directory so receipt writes cannot change the candidate.

| Contract | Existing checks | Shared behavior |
| --- | --- | --- |
| `operating-inputs` | evaluation-context and operating-comparison regressions; retained 34-case oracle with integration consumers | physical load/CG, fluid, operating intent, exact speeds, CLI/sweep budget forwarding |
| `recorded-methods` | recorded-method binding regressions | conflicting saved method identities refuse; matching historical/unavailable identities and missing legacy metadata remain readable without evaluator calls |
| `numerical-admission` | assessment, interval and admission regressions | actual Fn/speed binding, wave/viscous contributions, supported policy admission, wider-pair dominance and unresolved close pairs |
| `presentation` | web speed-context and evaluation-context consumer regressions | actual sampled-speed labels and off-grid notices without inserting samples |

The work packet lists source owners, consumers, watched paths, selected pytest
targets and unmapped paths. A shared `eval/contract.py` change selects all groups;
web/desktop adapter and web-state changes select operating inputs plus
presentation. An explicit `--contract presentation` packet selects the narrower
display checks. An unrelated documentation change selects none. Operators can add an explicit group for a new consumer or a
path the maintained mapping does not yet recognize. The mapping is a bounded
routing aid, not a complete blast-radius proof.

The caller executes the real selected pytest files with environment-only
selectors and inherited full-gate skip enforcement removed. It requires a
nonempty successful JUnit result with zero skipped/deselected cases. Operating
checks additionally execute the exact retained oracle with explicit checked-in
curve/study paths, requiring all 34 cases, zero evaluator calls, unchanged source
and successful compatible/incompatible consumer controls. Historical receipt
wording remains historical; the new wrapper records the current invocation.

Receipts identify source snapshots before/after, interpreter, selected contracts,
commands, logs and observed outcomes. Candidate capture reuses
`operations.gate.source_snapshot`. A source change, failed check, missing result,
skip, timeout or interruption cannot produce a passing preflight. A new attempt
retains prior failed output rather than overwriting it.

Every outcome carries `evidence_scope="semantic_preflight"`,
`release_acceptance=false`, `full_release_gate_required=true` and
`scientific_claim_promotion=false`. No selected checks produces
`not_applicable`, never a passing release or passing semantic matrix. The
required complete release gate still runs after the candidate freezes.

## Alternatives and consequences

Leaving the existing tests as a session-local command list preserves their
oracles but loses the selected-contract handoff and source-bound result. Copying
numerical checks into a new validator creates a second policy authority. A
second git hook would duplicate the existing full/fast gate integration. The
selected wrapper owns only routing and evidence; current tests and the retained
oracle remain the semantic authorities.

## Acceptance criteria

- A context change selects the relevant consumer matrix and names shared inputs.
- Existing real regression paths cover all requested negative and positive cases.
- The operating oracle executes its 34 comparisons and consumers with zero
  numerical evaluator calls, using retained input data explicitly.
- Narrow changes avoid unrelated groups; unmapped paths are disclosed.
- Failed/partial/source-changing attempts never claim full-gate acceptance.
- The frozen candidate passes the complete pytest suite and then Ruff separately.

## Open questions

None for this bounded preflight. Add or revise routing when a new shared-input
consumer appears; do not infer its coverage from a previous receipt.

## Implementation path

Selection and actual-caller regressions, the fixed existing-oracle wrapper,
operator documentation, a retained full semantic invocation, then frozen full
pytest followed by Ruff. Root retains trunk integration and Plane acceptance.

## Domain modeling

This is an operations boundary clarification. A semantic preflight work packet
names existing domain contracts and verification ownership; it is not a new
Hull aggregate, numerical-quality policy, or scientific accepted-use state.
