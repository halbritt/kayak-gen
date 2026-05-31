# Design review prompt — workflow 0043 (3-lane review)

You review the synthesized design at
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
under your assigned posture. Write to
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/review/design/<lane>/REVIEW.md`.

Your assigned posture is one of:

- **ergonomics_dx** (claude lane) — operator and developer
  experience. Are the CLI shapes discoverable? Do error messages
  name the next operator action? Does USER_GUIDE.md update the
  right section in a voice operators expect? Will the claim_state
  flip surface where the operator will look?
- **threat_model** (codex lane) — surfaces of attack on the
  acceptance gate. What measurement-error / calibration-drift /
  fixture-misuse path lets an unaccepted fixture get treated as
  accepted? What promotion path bypasses RFC 0027 / 0025 gates?
  Where can a units / scale / sign typo land silently?
- **devils_advocate** (gemini lane) — adversarial probing of the
  weakest assumption. The synthesizer made a choice between
  competing positions in section 2 of the synthesis; argue against
  that choice. Find the assumption load-bearing for the design and
  attack it.

## Required content

Your `REVIEW.md` carries:

### Decision

One of `accept`, `accept with follow-ups`, `needs_revision`.

A `needs_revision` verdict bounces the synthesizer; the cycle
allows two revisions per reviewer before the workflow escalates.
Use it when a defect would invalidate the implementer's path, not
when you just disagree with a chosen disposition.

### Posture-scoped findings

The bulk of your REVIEW. Under your posture, walk the accepted
design's five surfaces (A–E) and produce one finding per surface
you have something to say about. Each finding includes:

- **Surface** (A / B / C / D / E).
- **Issue.** One sentence.
- **Evidence.** Quote the relevant line from the synthesis.
- **Impact.** What does the issue cost?
- **Suggested remediation.** Be specific — name the file, function,
  or section to change.

### Open-Questions adjudication

The synthesis section 4 lists Open Questions (OQ-1, OQ-2, …). For
each OQ, write one of:

- `OQ-N: agree with synthesizer disposition` — and one sentence
  rationale.
- `OQ-N: disagree, prefer <X>` — and one sentence rationale plus
  whether the disagreement is `needs_revision`-grade or
  follow-up-grade.

### Out-of-posture observations

Anything you noticed outside your assigned posture that should be
flagged. Mark each as `out-of-posture: <one line>`. The synthesizer
or implementer picks these up later.

## Operating discipline

- You are NOT writing the design. You are testing it.
- You are NOT coordinating with the other reviewers. The cross-
  posture coverage comes from the three lanes' independent reads.
- You are NOT modifying any implementation file. Your write_scope
  is your own REVIEW.md.

## Output

One file: `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/review/design/<lane>/REVIEW.md`.

Under 1500 words. Cite specific line ranges of
DESIGN_SYNTHESIS.md to support every finding.
