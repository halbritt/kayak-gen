---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-002
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Public Demo Operations Vote

## Vote

**Vote: Option A — Defer public operation until the D008 operator-evidence
gates are recorded; Option B (single fixed managed container) becomes the
correct posture the moment those records exist, in a successor workflow.**

## Decision Sentence

Workflow 0052 does not accept a public hosted browser demo. D008's narrow
server-backed exploratory posture remains the only authorized shape for any
future public URL, and a successor workflow may stand one up only after it
records a named operator owner and backup, a hosting budget/cap with the
provider/account/region named, a deployed git SHA, a hosted smoke transcript
against the deployed URL, bounded persistence policy, a cleanup receipt,
and the no-SLA / no-production / no-hosted-CFD / no-real-solver /
no-calibration / no-final-design-fitness wording required by RFC 0030,
RFC 0032, and `docs/WEB_VERIFICATION.md`. If a public URL is ever stood up,
its lowest-risk shape is the existing repo Docker image running
`kayakgen serve --host 0.0.0.0 --port 8080` as exactly one managed
container web service, on a provider whose pricing the operator records as
flat/monthly-capped or whose hard usage limit takes the service offline
(DigitalOcean App Platform fixed shared container is the clearest current
example; Render paid web service or Railway with a hard usage limit are
acceptable alternatives only with their caps recorded; Fly.io is not the
default because its own cost-management docs warn that free allowances do
not cap bills and billing alerts are unsupported).

## Evidence

### Local sources

- `striatum/0052-successor-decision-research/research/public_demo_ops/RESEARCH.md`
  — the research packet's own conclusion: the conservative answer is *not
  yet* because the repo records "no operator owner, no budget/cap, no
  deployment revision, no hosted smoke, and no cleanup receipt." The
  packet's Recommendation section explicitly directs Option A "unless the
  panel packet or operator report can name an owner and budget/cap now."
- `docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md:6-28`
  — the operator's notes for this workflow do not name an operator owner,
  hosting budget/cap, provider/account, deployment revision, hosted smoke,
  persistence policy, or cleanup plan. The packet's Option B precondition
  is therefore not satisfied within this run's evidence envelope.
- `docs/DECISION_LOG.md:41` (D008) — already authorizes the narrow
  server-backed exploratory demo posture, and explicitly states that no
  public URL was delivered by workflow 0050. D008's `Revisit` cell triggers
  *exactly* the conditions Option A says are still missing.
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md:131-145`
  — D008's accepted shape (Option B-style hosting) is gated on operator
  owner, budget/cap, deployment revision, environment, persistence, smoke,
  and cleanup before any public URL is treated as accepted. Claude's prior
  dissent was preserved as an implementation gate.
- `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md:122-127,262-267`
  — the workflow 0050 final review affirms that no public URL was
  delivered and that the prior dissent's operational concerns must be
  satisfied before any public URL is treated as accepted.
- `striatum/0051-implementation-burndown-stage1/final/FINAL_REVIEW.md:51-53`
  — workflow 0051 stage 1 burn-down explicitly did not land D008
  (browser hosting). RUNBOOK kept hosted CFD and public production
  hosting blocked. So between D008 and today, no operator-evidence record
  has been added by any landed workflow.
- `docs/ROADMAP.md:86-89,146-167` — Batch C is `partial` / `blocked`: a
  public hosted demo operation "only after an operator owner, budget/cap,
  deployment revision, hosted smoke, persistence limits, and cleanup
  policy are recorded." This is the same gate that is still unmet.
- `docs/ROADMAP.md:33-59` — the No-Claims Rules already in force: the
  web frontend is local/browser-capable with runbook coverage, not a
  completed public hosted demo, full dashboard parity, hosted CFD system,
  or desktop parity rewrite. A successor public-URL workflow must not
  weaken those statements; it may only localize them to a deployed page.
- `docs/PRD.md:46-49` — full browser parity, console-clean Lighthouse
  acceptance, hosted-demo acceptance, hosted CFD workers, and real solver
  adapters remain roadmap items. A public URL must not appear to retire
  any of those.

### Independent external check (accessed 2026-05-14)

- Trame guide — `https://kitware.github.io/trame/guide/`. Trame is a
  Python framework for visual analytics that "can run locally or as a
  client/server app, and can be deployed in the cloud as a service."
  Independently verified: hosting is server-backed, not static.
- Trame architecture and capabilities —
  `https://kitware.github.io/trame/blogs/trame-architecture-and-capabilities`.
  Trame uses a stateful Python server per client over WebSocket.
  Independently verified: capacity planning is not a paperwork formality;
  one always-on instance hosts a small number of concurrent sessions.
- Trame Docker deployment —
  `https://kitware.github.io/trame/guide/deployment/docker.html`.
  Guidance discusses EGL/offscreen VTK/ParaView setup, which aligns with
  kayak-gen's existing Dockerfile installing Mesa/OpenGL libraries and
  argues for smoke-testing the *built* container before public traffic.
- Trame NGINX deployment —
  `https://kitware.github.io/trame/guide/deployment/nginx.html`. Any
  reverse proxy in front of Trame must be WebSocket-aware. Independently
  verified: a hosted smoke must include a WebSocket connectivity check.
- GitHub Pages —
  `https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages`.
  GitHub Pages hosts static HTML/CSS/JS only. Independently verified:
  Pages cannot host the current Python/Trame server.
- Pyodide — `https://pyodide.org/en/stable/usage/packages-in-pyodide.html`.
  Pyodide can run pure-Python wheels plus a curated set of ported
  packages. Independently verified: PyVista/VTK/Trame as currently used
  are not a drop-in for Pyodide; a Pyodide demo is a *separate* runtime
  decision, not a deployment of the current app.
- DigitalOcean App Platform container deployment —
  `https://docs.digitalocean.com/products/app-platform/how-to/deploy-from-container-images/`.
  Confirms Linux AMD64 image deployment, default web-service HTTP port
  8080, and the `0.0.0.0` bind requirement. Independently verified to
  match kayak-gen's current Dockerfile and `kayakgen serve` defaults.
- DigitalOcean App Platform pricing —
  `https://www.digitalocean.com/pricing/app-platform`. Advertises
  flat/monthly-capped pricing tiers and one-instance fixed shared CPU
  options. Independently verified: a single instance with autoscaling
  disabled supports the budget-capped posture Option B requires.
- DigitalOcean App Platform limits —
  `https://docs.digitalocean.com/products/app-platform/details/limits/`.
  Containers have no persistent local storage and a 4 GiB local
  filesystem cap. Independently verified: acceptable for an exploratory
  demo if `/api/cfd/*` outputs are ephemeral and `?hull=...` Share URLs
  are the only durable persistence.
- Render Docker docs — `https://render.com/docs/docker`. Confirms
  Dockerfile builds, WebSockets, custom commands, automatic HTTPS, and
  health checks. Independently verified as a viable managed-container
  alternative if its instance size and bandwidth cap are recorded.
- Render free instance — `https://render.com/docs/free`. Free web
  services spin down after 15 minutes idle, can lose local filesystem
  changes, and are non-production. Independently verified: useful as a
  no-cost preview, but operationally brittle for Trame/VTK first-render
  smoke — first-touch wake times can confuse a smoke transcript.
- Railway cost control —
  `https://docs.railway.com/pricing/cost-control`. Railway supports a
  hard usage limit that takes workloads offline at the configured limit.
  Independently verified: viable Option C if hard cap is recorded.
- Fly cost management — `https://fly.io/docs/about/cost-management/`.
  Fly states free allowances do not cap bills and billing alerts are not
  supported. Independently verified: Fly is not the lowest-risk default
  for a budget-capped public demo, despite fitting the Docker shape.
- Hugging Face Docker Spaces —
  `https://huggingface.co/docs/hub/main/spaces-sdks-docker`. Supports
  arbitrary Dockerfiles with configurable `app_port` and ephemeral disk.
  Independently verified: viable as a future alternative, but requires
  separate port/user/filesystem smoke before it can be called
  "lowest-risk" relative to App Platform.

### What the evidence supports

The technical path for Option B exists and is well-documented in current
provider docs (App Platform, Render, Railway, Fly, Spaces). The
*operational* preconditions D008 requires — operator owner, budget/cap,
deployment revision, hosted smoke, persistence policy, cleanup receipt —
are still not recorded for kayak-gen in this run's packet, in
`docs/WEB_VERIFICATION.md`, in the workflow 0050 / 0051 artifacts, or in
the operator report. Capacity planning is not a paperwork formality: the
Trame architecture post independently confirms a stateful Python server
per client, so a public URL has real concurrency, memory, abuse, and
cleanup surface that must be owned by name before a deploy commit.

## Why Rejected Alternatives Lose

- **Option B now (single fixed managed container).** Loses on
  preconditions, not direction. The operator owner, hosting budget/cap,
  shutdown/redeploy procedure, abuse policy, and hosted smoke required by
  D008's revisit conditions, RFC 0030, RFC 0032, and the research
  packet's own Required Gates section are not recorded in any artifact
  this workflow can cite. Option B is the right *shape*; standing it up
  inside *this* decision (which has no operator-attestation channel)
  would either bundle ops scope this workflow was not chartered to own or
  land an unowned endpoint. The successor public-URL workflow should
  adopt Option B verbatim with this vote's acceptance bar.
- **Option C now (usage-based platform with hard limit).** Loses for the
  same precondition reason as Option B and adds platform-specific risk:
  Fly.io's own cost-management docs say free allowances do not cap bills
  and billing alerts are unsupported, so Fly is not the lowest-risk
  default. Railway's hard usage limit is real and acceptable *if* the
  operator selects it, but the choice between Option B (fixed price) and
  Option C (usage-based + hard cap) is an operator preference that no
  operator has recorded. Defer to the same successor workflow as
  Option B.
- **Option D (static/Pyodide or demo-specialty rewrite).** Loses on
  identity. Pyodide and GitHub Pages independently confirm this is a new
  *runtime and viewer* commitment, not a cheaper hosting target for the
  current Trame app. No RFC currently scopes a static viewer, evaluator
  subset, 3D renderer choice, or file-export path. Choosing it here
  would silently fund a frontend rewrite without an RFC. Hugging Face
  Docker Spaces is server-backed but still needs port/user/filesystem
  smoke before it can be ranked against App Platform. Option D belongs
  in a separate RFC, not this decision.

## Implementation Gates That Must Remain In Force

These gates apply to any successor workflow that proposes to stand up a
public URL. The current decision is **Option A**, so the gates below are
a forward-looking acceptance bar.

1. **Posture must be named explicitly.** The successor workflow's
   RUNBOOK and prompts must say which posture is being closed (D008
   Option B narrow server-backed demo, or a separate Option D rewrite).
   No silent promotion via a doc edit, CI change, or CHANGELOG entry.
2. **Operator and budget before any deploy commit.** A named operator
   owner *and backup*, with contact handle; provider/account/region;
   monthly cap evidence in one of these acceptable forms: fixed
   one-instance pricing with autoscaling disabled and bandwidth overage
   policy recorded; provider hard usage limit that takes the service
   offline (Railway-style); free-account suspension policy if using a
   free tier; or a documented always-on worst-case budget plus explicit
   manual monitoring cadence if the provider has no hard cap (Fly-style).
3. **Deployment evidence.** Git SHA and branch; Docker image digest or
   clean-checkout transcript; exact command
   `kayakgen serve --host 0.0.0.0 --port 8080`; environment variables
   (including the `KAYAKGEN_WEB_CFD_JOBS_ROOT` choice if `/api/cfd/*`
   routes are enabled); instance size, memory, CPU, and concurrency
   limits; confirmation of `0.0.0.0` bind and WebSocket survival under
   the chosen reverse proxy (Trame NGINX guidance) or platform proxy.
4. **Persistence boundaries stay explicit.** `?hull=...` Share URLs are
   the only durable persistence by default. `/api/hulls` IDs remain
   in-memory; `/api/cfd/*` artifacts are either disabled by policy or
   live in `KAYAKGEN_WEB_CFD_JOBS_ROOT` under a recorded storage cap and
   cleanup TTL. Prefer ephemeral filesystem and no mounted volume for
   the first public demo. If any volume is mounted, record size,
   retention, cleanup command, and cost.
5. **Hosted smoke is required evidence.** Either browser acceptance
   checks run against the deployed URL or an equivalent recorded smoke
   covers: public URL loads without local Python; hull/deck view is
   nonblank; core controls and compact analysis rows render; a
   representative slider mutation changes visible metrics without
   blanking the 3D view; Share URL reload reconstructs the hull; hull or
   deck STL export returns STL bytes; browser console / page / network
   are clean apart from exact, scoped allowlists; the CFD panel/API
   still says local/raw/unvalidated and no hosted worker; and the public
   page or adjacent docs carry the no-SLA / no-production / exploratory
   wording listed below. Lighthouse Best Practices `>= 90` is a gate
   *only* when the workflow claims RFC 0030 Lighthouse upkeep or RFC
   0008 hosted-Lighthouse closure; otherwise it is optional evidence.
6. **Exact, scoped allowlists.** Any console/network allowlist (Trame,
   VTK, `/paraview/`, etc.) must record URL pattern, status, rationale,
   owner, and removal condition. No broad permanent allowlists. This
   carries forward RFC 0030 §3 and RFC 0032 §2.
7. **No bundling.** A public-URL workflow does not close RFC 0040
   (mesh readiness), RFC 0041 (real OpenFOAM `succeeded` path), RFC 0042
   (resistance source acceptance), RFC 0043 (high-angle stability
   surfaces), desktop parity, or mobile parity. Each is a separate
   decision per `docs/ROADMAP.md:67`.
8. **Same artifact as local.** "Hosted" means the existing repo
   `Dockerfile` or `kayakgen serve` command at a specific repo revision
   recorded in the workflow. No vendor-specific image, no custom build,
   no forked frontend. No OpenFOAM/SU2 binaries installed in the hosted
   image, no Docker socket mounted, no external worker queue configured.
9. **Cleanup receipt is part of acceptance.** The cleanup procedure
   must delete or stop the web service; remove images / build cache if
   billed; remove domains / DNS records if applicable; delete volumes,
   managed databases, object stores, queues, public IPs, and
   provider-side project/org resources. Final acceptance must include a
   URL-offline check and a provider dashboard/billing screenshot showing
   no leftover billable resources.
10. **Option D requires its own RFC.** A static / Pyodide / custom-JS
    frontend is a runtime and viewer choice, not a hosting choice. It
    must land via its own RFC covering runtime, package compatibility,
    3D renderer, evaluator subset, file-export path, and explicit
    no-CFD boundary before any implementation work.
11. **No silent SLA wording.** Documentation, marketing surface, and
    page copy must not imply uptime guarantees, support response, or
    production reliability — even by omission.

## No-Claims Language That Must Remain In Force

The public demo page, README snippet, or linked status note (and any
DECISION_LOG / ROADMAP / CHANGELOG row touching public hosting) must
retain the following statements verbatim or in substance:

- Exploratory browser demo; best-effort availability; may be shut down
  or redeployed without notice; no public-service SLA.
- No accounts, quotas, collaboration features, or design library.
- No hosted CFD workers, OpenFOAM, SU2, Dockerized solver execution, or
  real solver adapter `succeeded` path.
- Analytical resistance remains `uncalibrated_comparative`; the local
  and routed `/api/cfd/*` records remain raw and unvalidated; no
  calibrated resistance, final prediction, final design fitness,
  seaworthiness, safety, or production watertight-solver-readiness
  claim.
- `docs/ROADMAP.md:57-59` — "The web frontend is local/browser-capable
  with runbook coverage, not a completed public hosted demo, full
  dashboard parity, hosted CFD system, or desktop parity rewrite."
- `docs/WEB_VERIFICATION.md:147-210` — no hosted public demo URL is
  deployed today; this section is not a production-hosting claim; the
  demo does not run real CFD; there is no production database, account
  system, quota system, design library, hosted worker queue, or
  public-service SLA.

A future hosted-demo workflow may localize these statements to the
deployed page, but it may not weaken them.

## Risks Acknowledged By This Vote

- Choosing Option A means the project continues to lack a shareable URL.
  Mitigation: the share/no-install motivation is partially served today
  by `?hull=...` Share URLs combined with the documented `kayakgen serve`
  runbook; full public shareability is a deferral, not a rejection. A
  successor workflow can adopt Option B at any time without rework on
  the local app or its docs.
- A future Option B workflow inherits real operational surface (cost,
  uptime, abuse, concurrency, Trame per-client capacity, dependency
  updates, security patching, cleanup). This vote does not pretend that
  surface goes away; it requires that it be owned by name before code
  lands.
- Provider terms and pricing can change after the access date
  (2026-05-14). The successor workflow's hosted-smoke evidence must
  re-verify pricing, cap policy, and bind/port behavior against the
  provider docs at the time the demo is stood up; this vote's external
  citations are not a forward guarantee.
- A free-tier or spin-down platform (Render free, Spaces, etc.) can
  make a smoke transcript misleading because first-touch wake times
  hide real cold-start failures. If a free tier is used, the smoke must
  exercise a cold start explicitly.
- Static-hosting demand may keep recurring. Option D remains gate-able
  via a dedicated RFC; this vote refuses only the *implicit* adoption
  of a runtime/viewer rewrite.

## Confidence

**high.**

Reasons: the research packet's own conclusion matches this vote; the
local source set (PRD, ROADMAP, RFC 0030, RFC 0032, D008,
`docs/WEB_VERIFICATION.md`, workflow 0050 / 0051 final reviews) is
internally consistent and points the same direction; the independent
external check confirms Trame's stateful-server architecture, the
static-vs-server distinction, and the provider-by-provider pricing /
cap claims the research relies on; the operator report does not record
any of the D008 revisit conditions; and the choice is reversible — a
successor workflow can adopt Option B at any time without rework on the
local app or its docs.

## Sub-Agent Help

No spawned sub-agents were used. Independent verification used direct
reads of local docs and the external sources cited above.
