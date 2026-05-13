Read `docs/workflows/0028-real-cfd-solver-adapter/SOURCES.md`, especially RFC
0012, RFC 0015, and proposed or accepted RFC 0017.

Produce `striatum/0028-real-cfd-solver-adapter/domain_cfd/REVIEW_DOMAIN_CFD.md`
with:

- author line: `author: operator [self-declared: operator-domain-cfd-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- selected solver setup and installation prerequisites;
- boundary conditions, speed/fluid inputs, and supported speed range;
- mesh-readiness requirements, including watertight input if required;
- raw output collection, residual and force provenance, and solver version
  capture;
- wording that prevents raw CFD output from becoming calibrated or validated
  resistance claims.
