# Falsifier 1 — maintainability and migration risk

author: falsifier-claude-001

Date: 2026-06-05
Run: `run_28c3e3f04b2faa6dbe285358c5ea530e`, stage 1 (falsifier_1)
Target: `striatum/refactoring/kayakgen-smoke-1/01-plan/REFACTORING_PLAN.md`
(plan `plan_kayakgen-smoke-1-split-ui-web-app`, author `plan-holder-claude-001`)
Posture: maintainability and migration risk.
Tree examined: `main` @ `85aaf94`, working tree carrying only the plan artifact.

Three objections survive their strongest rebuttals. Each names the claim it
attacks and the tree evidence. Checks that came back clean are listed at the
end so the adjudicator knows what was probed and cut.

---

## O1 — S4 breaks the event-ordering witness file through a channel by-name re-export cannot preserve; the plan's own stop condition 1 fires

**Attacks:** step table S4 (files + preservation claim), finding F1's
sufficiency claim ("handled by explicit by-name re-export imports"), F2's
claim that exactly three test files need redirects, and stop condition 1's
"modulo the declared mechanical test-pointer redirects of F2".

**Evidence:**

- `tests/test_generative_jobs_web.py:547` —
  `monkeypatch.setattr(app_module, "render_fork_button", fake_render_fork_button)`.
- The **only** consumer of that name is
  `_render_generate_job_fork_buttons` (`kayakgen/ui/web/app.py:2476–2495`,
  call at `:2495`), squarely inside the layout region (1752–2532) that S4
  moves byte-identical into `layout.py` / `LayoutMixin`.
- The test then runs `create_app(...)` and asserts
  `calls == ["done-job"]` — the fake must be invoked during layout build
  (the method's docstring: "known at layout build time").

After S4, the moved method's body resolves `render_fork_button` in
**`layout.py`'s module namespace** (the slice must add
`from kayakgen.ui.web.generate_fork_button import render_fork_button` there
for the byte-identical body to work). The monkeypatch writes to
**`app.py`'s namespace**, which the moved code no longer reads. The fake is
never called; the real widget renders; `calls` stays `[]`; the test goes
hard red at S4. This is deterministic, not a flake.

**Consequences for the plan as written:**

1. Stop condition 7 fires at S4 (a new full-suite failure beyond the F3
   singleton) — unless S4 edits `tests/test_generative_jobs_web.py`.
2. That file is in **no** slice's declared file set, and F2 names exactly
   three editable test files. Stop condition 1 permits non-move edits only
   "modulo the declared mechanical test-pointer redirects of F2 and the
   ≤2-line cli redirect of S3". An S4 edit to the generative-jobs test is
   outside the declared modulo set → stop condition 1 fires by the plan's
   own text. The plan self-halts at S4 either way.
3. The file is the named frozen-surface **witness** for generative-job
   state-transition order (plan §5 row 4; decision §3 "event ordering").
   Editing the witness in the same commit that moves the code it pins is
   exactly the reviewability hazard F2 carefully manages for the other
   three files — here it is undeclared.
4. Structurally, this falsifies F1's preservation mechanism as stated:
   the audit enumerated names tests **read** from `app.py` and concluded
   by-name re-exports suffice. Re-exports preserve reads; they do not
   preserve **monkeypatch writes**, because patching a re-export does not
   reach the consuming module's globals. The F1 audit was read-biased and
   had this site in hand (it audited all 9 web test files).

**Strongest plan-holder rebuttal:** "Add one mechanical edit to S4t: the
patch target string becomes `layout`'s namespace (or the method is left
behind in `app.py` as a declared carve-out). Two lines, cap headroom
exists."

**Does it survive?** As an *amendment*, yes — the fix is cheap. As a
defense of the plan **as written**, no: the step table, F2's three-file
inventory, and stop condition 1's modulo clause are mutually inconsistent
with S4 landing. Whichever repair is chosen (witness-file pointer edit, or
carving `_render_generate_job_fork_buttons` out of the S4 move) must be
declared and adjudicated before the gate clears, because both repairs
touch surfaces the plan currently promises not to touch (the witness file,
or the "all `_render_*` move" shape of S4). An undeclared mid-campaign
discovery at S4 — the most expensive slice, behind the mandatory browser
gate — is the migration-risk scenario this gate exists to prevent.

---

## O2 — the F2 "mechanical pointer redirect, strings unchanged" recipe is not executable as specified; negative and union assertions weaken silently under source partition

**Attacks:** F2's characterization of the test edits as "mechanical
test-pointer redirect ... repoint the `read_text()` source target ...
assertion strings unchanged", S1t/S4t step-table rows, and the plan's
position that revisit condition 2 does not fire.

**Evidence (three independent mechanisms):**

**(a) Mixed-destination single-read functions.**
`tests/test_web_layout.py:68`
(`test_parameter_slider_labels_spacing_and_accessibility_contract`) does
one `app_source = read_text()` (line 69) and then asserts, from the same
variable:

- `f'aria-label="{escaped_label}"'` — lives at `app.py:709` inside
  `_param_row_raw_attrs` → moves in **S1** to `presentation.py`;
- `thumb_label=True` and `classes=f"kg-param-slider kg-param-{key} mt-3"`
  — live at `app.py:1865` / `:1857` in `_build_layout` → move in **S4**
  to `layout.py`.

No single redirect target exists for this function at any point in the
campaign. The minimal correct edit is to split one read into two source
variables and reassign assertions between them — a structural rewrite of
the function, performed **twice** (S1t and S4t). That is a judgment edit,
not a pointer move.

**(b) The union test cannot be "repointed" and erodes a globally frozen
guard.** `tests/test_web_layout.py:397`
(`test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`)
builds a **union** of `app.py` + `controllers.py` + `generate_spec_form.py`
+ the frontier render hook, scrubs four allowed phrases, then asserts a
forbidden claim-vocabulary list (`GZ_max`, `cfd_ready`, `OpenFOAM`,
"calibrated drag", ...) is absent from the union. The phrases it depends
on are scattered across **four** destination slices:

- allowed phrases / state copy at `app.py:568–596`
  (`RAW_COMPARATIVE_CAPTION`, `MESH_PACKAGE_READINESS_COPY`,
  `GENERATIVE_JOBS_*_COPY`, `INVALID_HULL_STATE_COPY`) → S1;
- `"No CFD job prepared."` at `app.py:2227` (`_render_cfd_tab`) → S4;
- `"Invalid hull state"` and `"... not final prediction"` at
  `app.py:1106` / `:1123` (`_refresh_metrics`, handlers region) → **S5**;
- `"no hosted worker is running"` in `controllers.py:92` (stays).

The only meaning-preserving edit is **union expansion** (add
`presentation.py` at S1, `layout.py` at S4, `handlers.py` +
`generate_panel.py` at S5). S1t/S4t could absorb the first two — but
**S5 declares no test edits at all**. After S5 as written, `handlers.py`
— code that writes user-rendered strings (`state.metrics_lines`,
`app.py:1106`) — sits **outside** the forbidden-claim scan. The test stays
green while the guard for the claim/readiness vocabulary (a *globally*
frozen surface, decision §3 closing paragraph) silently stops covering a
render-feeding module. No named verification — full suite, ruff, browser
gate, extras-less run — can detect this erosion.

**(c) Negative assertions weaken by construction under partition.** There
are 8 negative source assertions (`not in app_source`):
`tests/test_web_layout.py:86,89,343,344,652,675,710` and
`tests/test_hydro_tab_descriptions.py:112`. Today each scans the whole
2,550-line integrator; after redirect, each scans only the fragment its
pointer picks. "Strings unchanged" preserves the assertion text while
shrinking what it guards. The plan's own rejected-alternative reasoning
(§F2: concatenation "weakens 'this string exists in this file' to 'exists
somewhere in the package'") is the mirror image of this problem — the plan
weighed the weakening of **positive** assertions and never weighed the
symmetric weakening of **negative** ones, which its chosen approach
inflicts.

**Strongest plan-holder rebuttal:** "F2 already flags this as the
falsifiers' cleanest attack; the caps (S1t ≤20, S4t ≤40) have headroom;
per-function recipes can be settled at slice time; and negative-assertion
scope is a test-suite quality question, not a behavior-preservation one."

**Does it survive?** Partially, and only by conceding the point. The caps
may hold numerically, but the *characterization* — "mechanical",
"pointer", "strings unchanged" — is what stop condition 1 and revisit
condition 2 hinge on, and it is false for at least functions (a) and (b):
those edits require per-assertion destination reasoning and structural
rewrites in the witness suite, twice. "Settled at slice time" is precisely
the migration risk: scope decisions made under slice pressure, invisible
to verification when wrong (the failure mode of (b)/(c) is a **green**
test). If the gate clears, it should clear over an amended F2 that (i)
enumerates the per-function recipe for `test_web_layout.py:68` and `:397`,
(ii) adds the S5 union-expansion edit to the step table, and (iii) states
the intended post-split scope of each of the 8 negative assertions. The
adjudicator may still judge this inside the move-only premise — but on the
current text, the plan's position that revisit condition 2 "does not fire"
rests on an inventory that undercounts the work in its own three files.

---

## O3 — the per-slice rollback claim is false for S1–S3 once successors land; the unwind discipline is undeclared

**Attacks:** step table §7 preamble ("Every slice: one commit,
independently revertible by `git revert` of that commit") and each
"rollback unit" cell.

**Evidence:** invariant 7 freezes dependency direction "sibling →
imported-by-app; **no sibling imports `app.py`**". Therefore every
post-S1 sibling must import S1's `presentation.py` names directly, and the
tree confirms every later region needs them:

- layout region (S4): `LAYOUT_TEST_IDS` / `REGION_CLASSES`
  (`app.py:1756–1759`), `_param_row_raw_attrs` (`:1856`), `REVIEW_TABS`
  (`:1915`), `EXPORT_MENU_ROWS` (`:1940`);
- handlers region (S5): `INVALID_HULL_STATE_COPY` (`:1108`), `_pre_html`
  (`:1158`), `_resistance_table_html` (`:1163`),
  `MESH_PACKAGE_READINESS_COPY` (`:1206,1210`), `validity_badge_title_for`
  (`:1234`), `STATUS_SEGMENTS` (`:1256`);
- panel region (S3): `GENERATIVE_JOBS_EMPTY_COPY` (`:1562`),
  `_generative_job_state_flags` (`:1565`);
- scene region (S2): moved builders feed `_rebuild_scene` in the same
  module.

So after S2 lands, `git revert <S1>` deletes `presentation.py` while a
surviving sibling imports it — a broken tree. Additionally, **every**
slice rewrites `app.py` (each move edits its import/re-export block and
class statement), so any non-LIFO revert conflicts textually in `app.py`.
"Independently revertible" is true only for the newest landed slice; the
real unwind primitive is a reverse-order multi-revert, declared nowhere.

**Why this is load-bearing for migration risk specifically:** O1 and O2
make a mid-campaign halt at S4–S5 a live possibility (their own stop
conditions say so). The moment a halt fires at S4, the operator holds
three landed slices whose advertised exit ("revert that commit") does not
work, and the actual exit (revert S3→S2→S1 in order, resolving `app.py`
each step) has never been stated, costed, or rehearsed. The decision
scored Goal B "reversibility High (8/10)" — that score was an input to
selecting B over A, and it rests on the per-slice claim this objection
falsifies for 3 of 6 slices.

**Strongest plan-holder rebuttal:** "Rollback unit means abort-the-failing-
slice before the next one lands — standard stacked-refactor discipline;
LIFO unwind is implied; reverse-order reverts of a linear stack are
clean."

**Does it survive?** Operationally it is the right discipline — but it is
not what the table says, and the falsification prompt names exactly this
pattern (a rollback unit that later slices depend on in a way the plan
does not declare). The gap is cheap to close: one paragraph declaring
(i) rollback guarantees are LIFO-only, (ii) S1 is load-bearing for every
later slice and is the last thing unwound, (iii) the halt-at-S4 unwind
path. Until that paragraph exists, the step table overstates
reversibility — the exact axis on which Goal B beat Goal A.

---

## Probed and cut (clean checks, for the adjudicator's economy)

These attack lines were investigated and **rebutted by the tree**; they are
not objections:

- **Mixin hazards (plan §10 item 3):** no `self.__name` mangling, no
  `super()` calls, no `__slots__`, no `cached_property`/`__init_subclass__`
  /`__set_name__` anywhere in `app.py`; no test touches `__mro__`,
  `__bases__`, `inspect.getsource`, or pickling of the app. Method names
  across the five regions are disjoint; the class body is `__init__` +
  methods only. The "MRO is inert" claim stands.
- **`test_cli_serve.py:24`'s `patch("kayakgen.ui.web.app.KayakgenApp")`:**
  safe — `create_app` stays in `app.py` and resolves `KayakgenApp` in
  `app.py`'s namespace, so the patch keeps working through every slice.
- **`__import__("kayakgen.ui.web.app", fromlist=["REVIEW_TABS"])`
  (`tests/test_generative_jobs_web.py:432`):** read path; by-name
  re-export preserves it.
- **Region size arithmetic (§7 gross-moved estimates):** verified against
  marker lines 985/1045/1072/1473/1752 and `create_app` at 2533; the
  gross estimates are honest.
- **`tests/test_web_browser.py` does no source reading:** confirmed (only
  a `visual_baselines` path constant at `:42`).
- **The other `monkeypatch.setattr` (`tests/test_generative_jobs_web.py:228`):**
  targets `kayakgen.search.sweep.run_sweep`, outside the blast radius.

## Net assessment

The seam choice is sound and the preservation instincts (byte-identical
bodies, mixins, re-exports) are the right ones. What fails falsification
is the **test-migration inventory**: one undeclared witness-file breakage
that halts S4 under the plan's own stop conditions (O1), a redirect recipe
that is not mechanical for at least two named functions and silently
weakens negative/union guards with no detecting verification (O2), and a
rollback promise that is false for 3 of 6 slices in exactly the scenario
O1/O2 make likely (O3). All three are repairable by amendment before
slicing; none is safely discoverable mid-campaign.
