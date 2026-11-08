"""Geometry-kind substitution and publication checks for native exports."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import ezdxf
import numpy as np
import pytest
from stl import mesh as stl_mesh
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.io.json import save_hull
from kayakgen.model.distribution_v2 import DistributionV2Spec, PolynomialDistribution, UniformDistribution
from kayakgen.model.hull import Hull


FAMILY_CASES = [(family, 2) for family in ("round", "shallow_arch", "shallow_v", "deep_v", "hard_chine")] + [("multi_chine", count) for count in (2, 3, 4)]


def _hull(family: str, chine_count: int = 2) -> Hull:
    return Hull(
        geometry_kind="distribution_v2",
        distribution_v2=DistributionV2Spec(
            waterline_half_breadth=PolynomialDistribution(coefficients=[0.25, 0.0, -0.25]),
            draft_profile=UniformDistribution(value=0.12),
            section_area_curve=UniformDistribution(value=0.04),
            deck_freeboard=UniformDistribution(value=0.15),
            rocker=UniformDistribution(value=0.0),
            cross_section_family=family,
            multi_chine_count=chine_count,
        ),
    )


@pytest.mark.parametrize("family, chine_count", FAMILY_CASES)
def test_generate_v2_stl_preserves_mesh_geometry_and_metre_frame(tmp_path: Path, family: str, chine_count: int) -> None:
    hull = _hull(family, chine_count)
    source = tmp_path / "hull.json"
    save_hull(hull, source)
    result = CliRunner().invoke(app, ["generate", str(source), "--stl-out", str(tmp_path / "export")])
    assert result.exit_code == 0, result.output
    for part in ("hull", "deck"):
        exported = stl_mesh.Mesh.from_file(str(tmp_path / f"export_{part}.stl"))
        vertices, faces = hull.to_geometry().mesh(part)
        np.testing.assert_allclose(exported.vectors, vertices[faces], rtol=1e-6, atol=1e-7)
        assert float(exported.x.max() - exported.x.min()) == pytest.approx(hull.length_m)
        # These are intentionally open inspection surfaces, with boundary edges.
        edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
        _, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
        assert np.any(counts == 1)


@pytest.mark.parametrize("family, chine_count", FAMILY_CASES)
def test_build_export_v2_roundtrips_sections_units_and_offsets(tmp_path: Path, family: str, chine_count: int) -> None:
    hull = _hull(family, chine_count)
    source = tmp_path / "hull.json"
    save_hull(hull, source)
    destination = tmp_path / "bundle"
    result = CliRunner().invoke(app, ["build-export", str(source), "--out", str(destination), "--n-stations", "5"])
    assert result.exit_code == 0, result.output
    manifest = json.loads((destination / "manifest.json").read_text())
    assert manifest["hull_sha256"] == hull.record_hash()
    for entry in manifest["artifacts"]:
        assert hashlib.sha256((destination / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    with (destination / "offsets.csv").open() as stream:
        rows = list(csv.DictReader(line for line in stream if not line.startswith("#")))
    doc = ezdxf.readfile(destination / "sections.dxf")
    assert doc.header["$INSUNITS"] == 4  # DXF modelspace millimetres.
    polylines = list(doc.modelspace().query("LWPOLYLINE"))
    for row, polyline in zip(rows, polylines, strict=True):
        x = float(row["X"])
        expected = hull.to_geometry().section_for_closed_body(x, "hull")
        yz = np.array(list(polyline.get_points("xy"))) / 1000.0
        np.testing.assert_allclose(yz, expected, atol=1e-9)
        assert float(row["half_breadth_Y"]) == pytest.approx(np.max(np.abs(yz[:, 0])), abs=1e-9)
        assert float(row["keel_Z"]) == pytest.approx(np.min(yz[:, 1]), abs=1e-9)
    molds = ezdxf.readfile(destination / "station_molds.dxf")
    assert all(polyline.closed for polyline in molds.modelspace().query("LWPOLYLINE"))


def test_build_export_refuses_existing_bundle_before_replacing_bytes(tmp_path: Path) -> None:
    from kayakgen.services.build_export import BuildExportSpec, write_build_export

    destination = tmp_path / "bundle"
    write_build_export(Hull(), destination, spec=BuildExportSpec(n_stations=3))
    before = {path.name: path.read_bytes() for path in destination.iterdir()}
    with pytest.raises(FileExistsError, match="new or empty directory"):
        write_build_export(_hull("round"), destination)
    assert {path.name: path.read_bytes() for path in destination.iterdir()} == before


def test_failed_build_export_does_not_publish_partial_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.services import build_export

    def fail_dxf(*args, **kwargs):
        raise OSError("injected DXF write failure")

    monkeypatch.setattr(build_export, "write_sections_dxf", fail_dxf)
    destination = tmp_path / "bundle"
    with pytest.raises(OSError, match="injected DXF write failure"):
        build_export.write_build_export(Hull(), destination)
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_builder_preflight_does_not_create_destination_on_missing_extra(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from kayakgen.services.build_export import write_build_export

    monkeypatch.setitem(sys.modules, "ezdxf", None)
    destination = tmp_path / "new-parent" / "bundle"
    with pytest.raises(ImportError):
        write_build_export(Hull(), destination)
    assert not destination.parent.exists()


def test_builder_preflight_validates_station_count_before_writes(tmp_path: Path) -> None:
    from kayakgen.services.build_export import BuildExportSpec, write_build_export

    destination = tmp_path / "new-parent" / "bundle"
    with pytest.raises(ValueError, match="n_stations"):
        write_build_export(Hull(), destination, spec=BuildExportSpec(n_stations=1))
    assert not destination.parent.exists()


def test_builder_preflight_refuses_missing_section_capability(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.services.build_export import write_build_export

    monkeypatch.setattr(Hull, "to_geometry", lambda self: object())
    with pytest.raises(TypeError, match="closed-section export capability"):
        write_build_export(Hull(), tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()


def test_failed_stl_serialization_preserves_prior_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.io.stl import write_stl

    destination = tmp_path / "hull.stl"
    destination.write_bytes(b"prior artifact")

    def fail_save(self, filename, *args, **kwargs):
        Path(filename).write_bytes(b"partial new bytes")
        raise OSError("injected STL write failure")

    monkeypatch.setattr(stl_mesh.Mesh, "save", fail_save)
    with pytest.raises(OSError, match="injected STL write failure"):
        write_stl(_hull("round"), "hull", destination)
    assert destination.read_bytes() == b"prior artifact"
    assert [path.name for path in tmp_path.iterdir()] == ["hull.stl"]


def test_builder_refuses_replacing_the_callers_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.services.build_export import write_build_export

    destination = tmp_path / "working"
    destination.mkdir()
    monkeypatch.chdir(destination)
    with pytest.raises(ValueError, match="working directory"):
        write_build_export(Hull(), Path("."))
    assert Path.cwd() == destination
    assert list(destination.iterdir()) == []


def test_v2_mold_layout_uses_actual_section_width_and_depth(tmp_path: Path) -> None:
    from kayakgen.services.build_export import write_station_molds_dxf

    hull = _hull("round")
    spec = hull.distribution_v2.model_copy(update={
        "waterline_half_breadth": UniformDistribution(value=0.5),
        "draft_profile": UniformDistribution(value=0.3),
    })
    hull = hull.model_copy(update={"distribution_v2": spec})
    path = write_station_molds_dxf(hull, tmp_path / "molds.dxf", n_stations=3)
    doc = ezdxf.readfile(path)
    contours = list(doc.modelspace().query("LWPOLYLINE"))
    bounds = [(min(p[0] for p in e.get_points("xy")), max(p[0] for p in e.get_points("xy"))) for e in contours]
    for left, right in zip(bounds, bounds[1:]):
        assert right[0] - left[1] >= 199.9
    scale_bars = [e for e in doc.modelspace().query("LINE") if abs(e.dxf.end.x - e.dxf.start.x) == 100.0]
    assert len(scale_bars) == 3
    assert all(e.dxf.start.y < -300.0 for e in scale_bars)
