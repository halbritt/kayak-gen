"""Fixed canonical-body geometry clipped by the operating waterplane."""

from __future__ import annotations

from functools import lru_cache
import math

import numpy as np

from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
from kayakgen.model.hull import Hull
from kayakgen.model.operating_state import OperatingPose


@lru_cache(maxsize=1)
def _canonical_arrays(hull_json: str, stations: int) -> tuple[np.ndarray, np.ndarray]:
    body = generated_hull_plus_deck_body(Hull.model_validate_json(hull_json), stations=stations, section_points=40)
    vertices = np.asarray(body.parts[0].vertices, dtype=float)
    faces = np.asarray(body.parts[0].faces, dtype=np.int64)
    vertices.setflags(write=False)
    faces.setflags(write=False)
    return vertices, faces


def _clip_triangles(vertices: np.ndarray, faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    triangles = vertices[faces]
    heights = triangles[:, :, 2]
    kept = faces[(heights <= 0.0).all(axis=1)]
    crossing = triangles[(heights < 0.0).any(axis=1) & (heights > 0.0).any(axis=1)]
    added_vertices: list[np.ndarray] = []
    added_faces: list[list[int]] = []
    for triangle in crossing:
        polygon: list[np.ndarray] = []
        for index, current in enumerate(triangle):
            previous = triangle[index - 1]
            if (current[2] <= 0.0) != (previous[2] <= 0.0):
                point = previous + (current - previous) * (-previous[2] / (current[2] - previous[2]))
                point[2] = 0.0
                polygon.append(point)
            if current[2] <= 0.0:
                polygon.append(current)
        offset = len(vertices) + len(added_vertices)
        added_vertices.extend(polygon)
        added_faces.extend([offset, offset + i, offset + i + 1] for i in range(1, len(polygon) - 1))
    if added_vertices:
        vertices = np.vstack([vertices, added_vertices])
        kept = np.vstack([kept, added_faces])
    used, inverse = np.unique(kept.ravel(), return_inverse=True)
    return vertices[used], inverse.reshape((-1, 3))


class ImmersedGeometry:
    """One fixed-body mesh and pose shared by hydrostatics and resistance.

    X is positive sternward, Y starboard and Z upward. The physical model
    is rotated stern-down about Y and translated relative to the design
    waterplane; world Z=0 is the operating waterplane. This is not a new
    shape, and the Hull record is never changed.
    """

    def __init__(self, hull: Hull, pose: OperatingPose, stations: int = 150) -> None:
        self.hull = hull
        self.pose = pose
        self.body_vertices, self.body_faces = _canonical_arrays(hull.model_dump_json(), stations)
        angle = math.radians(pose.trim_angle_deg)
        self.cos_trim, self.sin_trim = math.cos(angle), math.sin(angle)
        centered_z = self.body_vertices[:, 2] - pose.sinkage_m
        self.world_vertices = np.column_stack([
            self.body_vertices[:, 0] * self.cos_trim + centered_z * self.sin_trim,
            self.body_vertices[:, 1],
            -self.body_vertices[:, 0] * self.sin_trim + centered_z * self.cos_trim,
        ])
        self.vertices, self.faces = _clip_triangles(self.world_vertices, self.body_faces)
        self._station_xs, self._station_sections = self._station_rings()
        self.stations = stations

    def _station_rings(self) -> tuple[np.ndarray, np.ndarray]:
        xs, counts = np.unique(self.body_vertices[:, 0], return_counts=True)
        # End cap centers follow their station ring in the canonical builder.
        ring_count = min(int(n) for n in counts if n > 3)
        rings = []
        for x in xs:
            ring = self.body_vertices[self.body_vertices[:, 0] == x, 1:3][:ring_count]
            if len(ring) == 1:
                ring = np.repeat(ring, ring_count, axis=0)
            rings.append(ring)
        return xs, np.stack(rings)

    def mesh(self, part: str = "hull", stations: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        if part != "hull":
            raise ValueError("immersed geometry exposes the wetted physical surface only")
        if stations is not None and stations != self.stations:
            return immersed_geometry(self.hull, self.pose, stations).mesh(part)
        return self.vertices, self.faces

    def waterplane_edges(self) -> np.ndarray:
        triangles = self.vertices[self.faces]
        edges = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
        return edges[(np.abs(edges[:, :, 2]) <= 1e-12).all(axis=1)]

    def _section_queries(self, xs: np.ndarray) -> np.ndarray:
        upper = np.clip(np.searchsorted(self._station_xs, xs, side="right"), 1, len(self._station_xs) - 1)
        low, high = self._station_sections[upper - 1], self._station_sections[upper]
        ratio = ((xs - self._station_xs[upper - 1]) / (self._station_xs[upper] - self._station_xs[upper - 1]))[:, None, None]
        vertices = low + ratio * (high - low)
        # The canonical loft triangulates each quad along low[i+1]→high[i].
        # Include that intersection so samples follow physical facets exactly.
        diagonal = np.roll(low, -1, axis=1) * (1.0 - ratio) + high * ratio
        sections = np.empty((len(xs), vertices.shape[1] * 2, 2))
        sections[:, 0::2], sections[:, 1::2] = vertices, diagonal
        return sections

    def _body_section(self, x: float) -> np.ndarray:
        if x < self._station_xs[0] or x > self._station_xs[-1]:
            return np.empty((0, 2))
        return self._section_queries(np.array([x]))[0]

    def _breadth_queries(self, xs: np.ndarray, zs: np.ndarray) -> np.ndarray:
        half_breadths = np.zeros(len(xs))
        # Bound temporary polygon arrays independently of a requested grid size.
        for start in range(0, len(xs), 512):
            x, z = xs[start:start + 512], zs[start:start + 512]
            sections = self._section_queries(x)
            previous = np.roll(sections, 1, axis=1)
            z0, z1 = previous[:, :, 1], sections[:, :, 1]
            crosses = ((z[:, None] >= z0) & (z[:, None] < z1)) | ((z[:, None] >= z1) & (z[:, None] < z0))
            ratio = np.divide(z[:, None] - z0, z1 - z0, out=np.zeros_like(z0), where=z1 != z0)
            intersections = previous[:, :, 0] + ratio * (sections[:, :, 0] - previous[:, :, 0])
            values = np.max(np.where(crosses, np.abs(intersections), 0.), axis=1)
            values[(x < self._station_xs[0]) | (x > self._station_xs[-1])] = 0.
            half_breadths[start:start + len(x)] = values
        return half_breadths

    @staticmethod
    def _breadth_at(section: np.ndarray, z: np.ndarray) -> np.ndarray:
        if len(section) < 3:
            return np.zeros_like(z)
        previous = np.roll(section, 1, axis=0)
        z0, z1 = previous[:, 1], section[:, 1]
        crosses = ((z[:, None] >= z0) & (z[:, None] < z1)) | ((z[:, None] >= z1) & (z[:, None] < z0))
        ratio = np.divide(z[:, None] - z0, z1 - z0, out=np.zeros((len(z), len(z0))), where=(z1 != z0))
        intersections = previous[:, 0] + ratio * (section[:, 0] - previous[:, 0])
        return np.max(np.where(crosses, np.abs(intersections), 0.0), axis=1)

    def half_breadth_grid(self, n_stations: int, n_depths: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        xs = np.linspace(float(self.world_vertices[:, 0].min()), float(self.world_vertices[:, 0].max()), n_stations)
        depths = np.linspace(0.0, max(0.0, -float(self.world_vertices[:, 2].min())), n_depths)
        body_x = xs[:, None] * self.cos_trim + depths[None, :] * self.sin_trim
        body_z = self.pose.sinkage_m + xs[:, None] * self.sin_trim - depths[None, :] * self.cos_trim
        breadths = self._breadth_queries(body_x.ravel(), body_z.ravel()).reshape(n_stations, n_depths)
        return xs, depths, breadths

    def reference_draft_m(self) -> float:
        return -float(self._body_section(0.0)[:, 1].min())


def immersed_geometry(hull: Hull, pose: OperatingPose, stations: int | None = None) -> ImmersedGeometry:
    return ImmersedGeometry(hull, pose, stations or 150)


def evaluate_immersed(hull: Hull, pose: OperatingPose, stations: int | None = None, density_kg_m3: float = 1025.0):
    """Integrate clipped physical facets; the virtual Z=0 cap has zero moment."""
    from kayakgen.eval.hydrostatics import Hydrostatics

    geometry = immersed_geometry(hull, pose, stations)
    vertices, faces = geometry.mesh()
    triangles = vertices[faces]
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    tet_volumes = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    signed_volume = float(tet_volumes.sum())
    volume = abs(signed_volume)
    wetted = float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2.0)
    edges = geometry.waterplane_edges()
    cross_xy = edges[:, 0, 0] * edges[:, 1, 1] - edges[:, 1, 0] * edges[:, 0, 1]
    waterplane = abs(float(cross_xy.sum())) / 2.0
    waterplane_i = abs(float(np.sum(cross_xy * (edges[:, 0, 1]**2 + edges[:, 0, 1] * edges[:, 1, 1] + edges[:, 1, 1]**2)))) / 12.0
    if volume > 0:
        centroid = np.sum(tet_volumes[:, None] * (a + b + c) / 4.0, axis=0) / signed_volume
    else:
        centroid = np.zeros(3)
    reference_draft = geometry.reference_draft_m()
    keel_z = -(reference_draft + pose.sinkage_m) * geometry.cos_trim
    gm0 = (waterplane_i / volume + centroid[2] - keel_z - .25 * geometry.cos_trim) if volume > 0 and waterplane > 0 else None
    depths = np.linspace(0.0, max(0.0, -float(geometry.world_vertices[:, 2].min())), 200)
    if geometry.sin_trim == 0:
        breadths = geometry._breadth_at(geometry._body_section(0.0), pose.sinkage_m - depths)
    else:
        breadths = geometry._breadth_queries(depths * geometry.sin_trim, pose.sinkage_m - depths * geometry.cos_trim)
    midship_area = float(np.trapezoid(2.0 * breadths, depths))
    beam = 2.0 * float(breadths.max())
    draft = max(0.0, reference_draft + pose.sinkage_m)
    notes = ["fixed_body_operating_pose_v1"]
    if volume == 0:
        notes.append("operating_pose_dry")
    elif waterplane == 0:
        notes.append("operating_pose_fully_submerged")
    return Hydrostatics(
        displaced_volume_m3=volume, displaced_mass_kg=volume * density_kg_m3,
        wetted_surface_m2=wetted, waterplane_area_m2=waterplane,
        LCB_frac=float(centroid[0] / hull.length_m + .5),
        Cp_actual=volume / (midship_area * hull.length_m) if midship_area else 0.0,
        Cm_actual=midship_area / (beam * draft) if beam * draft else 0.0,
        GM0_m=gm0, notes=notes,
    )
