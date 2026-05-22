# Task — remediation plan

Read `docs/audits/<RUN_DATE>-code-doc-audit/SYNTHESIS.md` and the three
lane `FINDINGS.md` artifacts. Produce
`docs/audits/<RUN_DATE>-code-doc-audit/REMEDIATION_PLAN.md`.

For each remediation batch (R1, R2, ...) in the synthesis, write:

- **Severity** — the highest severity among the bundled findings.
- **Findings** — the AUD-X-NNN ids it closes.
- **Owner surface** — `documentation only` | `CLI source + docs` |
  `Pydantic schema + tests` | etc.
- **Touched files** — explicit list with file paths (and line numbers
  when known).
- **Gating** — tests that should run before this batch is considered
  closed.
- **Follow-up classification** — one of the seven from RFC 0059 §4:
  - already covered by an existing `docs/TODO.md` /
    `docs/BACKLOG_EXECUTION_PLAN.md` row or open RFC;
  - needs a new RFC;
  - needs a `DECISION_LOG.md` row;
  - needs a docs-only correction;
  - needs source / test work;
  - historical only, no action;
  - accepted risk or wontfix.
- **Status** — `landed in the same change as this remediation plan` (for
  docs-only batches the operator drives in-place) | `deferred to a
  follow-up striatum workflow` (for code/test batches that must go
  through the standard workflow per project memory
  `feedback_striatum_required`).

Every high or critical finding MUST appear in exactly one batch and MUST
carry a follow-up classification. Info / null findings can be omitted.

Add a "Follow-up workflow needs" section at the end that lists the
striatum workflows the deferred batches should spawn (suggested workflow
number + topic).

Add a "Status closure rule" section at the end describing what needs to
be true for a finding's `status:` to flip from `open` to `closed`.

Do not propose final wording for the docs fixes — that belongs in the
follow-up workflow or in this run's in-place docs landing, not in the
remediation plan itself.
