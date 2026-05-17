"""Tests for the RFC 0051 builder-oriented exports.

The whole suite skips when the ``[builder]`` extras (``ezdxf``) are not
installed -- the writers degrade cleanly, but the on-disk round-trip
tests here need the parser to be importable.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from typer.testing import CliRunner

ezdxf = pytest.importorskip("ezdxf", reason="builder extras not installed")

from kayakgen import __version__ as KAYAKGEN_VERSION  # noqa: E402
from kayakgen.cli.main import app  # noqa: E402
from kayakgen.io.json import save_hull  # noqa: E402
from kayakgen.model.hull import Hull  # noqa: E402
from kayakgen.services.build_export import (  # noqa: E402
    ARTIFACT_KINDS,
    BuildExportSpec,
    write_build_export,
    write_deck_centreline_svg,
    write_keel_svg,
    write_offsets_csv,
    write_sections_dxf,
    write_sheer_svg,
    write_station_molds_dxf,
    write_waterline_svg,
)

SVG_NS = "{http://www.w3.org/2000/svg}"


def _read_offsets_csv(path: Path) -> tuple[list[dict[str, float]], list[str]]:
    """Return (rows, comment-lines) parsed from an offsets CSV."""
    text = path.read_text()
    comments = [ln for ln in text.splitlines() if ln.startswith("#")]
    body = "\n".join(ln for ln in text.splitlines() if not ln.startswith("#"))
    reader = csv.DictReader(body.splitlines())
    rows: list[dict[str, float]] = []
    for raw in reader:
        rows.append({k: float(v) for k, v in raw.items()})
    return rows, comments


def test_write_offsets_csv_round_trips_and_carries_header(tmp_path: Path) -> None:
    hull = Hull()
    path = write_offsets_csv(hull, tmp_path / "offsets.csv", n_stations=16)
    rows, comments = _read_offsets_csv(path)

    assert len(rows) == 16
    expected_cols = {"X", "half_breadth_Y", "keel_Z", "sheer_Z", "deck_centreline_Z"}
    assert expected_cols.issubset(rows[0].keys())
    joined = "\n".join(comments)
    assert hull.hash() in joined
    assert KAYAKGEN_VERSION in joined


def test_write_sections_dxf_parses_with_ezdxf(tmp_path: Path) -> None:
    hull = Hull()
    path = write_sections_dxf(hull, tmp_path / "sections.dxf", n_stations=12)
    doc = ezdxf.readfile(str(path))
    station_layers = [layer.dxf.name for layer in doc.layers if layer.dxf.name.startswith("STATION_")]
    assert len(station_layers) == 12
    polylines = [
        e for e in doc.modelspace() if e.dxftype() == "LWPOLYLINE"
    ]
    assert len(polylines) == 12

    custom_vars = {name: value for name, value in doc.header.custom_vars}
    assert custom_vars.get("HULL_SHA256") == hull.hash()
    assert custom_vars.get("KAYAKGEN_VERSION") == KAYAKGEN_VERSION


@pytest.mark.parametrize(
    "writer, filename",
    [
        (write_sheer_svg, "sheer.svg"),
        (write_keel_svg, "keel.svg"),
        (write_waterline_svg, "waterline.svg"),
        (write_deck_centreline_svg, "deck_centreline.svg"),
    ],
)
def test_svg_writers_parse_and_carry_header(
    tmp_path: Path, writer, filename: str
) -> None:
    hull = Hull()
    path = writer(hull, tmp_path / filename)
    text = path.read_text()
    assert hull.hash() in text
    assert KAYAKGEN_VERSION in text
    root = ET.fromstring(text)
    assert root.tag.endswith("svg")
    # At least one path (the curve) and at least one line (grid/scale-bar).
    assert root.findall(f".//{SVG_NS}path"), "expected at least one <path>"
    assert root.findall(f".//{SVG_NS}line"), "expected at least one <line>"


def test_write_station_molds_dxf_parses_with_ezdxf(tmp_path: Path) -> None:
    hull = Hull()
    path = write_station_molds_dxf(hull, tmp_path / "molds.dxf", n_stations=8)
    doc = ezdxf.readfile(str(path))
    station_layers = [layer.dxf.name for layer in doc.layers if layer.dxf.name.startswith("STATION_")]
    assert len(station_layers) == 8

    entities_by_type: dict[str, int] = {}
    for entity in doc.modelspace():
        entities_by_type[entity.dxftype()] = entities_by_type.get(entity.dxftype(), 0) + 1
    # Each station contributes 2 registration LINEs, 1 scale-bar LINE, 1
    # closed LWPOLYLINE, and 1 TEXT label.
    assert entities_by_type.get("LWPOLYLINE", 0) == 8
    assert entities_by_type.get("LINE", 0) >= 8 * 3
    assert entities_by_type.get("TEXT", 0) >= 8


def test_offsets_csv_agrees_with_section_dxf_within_1mm(tmp_path: Path) -> None:
    hull = Hull()
    csv_path = write_offsets_csv(hull, tmp_path / "offsets.csv", n_stations=20)
    dxf_path = write_sections_dxf(hull, tmp_path / "sections.dxf", n_stations=20)

    rows, _ = _read_offsets_csv(csv_path)
    by_layer: dict[str, float] = {}
    by_layer_z_min: dict[str, float] = {}
    by_layer_z_max: dict[str, float] = {}
    doc = ezdxf.readfile(str(dxf_path))
    for entity in doc.modelspace():
        if entity.dxftype() != "LWPOLYLINE":
            continue
        ys: list[float] = []
        zs: list[float] = []
        for x, y, *_ in entity.get_points():
            # The DXF stores (Y_mm, Z_mm) in the polyline's 2D points
            # (we wrote modelspace as the YZ plane in mm). Convert back
            # to metres for comparison with the offsets table.
            ys.append(float(x) / 1000.0)
            zs.append(float(y) / 1000.0)
        if not ys:
            continue
        layer = entity.dxf.layer
        by_layer[layer] = max(abs(v) for v in ys)
        by_layer_z_min[layer] = min(zs)
        by_layer_z_max[layer] = max(zs)

    # The offsets rows came from the same evenly-spaced X grid, so they
    # match the DXF entities one-for-one in order.
    sorted_layers = sorted(by_layer.keys())
    # Order layers by the X they encode rather than alphabetically (the
    # leading sign character breaks lexicographic order around 0).
    sorted_layers.sort(key=lambda name: float(name.removeprefix("STATION_").removesuffix("m")))
    assert len(sorted_layers) == len(rows)
    for row, layer in zip(rows, sorted_layers):
        # 1 mm tolerance, per RFC 0051 acceptance criteria.
        assert abs(row["half_breadth_Y"] - by_layer[layer]) < 1e-3
        assert abs(row["keel_Z"] - by_layer_z_min[layer]) < 1e-3
        assert abs(row["sheer_Z"] - by_layer_z_max[layer]) < 1e-3


def _content_signature_for_dxf(path: Path) -> str:
    """Hash the *parsed* entity content of a DXF (skip lib-injected GUIDs)."""
    doc = ezdxf.readfile(str(path))
    sig = hashlib.sha256()
    for layer in sorted(layer.dxf.name for layer in doc.layers):
        sig.update(layer.encode("utf-8"))
        sig.update(b"|")
    rendered_entities: list[str] = []
    for entity in doc.modelspace():
        parts: list[str] = [entity.dxftype(), entity.dxf.layer]
        if entity.dxftype() == "LWPOLYLINE":
            parts.append(repr(list(entity.get_points("xy"))))
        elif entity.dxftype() == "LINE":
            parts.append(repr((tuple(entity.dxf.start), tuple(entity.dxf.end))))
        elif entity.dxftype() == "TEXT":
            parts.append(entity.dxf.text)
            parts.append(repr(tuple(entity.dxf.insert)))
        rendered_entities.append("::".join(parts))
    for line in sorted(rendered_entities):
        sig.update(line.encode("utf-8"))
        sig.update(b"\n")
    custom = {name: value for name, value in doc.header.custom_vars}
    for key in sorted(custom):
        sig.update(f"{key}={custom[key]}".encode("utf-8"))
        sig.update(b"\n")
    return sig.hexdigest()


def test_build_export_is_deterministic_across_two_invocations(tmp_path: Path) -> None:
    hull = Hull()
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    write_build_export(hull, dir_a, spec=BuildExportSpec(n_stations=10))
    # Sleep so any wall-clock-time leakage we missed would surface.
    time.sleep(0.05)
    write_build_export(hull, dir_b, spec=BuildExportSpec(n_stations=10))

    text_kinds = ("offsets.csv", "sheer.svg", "keel.svg", "waterline.svg", "deck_centreline.svg")
    for name in text_kinds:
        a_bytes = (dir_a / name).read_bytes()
        b_bytes = (dir_b / name).read_bytes()
        assert a_bytes == b_bytes, f"{name} differs across invocations"

    for name in ("sections.dxf", "station_molds.dxf"):
        assert _content_signature_for_dxf(dir_a / name) == _content_signature_for_dxf(
            dir_b / name
        ), f"{name} parsed content differs across invocations"

    # Manifest entries (excluding sha256 + bytes, which legitimately
    # vary for the DXF artifacts because of the lib-injected GUIDs)
    # should be otherwise stable.
    manifest_a = json.loads((dir_a / "manifest.json").read_text())
    manifest_b = json.loads((dir_b / "manifest.json").read_text())
    for entry_a, entry_b in zip(manifest_a["artifacts"], manifest_b["artifacts"]):
        assert entry_a["kind"] == entry_b["kind"]
        assert entry_a["path"] == entry_b["path"]
        if entry_a["path"].endswith(".dxf"):
            continue
        assert entry_a["sha256"] == entry_b["sha256"]
        assert entry_a["bytes"] == entry_b["bytes"]
    assert manifest_a["hull_sha256"] == manifest_b["hull_sha256"] == hull.hash()
    assert manifest_a["kayakgen_version"] == manifest_b["kayakgen_version"] == KAYAKGEN_VERSION


def test_build_export_manifest_enumerates_every_artifact(tmp_path: Path) -> None:
    hull = Hull()
    write_build_export(hull, tmp_path, spec=BuildExportSpec(n_stations=6))
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    kinds = {entry["kind"] for entry in manifest["artifacts"]}
    assert kinds == set(ARTIFACT_KINDS)
    for entry in manifest["artifacts"]:
        path = tmp_path / entry["path"]
        assert path.exists()
        assert path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_cli_build_export_smoke(tmp_path: Path) -> None:
    hull_path = tmp_path / "hull.json"
    save_hull(Hull(), hull_path)
    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["build-export", str(hull_path), "--out", str(out_dir), "--n-stations", "8"],
    )
    assert result.exit_code == 0, result.output
    assert "wrote" in result.output
    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["n_stations"] == 8
    assert {entry["kind"] for entry in manifest["artifacts"]} == set(ARTIFACT_KINDS)
