# RFC 0086: Phase- and packet-bound doctrine citation closure

Status: landed maintained closure, verification and attribution correction
Date: 2026-11-08
Context: KAYGEN-23 / retrospective R8; D072; `kayakgen/operations/citation_closure.py`.

## Problem

A completed export repair's original final-packet closure listed a concept
that the final Pincite packet had not activated. The installed classifier
reported it as `injected-non-activated-citation` and still exited zero, so a
caller that checked only the exit code would accept the closure. The concept
had in fact been served and relied on during discovery, under a different
packet. The session-local correction kept both records by hand, with no
maintained tool to bind each phase's citations to the packet that served them.

## Goals

- Run the existing installed `pincite-citations` classifier for each closure
  and record the phase and the immutable packet identity it classified.
- Decide closure from the per-citation classifications, not the exit code.
- Accept a concept absent from a final packet only as a discovery attribution
  backed by a closure of the discovery packet that actually cited it.
- Keep original refused closures and record corrections separately, with no
  new runtime or acceptance evidence.
- Allow repository and evidence locators that are outside the doctrine index
  as provenance, without treating them as injected doctrine.

## Non-Goals

Changing the classifier, the released doctrine corpus or index, packet
assembly, typed-evidence reassembly or any hull, calibration, readiness,
safety or hosted-worker claim. Authentication of closures, cross-host
immutability and inference of citations from prose are also out of scope.

## Proposal and decision D072

`python -m kayakgen.operations.citation_closure close --phase PHASE --packet
PACKET --observations OBSERVATIONS --out NEW_DIR` copies the exact packet and
`citation-observations/1` bytes into a new directory and runs the installed
`$PINCITE_RELEASE_HOME/doctrine/bin/pincite-citations` (default
`~/.local/share/pincite/release`) on those retained copies with the release's
compiled index. It keeps stdout, stderr, exit status, classifier and index
SHA-256 values, the packet file SHA-256, `packet_id` and
`packet_content_sha256`. `closure.json` is written last; an existing
directory is refused, so a closure is never replaced.

A report must be `citation-classification/2` for the same packet ID and
content hash, use the `structured` channel and list the same observations in
the same order with `output` origin. Otherwise, or on a nonzero classifier exit,
the closure is `classifier_failed` (exit 1). Each citation then gets a
disposition:

| Kind | Classification | Disposition |
| --- | --- | --- |
| concept or formulation | `valid-packet-citation` | `accepted-packet-citation` |
| source locator | `valid-packet-citation` | `accepted-packet-provenance` |
| source locator | `foreign-citation` | `accepted-external-provenance` |
| any | `injected-non-activated-citation` | `refused-not-served-by-packet` |
| concept or formulation | `foreign-citation` | `refused-unknown-doctrine-identifier` |
| any | anything else | `refused-unrecognized-classification` |

All accepted gives `closed` (exit 0); any refusal gives `refused` (exit 2).
`verify CLOSURE` rehashes retained files, recomputes the status from the
retained report and reruns the installed classifier, which must reproduce the
same bytes and exit status.

`correct --original REFUSED --corrected CLOSED --out NEW_FILE` records an
attribution correction after verifying every referenced closure. The
corrected closure must keep the original phase and packet bytes and list
exactly the original accepted citations in order. Every refused identifier
needs one `--attribute ID=CLOSURE` or `--withdraw ID=REASON`. An attribution
closure must be closed, come from a different phase and contain that
identifier as an accepted packet citation. Activation in the discovery packet
alone, or a directory name, is not consumption. The record lists the original,
corrected and attribution closures by path and SHA-256, and fixes
`evidence_effect` to no runtime verification and no acceptance.

## Alternatives and consequences

Checking the classifier exit code alone repeats the incident. Reimplementing
classification in Kayak Gen would duplicate the Pincite classifier and its
index semantics. Editing the closure in place would destroy the invalid
record. The selected wrapper keeps classification in Pincite and keeps
policy, retention and correction in the operations package beside the
completion guard. It reuses that guard's strict JSON ingress. Closures need
the installed Pincite release at closure and verification time.

## Acceptance Criteria

- Each closure records phase, packet hashes and identity and the actual
  installed classifier run. A classifier exit 0 with a non-activated concept
  refuses.
- A non-activated concept cannot close a final packet, and a correction
  cannot add citations or switch packets.
- Discovery attribution needs a closed, different-phase closure that cited the
  concept. Activation-only and same-phase attributions refuse.
- Originals are byte-preserved and corrections never replace records or
  create runtime or acceptance evidence.
- Foreign repository locators close as external provenance. Foreign concept
  identifiers refuse.

## Open Questions

None within this scope. Signed closures, shared closure stores and root final
typed-evidence reassembly are separate work.

## Implementation Path

One coherent landing: behavioral tests against a canned-output classifier
stand-in at the installed layout, the module, operator documentation, then
frozen-source full pytest and Ruff. External acceptance uses the actual
installed classifier on the retained KAYGEN implementation packets and the
root follow-up discovery packet.

## Domain Modeling

This is an operations boundary clarification under `DDD.md`'s “Adding to the
model” guidance. Closures and correction records are immutable operational
evidence descriptions, not hull-domain aggregates or scientific acceptance.
