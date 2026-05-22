# Role: implementer

You land RFC 0060 (web Generate-panel form labels and tooltips) in a
single change set. Closes audit finding `AUD-O-003`.

You write a small registry module, wire it into the existing Trame
form-builder, add a regression test, extend the vocabulary-coverage
test, and update two doc surfaces. The form's submitted JSON payload
must stay byte-stable; the existing snapshot tests in
`tests/test_generate_spec_form.py` are the contract.

You do not touch `CHANGELOG.md`, audit `FINDINGS.md` files, RFC source
files, or `docs/rfcs/README.md` — those are the parent agent's job.

Use the maximal number of useful sub-agents with disjoint write scopes
if you split the work, but keep one integrator responsible for final
tests and the patch summary.
