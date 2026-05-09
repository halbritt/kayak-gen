# Task: Implement RFC 0003 — Layout Fix, Sheer Plan, Interactive Station View

The full RFC is provided as a context file. The current `gui.py` is also
provided. Read both carefully. All changes are in `gui.py` only.

---

## Step 1: Fix layout coordinate conflicts

Change the GridSpec left margin and bottom margin:

```python
gs = GridSpec(2, 2, figure=self.fig,
              left=0.38, right=0.97, top=0.93, bottom=0.13,
              hspace=0.45, wspace=0.35)
```

In `_build_sliders`, change the slider axes position:
```python
ax = self.fig.add_axes([0.07, y, 0.26, 0.025])
```

In `_build_button`, update ALL axes positions:
```python
ax_btn  = self.fig.add_axes([0.05, 0.205, 0.12, 0.045])
ax_rst  = self.fig.add_axes([0.19, 0.205, 0.12, 0.045])
ax_3d   = self.fig.add_axes([0.05, 0.255, 0.26, 0.045])
ax_status  = self.fig.add_axes([0.05, 0.160, 0.26, 0.040])
ax_metrics = self.fig.add_axes([0.05, 0.020, 0.26, 0.100])
```

---

## Step 2: Rename "Side Profile" → "Sheer Plan"

In `update_plots`, in the side profile section, make these changes:

```python
ax.set_title("Sheer Plan", fontsize=10)
ax.set_xlabel("X — bow (−) to stern (+)  (m)")
ax.set_ylabel("Z (m)")
```

Change the plot calls to use labelled legend entries:
```python
ax.plot(xs, keel_z,    color="steelblue", linewidth=2, label="Keel line")
ax.axhline(0, color="k", lw=0.8, ls="--", alpha=0.5, label="Waterline")
ax.plot(xs, deck_cl_z, color="seagreen",  linewidth=2, label="Deck centreline")
```

Remove the existing unlabelled `ax.plot(xs, np.zeros_like(xs), ...)` line
(it's replaced by the labelled `axhline` above).

---

## Step 3: Add interactive station cross-section

### 3a. Add station_x state in `__init__`

After `self._pv_window = None`, add:
```python
self.station_x = 0.0
```

### 3b. Add station slider in `_build_button`

After the metrics axes, add:
```python
half_L = self.params["length"] / 2
self.ax_station = self.fig.add_axes([0.38, 0.04, 0.59, 0.025])
self.station_slider = widgets.Slider(
    self.ax_station, "Station X (m)",
    -half_L, half_L, valinit=0.0,
)
self.station_slider.on_changed(self._on_station_change)
```

### 3c. Add station change callback

```python
def _on_station_change(self, val):
    self.station_x = float(val)
    self.update_plots()
```

### 3d. Update `_on_change` to clamp and refresh station slider range

At the end of `_on_change`, after `self._refresh_metrics()`, add:
```python
half_L = self.params["length"] / 2
self.station_slider.valmin = -half_L
self.station_slider.valmax =  half_L
self.station_slider.ax.set_xlim(-half_L, half_L)
self.station_x = float(np.clip(self.station_x, -half_L, half_L))
self.station_slider.set_val(self.station_x)
```

### 3e. Update cross-section panel in `update_plots`

Change:
```python
hull_pts = kg._get_slice_points(0, "hull")
deck_pts = kg._get_slice_points(0, "deck")
```
to:
```python
hull_pts = kg._get_slice_points(self.station_x, "hull")
deck_pts = kg._get_slice_points(self.station_x, "deck")
```

Change the title from the hardcoded `"Midship Cross-Section"` to:
```python
half_L = kg.L / 2
pct = (self.station_x / half_L * 100) if half_L > 0 else 0
side = "fwd" if self.station_x < -0.01 else ("aft" if self.station_x > 0.01 else "mid")
ax.set_title(
    f"Cross-Section  x = {self.station_x:+.2f} m  ({abs(pct):.0f}% {side})",
    fontsize=9,
)
```

### 3f. Add cursor lines in `update_plots`

At the end of the cross-section section (after `ax.grid(...)`), add:
```python
self.ax_plan.axvline(self.station_x, color="crimson", lw=1.2, ls="--", alpha=0.85)
```

At the end of the sheer plan section (after `ax.grid(...)`), add:
```python
self.ax_profile.axvline(self.station_x, color="crimson", lw=1.2, ls="--", alpha=0.85)
```

Note: because `update_plots` calls `ax.cla()` at the top of each section,
the cursor lines must be drawn AFTER the main plot content in each section —
the order matters. Place each `axvline` call as the very last line of its
respective plot section, before the `ax.grid(...)` or just after it.

---

## Verify

```bash
python -m py_compile gui.py
```

Then write `docs/workflows/layout-station-view.json/IMPLEMENTATION.md`
summarising what changed and how to verify each of the three steps.
