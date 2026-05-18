# Remediation Prompt

Read all implementation summaries and the findings ledger. Fix the must-fix
items only.

Use the maximal useful number of Codex sub-agents for disjoint remediation
tasks. Keep fixes scoped, preserve all stage-4 decisions and accepted
no-claims boundaries, update `CHANGELOG.md` where appropriate, and run
focused validation plus the full repo suite (minus the env-gated OpenFOAM
smoke) before publishing.

Publish the patch summary artifact.
