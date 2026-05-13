Operator parallelism instruction: use the maximal number of useful sub-agents or parallel workers available for independent investigation or verification. Keep scopes disjoint, preserve this assigned Striatum role, and state what sub-agent help was used in the artifact.

Read `docs/workflows/0043-web-hosted-browser-acceptance-revision/SOURCES.md`
and the review anchor artifact.

Produce
`striatum/0043-web-hosted-browser-acceptance-revision/browser/REVIEW_BROWSER.md`.
Do not add a plain byline whose first characters are `author:`.

Focus on required real-browser acceptance for local `kayakgen serve`: browser
tooling must fail rather than skip in the acceptance profile, initial render
must show hull/deck, controls, metrics, and analysis content, representative
control mutation must update visible metrics, the 3D view must remain nonblank,
share URL state must round-trip, STL export must return STL bytes, and browser
console/network collection must fail on unexpected errors or failed requests.

Also review Lighthouse Best Practices handling and any console/network
allowlist. A broad permanent allowlist for Trame, VTK, or `/paraview/` errors
is not acceptable. If browser acceptance remains too weak to implement safely,
record `needs_revision` with concrete remediation actions for the revision
cycle.
