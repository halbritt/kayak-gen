"""Builder-oriented exports for a Hull (RFC 0051).

The writers in this module turn a :class:`Hull` aggregate into shop-floor
artifacts: an offsets table (CSV), per-station section polylines (DXF),
profile/plan curves (SVG), and per-station mold cross-sections (DXF).
Every artifact carries a header comment with the hull SHA-256 and the
``kayakgen`` version pin so a builder can chase a printed plate back to
the design input that produced it.

The DXF writers depend on ``ezdxf``, installed via the ``[builder]``
extras group. The SVG writers are pure-Python. The CSV writer uses the
stdlib :mod:`csv` module. None of the writers reach across into
``kayakgen.ui`` or ``kayakgen.cli`` -- they consume the geometry the
hull already exposes through :meth:`Hull.to_geometry`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from kayakgen import __version__ as KAYAKGEN_VERSION
from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull

DEFAULT_N_STATIONS = 32
MM_PER_M = 1000.0
SVG_GRID_MM = 100.0
SVG_MARGIN_MM = 50.0


# ---------------------------------------------------------------------------
# Domain options record (RFC 0051: BuildExportSpec).


@dataclass(frozen=True)
class BuildExportSpec:
    """Per-invocation options for :func:`write_build_export`.

    A small value object capturing the operator-facing knobs for a build
    export run. ``n_stations`` controls how many evenly-spaced section
    cuts the exporter samples between the bow and stern. The default
    (32) matches the RFC 0051 acceptance criteria.
    """

    n_stations: int = DEFAULT_N_STATIONS


# Artifact kind literals (RFC 0051). Each value pairs to a writer below.
ArtifactKind = str  # one of ARTIFACT_KINDS below
ARTIFACT_KINDS: tuple[str, ...] = (
    "offsets_csv",
    "sections_dxf",
    "sheer_svg",
    "keel_svg",
    "waterline_svg",
    "deck_centreline_svg",
    "station_molds_dxf",
)


# ---------------------------------------------------------------------------
# Header / hash helpers.


def _hull_hash(hull: Hull) -> str:
    """Return the stable hull SHA-256 (RFC 0049 ``record_hash`` once landed)."""
    # ``Hull.hash`` is the current accessor. RFC 0049 will rename this to
    # ``record_hash``; when that lands this function will pick up the new
    # name without callers needing to change.
    return hull.hash()


def _header_lines(hull: Hull, *, comment_prefix: str) -> list[str]:
    """Return header comment lines (no trailing newlines) for ``hull``."""
    hash_ = _hull_hash(hull)
    return [
        f"{comment_prefix} kayakgen build-export artifact (RFC 0051)",
        f"{comment_prefix} kayakgen_version: {KAYAKGEN_VERSION}",
        f"{comment_prefix} hull_sha256: {hash_}",
    ]


def _station_xs(hull: Hull, n_stations: int) -> np.ndarray:
    """Return the evenly-spaced X coordinates (metres) for ``n_stations`` cuts."""
    if n_stations < 2:
        raise ValueError("n_stations must be >= 2")
    return np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, n_stations)


def _geom(hull: Hull) -> LoftedHullGeometry:
    """Return the lofted geometry implementation for ``hull``."""
    geom = hull.to_geometry()
    # ``to_geometry`` returns a ``HullGeometry`` ABC; in practice the only
    # implementation today is ``LoftedHullGeometry``. The narrower type
    # gives us ``section_for_closed_body``.
    if not isinstance(geom, LoftedHullGeometry):  # pragma: no cover - defensive
        raise TypeError(f"unsupported geometry implementation: {type(geom).__name__}")
    return geom


def _section_yz(geom: LoftedHullGeometry, x: float, part: str) -> np.ndarray:
    """Return the (y, z) ring for ``part`` at station ``x``."""
    return geom.section_for_closed_body(x, part)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Per-station scalar helpers (offsets table + writer-side reuse).


def _half_breadth_at_waterline_m(geom: LoftedHullGeometry, x: float) -> float:
    """Half-breadth (Y, metres) at the design waterline for station ``x``.

    The hull section ring places its maximum ``|y|`` at the waterline
    (z=0); we return that maximum so the offsets table matches what a
    builder sees when running a level on the design WL.
    """
    pts = _section_yz(geom, x, "hull")
    if len(pts) == 0:
        return 0.0
    return float(np.max(np.abs(pts[:, 0])))


def _keel_z_m(geom: LoftedHullGeometry, x: float) -> float:
    """Keel-line Z (metres, negative below WL) for station ``x``."""
    pts = _section_yz(geom, x, "hull")
    if len(pts) == 0:
        return 0.0
    return float(np.min(pts[:, 1]))


def _sheer_z_m(geom: LoftedHullGeometry, x: float) -> float:
    """Sheer Z (metres) for station ``x``.

    The lofted geometry meets the deck at the design waterline, so the
    sheer line is z = 0 along the rail for every in-bounds station and
    drops to the keel curve at the exact plumb-stem endpoints. We
    report the maximum z attained by the hull section ring, which
    reduces to 0 in the body and to the local stem-tip z at endpoints.
    """
    pts = _section_yz(geom, x, "hull")
    if len(pts) == 0:
        return 0.0
    return float(np.max(pts[:, 1]))


def _deck_centreline_z_m(geom: LoftedHullGeometry, x: float) -> float:
    """Deck-centreline Z (metres) for station ``x``."""
    deck_pts = _section_yz(geom, x, "deck")
    if len(deck_pts) == 0:
        return 0.0
    # Deck section is mirrored around y=0; the centreline value is the
    # maximum z attained (peak of the deck arc).
    return float(np.max(deck_pts[:, 1]))


# ---------------------------------------------------------------------------
# CSV writer.


def write_offsets_csv(
    hull: Hull,
    out: Path,
    *,
    n_stations: int = DEFAULT_N_STATIONS,
) -> Path:
    """Write a per-station offsets table for ``hull`` to ``out``.

    Columns (units metres): ``X``, ``half_breadth_Y``, ``keel_Z``,
    ``sheer_Z``, ``deck_centreline_Z``. A header block of ``#``-
    prefixed comment lines carries the hull SHA-256 and the kayakgen
    version. ``out``'s parent directory must already exist.
    """
    out = Path(out)
    geom = _geom(hull)
    xs = _station_xs(hull, n_stations)

    buf = io.StringIO()
    for line in _header_lines(hull, comment_prefix="#"):
        buf.write(line + "\n")
    buf.write("# units: metres; columns: X, half_breadth_Y, keel_Z, sheer_Z, deck_centreline_Z\n")

    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["X", "half_breadth_Y", "keel_Z", "sheer_Z", "deck_centreline_Z"])
    for x in xs:
        writer.writerow(
            [
                f"{float(x):.9f}",
                f"{_half_breadth_at_waterline_m(geom, float(x)):.9f}",
                f"{_keel_z_m(geom, float(x)):.9f}",
                f"{_sheer_z_m(geom, float(x)):.9f}",
                f"{_deck_centreline_z_m(geom, float(x)):.9f}",
            ]
        )
    out.write_text(buf.getvalue())
    return out


# ---------------------------------------------------------------------------
# DXF helpers.


def _new_dxf_doc(hull: Hull):
    """Return a fresh ezdxf document with header comments wired in.

    The hull SHA-256 + kayakgen version land in ``doc.header.custom_vars``
    so a downstream CAD tool can read them and a re-parse via
    :func:`ezdxf.readfile` recovers them deterministically. Timestamp
    header variables are zeroed so the body of the file is as
    deterministic as ezdxf allows (the library still emits its own
    save-time GUIDs and a footer timestamp; the determinism test compares
    parsed entity content, not raw bytes).
    """
    import ezdxf  # local import: optional [builder] extras dependency.

    doc = ezdxf.new(setup=False)
    # Millimetres so the DXF reads naturally on a shop CAD viewer.
    doc.header["$INSUNITS"] = 4
    # Zero out the create/update timestamps we can reach. ezdxf injects a
    # save-time footer comment we can't easily suppress; tests treat DXF
    # determinism at the entity-content level.
    for var in ("$TDCREATE", "$TDUCREATE", "$TDUPDATE", "$TDUUPDATE"):
        doc.header[var] = 0
    custom = doc.header.custom_vars
    custom.append("KAYAKGEN_VERSION", KAYAKGEN_VERSION)
    custom.append("HULL_SHA256", _hull_hash(hull))
    custom.append("KAYAKGEN_ARTIFACT", "RFC 0051 build-export")
    return doc


def _station_layer_name(x_m: float) -> str:
    """Return the DXF layer name encoding station X (metres).

    Example: ``+1.234m``, ``-0.500m``. The fixed-width format keeps
    layer ordering stable when listed alphabetically.
    """
    sign = "+" if x_m >= 0 else "-"
    return f"STATION_{sign}{abs(x_m):07.3f}m"


def write_sections_dxf(
    hull: Hull,
    out: Path,
    *,
    n_stations: int = DEFAULT_N_STATIONS,
) -> Path:
    """Write per-station section polylines (YZ plane) to a DXF.

    Each station's section is written as a single LWPolyline on its own
    layer; the layer name encodes the X position via
    :func:`_station_layer_name`. Units are millimetres in DXF
    modelspace (1:1 scale), so a CAD viewer reads metres unchanged.
    """
    out = Path(out)
    geom = _geom(hull)
    xs = _station_xs(hull, n_stations)

    doc = _new_dxf_doc(hull)
    msp = doc.modelspace()
    for x in xs:
        layer = _station_layer_name(float(x))
        if layer not in doc.layers:
            doc.layers.add(layer)
        ring = _section_yz(geom, float(x), "hull")
        # YZ plane: builder sees Y (half-breadth) along the horizontal
        # and Z (depth/height) along the vertical. Convert metres to mm
        # for the modelspace.
        points = [(float(y) * MM_PER_M, float(z) * MM_PER_M) for y, z in ring]
        if points:
            msp.add_lwpolyline(
                points,
                close=False,
                dxfattribs={"layer": layer},
            )
    doc.saveas(str(out))
    return out


# ---------------------------------------------------------------------------
# SVG helpers.


def _svg_render_curve(
    hull: Hull,
    title: str,
    pts_mm: Sequence[tuple[float, float]],
) -> str:
    """Return the SVG body string for a single 2D curve in mm coordinates."""
    if not pts_mm:
        raise ValueError("curve must have at least one point")
    xs = [p[0] for p in pts_mm]
    ys = [p[1] for p in pts_mm]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    # Inflate the box so curves that lie on an axis still show grid.
    if xmax - xmin < 1.0:
        xmax = xmin + 1.0
    if ymax - ymin < 1.0:
        ymax = ymin + 1.0

    margin = SVG_MARGIN_MM
    width_mm = (xmax - xmin) + 2 * margin
    height_mm = (ymax - ymin) + 2 * margin + 40.0  # extra for scale bar

    def tx(x: float) -> float:
        return (x - xmin) + margin

    def ty(y: float) -> float:
        # Flip Y so positive Z renders upward like a profile view.
        return height_mm - margin - (y - ymin) - 40.0

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    for line in _header_lines(hull, comment_prefix="  "):
        parts.append(f"<!--{line} -->")
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{width_mm:.3f}mm" height="{height_mm:.3f}mm" '
        f'viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">'
    )
    parts.append(f"  <title>{title}</title>")

    # Grid: 100 mm squares.
    parts.append('  <g stroke="#cccccc" stroke-width="0.2" fill="none">')
    grid = SVG_GRID_MM
    x0 = (int(xmin // grid)) * grid
    x1 = (int(xmax // grid) + 1) * grid
    y0 = (int(ymin // grid)) * grid
    y1 = (int(ymax // grid) + 1) * grid
    gx = x0
    while gx <= x1 + 1e-6:
        sx = tx(gx)
        parts.append(
            f'    <line x1="{sx:.3f}" y1="{ty(ymin):.3f}" '
            f'x2="{sx:.3f}" y2="{ty(ymax):.3f}" />'
        )
        gx += grid
    gy = y0
    while gy <= y1 + 1e-6:
        sy = ty(gy)
        parts.append(
            f'    <line x1="{tx(xmin):.3f}" y1="{sy:.3f}" '
            f'x2="{tx(xmax):.3f}" y2="{sy:.3f}" />'
        )
        gy += grid
    parts.append("  </g>")

    # The curve itself.
    path_d = "M " + " L ".join(f"{tx(p[0]):.3f} {ty(p[1]):.3f}" for p in pts_mm)
    parts.append(
        f'  <path d="{path_d}" stroke="#000000" stroke-width="0.5" fill="none" />'
    )

    # Scale bar (100 mm, fixed position bottom-left).
    sb_x = margin
    sb_y = height_mm - 20.0
    parts.append('  <g stroke="#000000" stroke-width="0.5" fill="#000000">')
    parts.append(
        f'    <line x1="{sb_x:.3f}" y1="{sb_y:.3f}" '
        f'x2="{sb_x + SVG_GRID_MM:.3f}" y2="{sb_y:.3f}" />'
    )
    parts.append(
        f'    <text x="{sb_x:.3f}" y="{sb_y - 5.0:.3f}" '
        f'font-family="monospace" font-size="6">100 mm</text>'
    )
    parts.append("  </g>")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _waterplane_curve_mm(hull: Hull) -> list[tuple[float, float]]:
    """Plan-view design waterline as (X mm, half-breadth mm) samples."""
    geom = _geom(hull)
    wp = geom.waterplane(200)
    return [(float(x) * MM_PER_M, float(y) * MM_PER_M) for x, y in wp]


def _keel_curve_mm(hull: Hull) -> list[tuple[float, float]]:
    """Profile-view keel line as (X mm, Z mm) samples."""
    geom = _geom(hull)
    kl = geom.keel_line(200)
    return [(float(x) * MM_PER_M, float(z) * MM_PER_M) for x, z in kl]


def _deck_centreline_curve_mm(hull: Hull) -> list[tuple[float, float]]:
    """Profile-view deck-centreline as (X mm, Z mm) samples."""
    geom = _geom(hull)
    dc = geom.deck_centreline(200)
    return [(float(x) * MM_PER_M, float(z) * MM_PER_M) for x, z in dc]


def _sheer_curve_mm(hull: Hull) -> list[tuple[float, float]]:
    """Profile-view sheer line as (X mm, Z mm) samples.

    The sheer in this geometry is where the hull's wetted surface meets
    the deck: the top of the hull ring at each station. We resample at
    200 stations to match the other curves' resolution.
    """
    geom = _geom(hull)
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, 200)
    return [(float(x) * MM_PER_M, _sheer_z_m(geom, float(x)) * MM_PER_M) for x in xs]


def write_sheer_svg(hull: Hull, out: Path) -> Path:
    """Write the profile-view sheer SVG for ``hull`` to ``out``."""
    out = Path(out)
    out.write_text(_svg_render_curve(hull, "sheer", _sheer_curve_mm(hull)))
    return out


def write_keel_svg(hull: Hull, out: Path) -> Path:
    """Write the profile-view keel-line SVG for ``hull`` to ``out``."""
    out = Path(out)
    out.write_text(_svg_render_curve(hull, "keel", _keel_curve_mm(hull)))
    return out


def write_waterline_svg(hull: Hull, out: Path) -> Path:
    """Write the plan-view design-waterline SVG for ``hull`` to ``out``."""
    out = Path(out)
    out.write_text(_svg_render_curve(hull, "waterline", _waterplane_curve_mm(hull)))
    return out


def write_deck_centreline_svg(hull: Hull, out: Path) -> Path:
    """Write the profile-view deck-centreline SVG for ``hull`` to ``out``."""
    out = Path(out)
    out.write_text(
        _svg_render_curve(hull, "deck_centreline", _deck_centreline_curve_mm(hull))
    )
    return out


# ---------------------------------------------------------------------------
# Station molds DXF (registration marks + scale bar per station).


def write_station_molds_dxf(
    hull: Hull,
    out: Path,
    *,
    n_stations: int = DEFAULT_N_STATIONS,
) -> Path:
    """Write a DXF whose entities are per-station mold cross-sections.

    Each station contributes:

    - a plus-sign registration mark at the origin of that station's
      cell (two short crossing lines),
    - the mold cross-section polyline (the union of the hull ring and
      the deck ring, traced as a single closed contour), and
    - a labelled 100 mm scale bar.

    Stations are tiled left-to-right in modelspace with a generous gap
    so a builder can plot and cut each cell from a single sheet.
    """
    out = Path(out)
    geom = _geom(hull)
    xs = _station_xs(hull, n_stations)

    doc = _new_dxf_doc(hull)
    msp = doc.modelspace()

    cell_width_mm = hull.beam_oa_m * MM_PER_M + 200.0
    for index, x in enumerate(xs):
        layer = _station_layer_name(float(x))
        if layer not in doc.layers:
            doc.layers.add(layer)
        cell_origin_x = index * cell_width_mm

        # Registration plus-sign (40 mm crossbar).
        plus = 20.0
        msp.add_line(
            (cell_origin_x - plus, 0.0),
            (cell_origin_x + plus, 0.0),
            dxfattribs={"layer": layer},
        )
        msp.add_line(
            (cell_origin_x, -plus),
            (cell_origin_x, plus),
            dxfattribs={"layer": layer},
        )

        # Hull ring (z negative, below WL) + deck ring (z positive,
        # above WL) traced as one closed contour. Hull ring already
        # spans port-to-starboard; we append the reversed deck ring to
        # close the mold profile across the top.
        hull_ring = _section_yz(geom, float(x), "hull")
        deck_ring = _section_yz(geom, float(x), "deck")
        contour: list[tuple[float, float]] = []
        for y, z in hull_ring:
            contour.append(
                (float(y) * MM_PER_M + cell_origin_x, float(z) * MM_PER_M)
            )
        for y, z in deck_ring[::-1]:
            contour.append(
                (float(y) * MM_PER_M + cell_origin_x, float(z) * MM_PER_M)
            )
        if contour:
            msp.add_lwpolyline(
                contour,
                close=True,
                dxfattribs={"layer": layer},
            )

        # Labelled 100 mm scale bar below the section.
        bar_y = (-hull.draft_m * MM_PER_M) - 60.0
        msp.add_line(
            (cell_origin_x - 50.0, bar_y),
            (cell_origin_x + 50.0, bar_y),
            dxfattribs={"layer": layer},
        )
        msp.add_text(
            f"100mm @ X={float(x):+.3f}m",
            dxfattribs={
                "layer": layer,
                "height": 6.0,
                "insert": (cell_origin_x - 50.0, bar_y - 12.0),
            },
        )

    doc.saveas(str(out))
    return out


# ---------------------------------------------------------------------------
# Manifest + top-level orchestration.


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_build_export(
    hull: Hull,
    out_dir: Path,
    *,
    spec: BuildExportSpec | None = None,
) -> Path:
    """Write every build-export artifact for ``hull`` under ``out_dir``.

    Creates ``out_dir`` if needed, runs each writer in turn, and writes a
    ``manifest.json`` enumerating every artifact with its SHA-256 and
    byte size. Returns the manifest path.
    """
    if spec is None:
        spec = BuildExportSpec()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[tuple[str, Path]] = [
        ("offsets_csv", write_offsets_csv(hull, out_dir / "offsets.csv", n_stations=spec.n_stations)),
        ("sections_dxf", write_sections_dxf(hull, out_dir / "sections.dxf", n_stations=spec.n_stations)),
        ("sheer_svg", write_sheer_svg(hull, out_dir / "sheer.svg")),
        ("keel_svg", write_keel_svg(hull, out_dir / "keel.svg")),
        ("waterline_svg", write_waterline_svg(hull, out_dir / "waterline.svg")),
        ("deck_centreline_svg", write_deck_centreline_svg(hull, out_dir / "deck_centreline.svg")),
        (
            "station_molds_dxf",
            write_station_molds_dxf(
                hull, out_dir / "station_molds.dxf", n_stations=spec.n_stations
            ),
        ),
    ]

    entries: list[dict[str, object]] = []
    for kind, path in artifacts:
        entries.append(
            {
                "kind": kind,
                "path": path.name,
                "sha256": _sha256_of(path),
                "bytes": path.stat().st_size,
            }
        )

    manifest = {
        "artifact_set": "rfc_0051_build_export",
        "kayakgen_version": KAYAKGEN_VERSION,
        "hull_sha256": _hull_hash(hull),
        "n_stations": spec.n_stations,
        "artifacts": entries,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path
