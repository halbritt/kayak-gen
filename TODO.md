# TODO — kayakgen

Working action list derived from `KAYAKGEN_DEEP_ARCHITECTURE_REVIEW_CLAUDE_OPUS_4_8_2026-06-03.md`
(+ Addendum A). This is the lean operator-facing complement to
`docs/BACKLOG_EXECUTION_PLAN.md` — checkboxes a solo operator can act on, not a
process artifact. Code-touching items route through the normal workflow when
picked up; this file is just the derived plan.

**Orientation in one line:** the optimizer is not the bottleneck — NSGA-II
already runs. *The fitness function is.* Spend effort on validating fitness and
subtracting carry-cost, not on building more machinery.

Priorities: **P0** do now · **P1** soon · **P2** when convenient · **DECIDE**
blocks other items · **WATCH** striatum tendencies to observe.

**Framing update (C1 resolved 2026-06-03):** kayak-gen is a *test harness for
striatum* — the kayak tool is the workload, the process layer is the
experimental readout (see review **Addendum B**). This re-weights everything
below: the process layer is **not** exhaust to subtract (**B3 withdrawn**), B1's
freeze is now a *test-design* choice rather than an obvious win, and Track A's
value is that it injects the ground truth the workload lacks — making the next
striatum run measure something reality can veto.

---

## Track A — Get a genetic algorithm running honestly (the constructive path)

The destination (evolve optimal hulls) is reachable *today* on the trustworthy
slice of the physics, with zero overclaiming. Do the rungs in order; each gates
the next.

### A0 · Ordinal validation of fitness — **P0, free, do first**
A GA's selection pressure consumes *ordering*, not calibrated magnitudes. Before
trusting any optimizer, prove the model ranks known hulls the way reality does.

- [ ] Pick 3–5 real boats with known reputations (fast surfski, stable tourer, a
      known dog). Encode each as a `Hull` JSON (`kayakgen init`, then edit
      length/beam/draft/Cp/Cm to match published dims).
- [ ] `kayakgen evaluate` each; tabulate `GM0_m`, `wetted_surface_m2`, and `Rt_N`
      across the speed band.
- [ ] Check ordering vs. reality: surfski lowest frictional drag, tourer highest
      `GM0_m`, etc.
- **Gate:** ordering matches → proceed to A1. Ordering wrong → **stop**; the
  model needs work before *any* GA is meaningful. (You learned this for 5
  `evaluate` calls instead of a tank campaign.)

### A1 · A claim-clean GA you can run now — **P0**
Three registry objectives are `role="default_conservative"` — admissible with
**no** exploratory flag, no overclaiming (`kayakgen/search/objectives.py:80-155`).

- [ ] Run a tiny `kayakgen sweep` first; read `summary.csv` to confirm the exact
      metric column names your candidate records actually emit.
- [ ] Write an NSGA-II `SearchSpec` (schema `kayakgen/search/active/spec.py:165`;
      template in review Addendum A) with:
  - minimize **`wetted_surface_m2`** — the *trustworthy* drag proxy. Viscous drag
    ∝ wetted surface (`kayakgen/eval/resistance.py:79-95`), and friction is the
    component the model gets right — this sidesteps the Michell sharp-end blind
    spot. Read it as "minimize frictional drag for a given displacement."
  - maximize **`GM0_m`** — initial stability.
  - minimize **`displacement_error_kg`** — keeps A1 from just shrinking the boat.
  - constraint **`mesh_problem_count` max 0** — feasible geometry only.
- [ ] `kayakgen search spec.json` → `kayakgen compare <run>` for the Pareto front.
- [ ] **Anti-gaming guard:** keep `search_space` bounds tight (inside the envelope
      the geometry kernel is fair over), and *inspect the geometry* of 2-3 frontier
      members — not just their numbers.
- **Done when:** a non-degenerate Pareto front of feasible, sane-looking hulls.

### A2 · Add wave-making drag — **P1, only after A0 passes**
- [ ] Add `Rt_N_last` to objectives and set `"objectives_explicit_exploratory":
      true` (the gate refuses it otherwise — `objectives.py:404`).
- [ ] Watch for the fitness-gaming trap: if the GA evolves needle bows / knife
      sterns, that's the Michell blind spot being exploited
      (`resistance.py:19-29`). Tighten bounds or add a sharpness/fairness
      constraint. Inspect frontier geometry every run.

### A3 · The honest "optimal" — **P2 / later (blocked, see C2)**
- [ ] Only when a *validated* expensive evaluator exists (CFD-in-loop anchored to
      one real measurement) does "optimal" mean optimal-in-the-water. **That** is
      when the frozen GP/EHVI surrogate stack earns its keep (it's built for
      expensive fitness). Until then A1–A2 are the product.

---

## Track B — Subtraction (reduce carry-cost; nothing user-facing breaks)

Bias is toward removal. Each item below currently produces no usable output or
duplicates a boundary.

- [ ] **B1 · Freeze the gated dead-ends** — **P0, ~hours.** Mark calibration
      ingest/accept, measured-stability acceptance, and the real-OpenFOAM path
      "dormant pending data" in one place; stop filing bugs against unreachable
      code. Close `docs/bug-hunt/LEDGER.md` BUG-001 as wontfix-until-data (its
      precondition — a promoted real fit — can't exist without D007/D014 rig
      data). Breaks: nothing; these emit no output today.
- [ ] **B2 · Split `kayakgen/ui/web/app.py`** (2,550 lines) — **P1, 1-2 days.**
      The one untamed boundary; grew 10.6× post-refactor by absorbing the Generate
      panel. Split along the seam the import block already exposes. Behind the
      browser-acceptance suite.
- [x] ~~**B3 · Evict process exhaust from the product repo**~~ — **WITHDRAWN
      (C1 resolved).** The process layer (`striatum/`, `docs/workflows/`, audits,
      dated reports) is the experimental *readout* of the striatum test, not
      exhaust. Keep it; do not evict. If anything, it's the data.
- [ ] **B4 · Freeze GP/EHVI** (`search/active/gp.py`, `ehvi.py`) — **P2.** Correctly
      aimed but premature; NSGA-II covers every admissible objective today. Revisit
      at A3, not before. (Do **not** delete — it's the right tool for the eventual
      expensive-fitness use case.)
- [ ] **B5 · Reconcile `ClaimMetadata` field drift** — **P2, ~hours.** Collapse the
      `accepted_use`→`accepted_uses` and `calibration_version`→`model_version`
      legacy aliases (`claims.py:172-175`); stop double-populating both in
      `resistance.py:166-177`. The canonical integrity contract shouldn't carry
      duplicates. Covered by claim tests.
- [ ] **B6 · Trim dormant claim rungs** — **P2, optional.** `calibrated_model` /
      `validated_design_fitness` and their gates (`claims.py:213`) are unreachable
      today. Keep the literals; demote the unused gate bodies to a comment until a
      real path exists. Low value either way — lowest priority.

---

## Track C — Decisions to resolve (these gate the tracks above)

- [x] **C1 · RESOLVED (2026-06-03): kayak-gen is a test harness for striatum.**
      The kayak tool is the workload; the process layer is the readout.
      Consequences: B3 withdrawn; judge work by what it teaches about striatum;
      "overbuilt as a kayak tool" is the wrong yardstick. The open follow-on is
      a *test-design* question — see C2 and the WATCH section.
- [ ] **C2 · Inject ground truth into the workload? (now a test-design choice.)**
      Post-C1 this is the load-bearing decision: do you want the striatum test to
      measure *value delivery* (not just internal consistency)? If **yes**, give
      the workload something reality can veto — the A0 ordinal check is the
      cheapest; a borrowed inclining test / measurement is the next. If **no**
      (you only want to test coherence-generation), the gated calibration/CFD/
      stability machinery can stay dead as a deliberate stress case, and BUG-001
      becomes a *feature* of the test (does striatum notice dead code?), not a bug.
- [ ] **C3 · Does anyone (incl. you) use the PyQt desktop GUI?** If not, it +
      the `desktop`/PyQt6/pyvistaqt extras are a clean ~600-LOC deletion under
      D009 ("web is primary").
- [x] **C4 · Partially resolved: velocity is a means.** The whole project is a
      means to test striatum, so throughput-with-coherence is the readout, not the
      end. Open part: is striatum's *inability to stop accreting* an acceptable
      property of the methodology, or the thing the next iteration should fix?

---

## WATCH — striatum tendencies this workload reveals

Post-C1 these aren't prohibitions on the kayak tool — features *are* the workload
— they're behaviors to observe in **striatum**, where the real findings live:

- **Reviews become build queues.** RFCs 0048–0058 came straight from a prior
  review's wishlist; striatum ingests suggestions as mandates. Decide whether it
  needs a filter between *review judgment* and *build backlog*. (This review
  withheld a feature wishlist for exactly this reason — don't let it become one.)
- **The process manufactures its own demand.** The audit→RFC→workflow→decision
  loop generates work with no external trigger (D042 names an empty tuple).
  Watch whether striatum ever reaches a stopping condition on its own.
- **Rigor without an anchor.** Striatum's QA finds real defects (BUG-001) in code
  that can never run. Capability is not the gap; a reality check is.

The one rule that stays a genuine product-integrity invariant regardless of
framing: **don't promote** resistance/CFD/GZ past their claim states — and note
that the A1 GA path is honest precisely because it optimizes only admissible
metrics.
