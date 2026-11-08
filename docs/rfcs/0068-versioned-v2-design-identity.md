# RFC 0068: Versioned physical identity for distribution_v2 hulls

Status: landed versioned v2 physical identity
Date: 2026-11-07
Context: KAYGEN-6; D029/D030/D053; RFCs 0048/0049/0067; system review kayakgen-system-20261107.

## Problem

The scalar-only design hash omitted every nested `distribution_v2` input. Two
v2 hulls with different vertices and displaced volumes could have one identity.
Using that value for evidence scope or cross-run lookup erased a physical
boundary. A new unmarked digest would also obscure which meaning an old value
had. Calibration ingest still used the obsolete record-hash placeholder.

## Goals

- Distinguish v2 shape inputs and identify their hashing scheme explicitly.
- Preserve lofted design hashes, full record/content/run hashes and historical files.
- Keep old ambiguous v2 identities out of new physical evidence applicability.
- Support existing string-based index, query, campaign and fit consumers.

## Non-Goals

No geometry/evaluator changes, new storage backend, automatic fit reacceptance,
physical validation, or historical evidence rewriting. This does not infer
physical equivalence from two different parametrizations of the same surface.

## Proposal

`Hull.design_hash()` and `design_hash_for_hull` return:

- Lofted: exactly the existing bare 64-character SHA-256 value.
- V2: `distribution_v2_v2:<sha256>`, hashing canonical sorted compact JSON with
  `scheme="distribution_v2_v2"`, `length_m`, and the complete serialized nested
  `distribution_v2` spec. The prefix and digest payload both name the scheme.

The v2 strategy reads length and nested distributions/family controls. Legacy
scalar draft/beam/coefficient fields do not drive its shape and are excluded.
The whole nested spec is conservatively bound, including reserved intent
controls, so a future geometry change cannot silently reuse their old identity.
Names and hull-class labels are excluded. Record serialization is unchanged.

`Hull.legacy_design_hash()` / `legacy_design_hash_for_hull` reproduce the former
scalar-only algorithm for historical inspection. For v2 this accessor is not
physical-equivalence evidence and is never used by current applicability gates.
Old files and expected artifact hashes are not modified. No read-time conversion
from a bare digest to a v2 identity exists.

### Consumer inventory and enforcement

| Consumer | Handling |
|---|---|
| `search/sweep.py:_index_row_for_candidate`, active runner | New rows call the current `Hull.design_hash()`. Candidate keys remain spec/parameter identities. |
| `services/artifact_store.py:reindex_run` | Computes derived candidate identity from the full verified record; canonical files, manifests and expected content hashes remain unchanged. Legacy incomplete provenance stays incomplete. |
| `SqliteIndex`, `CandidateSummary`, `runs query` | Store/return full strings; no 64-hex validation or prefix stripping. Filter parsing splits only the first colon. No SQLite schema migration is necessary. Historical index entries remain historical until explicit verified reindex. |
| `eval/stability/high_angle_contracts.py`, `cli/stability_cli.py` | Exact membership in the fit's full identity envelope. Old bare or different-version entries cannot cover a current prefixed v2 identity. No fit files are updated. |
| `services/generative_jobs.py:cfd_in_loop_evaluator_status`, web scope builder | Exact envelope-set comparison preserves the namespace. Existing lofted and synthetic fixture values retain their meaning. |
| Calibration ingest CLI and campaign rows | New writes use the actual `Hull.design_hash()` in rows and geometry references. Historical record-hash placeholders are preserved, not relabelled or reaccepted. |
| Mesh/evaluation/closed-body/source bindings and artifact bytes | Use full hull record/content hashes, unchanged. No v2 scalar alias is substituted for those hashes. |
| Design report | Its legacy mirrored design label is an independently tracked context/report correction (KAYGEN-8); this RFC supplies the physical accessor it must use. |

A historical bare v2 value cannot identify its full shape. Recovery needs the
original full hull record and trusted provenance. Reindexing a derived row does
not transfer fit acceptance; any new evidence envelope must be explicitly
reviewed against the versioned identity. Unknown schemes never match by suffix.

## Acceptance Criteria

- A breadth change with independently changed displaced volume changes identity.
- Coefficients, knots, every nested distribution/family input and length change it.
- Cosmetic names and unused legacy v2 reporting scalars do not change it.
- Canonical JSON ordering is invariant; default lofted and record hashes match
  pre-change literal golden values.
- Old scalar-only/bare/different-version fit envelopes refuse v2 applicability;
  an explicitly accepted exact new envelope remains the existing resolver path.
- Real sweep/index/query round-trip retains the prefix. Explicit reindex from
  verified full input corrects a legacy projection without rewriting its manifest.
- New tank/inclining campaign rows use physical identity rather than record hash.

## Open Questions

An independent third-party consumer that requires all design identities to be
64 hex must adopt the versioned string before consuming new v2 values. No such
validator exists in this repository. Cross-version equivalence must be designed
explicitly if a later physical-identity scheme changes.

## Implementation Path

Characterize the identity and calibration-ingest failures; implement the versioned
value and explicit legacy accessor; exercise applicability/index/CLI behavior;
run full pytest then Ruff; integrate one coherent RFC. No database copy or
historical artifact migration is performed.

## Domain Modeling

Physical design identity describes geometry inputs. Record identity describes
serialized content. Evaluation context describes operating conditions and method
settings. A load/pose change belongs to evaluation context, not v2 physical shape.

## Migration and reversal

Existing lofted outputs and all old artifact bytes remain readable. New v2
identity values use a namespace old software must not strip. Before new identity-
bearing writes, rollback is a code reversal. After them, retain files and use a
compatible reader or forward repair; never strip prefixes or rewrite fit scopes
to make an old reader accept new evidence. Derived indexes may be rebuilt from
verified full records, independently of physical evidence acceptance.
