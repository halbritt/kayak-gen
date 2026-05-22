# Task — synthesis

Read all three lane FINDINGS.md artifacts in this run's audit directory:

- `docs/audits/<RUN_DATE>-code-doc-audit/pipeline-integrity/FINDINGS.md`
- `docs/audits/<RUN_DATE>-code-doc-audit/docs-decision-drift/FINDINGS.md`
- `docs/audits/<RUN_DATE>-code-doc-audit/operator-adoption/FINDINGS.md`

Produce `docs/audits/<RUN_DATE>-code-doc-audit/SYNTHESIS.md` covering:

1. **Lane-diversity caveat.** Name the providers each lane ran on. If a
   lane ran on the same provider as another, say so honestly.
2. **Roll-up table** keyed by finding ID with columns: lane, severity,
   category, follow-up path.
3. **Cross-lane duplicates and overlap.** Findings that name the same
   root cause from different reading postures get grouped into one
   remediation batch. Cite the related IDs explicitly.
4. **Conflicts between lanes.** If two lanes disagree (e.g. one flags a
   doc gap that another lane verifies is documented elsewhere), record
   the conflict and the resolution. If none, write "None."
5. **Priority order.** Group related findings into named remediation
   batches (R1, R2, ...). Highest-leverage first: docs-only batches that
   close multiple findings beat single source-change batches.
6. **Notes for the workflow scaffold** (optional). If this run discovers
   that the workflow itself needs tweaks, record them at the bottom so
   the next run can pick them up.

Do not propose remediation work inside this artifact — that is the
remediation_plan job's responsibility. Stop after producing SYNTHESIS.md.

Do not edit or rewrite the per-lane FINDINGS.md artifacts. The write
scope of this job explicitly forbids the lane subdirectories.
