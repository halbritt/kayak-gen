# RFC 0087: Current ledger acceptance versus historical pending flags

Status: landed receipt-applicability ledger view and proposed finalization
Date: 2026-11-08
Context: KAYGEN-24 / retrospective R9; D073; `kayakgen/operations/ledger_finalization.py`.

## Problem

The final implementation ledger for 2026-11-07 marks W3 accepted and deployed.
`final_verification.installed_workflow` is `"full passed"` and the item's final
source is tree `74d6a42f`. Its component `verification` block still holds
`final_numerical_render_pending: true`. Nothing in the ledger says whether that
flag is a current failure or a milestone snapshot taken before the final
render. A reader cannot tell. A finalizer that clears every pending flag could
also erase a real newer obligation, or let an old green receipt hide a
regression on another source.

## Goals

- Derive each mandatory criterion's current status from receipts that apply to
  the item's accepted source, and link the criterion to those receipts.
- Keep a retained pending flag visible. Classify it as history only when
  ordering is proven; otherwise report an explicit conflict.
- Never clear a pending flag that is newer, observed on another source, or
  observed at an unknown time without other proof.
- Represent future physical obligations, such as calibration, as open
  obligations that receipts cannot clear and that do not block current
  acceptance.
- Produce a proposed finalized ledger. Keep the exact original bytes in a
  separate history file and never overwrite the original.

## Non-Goals

Authenticated receipts, automatic application to a live ledger, inference of
legacy timestamps, Plane state changes, and any widening of calibration,
physical validation, safety, final-fitness or hosted-worker claims are out of
scope. The tool changes no scientific claim state.

## Proposal

A version-1 **Ledger finalization policy** names the ledger by SHA-256 and
lists criteria. Each criterion names a ledger item `work_id` and has one of two
`obligation` values:

- `mandatory` declares `applicable_source` (`source_tree` and/or
  `source_commit`) and supporting `receipts`. It can also declare the `pending`
  flag it explains.
- `future` holds only a requirement. Receipts or pending declarations on a
  future obligation are refused. Its status is always `open_future`.

Receipt specifications use the RFC 0079 shape and validator: path, byte SHA-256,
source-field JSON pointers and `equals` predicates. Each receipt binds a
nonempty subset of the declared source. Together the receipts must bind all of
it. An optional `observed_at` pointer selects an RFC 3339 time recorded inside
the receipt.

Applicability rules for a mandatory criterion:

1. The applicable source must equal the item's accepted `final_source_tree` and
   `final_source_commit`. A criterion bound to newer main is a conflict, not a
   reinterpretation of historical acceptance.
2. Every receipt must match its bytes, source binding and predicates. A
   failing receipt is listed as a reason and does not support the criterion.
3. A pending flag whose value is `true` is classified `historical` only if one
   of these ordering proofs holds and no rule fails:
   - `git_ancestry`: the snapshot's evidenced `observed_source.source_commit`
     is a strict ancestor of the accepted commit (`--repo` is required).
   - `timestamps`: the snapshot's known `as_of` is earlier than the recorded
     `observed_at` of every supporting receipt.

   `as_of: "unknown"` is allowed. A snapshot with unknown time and unknown
   source, a snapshot observed on the accepted source, a descendant or
   unrelated commit, or a receipt that is not later stays `current_conflict`.
4. Any other `true` flag whose key contains `pending` in a ledger item, outside
   the tool-owned history and current blocks, is reported as
   `undeclared_pending`. That makes the item a conflict.

The **Ledger view** (`kayakgen.ledger-view/1`) reports each item's
`current_status`:

- `accepted`: Plane `Done` with at least one accepted mandatory criterion and
  no conflict.
- `claimed_unreviewed`: `Done` with no declared criteria.
- `not_accepted`: not `Done`.
- `conflict`: any conflicting criterion or undeclared pending flag.

`python -m kayakgen.operations.ledger_finalization view --ledger L --policy P
[--repo R]` prints the view. It exits 0 when consistent, 1 on conflict and 2
on refusal. `finalize ... --out NEW --history NEW` refuses conflicting views
and existing paths. It writes the original ledger bytes to `--history`. It then
writes a proposed ledger. In that ledger, only proven-historical flags move into
the item's `ledger_history` with value, `as_of`, observed source, ordering
basis and superseding receipt hashes. Each item also gets
`current_criteria` with receipt links, and the top level gets `finalization`
with the previous ledger SHA-256. All other fields, including unrelated flags,
stay unchanged. Running `view` again over the proposed ledger reads the flag
from `ledger_history` and reaches the same classification.

## Real-ledger evidence

This check ran on an isolated byte copy of the actual ledger (`00bf8d5c…`) and
its final receipts. The W3 pending flag came from a component gate receipt
whose source fingerprint `074b4a…` was recomputed exactly from commit
`3cbb84f`. That commit is a strict ancestor of accepted commit `95d2bf7`. The
installed handoff, final render provenance and activation receipts bind tree
`74d6a42f`. W3 is therefore `accepted`, and its flag is `historical` by Git
ancestry with `as_of: "unknown"`. Four controls each produced a conflict: a
pending flag declared on newer main, a criterion moved to newer main, an
undeclared flag, and a missing repository. Root owns application to the live
ledger after review.

## Acceptance Criteria

- The final W3 render criterion is accepted from its installed/report receipts,
  and its earlier pending snapshot is preserved as history.
- An accepted item cannot keep an unresolved mandatory pending flag unless an
  explicit conflict or historical classification is present.
- An older successful receipt cannot clear a newer or source-mismatched pending
  flag. A receipt bound to another source does not support the criterion.
- Future calibration obligations and conflicting snapshots remain
  representable, and finalization moves only proven history.
- Controlled mixed fixtures, plus the real ledger copy, produce a verifiable
  view and proposed ledger with each current criterion linked to its receipts.

## Open Questions

None in this scope. Authenticated receipts, concurrent ledger writers or
automatic live application need a separately accepted contract.

## Implementation Path

One landing: mixed Git-lineage fixture tests, the module and CLI, operator
documentation, then frozen-source full pytest and Ruff. Root applies the
proposed ledger after review.

## Domain Modeling

This is an operations boundary under `DDD.md`'s “Adding to the model” guidance.
Ledger finalization policies and views are operational value descriptions.
They are not hull-domain aggregates or scientific acceptance states.
