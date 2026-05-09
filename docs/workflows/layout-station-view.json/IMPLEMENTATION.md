# RFC 0003 Implementation

## Changes Made

### Step 1: Layout Coordinate Conflicts

- Updated the main `GridSpec` plot area to start at `left=0.38` and reserve bottom space with `bottom=0.13`.
- Moved all existing slider axes to `[0.07, y, 0.26, 0.025]`.
- Repositioned the generate, reset, 3D view, status, and metrics axes so their right edges stay at or before `x=0.31`.

Verification:

- Run `python gui.py` and confirm slider tracks, value labels, buttons, status text, and metrics no longer overlap the plot panels.
- At a 1440x900 window size, compare widget axes against plot axes and confirm the controls end before `x=0.33` while plots begin at `x=0.38`.

### Step 2: Sheer Plan Rename

- Renamed the top-right plot from `Side Profile` to `Sheer Plan`.
- Updated the X-axis label to describe bow-negative through stern-positive station coordinates.
- Updated legend labels to `Keel line`, `Waterline`, and `Deck centreline`, using a labelled `axhline()` for the waterline.

Verification:

- Run `python gui.py` and confirm the top-right panel title reads `Sheer Plan`.
- Confirm its legend contains `Keel line`, `Waterline`, and `Deck centreline`.

### Step 3: Interactive Station View

- Added `self.station_x` state initialized to `0.0`.
- Added a `Station X (m)` slider below the plan view with dynamic range `[-length / 2, length / 2]`.
- Added `_on_station_change()` so moving the station slider redraws the plots.
- Updated `_on_change()` to refresh the station slider range when length changes and clamp the current station to the new range.
- Updated the cross-section panel to use `kg._get_slice_points(self.station_x, ...)`.
- Added a dynamic cross-section title showing the selected station, percentage from midship to the end, and `fwd`, `mid`, or `aft`.
- Added crimson dashed station cursor lines on both the plan view and sheer plan.

Verification:

- Run `python gui.py`, drag `Station X (m)` from bow to stern, and confirm the cross-section changes continuously.
- Confirm the crimson cursor moves on both the plan view and sheer plan as the station changes.
- Move the length slider and confirm the station slider range updates to the new `[-L/2, +L/2]` bounds.
- Set the station to `0.0` and confirm the cross-section matches the previous midship view.

## Syntax Check

```bash
python -m py_compile gui.py
```
