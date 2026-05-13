Read `docs/workflows/0029-web-cfd-job-routes/SOURCES.md`, especially RFC 0018,
RFC 0015, and the web frontend modules.

Produce
`striatum/0029-web-cfd-job-routes/browser_domain/REVIEW_BROWSER_DOMAIN.md`
with:

- author line: `author: operator [self-declared: operator-browser-domain-review]`
- verdict intent
- findings `B-001`, `B-002`, ...
- required action for each finding

Focus on:

- browser-visible wording for queued, running, succeeded, failed, and
  unavailable CFD states;
- how profiles, readiness rejection, logs, raw outputs, timestamps, and error
  details should appear without suggesting validated physics;
- artifact visibility and warnings around raw/unvalidated outputs;
- UI behavior when no real solver is installed or when the selected profile is
  unavailable;
- domain boundaries between analytical resistance, raw CFD artifacts, and any
  future calibrated result.
