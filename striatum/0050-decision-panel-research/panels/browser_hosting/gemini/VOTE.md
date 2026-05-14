---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---
author: panelist-gemini-pro-3.1-001
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Vote: Browser Hosting Posture

**Vote:** Option B

**Decision:** The project will deploy a narrow, server-backed public exploratory demo using the existing Trame application and documented Docker/server path, explicitly bounded as an exploratory surface without production SLAs, hosted CFD workers, or validated claims.

**Evidence and Citations:**
- `docs/ROADMAP.md` marks "Browser hosting and parity" as `partial` / `blocked`, recommending splitting public hosted demo operation into an independent workflow.
- `striatum/0050-decision-panel-research/research/browser_hosting/RESEARCH.md` confirms Trame's stateful per-client process model supports cloud deployment via Docker (citing Trame official documentation at https://kitware.github.io/trame/examples/core/docker.html).
- `docs/WEB_VERIFICATION.md` confirms that local acceptance of `kayakgen serve` via Docker already establishes the baseline for a deployed server-backed approach.

**Why Rejected Alternatives Lose:**
- **Option A (Conservative Default):** Keeping this completely deferred stalls the delivery of the URL-shareable goal established back in RFC 0008, despite the application already being capable of a narrow deployment.
- **Option C (Static / Backend-Free):** A static GitHub Pages or Pyodide port would demand an unfunded frontend architectural rewrite, discarding the current Trame implementation.
- **Option D (Production Hosted App):** Building out a full production app with hosted worker queues, accounts, or real solvers explicitly violates the no-claims boundaries and blocked roadmap states (`docs/ROADMAP.md` and `docs/PRD.md`).

**Implementation Gates and No-Claims Language:**
- The deployment must use the existing Trame app (`kayakgen serve --host 0.0.0.0 --port 8080`) and Docker path.
- The web frontend must remain labeled as exploratory, preserving the no-claims language that it does not provide validated CFD, calibrated performance, or production solver execution.
- Persistence must be strictly bounded to URL state or temporary in-memory IDs, with no persistent user data or database.
- An operator owner must be assigned to accept responsibility for cost caps and capacity limits before implementation begins.

**Confidence:**
High
