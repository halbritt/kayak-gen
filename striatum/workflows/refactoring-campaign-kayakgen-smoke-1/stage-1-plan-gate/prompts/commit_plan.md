# Commit The Gated Plan

Publish the committed plan only after the adjudicator ledger records a
clearing verdict. If the ledger refused the gate, publish a short refusal
note instead, naming the undischarged constraints — do not publish an
executable plan.

The committed plan is the stage-2 input contract:

- The full plan from the holder artifact, with every `binding` constraint
  from the ledger discharged in place — amended slices, added frozen
  surfaces, added characterization-test slices, tightened caps, added
  stop conditions. Mark each discharge with the constraint it discharges.
- The final step table, with move-only and edit slices separate.
- The verification commands and the recorded baseline stage 2 must
  reproduce before its first slice.

Include the exact lowercase `author:` byline near the top of the artifact.
