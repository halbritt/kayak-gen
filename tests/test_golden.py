"""
Golden tests pinning current KayakGenerator behavior at default parameters.

These tests are the regression net for the RFC 0007 architectural extraction:
they must stay green as KayakGenerator moves into kayakgen.model.geometry as
LoftedHullGeometry, and as RFC 0006/0005/0004 land follow-on changes.

Three layers of checks, in increasing tolerance:

1. **Hard counts** (exact equality): mesh vertex/face shape. These come from
   integer parameters (num_stations, num_points) and must not drift silently.

2. **Geometry numbers** (1e-9 tolerance): bounding box per axis, hull
   displaced volume (divergence-theorem signed volume; the open hull is
   bounded above by z=0 and the cap contributes 0 to the integral), and
   surface area. Tighter than what numpy summation order can shift across
   reasonable refactors.

3. **STL triangle-payload hash** (exact equality): SHA256 over the binary
   STL's triangle data only (skipping the 80-byte header, which numpy-stl
   leaves uninitialized — back-to-back calls to generate_stl produce
   different header bytes but identical triangle payloads). The golden STL
   files at tests/golden/default_{hull,deck}.stl serve as a human-readable
   reference (openable in a slicer); the test only compares payload hashes,
   not whole-file bytes. If the geometry change is intentional, regenerate
   the goldens via tests/golden/regenerate.py and update the constants
   below in the same commit.

The reference STLs at the repo root (kayak_hull.stl, kayak_deck.stl, …)
are NOT used as oracles — they predate this test suite and can drift with
numpy versions. tests/golden/ is the test-owned source of truth.
"""

import hashlib
import struct
from pathlib import Path

import numpy as np
import pytest

from generator import KayakGenerator


GOLDEN_DIR = Path(__file__).parent / "golden"

DEFAULT_PARAMS = dict(
    length=4.5,
    beam=0.55,
    draft=0.12,
    deck_height=0.23,
    Cp=0.55,
    deck_flatness=8.0,
    center_box_ratio=0.33,
)

# num_stations=150, num_points=40 → 79 points per slice (port-mirror without
# duplicating the centerline) → 150*79 vertices, 149 strips × 78 quads × 2
# triangles = 23244 faces. Pinned for both hull and deck.
EXPECTED_VERTEX_SHAPE = (150 * 79, 3)
EXPECTED_FACE_SHAPE = (149 * 78 * 2, 3)


# Geometry numbers measured from the integrated mesh at default parameters.
# These are the read-side hydrostatics RFC 0007 §4 promotes to the truth
# source; they must be reproduced by kayakgen.eval.hydrostatics post-refactor.
HULL_BBOX_MIN = np.array([-2.25, -0.27469631268496974, -0.11986747846689937])
HULL_BBOX_MAX = np.array([2.25, 0.27469631268496974, 0.0])
HULL_DISPLACED_VOLUME_M3 = 0.11436507419829935
HULL_SURFACE_AREA_M2 = 1.962403180945398

DECK_BBOX_MIN = np.array([-2.25, -0.27469631268496974, 0.0])
DECK_BBOX_MAX = np.array([2.25, 0.27469631268496974, 0.11])
DECK_SURFACE_AREA_M2 = 2.1629635270787663

# SHA256 over the triangle-data payload of the binary STL (header excluded).
# Regenerate via `python tests/golden/regenerate.py` if the change is intentional.
HULL_STL_PAYLOAD_SHA256 = "bd3ba7d497e78349d43495bb0d02097ddfcc3c0e2c5781945c25f781218a4c39"
DECK_STL_PAYLOAD_SHA256 = "fc00ffd0ba772ba6088280fa1aa352a0c9f4f58a5a830cf088a7b09fff763761"


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0))


def _surface_area(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def _stl_payload_sha256(path: Path) -> str:
    """SHA256 over the triangle data of a binary STL, header excluded.

    Layout: 80B header, uint32 triangle count, then n × 50B per triangle
    (12 floats + 2-byte attribute). numpy-stl leaves the header
    uninitialized, so back-to-back writes differ in those 80 bytes despite
    identical geometry; the payload region is deterministic.
    """
    data = path.read_bytes()
    n_tris = struct.unpack("<I", data[80:84])[0]
    return hashlib.sha256(data[84 : 84 + n_tris * 50]).hexdigest()


@pytest.fixture(scope="module")
def kg() -> KayakGenerator:
    return KayakGenerator(**DEFAULT_PARAMS)


@pytest.mark.parametrize("part", ["hull", "deck"])
def test_mesh_counts(kg: KayakGenerator, part: str) -> None:
    vertices, faces = kg.get_mesh_arrays(part)
    assert vertices.shape == EXPECTED_VERTEX_SHAPE
    assert faces.shape == EXPECTED_FACE_SHAPE


def test_hull_bounding_box(kg: KayakGenerator) -> None:
    vertices, _ = kg.get_mesh_arrays("hull")
    np.testing.assert_allclose(vertices.min(axis=0), HULL_BBOX_MIN, atol=1e-12)
    np.testing.assert_allclose(vertices.max(axis=0), HULL_BBOX_MAX, atol=1e-12)


def test_deck_bounding_box(kg: KayakGenerator) -> None:
    vertices, _ = kg.get_mesh_arrays("deck")
    np.testing.assert_allclose(vertices.min(axis=0), DECK_BBOX_MIN, atol=1e-12)
    np.testing.assert_allclose(vertices.max(axis=0), DECK_BBOX_MAX, atol=1e-12)


def test_hull_displaced_volume(kg: KayakGenerator) -> None:
    vertices, faces = kg.get_mesh_arrays("hull")
    volume = _signed_volume(vertices, faces)
    np.testing.assert_allclose(volume, HULL_DISPLACED_VOLUME_M3, rtol=1e-9)


def test_hull_surface_area(kg: KayakGenerator) -> None:
    vertices, faces = kg.get_mesh_arrays("hull")
    area = _surface_area(vertices, faces)
    np.testing.assert_allclose(area, HULL_SURFACE_AREA_M2, rtol=1e-9)


def test_deck_surface_area(kg: KayakGenerator) -> None:
    vertices, faces = kg.get_mesh_arrays("deck")
    area = _surface_area(vertices, faces)
    np.testing.assert_allclose(area, DECK_SURFACE_AREA_M2, rtol=1e-9)


@pytest.mark.parametrize(
    "part,expected_payload_sha",
    [("hull", HULL_STL_PAYLOAD_SHA256), ("deck", DECK_STL_PAYLOAD_SHA256)],
)
def test_stl_payload_hash(
    kg: KayakGenerator, part: str, expected_payload_sha: str, tmp_path: Path
) -> None:
    out = tmp_path / f"{part}.stl"
    kg.generate_stl(part, str(out))

    fresh = _stl_payload_sha256(out)
    assert fresh == expected_payload_sha, (
        f"generated {part} STL payload SHA256 differs from golden; "
        f"regenerate via `python tests/golden/regenerate.py` if intentional"
    )

    golden_payload = _stl_payload_sha256(GOLDEN_DIR / f"default_{part}.stl")
    assert golden_payload == expected_payload_sha, (
        f"golden {part} STL payload SHA256 disagrees with the constant in "
        f"this file; the test data file and constants must move together"
    )
