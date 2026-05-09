import numpy as np
from stl import mesh

class KayakGenerator:
    def __init__(self, length=4.5, beam=0.55, draft=0.12, deck_height=0.23, Cp=0.54, 
                 deck_flatness=8.0, center_box_ratio=0.33):
        """
        Fixed "Half-Deck" bug by standardizing loop logic.
        """
        self.L = length
        self.B = beam
        self.T = draft
        self.H = deck_height
        self.Cp = Cp
        self.Cm = 0.85 
        
        self.deck_power = deck_flatness 
        self.center_ratio = center_box_ratio
        
        self.num_stations = 150 
        self.num_points = 40

    def _get_area_fraction(self, x):
        x_norm = (2 * x) / self.L
        if abs(x_norm) >= 0.9999: return 0.0
        exponent = self.Cp / (1.0 - self.Cp)
        return (1 - abs(x_norm)**exponent)

    def _get_deck_height_scaling(self, x):
        x_norm = abs((2 * x) / self.L) 
        if x_norm <= self.center_ratio:
            return 1.0
        decay_phase = (x_norm - self.center_ratio) / (1.0 - self.center_ratio)
        return (1 - decay_phase**2)

    def _get_slice_points(self, x, part_type):
        # 1. Dimensions
        fraction = self._get_area_fraction(x)
        hull_decay = np.sqrt(fraction)
        
        local_B = (self.B / 2.0) * hull_decay
        local_T = self.T * hull_decay
        
        deck_scale = self._get_deck_height_scaling(x)
        local_Deck = (self.H - self.T) * deck_scale
        
        if local_B < 0.0001: local_B = 0.0001
        
        # 2. Generate Quarter-Slice (Center -> Starboard)
        # We will mirror this to create the full Left->Right span
        starboard_pts = []
        
        if part_type == "hull":
            # Hull Quarter: Keel (0, -T) -> Sheer (B, 0)
            angles = np.linspace(-np.pi/2, 0, self.num_points)
            m = 2.0 + (self.Cm - 0.78) * 5 
            
            for theta in angles:
                t_norm = (theta + np.pi/2) / (np.pi/2)
                y = local_B * (t_norm ** (1/m))
                z = -local_T + (local_T * t_norm)
                starboard_pts.append([y, z])
                
        elif part_type == "deck":
            # Deck Quarter: Center (0, H) -> Sheer (B, 0)
            ys = np.linspace(0, local_B, self.num_points)
            for y in ys:
                y_norm = y / local_B
                z = local_Deck * (1 - y_norm**self.deck_power)
                starboard_pts.append([y, z])

        # 3. Stitch Full Span (Port -> Starboard)
        # This standardized direction fixes the "Half Deck" issue
        points = []
        
        # A. PORT SIDE (Mirror X, keep Z)
        # Iterate backwards so we go from Edge(-B) to Center(0)
        for i in range(len(starboard_pts)-1, -1, -1):
            p = starboard_pts[i]
            points.append([-p[0], p[1]])
            
        # B. STARBOARD SIDE (Original)
        # Iterate forwards from 1 (skip 0 to avoid duplicate center)
        for i in range(1, len(starboard_pts)):
            p = starboard_pts[i]
            points.append([p[0], p[1]])

        return np.array(points)

    def generate_stl(self, part_type, filename):
        x_positions = np.linspace(-self.L/2, self.L/2, self.num_stations)
        
        all_slices = []
        for x in x_positions:
            slice_pts = self._get_slice_points(x, part_type)
            # Add X coordinate
            full_pts = np.column_stack((np.full(len(slice_pts), x), slice_pts[:,0], slice_pts[:,1]))
            all_slices.append(full_pts)
            
        vertices = np.vstack(all_slices)
        num_slices = len(all_slices)
        pts_per_slice = len(all_slices[0])
        
        faces = []
        
        for i in range(num_slices - 1):
            start_curr = i * pts_per_slice
            start_next = (i + 1) * pts_per_slice
            
            for j in range(pts_per_slice - 1):
                c1 = start_curr + j
                c2 = start_curr + j + 1
                n1 = start_next + j
                n2 = start_next + j + 1
                
                # Winding Order (Logic: Points go Left->Right, Slices go Back->Front)
                # Hull: Normals Down/Out
                if part_type == "hull":
                    faces.append([c1, n1, c2])
                    faces.append([c2, n1, n2])
                # Deck: Normals Up/Out
                else:
                    faces.append([c1, n2, c2])
                    faces.append([c2, n2, n1])

        data = np.zeros(len(faces), dtype=mesh.Mesh.dtype)
        mesh_obj = mesh.Mesh(data)
        for i, f in enumerate(faces):
            for j in range(3):
                mesh_obj.vectors[i][j] = vertices[f[j], :]
                
        mesh_obj.save(filename)
        print(f"Saved {filename}")

    def get_mesh_arrays(self, part_type: str) -> tuple[np.ndarray, np.ndarray]:
        """Return (vertices, faces) as NumPy arrays.

        vertices: shape (N, 3) - x, y, z
        faces:    shape (M, 3) - triangle indices into vertices
        """
        x_positions = np.linspace(-self.L / 2, self.L / 2, self.num_stations)
        all_slices = []
        for x in x_positions:
            slice_pts = self._get_slice_points(x, part_type)
            full_pts = np.column_stack(
                (np.full(len(slice_pts), x), slice_pts[:, 0], slice_pts[:, 1])
            )
            all_slices.append(full_pts)

        vertices = np.vstack(all_slices)
        pts_per_slice = len(all_slices[0])
        num_slices = len(all_slices)

        faces = []
        for i in range(num_slices - 1):
            s, n = i * pts_per_slice, (i + 1) * pts_per_slice
            for j in range(pts_per_slice - 1):
                c1, c2, n1, n2 = s + j, s + j + 1, n + j, n + j + 1
                if part_type == "hull":
                    faces.extend([[c1, n1, c2], [c2, n1, n2]])
                else:
                    faces.extend([[c1, n2, c2], [c2, n2, n1]])

        return vertices, np.array(faces)

if __name__ == "__main__":
    kayak = KayakGenerator(length=4.5, beam=0.55, draft=0.12, deck_height=0.23, 
                           Cp=0.55, deck_flatness=8.0, center_box_ratio=0.33)
    
    print("Generating Hull...")
    kayak.generate_stl("hull", "kayak_hull.stl")
    
    print("Generating Deck...")
    kayak.generate_stl("deck", "kayak_deck.stl")
