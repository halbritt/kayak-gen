# Role: Reviewer — Claims and user-facing boundaries

Review every new UI string, payload field, and route response for
overclaiming. Stage-4-specific concerns:

- CFD-in-loop acknowledgement copy must not promise calibration, validated
  prediction, design fitness, or seaworthiness.
- Fork-with-seed button labels must not imply the forked run is validated
  or calibrated.
- Pareto-frontier captions and tooltips must not surface display-only
  metrics (max_gz_m, heel_at_max_gz_deg, range_positive_stability_deg,
  fixture_only, OpenFOAM, SU2, calibrated drag, hosted, cloud).
- The existing allowed-phrase set in `tests/test_web_layout.py` is
  authoritative — do not introduce new exceptions.

Findings cite the file, line, and offending phrase.
