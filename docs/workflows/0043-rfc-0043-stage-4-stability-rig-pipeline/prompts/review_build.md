# Build review prompt — workflow 0043 (3-lane build review)

You review the implementation landed by the `implement` job under
your assigned posture. The accepted design is at
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`;
the implementer's handoff is at
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/HANDOFF.md`.

Write to
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/review/build/<lane>/REVIEW.md`.

Your assigned posture is one of:

- **ergonomics_dx** (claude lane) — operator and developer
  experience of the landed code. Run
  `kayakgen calibration --help` and confirm the new commands
  surface. Trigger a structured rejection from the acceptance
  gate and confirm the error message names the operator's next
  action. Read the USER_GUIDE.md addition and confirm an operator
  who only reads that section can run the pipeline.
- **threat_model** (codex lane) — surfaces of attack on the
  acceptance gate as landed. Find any code path where a non-
  accepted fixture gets treated as accepted, where the claim_state
  flip escapes the RFC 0027 / 0025 audit trail, or where a
  measurement-error / units typo lands silently. Verify the test
  suite covers the threat surface, not just the happy path.
- **devils_advocate** (agy lane) — adversarially probe what
  the implementer skipped. Compare the synthesis section 3
  (accepted design) line-by-line against the landed code. Find
  any spot where the implementer rationalized away part of the
  design. Find the test case the design called for that isn't in
  the test files.

## Required content

Your `REVIEW.md` carries:

### Decision

Your verdict MUST be exactly one of these three:
`accept` · `accept_with_findings` · `needs_revision`.

**Do NOT use `reject`.** In this workflow `reject` is a terminal,
non-recoverable verdict: it fails the review job permanently, cannot
be re-cycled, retried, or overridden, and wedges the run with no
operator recovery path. However serious your findings, if the
implementer could revise the code to address them, return
`needs_revision`, not `reject`. A `needs_revision` verdict bounces
the implementer; the cycle allows two revisions before escalation.

Use `needs_revision` for defects that block the design from being
correctly realized; `accept_with_findings` for sound code with
non-blocking findings; `accept` for sound code with nothing
blocking. Not for refactor preferences.

### Required checks

The HANDOFF.md numbers six required surfaces (1–6). For each,
mark `pass` / `fail` / `n/a` and cite the evidence:

1. **Ingestion + acceptance CLI** — verify `kayakgen calibration
   --help` lists both new commands and that each one runs
   end-to-end on the in-test fixture.
2. **Acceptance-gate module** — verify
   `kayakgen/eval/stability/measured_acceptance.py` exists and
   each gate the synthesis called for has a matching function +
   test.
3. **Claim-state resolution** — verify `kayakgen/eval/claims.py`
   honors the new resolution path AND continues to honor
   RFC 0025 claim-gate enforcement (no parallel gate).
4. **Tests** — verify the three new test files exist, all
   function names match the synthesis section D list, and
   `pytest` for each passes.
5. **Operator-facing docs** — verify USER_GUIDE.md +
   DECISION_LOG.md updates land in the right sections in the
   project's existing voice.
6. **Workflow handoff** — verify HANDOFF.md cites file:line for
   every surface and the pytest summary matches the implementer's
   claim.

### Posture-scoped findings

Beyond the required checks, file posture-specific findings using
the shape from the design-review prompt:

- Surface (1–6).
- Issue. One sentence.
- Evidence. File:line citation.
- Impact.
- Suggested remediation.

### Out-of-posture observations

Anything you noticed outside your posture that should be flagged.
Mark each as `out-of-posture: <one line>`.

## Operating discipline

- You are NOT writing or modifying implementation files. Your
  write_scope is your own REVIEW.md.
- You are NOT coordinating with the other build reviewers.
- You MAY run pytest and `kayakgen calibration --help` to
  verify; both are read-only operations on the landed code.

## Output

One file: `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/review/build/<lane>/REVIEW.md`.

Under 1500 words. Cite file:line for every finding.
