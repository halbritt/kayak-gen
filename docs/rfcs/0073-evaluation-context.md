# RFC 0073 — Immutable evaluation context and selected-result reports

Status: landed shared context and selected-result reporting.

## Problem and decision

A hull-only report recalculated a 115.666 kg design with the 103 kg default,
and fluid constants differed between evaluators. D059 adopts one explicitly
passed `EvaluationContext` value object, deeply snapshotted inside each
`EvaluationResult`. It binds the full hull record and versioned physical
identity, load/CG, supplied load-field paths, default origin, fluid density,
viscosity, speed grid, numerical settings, method versions and operating pose.
Its canonical fingerprint identifies those inputs. It is not a new persisted
request/job lifecycle. Historical evaluations keep unknown context.

## Behavior

`evaluate --context FILE` executes the specified settings. `--load-case FILE`
requests a fixed-body load equilibrium. A solved pose replaces the requested
pose in the result snapshot and contributes to its fingerprint; hull geometry
is unchanged. Hydrostatics and resistance share that realized pose and fluid.
The mass solver uses the recorded hydrostatic mesh resolution; component loads
retain their mass and CG, and the GM correction applies load CG once.
A failed equilibrium refuses evaluation. Resistance arrays, grid and fluid
constants must agree with the attached context when records are loaded.
When both context and curve record a resistance numerical method version, those
recorded versions must agree. Loading accepts matching historical methods without
checking the installed evaluator and preserves missing legacy metadata as unknown;
only explicit recomputation requires an available requested runtime method.

`design-report --evaluation FILE` renders saved numerical results without
calling evaluators. Missing sections remain unavailable; hull and context
mismatches refuse before output. `--load-case FILE` explicitly creates a new
identified sibling evaluation before rendering. Hull-only compatibility calls
record and disclose their legacy default inputs; they are not the requested
saved run. Full record hashes and physical design hashes have distinct labels.
Comparison-position binding requires the same context, rather than hull-only
equivalence. Immutable component tuples prevent caller mutation after capture.

REST and sweep adapters pass the context through the common service. Explicit
web analysis retains its result and context hash. Desktop
`set_evaluation_context` uses the same service and retains `last_evaluation`;
the live default path records its actual cheaper settings separately.
Existing default web hydro/resistance refresh behavior stays one call per
analysis stage. The report remains a single HTML file with a proportional
embedded preview, responsive tables and collapsible full input records.

## Acceptance and boundaries

Exercise persisted CLI/service roundtrips, two loads, freshwater/seawater,
distinct grids, real v2 matched immersion, web/desktop adapters, deep mutation,
wrong references and forbidden report recomputation. Inspect desktop and
phone report renders with UIPass, including expanded input records. Run the
full suite followed by Ruff. KAYGEN-14 supplies fixed-body geometry and
KAYGEN-15 supplies numerical refinement/admission; no convergence or physical
fitness is inferred merely from retained context. All existing claim gates
and the public-hosting deferral remain closed.

## Migration and reversal

Context and fingerprint fields are additive. No legacy saved record is assigned
an invented original load or environment; newly requested default computations
are explicitly labelled. Saved input records permit deliberate recomputation
with a new method/context. Reversing a deployment preserves artifacts and
selects the preceding installed release; it does not rewrite old provenance.
