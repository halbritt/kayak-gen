# RFC 0003: Layout Fix, Sheer Plan Rename, and Interactive Station View

Status: landed
Date: 2026-05-09
Context: gui.py; follows RFC 0002 (GUI usability improvements)

## Problem

Three issues observed after first live use of the GUI:

**1. Sliders occlude the plot area.**
The slider axes (x=0.13–0.30) and button axes (x=0.04–0.28) are placed in
figure coordinates that are too close to the GridSpec left boundary (x=0.32).
On typical screen sizes, matplotlib's slider value labels (rendered to the
right of the track) and axis clipping boxes bleed into the cross-section and
plan-view plots.

**2. "Side Profile" is confusing.**
The top-right panel is labelled "Side Profile" but it shows the longitudinal
*elevation* of the hull — specifically, the keel depth and deck centreline
height plotted against x (bow-to-stern position). Users expect a "side
profile" to be a transverse section seen from the side, not a longitudinal
centreline cut. The naval architecture term for this view is the **Sheer
Plan**: it shows the *sheer* line (where hull meets deck), the keel rocker,
and the deck crown profile along the boat's length.

**3. The cross-section is always at midship.**
The "Midship Cross-Section" panel is hardcoded to x=0. A builder wants to
inspect sections at the bow entry, the stern, or any intermediate station —
especially to check the entry angle and rocker at the ends. There is no way
to do this without editing source code.

## Goals

- Slider and button widgets are visually separated from all plot axes at any
  window size between 1280×800 and 2560×1440.
- The top-right panel is labelled "Sheer Plan" with a one-line subtitle
  explaining what the axes show.
- The cross-section panel updates to show the hull profile at any x position
  the user selects, not just midship.
- A cursor line on the plan view and sheer plan tracks the selected station.
- The cross-section panel title shows the current station position in metres.

## Non-Goals

- Full Qt migration of the matplotlib figure layout.
- Showing multiple cross-sections simultaneously.
- Animating the station cursor automatically.

## Proposal

### 1. Fix layout coordinate conflicts

Widen the left margin so plots never conflict with controls:

```python
gs = GridSpec(2, 2, figure=self.fig,
              left=0.38, right=0.97, top=0.93, bottom=0.08,
              hspace=0.45, wspace=0.35)
```

Constrain all slider/button axes to `x ≤ 0.33` and `width ≤ 0.28`:

- Sliders: `[0.07, y, 0.26, 0.025]`  (right edge = 0.33)
- `ax_btn`:     `[0.05, 0.205, 0.12, 0.045]`
- `ax_rst`:     `[0.19, 0.205, 0.12, 0.045]`
- `ax_3d`:      `[0.05, 0.255, 0.26, 0.045]`
- `ax_status`:  `[0.05, 0.160, 0.26, 0.040]`
- `ax_metrics`: `[0.05, 0.020, 0.26, 0.100]`

The 5% gap between x=0.33 and GridSpec left=0.38 is enough that no text or
clipping box can reach the plot area.

### 2. Rename "Side Profile" → "Sheer Plan"

Change the panel title and add a subtitle:

```python
ax.set_title("Sheer Plan", fontsize=10)
ax.set_xlabel("X — bow (−) to stern (+)  (m)")
ax.set_ylabel("Z (m)")
```

Rename the legend entries:
- "Keel" → "Keel line"
- "Deck CL" → "Deck centreline"
- Remove the unlabelled waterline `axhline`; replace it with a labelled entry:
  `ax.axhline(0, color="k", lw=0.8, ls="--", alpha=0.5, label="Waterline")`

### 3. Interactive station cross-section

#### State

Add `self.station_x = 0.0` to `__init__` (metres from centreline; 0 = midship).

#### Station slider

Below the plan view, add a `widgets.Slider` for station position. The slider
range is dynamic: `[-L/2, +L/2]`. Because `L` changes when the length slider
moves, the station slider's range must be updated in `_on_change`:

```python
half_L = self.params["length"] / 2
self.station_slider.valmin = -half_L
self.station_slider.valmax =  half_L
self.station_slider.ax.set_xlim(-half_L, half_L)
self.station_x = float(np.clip(self.station_x, -half_L, half_L))
self.station_slider.set_val(self.station_x)
```

The station slider lives in its own axes below `ax_plan`. Shift the GridSpec
`bottom` from 0.08 to 0.13 to make room, and place the slider axes at
`[0.38, 0.04, 0.59, 0.025]` (aligned with the plan view's x extent).

Label the slider "Station X (m)" with the value displayed.

#### Cross-section panel

Rename `ax_section` title dynamically based on the selected station:

```python
pct = (self.station_x / (self.params["length"] / 2)) * 100
side = "fwd" if self.station_x < 0 else ("aft" if self.station_x > 0 else "mid")
ax.set_title(f"Cross-Section  x = {self.station_x:+.2f} m  ({abs(pct):.0f}% {side})",
             fontsize=9)
```

Replace the hardcoded `kg._get_slice_points(0, ...)` calls with
`kg._get_slice_points(self.station_x, ...)`.

#### Cursor lines

After plotting in `update_plots`, draw a vertical dashed cursor on both the
plan view and the sheer plan:

```python
# Plan view cursor
self.ax_plan.axvline(self.station_x, color="red", lw=1.2, ls="--", alpha=0.8)

# Sheer plan cursor
self.ax_profile.axvline(self.station_x, color="red", lw=1.2, ls="--", alpha=0.8)
```

Because `ax.cla()` clears these on each redraw, the cursor is re-drawn as
part of `update_plots()` — no separate management needed.

#### Station slider callback

```python
def _on_station_change(self, val):
    self.station_x = float(val)
    self.update_plots()
```

Wire: `self.station_slider.on_changed(self._on_station_change)`

## Acceptance Criteria

- At 1440×900, no slider track, value label, or button bounding box overlaps
  any plot axes bounding box (verifiable by visual inspection or by comparing
  `ax.get_position()` bounds).
- The top-right panel title reads "Sheer Plan" and the legend contains
  "Keel line", "Deck centreline", "Waterline".
- Dragging the station slider from −L/2 to +L/2 continuously updates the
  cross-section panel and moves the red cursor on both the plan view and sheer
  plan.
- At the bow (x = −L/2) the cross-section is a near-zero-area sliver; at
  midship (x = 0) it matches the previous hardcoded behaviour.
- The cross-section title shows the current x value and percentage position.

## Open Questions

- Should the station slider snap to named stations (bow, 1/4, mid, 3/4,
  stern) in addition to free drag? Probably a future RFC.
- Should the red cursor also appear on the 3D PyVista view as a plane
  highlight? Deferred; requires passing state to `PyVistaWindow`.

## Implementation Path

- Step 1 — Fix GridSpec left margin and reposition all control axes. (~10
  lines in `_build_sliders`, `_build_button`). No behaviour change.
- Step 2 — Rename "Side Profile" to "Sheer Plan" and fix legend labels.
  (~6 lines in `update_plots`). No behaviour change.
- Step 3 — Add `station_x` state, station slider axes, and
  `_on_station_change`. Update `update_plots` to use `station_x` and draw
  cursor lines. Update `_on_change` to clamp and refresh station slider range.
  (~40 lines total).

Total: ~56 lines changed/added, all in `gui.py`.
