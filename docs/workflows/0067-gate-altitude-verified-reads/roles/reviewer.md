# Role: Reviewer (workflow 0067)

Review for enforcement honesty. A claim only counts if the mechanism fires
under a negative test.

Required checks:

- Scope first: the diff must stay inside the workflow allowed paths.
- Gate hook: with `KAYAKGEN_ENFORCE_SKIP_PIN=1`, a wrong expected skip count
  fails full-suite pytest; without the env knob and on partial pytest
  invocations, the hook does not punish legitimate subsets.
- Gate scripts: both export the env knob, guard the git-root `cd`, parse the
  final pytest summary line only, and harden malformed parsed values.
- OpenFOAM semantics: default gates expect the documented opt-ins to skip;
  opt-in smoke runs expect those tests to pass.
- Verified reads: every moved production read uses an expected hash from a
  real record/ref. Any path-only legacy read that remains is explicitly
  recorded, not papered over.
- Store hardening: corrupt siblings do not mask intact siblings, read
  OSErrors fall through, equal-length write occupants are rehashed, absolute
  `relative_path` values are contained/refused, and `ArtifactIntegrityError`
  is exported.
- Run focused tests and `scripts/full-gate.sh`; publish a structured finding
  with `accept`, `accept_with_findings`, or `needs_revision`.
