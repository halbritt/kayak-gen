# kayakgen

Design a sea kayak or surfski by editing its dimensions and cross sections.
Kayakgen generates hull and deck surfaces, calculates hydrostatics, and
compares candidate designs across parameter sweeps. You can use the same
hull file from the command line, the desktop GUI or the local web workspace.

## Try a hull

From a checkout with Python 3.11 or newer, run:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
kayakgen init hull.json
mkdir -p build
kayakgen generate hull.json --stl-out build/default
kayakgen evaluate hull.json --out build/default.eval.json
```

Open `build/default_hull.stl` and `build/default_deck.stl` in a mesh viewer.
Edit the dimensions in `hull.json` and rerun the last two commands to compare
shapes. Dimensions are in metres.

For the browser workspace, install `python -m pip install -e '.[web]'` and
run `kayakgen serve`. The [user guide](docs/USER_GUIDE.md) covers the desktop
GUI, search, builder exports and local OpenFOAM runs.

Resistance estimates support exploratory comparisons. Physical validation
requires measured data within the design envelope. The
[design constraints](docs/design/kayak_hull_design_constraints.md) explain
the speed and stability tradeoffs. See the [contributor guide](AGENTS.md)
for development and testing.

The project code uses the [MIT license](LICENSE). The
[Edinburgh calibration fixture](tests/fixtures/calibration/edinburgh/DATASHARE_PROVENANCE.md)
has its own CC BY 4.0 attribution and license.
