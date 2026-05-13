Operator parallelism instruction: use the maximal number of useful sub-agents or parallel workers available for independent investigation, implementation, and verification. Keep scopes disjoint, preserve this assigned Striatum role, and state what sub-agent help was used in the artifact.

Implement the safe-now findings from
`striatum/0043-web-hosted-browser-acceptance-revision/ledger/FINDINGS.md`.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent browser tests, console/network and Lighthouse
tooling, hosted-demo documentation, web route states, CLI/serve behavior,
Docker checks, and verification, but keep one agent responsible for final
integration.

If this job is re-entered after `final_review` returned `needs_revision`, read
`striatum/0043-web-hosted-browser-acceptance-revision/final/FINAL_REVIEW.md`,
remediate only the concrete final-review gaps, and add a `Revision pass`
section to the patch summary.

Write
`striatum/0043-web-hosted-browser-acceptance-revision/implementation/PATCH_SUMMARY.md`
with files changed, findings addressed, sub-agent help used, and verification
commands/results. Do not add a plain byline whose first characters are
`author:`.

Do not present unavailable CFD routes as runnable, hosted, calibrated, or
validated unless a later accepted RFC and ledger explicitly allow it.
