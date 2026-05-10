# Sources for review

## What this run reviews

The seven landed-on-`main` workflows from the 2026-05-09/10 push, in
order of appearance in `git log --oneline --first-parent`:

| Branch / merge | RFC / topic | Key paths |
|---|---|---|
| `feature/0007a-golden-tests` | RFC 0007 step 1 — regression net | `tests/test_golden.py`, `tests/golden/` |
| `feature/0007b-package-extract` | RFC 0007 steps 2-9 — `kayakgen` package | `kayakgen/`, `pyproject.toml`, top-level shims |
| `feature/0006-class-presets` | RFC 0006 — class presets + `beam_wl_m` | `kayakgen/model/classes.py`, `tests/test_classes.py` |
| `feature/0005-resistance` | RFC 0005 — Michell + ITTC | `kayakgen/eval/resistance.py`, `tests/test_resistance.py` |
| `feature/0004-plumb-bow` | RFC 0004 — `bow_rake`, blended `_end_decay` | `kayakgen/model/geometry.py`, `tests/test_plumb_bow.py` |
| `feature/0008-web-frontend` | RFC 0008 — Trame web UI | `kayakgen/ui/web/`, `Dockerfile`, `tests/test_web.py` |
| `feature/0002-0003-gui-cleanup` | RFC 0002 + 0003 audit + class radio | `docs/rfcs/0002-0003-audit.md`, `kayakgen/ui/desktop.py` |

## Where to look

- **RFCs (the contract):** `docs/rfcs/0002-0003-audit.md`,
  `docs/rfcs/0004-plumb-bow.md`, `docs/rfcs/0005-cfd-resistance.md`,
  `docs/rfcs/0006-design-constraints.md`,
  `docs/rfcs/0007-architectural-revisit.md`,
  `docs/rfcs/0008-web-frontend.md`.
- **Constraints document (the data):**
  `docs/design/kayak_hull_design_constraints.md`.
- **Implementation:** `kayakgen/` (model, eval, io, ui, cli).
- **Tests:** `tests/` (59 tests as of merge of `feature/0002-0003-gui-cleanup`).
- **Top-level shims:** `generator.py`, `gui.py`, `pyvista_view.py`.
- **Packaging:** `pyproject.toml`, `Dockerfile`, `requirements-dev.txt`.

## Known weak spots flagged by the implementer

These are areas where the implementing agent already noted limitations.
Reviewers are encouraged to verify and (re-)bound the limitation rather
than rediscovering it from scratch.

- **RFC 0005 / Michell stability.** `kayakgen/eval/resistance.py`'s
  module docstring documents that the lofted kayak's
  `ε^(-1/2)` gradient at the bow/stern produces non-monotone
  convergence with `np.gradient`. Tests assert qualitative shape +
  Wigley calibration; absolute kayak `R_w` is not pinned. Verify the
  Wigley benchmark and the qualitative tests are sufficient.
- **RFC 0008 / web verification.** No Trame server was launched
  against a browser in the implementing environment. Headless paths
  (state round-trip, controllers, factory) are unit-tested; visual
  parity claim is unverified.
- **Striatum-workflow bypass.** All seven workflows landed on plain
  `feature/<slug>` branches, **not** through the striatum runner
  (the directive given on 2026-05-09). This review run is the first
  use of the runner on this codebase. The integrity-track reviewer
  should call out where this matters and where it does not.
- **Author byline convention.** Every commit on the seven branches
  is authored as `Heath Albritton <halbritt@gmail.com>` with
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`. Heath
  was AFK during the work. Decide whether the convention is
  acceptable.

## Out of scope for this run

- Re-running pytest under load. Reviewers can assume the 59-test
  suite passes (verified before each merge); call out gaps in
  *coverage*, not flakiness.
- New RFCs. The remediation plan may *propose* follow-on RFCs but
  this run does not author them.
- Dependency upgrades or Python-version policy.
