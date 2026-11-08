# RFC 0078 — Ship runtime templates in installed packages

Status: landed installed runtime templates.

## Problem and decision

The baseline wheel contains Python modules but omits the Jinja design-report
resource and all fifteen vendored OpenFOAM case templates. Source-checkout
checks therefore do not establish that an installed release can render a
report or prepare a solver case. Include both directories as explicit
setuptools package data (D064). Keep their existing runtime paths and bytes.

## Scope and acceptance

Build a wheel, install it outside the source checkout, prove imports resolve
to that installation, render an actual HTML report and both OpenFOAM case
stages, and compare every packaged template against its source hash. Run the
full pytest suite followed by Ruff before integration. This changes package
contents only; no CFD, calibration, public hosting or physical claim expands.

## Deployment and reversal

A local release is a wheel installed into its own versioned virtualenv, with
an atomic current symlink and a loopback-only user service. Record the source
commit, wheel hash, dependency snapshot, installed module location and smoke
results. Reversal selects a previous complete release, then restarts the
service. It never points the installed package back into an editable checkout.
