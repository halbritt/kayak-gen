# Finalize The Campaign Report

Publish the final campaign report. This is the campaign's durable
provenance; a maintainer who reads only this artifact should be able to
review the change confidently.

Required sections:

- Goal and provenance: the stage-0 decision, the stage-1 gate verdict,
  and the binding constraints the committed plan discharged.
- Baseline: the recorded result and any named pre-existing failures.
- Frozen surfaces: the inventory and the evidence they are untouched.
- Step ledger summary: per slice — change, preservation claim,
  verification result, commit.
- Characterization tests added, labeled as preserving current behavior.
- Deviations from plan, including any stop condition that fired.
- Deferred findings: defects and cleanups noticed but correctly left
  alone, suitable for filing as issues.
- Rollback map: which commit reverts which slice.
- Residual risk.

Landing the executed worktree is the operator's serialized integrate
step, not this job's; do not push or merge here. Include the exact
lowercase `author:` byline near the top of the artifact.
