---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: operator [self-declared: operator-0052-panel-wave1-gemini-2]
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_51b7f18f5d2b4648b9abd2e463b807e1
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_public_demo_ops_gemini
lease: lease_a90a527cf55d439e9ed79738b46558dd
date: 2026-05-14

# Public Demo Operations Vote

## Vote

**Vote: Option A — Defer public operation until missing operator evidence is recorded. Once recorded, Option B (single fixed-size managed container) is the authorized posture.**

## Decision Sentence

A public hosted browser demo remains deferred. Workflow 0052 does not authorize a public URL because the required operator-evidence gates—a named operator owner, hosting budget/cap, deployed git SHA, hosted smoke transcript, bounded persistence policy, cleanup receipt, and no-claims wording—are not present in the current repository. The narrow server-backed exploratory demo approved in D008 is the only authorized shape for a successor workflow. Once the operator evidence is met, the lowest-risk hosted path is a single fixed-size managed container web service running the existing `kayakgen serve --host 0.0.0.0 --port 8080` command, ideally on a provider with flat/monthly-capped pricing (such as DigitalOcean App Platform) or a hard usage limit.

## Evidence

### Local sources

- `striatum/0052-successor-decision-research/research/public_demo_ops/RESEARCH.md` — The research packet recommends Option A due to the lack of an operator owner, budget/cap, deployment revision, hosted smoke, and cleanup receipt. It identifies Option B as the safest future state once these gates are cleared.
- `docs/DECISION_LOG.md` — D008 already accepts the server-backed demo posture but requires missing conditions (operator owner, budget/cap, deployment revision, hosted smoke) before proceeding.
- `docs/ROADMAP.md` — Browser hosting is allowed only as a narrow exploratory demo, blocking public operation until operator ownership and constraints are recorded.
- `docs/PRD.md` — Highlights that hosted-demo acceptance and real solver adapters are roadmap items, with the browser frontend serving locally.
- `docs/WEB_VERIFICATION.md` — Affirms the current runtime command and persistence caveats, and confirms no hosted public demo URL exists today.
- `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md` — Confirms that no browser hosting work landed and no hosted CFD claims were added in the previous workflow.
- `OPERATOR_REPORT.md` — Fails to supply the required D008 revisit conditions.

### Independent external check (accessed 2026-05-14)

- **Trame capabilities and deployment:** Trame is a Python framework that operates as a client/server application and requires a stateful Python server per client over WebSocket. It cannot be hosted statically.
- **GitHub Pages / Pyodide:** GitHub Pages only hosts static files. Pyodide represents a new runtime decision, not a deployment of the current Trame application.
- **DigitalOcean App Platform:** Offers flat/monthly-capped pricing tiers and container deployments matching the repo's `kayakgen serve` shape on port 8080 with a `0.0.0.0` bind requirement. It has a 4 GiB local filesystem limit and no persistent volumes, fitting an ephemeral demo.
- **Render / Railway / Fly.io:** Render and Railway are viable container alternatives if resource limits and caps are strictly recorded. Fly.io warns that free allowances do not cap bills, making it riskier as a default budget-capped demo host.

### What the evidence supports

The technical implementation for Option B is feasible using platforms like DigitalOcean App Platform or Render. However, the operational prerequisites outlined in D008 (budget, operator owner, cleanup receipt, smoke tests) remain unsatisfied. To prevent unowned operational surface area, the project must defer a public URL until a successor workflow explicitly fulfills these gates.

## Why Rejected Alternatives Lose

- **Option B now (single fixed managed container):** Loses because the critical operational preconditions (owner, budget, cleanup, smoke) are not met. While it is the correct future state, enacting it now would bypass established implementation gates.
- **Option C now (usage-based platform with hard limit):** Loses due to the same missing preconditions. Additionally, usage-based platforms carry surprise-billing risk. Fly.io explicitly lacks bill capping, and while Railway offers hard limits, the operator must explicitly choose and configure them.
- **Option D (static/Pyodide rewrite):** Loses because it abandons the current Trame app architecture. It requires a dedicated RFC to evaluate runtime changes, 3D renderer behavior, and package compatibility, rather than silently slipping in as a hosting workaround.

## Implementation Gates That Must Remain In Force

1. **Operator and Budget Record:** A named operator owner, contact handle, and explicit monthly budget/cap (e.g., fixed instance pricing or hard usage limits) must be recorded before any deploy commit.
2. **Deployment Evidence:** The successor workflow must record the deployed git SHA, exact `kayakgen serve` command, `0.0.0.0` bind confirmation, instance size, and environment variables.
3. **Hosted Smoke Requirement:** A recorded public hosted smoke check is mandatory. It must verify page load, hull/deck views, representative slider mutations, STL export, clean consoles, exact allowlists, and confirm no real solver execution occurs.
4. **Bounded Persistence:** Default persistence is limited to `?hull=...` Share URLs. `/api/cfd/*` artifacts must be ephemeral or bounded with a TTL and storage cap.
5. **Artifact Fidelity:** The deployed app must use the existing repo `Dockerfile` or `kayakgen serve` command without installing OpenFOAM/SU2 binaries or external queues.
6. **Cleanup Receipt:** Final acceptance requires a recorded cleanup procedure showing the URL is offline and no leftover billable resources remain.

## No-Claims Language That Must Remain In Force

Any public demo must explicitly include statements indicating:
- It is an exploratory browser demo with best-effort availability and no public-service SLA.
- There are no accounts, quotas, collaboration tools, or design libraries.
- There are no hosted CFD workers, OpenFOAM/SU2 execution, or calibrated resistance models.
- Analytical resistance is strictly `uncalibrated_comparative`.
- There are no final design fitness, seaworthiness, safety, or production readiness claims.

## Risks Acknowledged By This Vote

- By selecting Option A, the project defers having a publicly shareable URL. The mitigation is to rely on `?hull=...` Share URLs run locally via the current runbook.
- When Option B is eventually adopted, real operational risks (cost, uptime, security patching) will materialize. This vote mitigates that by requiring explicit ownership and budgeting beforehand.
- Free-tier or spin-down platforms may mask cold-start failures during smoke testing. A future smoke test must explicitly verify cold starts.

## Confidence

**high.**

The research packet, local constraints (D008, ROADMAP, PRD), and external verifications uniformly confirm that the Trame app requires server-backed hosting and that the operational preconditions for such hosting have not yet been satisfied by the operator.
