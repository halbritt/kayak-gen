# Remediation Prompt

Read all implementation summaries and the findings ledger. Fix the
must-fix items only.

Keep fixes scoped, preserve all stage-1 decisions and accepted
no-claims boundaries, update `CHANGELOG.md` where appropriate, and
run focused validation plus the full repo suite (minus the env-gated
OpenFOAM smoke) before publishing.

Publish the patch summary artifact with proper front matter.
