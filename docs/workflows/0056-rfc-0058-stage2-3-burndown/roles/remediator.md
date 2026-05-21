# Role: Remediator

Apply the must-fix items from the findings ledger. Keep fixes
scoped: preserve every settled decision row, preserve the byte-
stable default for an empty registry, preserve the forbidden-claim
scrub list, preserve the existing theme tokens. Run focused
validation + the full repo suite (minus env-gated OpenFOAM smoke)
before publishing the patch summary.

Publish the patch summary artifact with the exact packet byline.
