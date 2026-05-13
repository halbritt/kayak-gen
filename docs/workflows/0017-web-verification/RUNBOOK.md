# Runbook - 0017 web verification

1. Review RFC 0008, the current Trame web app, CLI serve command, Dockerfile,
   and web tests.
2. Run three review lanes:
   - RFC/status and acceptance traceability;
   - browser visual/runtime verification feasibility;
   - packaging, CLI, Docker, and test operations.
3. Consolidate findings into a ledger that separates safe-now web verification
   work from future hosted-demo or full Lighthouse work that cannot run in the
   current environment.
4. Implement only the safe verification and hardening slice: tests, docs, CLI or
   Docker fixes, demo/deployment notes, and truthful RFC status updates.
5. Final review should accept only if the web verification story is reproducible
   from the repo and any skipped browser/Lighthouse checks are explicitly
   documented with reasons.
