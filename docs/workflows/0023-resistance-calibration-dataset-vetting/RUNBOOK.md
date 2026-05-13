# Runbook - 0023 resistance calibration dataset vetting

1. Validate the workflow.
2. Prepare and start the run on `striatum/0023-resistance-calibration-dataset-vetting`.
3. Run source inventory first, with explicit focus on the University of
   Edinburgh Pacific-canoe dataset found after workflow 0012.
4. Run the three review lanes in parallel:
   - source/provenance/licensing;
   - domain/model-fit suitability;
   - implementation/testability.
5. Consolidate the findings.
6. Implement only the safe gate result:
   - if a source is acceptable for calibration, add the data/provenance
     contract and minimal fixtures needed for a future calibrated wrapper;
   - if a source is useful but not suitable for calibration, record it as a
     validation candidate or citation-only source without changing raw
     resistance behavior;
   - if no source is acceptable, update RFC 0012 and the queue to keep
     resistance uncalibrated.
7. Final review gates whether to proceed to the next queued workflow.

Do not write `.striatum/state.sqlite3` directly. Use the Striatum CLI for run
state.
