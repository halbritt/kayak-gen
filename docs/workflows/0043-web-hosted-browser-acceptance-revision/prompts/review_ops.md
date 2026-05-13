Operator parallelism instruction: use the maximal number of useful sub-agents or parallel workers available for independent investigation or verification. Keep scopes disjoint, preserve this assigned Striatum role, and state what sub-agent help was used in the artifact.

Read `docs/workflows/0043-web-hosted-browser-acceptance-revision/SOURCES.md`
and the review anchor artifact.

Produce
`striatum/0043-web-hosted-browser-acceptance-revision/ops/REVIEW_OPS.md`.
Do not add a plain byline whose first characters are `author:`.

Focus on hosted-demo documentation, Docker/local serve behavior, browser
tooling prerequisites, CI/profile separation between headless web checks and
required browser acceptance, deterministic test behavior, route dependency
states, and raw/unvalidated CFD wording.

Keep unavailable CFD routes explicit. Do not require OpenFOAM, SU2, hosted
workers, accounts, auth, quotas, cancellation guarantees, or calibrated CFD
claims in this slice. If operational prerequisites are unclear enough to block
implementation, record `needs_revision` with concrete remediation actions for
the revision cycle.
