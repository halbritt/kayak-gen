---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-002
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# Browser Hosting Posture Vote

## Vote

**Vote: Option A — Keep public hosting deferred; if and when public hosting is
ever pursued, it must take Option B's narrow server-backed shape and pass
Option B's acceptance bar in a dedicated workflow.**

## Decision Sentence

Kayak-gen does not operate a public hosted browser demo. The web frontend
remains local-only: `kayakgen serve` (or the repo Dockerfile) on a developer
or operator-managed host, governed by the local browser-acceptance and
hosted-demo-documentation contracts already landed in RFC 0032 and
`docs/WEB_VERIFICATION.md`. If a public URL is ever pursued, it must be
scoped as a separate workflow that deploys the same Trame server-backed app
(`kayakgen serve --host 0.0.0.0 --port 8080` or the repo Docker image),
records an operator owner, hosting budget/cap, environment variables,
persistence caveats, hosted-smoke evidence, and the no-CFD / no-calibration /
no-SLA wording required by RFC 0030 §1, RFC 0032 §3, and
`docs/WEB_VERIFICATION.md:147-210`; static/Pyodide and production-hosted-app
paths are explicitly not authorized by this decision.

## Evidence

### Local sources

- `docs/PRD.md:37-49` — current CFD plumbing is local job/run/profile only;
  full desktop parity, hosted-demo acceptance, hosted CFD workers, and real
  solver adapters remain roadmap items. A public URL must not appear to
  retire any of those.
- `docs/ROADMAP.md:57-59` — the web frontend is "local/browser-capable with
  runbook coverage," not a completed public hosted demo, full dashboard
  parity, hosted CFD system, or desktop parity rewrite. This is the active
  no-claims wording.
- `docs/ROADMAP.md:67`, `docs/ROADMAP.md:105-122` — Batch C explicitly says
  browser hosting and parity is `partial` / `blocked` and that the next work
  is to split public hosted demo operation, console-clean/Lighthouse upkeep,
  richer plot/dashboard parity, desktop parity rewrite, and mobile/view-only
  into independent workflows. The roadmap therefore already directs any
  public-URL effort into a dedicated workflow, not a side effect of 0050.
- `docs/rfcs/0030-web-hosted-browser-acceptance.md:42-57` — defines the
  acceptance contract for a future hosted demo: same Docker image or command
  surface as local, redeployable from clean checkout, bounded persistence,
  and explicit exploratory labeling. This is the bar Option B inherits.
- `docs/rfcs/0032-web-hosted-browser-acceptance-revision.md:9-16,54-66` —
  deliberately landed local-browser acceptance and hosted-demo *docs only*;
  public hosted operation, validated CFD, calibrated resistance, and final
  design-fitness claims remain deferred. RFC 0032 is the most recent
  authoritative scoping decision and chose docs over operation; this vote
  does not reverse it.
- `docs/WEB_VERIFICATION.md:147-210` — confirms no hosted public demo URL is
  deployed today, names the accepted runtime command, persistence caveats,
  and the absence of a production database, account system, quota system,
  hosted worker queue, or public-service SLA.
- `striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md` and
  `striatum/0049-roadmap-reconciliation/integration/PATCH_SUMMARY.md`
  reaffirm that hosted hosting and full parity are still blocked/partial in
  the reconciled roadmap. Adopting a public URL now would contradict the
  reconciliation that just landed.

### Independent external check (accessed 2026-05-14)

- Trame guide (`https://kitware.github.io/trame/guide/`) and Trame
  architecture post (`https://kitware.github.io/trame/blogs/trame-architecture-and-capabilities`)
  confirm Trame is a Python framework with a *dedicated stateful server
  process per client* and that cloud deployment is supported via Docker.
  Independently verified: public Trame hosting is a server-with-state
  workload, not a static asset workload. A "cheap static demo" framing of
  the current app is incorrect.
- Trame VTK tutorial (`https://kitware.github.io/trame/guide/tutorial/vtk.html`)
  confirms that local vs remote VTK rendering is a deployment knob with
  bandwidth/capacity tradeoffs, not an alternative to running a server.
- GitHub Pages docs
  (`https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages`)
  confirm Pages serves static files only. Independently confirmed: GitHub
  Pages cannot host the current `kayakgen serve` app.
- Pyodide docs (`https://pyodide.org/en/stable/index.html`) confirm CPython
  runs in the browser via WebAssembly with pure-Python wheels and *some*
  ported extension packages. Independently verified: Pyodide does not
  trivially run PyVista/VTK/Trame as currently used; treating Option C as a
  drop-in deployment of the existing app is unsupported.
- Fly.io launch docs (`https://fly.io/docs/getting-started/launch/`)
  corroborate that a small Docker-based public deployment is operationally
  plausible. This raises feasibility for Option B but not desirability —
  feasibility was never the blocker.

### What the evidence supports

The evidence supports that the *technical path* for Option B exists and is
well-documented, and that the *operational and claim-hygiene* preconditions
do not. The research packet itself records that Option B "is viable now only
if the operator accepts public endpoint ownership and cost/capacity limits."
No such operator commitment, hosting budget, or shutdown procedure is
recorded in this run's packet, in `docs/WEB_VERIFICATION.md`, or in the
0049 reconciliation. With that precondition unmet, the conservative default
is the correct choice today.

## Why Rejected Alternatives Lose

- **Option B now (narrow public exploratory demo).** Loses on
  preconditions, not direction. The operator owner, hosting budget/cap,
  shutdown/redeploy procedure, abuse handling plan, and Lighthouse / hosted
  smoke evidence required by RFC 0030 §1-§3 and the research's Option B
  acceptance bar are not in hand for this decision. Public Trame is
  per-client stateful (Trame architecture post), so capacity planning is not
  a paperwork formality. Standing up a URL inside this decision would either
  bundle ops scope that 0050 was not chartered to own or land an unowned
  endpoint — both contradict `docs/ROADMAP.md:67,105-122`, which directs
  hosted operation into its own workflow. Option B becomes the right answer
  the moment a workflow lands those preconditions; that workflow should
  inherit *this vote's* acceptance bar verbatim.
- **Option C (static / Pyodide / custom JS frontend).** Loses on identity.
  Pyodide and GitHub Pages independently confirm that Option C is a new
  *frontend and runtime* commitment, not a cheaper hosting target for the
  current Trame app. It also has no design coverage: no RFC currently
  scopes a static viewer, evaluator subset, 3D renderer choice, or
  file-export path. Choosing it here would silently fund a frontend rewrite
  with no RFC. Use this option only via a new RFC.
- **Option D (production hosted app / hosted CFD).** Loses on multiple
  prerequisite decisions. It collides with the no-claims rules in
  `docs/PRD.md:37-49`, `docs/ROADMAP.md:57-59`, RFC 0032 §non-goals, and the
  unfinished real-adapter / calibration / stability tracks (RFCs 0040,
  0041, 0042, 0043). It also assumes accounts/quotas/SLAs which the repo
  explicitly disclaims (`docs/WEB_VERIFICATION.md:192-194`). Defer entirely;
  do not budget for it under any browser-hosting workflow.

## Implementation Gates That Must Remain In Force

These are conditions on any future public-URL or static-demo workflow. The
present decision is **Option A**, so the gates below apply only when a
successor workflow proposes to change posture.

1. **Posture must be named explicitly.** The successor workflow's prompt or
   RFC must state which posture is being closed: no public URL, narrow
   server-backed public demo, or static rewrite exploration. No silent
   promotion via a doc edit, a CI script, or a CHANGELOG entry.
2. **Operator and budget before code.** A narrow public demo (future Option
   B) must have a named operator owner, hosting budget/cap, shutdown
   procedure, and cost/capacity boundary recorded *before* any deployment
   commit. Public Trame is per-client stateful; capacity is not optional.
3. **Same artifact as local.** "Hosted" means `kayakgen serve --host 0.0.0.0
   --port 8080` or the repo `Dockerfile`, deployed at a specific repo
   revision recorded in the workflow. No vendor-specific image, no custom
   build, no forked frontend.
4. **Hosted smoke is required evidence.** Either the existing browser
   acceptance checks run against the deployed URL, or an equivalent
   recorded hosted smoke covers: initial hull/deck render, controls,
   metrics, compact analysis rows, nonblank 3D, representative mutation,
   Share URL reload, STL bytes, and console/page/network cleanliness.
5. **Exact, scoped allowlists.** Any console/network allowlist (Trame, VTK,
   `/paraview/`, etc.) must record URL pattern, status, rationale, owner,
   and removal condition. No broad permanent allowlists. This carries
   forward RFC 0030 §3 and RFC 0032 §2.
6. **Lighthouse only when claimed.** Lighthouse Best Practices `>= 90` is a
   gate *only* when the workflow claims RFC 0030 Lighthouse upkeep or RFC
   0008 hosted-Lighthouse closure. Otherwise it is optional evidence.
7. **Persistence boundaries stay explicit.** `?hull=...` Share URLs survive
   restart; `/api/hulls` IDs are in memory unless a bounded store is
   deliberately configured; `/api/cfd/*` artifacts live only on the server
   filesystem or mounted volume. No production database, account system,
   quota system, design library, hosted worker queue, or public-service
   SLA.
8. **No-claims wording stays visible on the page and in docs.** The demo
   must say it does not run OpenFOAM, SU2, hosted workers, Dockerized
   solvers, or real CFD adapters; it does not provide validated CFD,
   calibrated resistance, high-angle `GZ`, final prediction, or final
   design-fitness decisions.
9. **No bundling with solver / calibration / parity work.** A public-URL
   workflow does not close RFC 0040, 0041, 0042, 0043, desktop parity, or
   mobile parity. Each of those is a separate decision per
   `docs/ROADMAP.md:67`.
10. **Option C requires a new RFC.** A static / Pyodide / custom-JS frontend
    is a runtime and viewer choice, not a hosting choice. It must land via
    its own RFC covering runtime, package compatibility, 3D renderer,
    evaluator subset, file-export path, and explicit no-CFD boundary
    before any implementation work begins.
11. **No silent SLA wording.** Documentation, marketing surface, and
    page copy must not imply uptime guarantees, support response, or
    production reliability.

## No-Claims Language That Must Remain In Force

The decision row, any successor workflow prompt, and any page/runbook copy
must retain (or carry equivalent) the following wording verbatim or in
substance:

- "The web frontend is local/browser-capable with runbook coverage, not a
  completed public hosted demo, full dashboard parity, hosted CFD system, or
  desktop parity rewrite." (`docs/ROADMAP.md:57-59`)
- "No hosted public demo URL is deployed from this repo today, and this
  section is not a production-hosting claim." (`docs/WEB_VERIFICATION.md:149-150`)
- "The demo remains exploratory: it does not run OpenFOAM, SU2, hosted
  workers, or Dockerized solvers; it does not provide validated CFD output,
  calibrated resistance, or final design-fitness decisions."
  (`docs/WEB_VERIFICATION.md:208-210`)
- "There is no production database, account system, quota system, design
  library, hosted worker queue, or public-service SLA in this slice."
  (`docs/WEB_VERIFICATION.md:192-194`)

A future hosted-demo workflow may localize these statements to the deployed
page, but it may not weaken them.

## Risks Acknowledged By This Vote

- Choosing Option A means the project continues to lack a shareable URL.
  Mitigation: the share/no-install motivation behind RFC 0008 is partially
  served today by `?hull=...` Share URLs combined with the documented
  `kayakgen serve` runbook; full public shareability is a deferral, not a
  rejection.
- A future Option B workflow inherits real operational surface (cost,
  uptime, abuse, concurrency, stale state, security updates, Trame
  per-client capacity). This vote does not pretend that surface goes away;
  it requires that it be owned before code lands.
- Static-hosting demand may keep recurring. Option C remains gate-able via
  a dedicated RFC; this vote refuses only the *implicit* adoption of a
  runtime rewrite.

## Confidence

**high.**

Reasons: the local source set (PRD, ROADMAP, RFC 0030, RFC 0032,
`docs/WEB_VERIFICATION.md`, and the 0049 reconciliation) is internally
consistent and points the same direction; the external check independently
confirms Trame's per-client stateful model and the static-vs-server
distinction the research relies on; the research packet's own recommended
posture matches this vote; and the choice is reversible — a successor
workflow can adopt Option B at any time without rework on the local app or
its docs.

## Sub-Agent Help

No spawned sub-agents were used. Independent verification used direct reads
of local docs and the external sources cited above.
