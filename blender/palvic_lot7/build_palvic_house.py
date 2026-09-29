"""
Palvic residence - The Pointe at Jackson Hill, Lot 7
3D model generator for Blender 5.x (tested with the Blender 5.0 Python module).

Source drawings: Drafting Designs LLC, sheets 1-3 (Feb 05, 2024)
  Sheet 1  Floor plan (1/4" = 1'-0"), typical wall section, partition details
  Sheet 2  Electrical plan, roof plan
  Sheet 3  Front / back / left / right elevations (1/4" = 1'-0")

All geometry below is written in FEET, exactly as measured from the vector PDF.
Plan coordinates: X grows to the right (east), Y grows toward the front of the
house (south), origin = back-left outside face of studs (top-left of sheet 1).
In Blender:  x = X,  y = -Y  (front of the house faces -Y),  z = up.
The scene uses Imperial units, so every dimension reads in feet/inches.

HOW TO RUN
  * Inside Blender: Scripting workspace -> Open this file -> Run Script.
    It (re)builds everything inside the collection "Palvic House - Lot 7"
    and leaves anything else in your file untouched.
  * Headless:  blender -b -P build_palvic_house.py -- --save palvic_lot7.blend
               (optional: --glb palvic_lot7.glb)
"""

import math
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh when used as a module)
import bmesh
from mathutils import Vector

FT = 0.3048                       # 1 ft in Blender units (metres)
ROOT_NAME = "Palvic House - Lot 7"

# ---------------------------------------------------------------------------
# Key heights (ft)
# ---------------------------------------------------------------------------
PLATE = 9.0          # 9' ceiling height in every room (per plan notes)
DOOR_H = 6 + 8 / 12  # 6'-8" doors
HEADER = 7 + 8 / 12  # "HEADER HEIGHT @ 7'-8"" for all windows
DW = 0.042           # 1/2" gypsum board
TS = 0.07            # lap siding + sheathing projection
STONE_T = 0.45       # stone veneer projection (partition detail - exterior)
STONE_TOP = 4.83     # stone wainscot height (front elevation)
GRADE = -0.5         # finished grade below the slab top
PITCH = 5 / 12       # main + carport roof 5:12
ZW = 9.5             # underside of roof deck at the outside wall line
ROOF_T = 0.6         # rafters + deck + shingles
RIDGE_Y = 29.3       # main ridge (runs east-west)
CARPORT_RIDGE_Y = 15.55

# ---------------------------------------------------------------------------
# Plan data (ft) - measured from sheet 1
# ---------------------------------------------------------------------------
# Wall stud footprints: (x0, y0, x1, y1, exterior_side or None, stone_veneer)
WALLS = [
    # exterior walls ------------------------------------------------------
    (7.37, 0.00, 19.54, 0.29, "N", 0),     # dining back
    (7.37, 0.29, 7.67, 10.00, "W", 0),     # dining west (back patio)
    (19.25, 0.29, 19.54, 10.37, "E", 0),   # dining east (back porch)
    (19.54, 10.37, 35.41, 10.66, "N", 0),  # kitchen back
    (35.13, 4.99, 35.41, 10.37, "W", 0),   # utility west
    (35.41, 4.99, 46.00, 5.29, "N", 0),    # utility back
    (46.00, 0.00, 46.29, 4.99, "W", 0),    # half bath west
    (46.00, 0.00, 58.54, 0.29, "N", 0),    # half bath + storage back
    (58.25, 0.29, 58.54, 6.67, "E", 0),    # storage east
    (46.29, 6.38, 58.25, 6.67, "S", 0),    # storage front (carport)
    (46.00, 6.67, 46.29, 50.16, "E", 0),   # east wall
    (32.63, 49.87, 46.29, 50.16, "S", 1),  # master bedroom front
    (32.63, 45.75, 32.91, 49.87, "W", 0),  # master bedroom west (porch)
    (16.04, 45.75, 32.91, 46.09, "S", 0),  # foyer front (porch)
    (15.75, 45.79, 16.04, 49.87, "E", 0),  # bedroom 2 closet east (porch)
    (0.00, 49.87, 16.04, 50.16, "S", 1),   # bedroom 2 front
    (0.00, 10.00, 0.29, 50.16, "W", 0),    # west wall
    (0.00, 10.00, 7.37, 10.29, "N", 0),    # walk-in closet back
    # interior partitions -------------------------------------------------
    (7.37, 10.29, 7.67, 16.38, None, 0),
    (0.29, 16.38, 11.87, 16.67, None, 0),
    (11.87, 16.38, 12.17, 24.16, None, 0),
    (12.17, 23.87, 15.75, 24.16, None, 0),
    (15.75, 23.87, 16.04, 45.79, None, 0),
    (11.87, 24.16, 12.17, 49.87, None, 0),
    (0.29, 28.75, 11.87, 29.05, None, 0),
    (2.40, 29.05, 2.70, 32.13, None, 0),
    (0.29, 32.13, 2.70, 32.42, None, 0),
    (7.85, 32.13, 11.87, 32.42, None, 0),
    (0.29, 37.50, 11.87, 37.79, None, 0),
    (12.17, 42.50, 15.75, 42.79, None, 0),
    (12.17, 44.87, 15.75, 45.17, None, 0),
    (35.13, 10.66, 35.41, 12.65, None, 0),
    (35.41, 10.37, 46.00, 10.66, None, 0),
    (35.00, 15.87, 46.00, 16.66, None, 0),
    (35.00, 16.66, 35.29, 23.87, None, 0),
    (35.29, 22.75, 46.00, 23.03, None, 0),
    (32.63, 23.87, 35.29, 24.16, None, 0),
    (32.63, 24.16, 32.91, 45.75, None, 0),
    (35.00, 24.16, 35.29, 31.12, None, 0),
    (32.91, 31.12, 38.46, 31.41, None, 0),
    (32.91, 31.41, 33.08, 34.99, None, 0),
    (38.17, 31.41, 38.46, 34.99, None, 0),
    (32.91, 34.99, 46.00, 35.29, None, 0),
    (42.13, 29.62, 46.00, 29.91, None, 0),
    (42.13, 29.91, 42.41, 30.77, None, 0),
    (42.13, 33.77, 42.41, 34.99, None, 0),
    (49.88, 0.29, 50.17, 6.38, None, 0),
    (46.00, 5.29, 46.29, 6.67, None, 0),
]

# Openings. "at" is any point inside the host wall at the centre of the opening.
# Door styles: ext6 = exterior 6-panel, glass = front door full lite,
#              int = interior 2-panel, cased = cased opening (no leaf)
DOORS = [
    ("Door - Dining to Back Porch", (19.40, 7.37), 3.0, "ext6"),
    ("Door - Half Bath", (46.15, 2.97), 2.0, "ext6"),
    ("Door - Storage", (54.21, 6.52), 3.0, "ext6"),
    ("Door - Utility", (39.00, 10.52), 3.0, "int"),
    ("Door - Carport Entry", (46.15, 14.35), 3.0, "ext6"),
    ("Door - Master Closet", (39.87, 22.89), 3.0, "int"),
    ("Door - Master Bath", (40.30, 35.14), 2 + 8 / 12, "int"),
    ("Door - Master WC", (38.32, 33.41), 2.0, "int"),
    ("Door - Master Bedroom", (32.77, 40.42), 3.0, "int"),
    ("Door - Front Entry", (24.33, 45.92), 3.0, "glass"),
    ("Door - Bedroom 1", (12.02, 26.83), 2 + 8 / 12, "int"),
    ("Door - Bedroom 1 Closet", (1.87, 16.52), 2.0, "int"),
    ("Door - Hall Bath", (12.02, 34.00), 2.0, "int"),
    ("Door - Bath Linen", (2.55, 30.53), 2.0, "int"),
    ("Door - Bedroom 2", (12.02, 39.71), 2 + 8 / 12, "int"),
    ("Door - Hall Closet", (13.71, 42.64), 2.0, "int"),
    ("Door - Bedroom 2 Closet", (12.02, 47.54), 2.0, "int"),
    ("Cased Opening - Hall 4'-6\"", (15.90, 39.71), 4.5, "cased"),
]

# Windows: (name, at, total width, height, units side by side)
WINDOWS = [
    ("Window 2-3060 - Dining", (13.40, 0.15), 6.0, 6.0, 2),
    ("Window 3060 - Dining", (19.40, 3.00), 3.0, 6.0, 1),
    ("Window 3-2040 - Kitchen", (27.33, 10.52), 6.0, 4.0, 3),
    ("Window 3060 - Bedroom 1", (0.15, 18.70), 3.0, 6.0, 1),
    ("Window 2-3060 - Bedroom 2", (8.10, 50.00), 6.0, 6.0, 2),
    ("Window 2-2060 - Foyer W", (19.04, 45.92), 4.0, 6.0, 2),
    ("Window 2-2060 - Foyer E", (29.63, 45.92), 4.0, 6.0, 2),
    ("Window 2-3060 - Master", (39.46, 50.00), 6.0, 6.0, 2),
]

# Outside face of studs, heated area + carport storage (clockwise on the sheet)
OUTLINE = [(7.37, 0), (19.54, 0), (19.54, 10.37), (35.13, 10.37), (35.13, 4.99),
           (46.0, 4.99), (46.0, 0), (58.54, 0), (58.54, 6.67), (46.29, 6.67),
           (46.29, 50.16), (32.63, 50.16), (32.63, 46.09), (16.04, 46.09),
           (16.04, 50.16), (0, 50.16), (0, 10.0), (7.37, 10.0)]

FRONT_PORCH = [(0, 50.16), (16.04, 50.16), (16.04, 46.09), (32.63, 46.09),
               (32.63, 50.16), (46.29, 50.16), (46.29, 58.63), (0, 58.63)]
BACK_PORCH = [(19.54, 0), (46.0, 0), (46.0, 4.99), (35.13, 4.99), (35.13, 10.37),
              (19.54, 10.37)]
PATIO = [(0, 0), (7.37, 0), (7.37, 10.0), (0, 10.0)]
CARPORT = [(46.29, 6.67), (58.54, 6.67), (58.54, 0), (74.79, 0), (74.79, 31.1),
           (46.29, 31.1)]

# Floor finishes (x0, y0, x1, y1, material)
FLOOR_ZONES = [
    (0.29, 16.67, 11.87, 28.75, "carpet"),     # bedroom 1
    (0.29, 10.29, 7.37, 16.38, "carpet"),      # bedroom 1 walk-in closet
    (0.29, 37.79, 11.87, 49.87, "carpet"),     # bedroom 2
    (12.17, 45.17, 15.75, 49.87, "carpet"),    # bedroom 2 closet
    (32.91, 35.29, 46.0, 49.87, "carpet"),     # master bedroom
    (35.29, 16.66, 46.0, 22.75, "carpet"),     # master closet
    (0.29, 29.05, 11.87, 37.5, "tile"),        # hall bath
    (35.29, 23.03, 46.0, 31.41, "tile"),       # master bath
    (38.46, 31.41, 46.0, 34.99, "tile"),       # master bath (shower side)
    (33.08, 31.41, 38.17, 34.99, "tile"),      # master WC
    (35.41, 5.29, 46.0, 10.37, "tile"),        # utility
    (35.41, 10.66, 46.0, 15.87, "tile"),       # mud hall
    (46.29, 0.29, 49.88, 6.38, "tile"),        # half bath
    (50.17, 0.29, 58.25, 6.38, "concrete"),    # carport storage
]

ROOM_LABELS = [
    ("DINING", 13.46, 8.2), ("KITCHEN", 27.0, 14.6), ("LIVING ROOM", 24.3, 31.0),
    ("FOYER", 24.3, 44.0), ("BEDROOM", 6.1, 22.7), ("BEDROOM", 6.1, 43.8),
    ("BATH", 6.0, 34.0), ("W.I.C.", 3.8, 13.3), ("MASTER\nBEDROOM", 39.5, 42.5),
    ("MASTER BATH", 39.5, 27.2), ("MASTER\nCLOSET", 40.6, 19.7),
    ("UTILITY", 40.7, 8.6), ("HALL", 40.7, 13.8), ("1/2 BATH", 48.1, 3.3),
    ("STORAGE", 54.2, 3.3), ("CARPORT", 64.0, 18.0), ("PORCH", 27.0, 5.0),
    ("PORCH", 24.3, 54.5), ("PORCH", 3.7, 5.0),
]

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def V(x, y, z=0.0):
    return Vector((x * FT, -y * FT, z * FT))


class MeshBuilder:
    """Accumulates boxes / prisms (plan feet) into one multi-material object."""

    def __init__(self, name, coll):
        self.name, self.coll = name, coll
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _face(self, verts, mat):
        f = self.bm.faces.new(verts)
        f.material_index = self._mi(mat)
        return f

    def box(self, x0, y0, z0, x1, y1, z1, mat, top=None):
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        v = [self.bm.verts.new(V(*p)) for p in c]
        for idx in ((0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self._face([v[i] for i in idx], mat)
        self._face([v[4], v[5], v[6], v[7]], top or mat)

    def prism(self, poly, z0, z1, mat, top=None, side=None):
        """Vertical extrusion of a plan polygon [(x, y), ...]."""
        b = [self.bm.verts.new(V(x, y, z0)) for x, y in poly]
        t = [self.bm.verts.new(V(x, y, z1)) for x, y in poly]
        n = len(poly)
        self._face(b[::-1], mat)
        self._face(t, top or mat)
        for i in range(n):
            j = (i + 1) % n
            self._face([b[i], b[j], t[j], t[i]], side or mat)

    def prism_x(self, poly_yz, x0, x1, mat, edge_mats=None):
        """Extrusion along X of a polygon drawn in the Y-Z plane."""
        a = [self.bm.verts.new(V(x0, y, z)) for y, z in poly_yz]
        b = [self.bm.verts.new(V(x1, y, z)) for y, z in poly_yz]
        n = len(poly_yz)
        self._face(a[::-1], mat)
        self._face(b, mat)
        for i in range(n):
            j = (i + 1) % n
            m = edge_mats[i] if edge_mats else mat
            self._face([a[i], a[j], b[j], b[i]], m)

    def prism_y(self, poly_xz, y0, y1, mat):
        """Extrusion along Y of a polygon drawn in the X-Z plane."""
        a = [self.bm.verts.new(V(x, y0, z)) for x, z in poly_xz]
        b = [self.bm.verts.new(V(x, y1, z)) for x, z in poly_xz]
        n = len(poly_xz)
        self._face(a[::-1], mat)
        self._face(b, mat)
        for i in range(n):
            j = (i + 1) % n
            self._face([a[i], a[j], b[j], b[i]], mat)

    def cyl(self, cx, cy, z0, z1, rx, ry=None, mat=None, seg=24, top=None):
        ry = rx if ry is None else ry
        poly = [(cx + rx * math.cos(2 * math.pi * i / seg),
                 cy + ry * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        self.prism(poly, z0, z1, mat, top=top)

    def hcyl(self, axis, c1, cz, a0, a1, r, mat, seg=20):
        """Horizontal cylinder along 'x' (c1 = y) or 'y' (c1 = x)."""
        poly = [(c1 + r * math.cos(2 * math.pi * i / seg),
                 cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        if axis == "x":
            self.prism_x(poly, a0, a1, mat)
        else:
            self.prism_y(poly, a0, a1, mat)

    def box_rot(self, cx, cy, z0, z1, length, width, ang, mat, offset=0.0):
        """Rectangle rotated by ang (radians) about (cx, cy), shifted along its length."""
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for u, v in ((offset, -width / 2), (offset + length, -width / 2),
                     (offset + length, width / 2), (offset, width / 2)):
            pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
        self.prism(pts, z0, z1, mat)

    def build(self):
        if not self.bm.verts:
            self.bm.free()
            return None
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        self.coll.objects.link(ob)
        return ob


DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


def fb(mb, f, face, u0, u1, a0, a1, z0, z1, mat):
    """Box measured from a wall face: u = distance into the room along facing f,
    a = absolute coordinate along the wall (X for N/S walls, Y for E/W walls)."""
    fx, fy = DIRS[f]
    if fx == 0:
        ya, yb = face + fy * u0, face + fy * u1
        mb.box(a0, ya, z0, a1, yb, z1, mat)
    else:
        xa, xb = face + fx * u0, face + fx * u1
        mb.box(xa, a0, z0, xb, a1, z1, mat)


def fc(mb, f, face, u, a, z0, z1, ru, ra, mat, seg=24):
    fx, fy = DIRS[f]
    if fx == 0:
        mb.cyl(a, face + fy * u, z0, z1, ra, ru, mat, seg)
    else:
        mb.cyl(face + fx * u, a, z0, z1, ru, ra, mat, seg)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
M = {}


def _new_mat(name, color, rough=0.5, metal=0.0):
    full = "PAL_" + name
    m = bpy.data.materials.new(full)
    if bpy.app.version < (5, 0, 0):
        m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*color, 1)
    m.roughness = rough
    m.metallic = metal
    M[name] = m
    return m, nt, b


def _link(nt, a, b):
    nt.links.new(a, b)


def _math(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    if isinstance(a, (int, float)):
        n.inputs[0].default_value = a
    else:
        _link(nt, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = b
        else:
            _link(nt, b, n.inputs[1])
    return n.outputs[0]


def _obj_xyz(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    _link(nt, tc.outputs["Object"], sep.inputs[0])
    return tc, sep


def _ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
    el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        e = el.new(pos)
        e.color = (*col, 1)
    _link(nt, fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _bump(nt, height, bsdf, strength=0.5, dist=0.01):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    _link(nt, height, bp.inputs["Height"])
    _link(nt, bp.outputs["Normal"], bsdf.inputs["Normal"])


def _brick(nt, vec, c1, c2, mortar, width, height, msize, offset=0.5, bias=0.0):
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = offset
    _link(nt, vec, br.inputs["Vector"])
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = msize
    br.inputs["Bias"].default_value = bias
    br.inputs["Brick Width"].default_value = width
    br.inputs["Row Height"].default_value = height
    return br


def mat_lap_siding(name, color, reveal=0.1778):
    m, nt, b = _new_mat(name, color, 0.6)
    _, sep = _obj_xyz(nt)
    fr = _math(nt, "FRACT", _math(nt, "DIVIDE", sep.outputs["Z"], reveal))
    dark = tuple(c * 0.72 for c in color)
    _link(nt, _ramp(nt, fr, [(0.0, dark), (0.1, color)]), b.inputs["Base Color"])
    _bump(nt, fr, b, 0.5, 0.012)


def mat_shingles(name):
    m, nt, b = _new_mat(name, (0.16, 0.16, 0.17), 0.85)
    tc, _ = _obj_xyz(nt)
    br = _brick(nt, tc.outputs["Object"], (0.13, 0.13, 0.14), (0.22, 0.21, 0.21),
                (0.05, 0.05, 0.05), 0.33, 0.14, 0.005, bias=0.2)
    _link(nt, br.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, br.outputs["Fac"], b, 0.4, 0.01)


def mat_stone(name):
    m, nt, b = _new_mat(name, (0.55, 0.5, 0.43), 0.9)
    _, sep = _obj_xyz(nt)
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    _link(nt, _math(nt, "ADD", sep.outputs["X"], sep.outputs["Y"]), comb.inputs["X"])
    _link(nt, sep.outputs["Z"], comb.inputs["Y"])
    br = _brick(nt, comb.outputs[0], (0.62, 0.56, 0.47), (0.45, 0.43, 0.40),
                (0.78, 0.76, 0.72), 0.52, 0.21, 0.012, offset=0.37, bias=0.1)
    br.offset_frequency = 2
    _link(nt, br.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, br.outputs["Fac"], b, 0.9, 0.02)


def mat_standing_seam(name):
    m, nt, b = _new_mat(name, (0.14, 0.12, 0.11), 0.45, 0.6)
    _, sep = _obj_xyz(nt)
    fr = _math(nt, "FRACT", _math(nt, "DIVIDE", sep.outputs["X"], 0.4064))
    seam = _math(nt, "LESS_THAN", fr, 0.04)
    _bump(nt, seam, b, 0.8, 0.01)


def mat_wood_floor(name):
    m, nt, b = _new_mat(name, (0.45, 0.3, 0.18), 0.35)
    tc, _ = _obj_xyz(nt)
    br = _brick(nt, tc.outputs["Object"], (0.47, 0.31, 0.18), (0.36, 0.23, 0.13),
                (0.2, 0.13, 0.08), 1.25, 0.127, 0.002, offset=0.37, bias=0.0)
    br.offset_frequency = 1
    _link(nt, br.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, br.outputs["Fac"], b, 0.2, 0.003)


def mat_tile(name, c1, c2, size=0.3048):
    m, nt, b = _new_mat(name, c1, 0.25)
    tc, _ = _obj_xyz(nt)
    br = _brick(nt, tc.outputs["Object"], c1, c2, (0.55, 0.55, 0.53), size, size, 0.004,
                offset=0.0, bias=0.0)
    _link(nt, br.outputs["Color"], b.inputs["Base Color"])
    _bump(nt, br.outputs["Fac"], b, 0.3, 0.004)


def mat_noise(name, c_lo, c_hi, rough, scale=40.0, bump=0.1, metal=0.0):
    m, nt, b = _new_mat(name, c_hi, rough, metal)
    tc, _ = _obj_xyz(nt)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 8.0
    _link(nt, tc.outputs["Object"], nz.inputs["Vector"])
    _link(nt, _ramp(nt, nz.outputs["Fac"], [(0.3, c_lo), (0.7, c_hi)]), b.inputs["Base Color"])
    if bump:
        _bump(nt, nz.outputs["Fac"], b, bump, 0.005)


def mat_glass(name):
    m, nt, b = _new_mat(name, (0.8, 0.88, 0.9), 0.0)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.45
    m.diffuse_color = (0.55, 0.7, 0.8, 0.35)


def mat_emit(name, color, strength):
    m, nt, b = _new_mat(name, color, 0.4)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength


def make_materials():
    mat_lap_siding("siding", (0.72, 0.71, 0.66))
    mat_shingles("shingles")
    mat_stone("stone")
    mat_standing_seam("metal_roof")
    mat_wood_floor("wood_floor")
    mat_tile("tile", (0.78, 0.77, 0.74), (0.74, 0.73, 0.70))
    mat_tile("tile_shower", (0.86, 0.86, 0.85), (0.83, 0.83, 0.82), 0.1524)
    mat_noise("carpet", (0.55, 0.5, 0.44), (0.66, 0.61, 0.54), 0.95, 300.0, 0.3)
    mat_noise("concrete", (0.5, 0.5, 0.48), (0.64, 0.63, 0.6), 0.8, 12.0, 0.05)
    mat_noise("grass", (0.12, 0.22, 0.06), (0.22, 0.36, 0.1), 0.9, 30.0, 0.2)
    mat_noise("granite", (0.08, 0.08, 0.08), (0.3, 0.28, 0.27), 0.15, 120.0, 0.0)
    mat_noise("fireplace_stone", (0.42, 0.39, 0.35), (0.62, 0.58, 0.52), 0.9, 6.0, 0.6)
    _new_mat("drywall", (0.9, 0.89, 0.86), 0.8)
    _new_mat("wall_cap", (0.25, 0.25, 0.27), 0.9)
    _new_mat("ceiling", (0.95, 0.95, 0.94), 0.85)
    _new_mat("trim", (0.95, 0.95, 0.93), 0.4)
    _new_mat("soffit", (0.93, 0.93, 0.91), 0.6)
    _new_mat("door", (0.93, 0.93, 0.9), 0.35)
    _new_mat("front_door", (0.28, 0.16, 0.09), 0.35)
    _new_mat("window_frame", (0.12, 0.12, 0.12), 0.35)
    _new_mat("cabinet", (0.94, 0.93, 0.9), 0.35)
    _new_mat("cabinet_front", (0.9, 0.89, 0.86), 0.3)
    _new_mat("toe_kick", (0.2, 0.2, 0.2), 0.6)
    _new_mat("steel", (0.72, 0.72, 0.72), 0.25, 1.0)
    _new_mat("chrome", (0.9, 0.9, 0.9), 0.05, 1.0)
    _new_mat("black_metal", (0.03, 0.03, 0.03), 0.4, 0.6)
    _new_mat("black_glass", (0.01, 0.01, 0.01), 0.05)
    _new_mat("porcelain", (0.95, 0.95, 0.95), 0.08)
    _new_mat("basin", (0.82, 0.84, 0.86), 0.08)
    _new_mat("appliance", (0.93, 0.93, 0.93), 0.25)
    _new_mat("mirror", (0.95, 0.95, 0.95), 0.02, 1.0)
    _new_mat("firebox", (0.03, 0.03, 0.03), 0.9)
    _new_mat("wood", (0.4, 0.25, 0.13), 0.45)
    _new_mat("post", (0.95, 0.95, 0.93), 0.45)
    _new_mat("slab_edge", (0.55, 0.55, 0.53), 0.9)
    mat_glass("glass")
    mat_emit("bulb", (1.0, 0.85, 0.65), 8.0)


# ---------------------------------------------------------------------------
# Walls, doors and windows
# ---------------------------------------------------------------------------


def split_run(a0, a1, holes, zb, zt):
    """Pieces (s, e, z0, z1) of a wall run with rectangular holes cut out."""
    out, cur = [], a0
    for c0, c1, h0, h1 in sorted(holes):
        c0, c1 = max(c0, a0), min(c1, a1)
        if c0 > cur:
            out.append((cur, c0, zb, zt))
        if h0 > zb:
            out.append((c0, c1, zb, min(h0, zt)))
        if h1 < zt:
            out.append((c0, c1, max(h1, zb), zt))
        cur = max(cur, c1)
    if cur < a1:
        out.append((cur, a1, zb, zt))
    return out


class Wall:
    def __init__(self, x0, y0, x1, y1, ext, stone, zb=0.0, zt=PLATE):
        self.axis = "x" if (x1 - x0) >= (y1 - y0) else "y"
        if self.axis == "x":
            self.a0, self.a1, self.p0, self.p1 = x0, x1, y0, y1
        else:
            self.a0, self.a1, self.p0, self.p1 = y0, y1, x0, x1
        self.ext, self.stone, self.zb, self.zt = ext, stone, zb, zt
        self.holes = []
        # outer side: sign +1 means the exterior is on the p1 side
        self.s = 0
        if ext in ("S", "E"):
            self.s = 1
        elif ext in ("N", "W"):
            self.s = -1
        self.po = self.p1 if self.s > 0 else self.p0          # outside stud face
        # drywall faces
        self.q0 = self.p0 - (0 if self.s < 0 else DW)
        self.q1 = self.p1 + (0 if self.s > 0 else DW)
        self.qin = self.q0 if self.s > 0 else self.q1           # inside face (ext walls)

    def contains(self, x, y):
        a, p = (x, y) if self.axis == "x" else (y, x)
        return self.a0 - 0.01 <= a <= self.a1 + 0.01 and self.p0 - 0.05 <= p <= self.p1 + 0.05

    def along(self, x, y):
        return x if self.axis == "x" else y

    def lbox(self, mb, a0, a1, p0, p1, z0, z1, mat):
        if self.axis == "x":
            mb.box(a0, p0, z0, a1, p1, z1, mat)
        else:
            mb.box(p0, a0, z0, p1, a1, z1, mat)

    def clad_face(self):
        return self.po + self.s * TS


def find_wall(walls, pt):
    for w in walls:
        if w.contains(*pt):
            return w
    raise ValueError("no wall at %s" % (pt,))


def build_wall_mesh(walls, mb_core, mb_clad, mb_base=None):
    for w in walls:
        for s, e, z0, z1 in split_run(w.a0, w.a1, w.holes, w.zb, w.zt):
            if w.axis == "x":
                mb_core.box(s, w.q0, z0, e, w.q1, z1, M["drywall"], top=M["wall_cap"])
            else:
                mb_core.box(w.q0, s, z0, w.q1, e, z1, M["drywall"], top=M["wall_cap"])
            if mb_base is not None and z0 == 0.0:
                # 3-1/4" painted baseboard on each room-side face
                faces = []
                if w.s <= 0:
                    faces.append((w.q1, w.q1 + 0.04))
                if w.s >= 0:
                    faces.append((w.q0 - 0.04, w.q0))
                for f0, f1 in faces:
                    w.lbox(mb_base, s, e, f0, f1, 0.02, 0.29, M["trim"])
        if not w.s:
            continue
        # exterior skin, returned 0.07' past each end so corners close
        a0, a1 = w.a0 - TS, w.a1 + TS
        zb = GRADE + 0.05 if w.zb == 0 else w.zb
        po, s = w.po, w.s
        if w.stone:
            for pc in split_run(a0, a1, w.holes, zb, STONE_TOP):
                w.lbox(mb_clad, pc[0], pc[1], po, po + s * STONE_T, pc[2], pc[3], M["stone"])
            for pc in split_run(a0 - 0.1, a1 + 0.1, w.holes, STONE_TOP, STONE_TOP + 0.15):
                w.lbox(mb_clad, pc[0], pc[1], po, po + s * (STONE_T + 0.1), pc[2], pc[3], M["stone"])
            zb = STONE_TOP + 0.15
        for pc in split_run(a0, a1, w.holes, zb, w.zt):
            w.lbox(mb_clad, pc[0], pc[1], po, po + s * TS, pc[2], pc[3], M["siding"])


def build_door(coll, w, name, c, width, style):
    mb = MeshBuilder(name, coll)
    a0, a1 = c - width / 2, c + width / 2
    h = DOOR_H if style != "cased" else 7.0
    q0, q1 = w.q0, w.q1
    if w.s:  # exterior: jamb runs out to the siding face
        if w.s > 0:
            q1 = w.clad_face()
        else:
            q0 = w.clad_face()
    tr = M["trim"]
    jt = 0.06
    w.lbox(mb, a0, a0 + jt, q0, q1, 0, h, tr)
    w.lbox(mb, a1 - jt, a1, q0, q1, 0, h, tr)
    w.lbox(mb, a0, a1, q0, q1, h - jt, h, tr)
    # casing on both faces
    for face, sgn in ((q0, -1), (q1, 1)):
        cw = 0.29 if not (w.s and face == (q1 if w.s > 0 else q0)) else 0.33
        p0, p1 = sorted((face, face + sgn * 0.05))
        w.lbox(mb, a0 - cw, a0, p0, p1, 0, h + cw, tr)
        w.lbox(mb, a1, a1 + cw, p0, p1, 0, h + cw, tr)
        w.lbox(mb, a0 - cw, a1 + cw, p0, p1, h, h + cw, tr)
        if w.s and face == (q1 if w.s > 0 else q0):  # drip cap on the exterior head
            p0, p1 = sorted((face, face + sgn * 0.12))
            w.lbox(mb, a0 - cw - 0.05, a1 + cw + 0.05, p0, p1, h + cw, h + cw + 0.06, tr)
    if w.s:
        w.lbox(mb, a0, a1, q0, q1, 0, 0.04, M["steel"])  # threshold
    if style == "cased":
        return mb.build()
    pm = (w.p0 + w.p1) / 2
    t = 0.146 / 2
    la0, la1 = a0 + jt + 0.01, a1 - jt - 0.01
    lz0, lz1 = 0.04, h - jt - 0.01
    lw = la1 - la0
    if style == "glass":
        dm = M["front_door"]
        st, rt, rb = 0.4, 0.45, 0.8
        w.lbox(mb, la0, la0 + st, pm - t, pm + t, lz0, lz1, dm)
        w.lbox(mb, la1 - st, la1, pm - t, pm + t, lz0, lz1, dm)
        w.lbox(mb, la0 + st, la1 - st, pm - t, pm + t, lz0, lz0 + rb, dm)
        w.lbox(mb, la0 + st, la1 - st, pm - t, pm + t, lz1 - rt, lz1, dm)
        w.lbox(mb, la0 + st, la1 - st, pm - 0.01, pm + 0.01, lz0 + rb, lz1 - rt, M["glass"])
    else:
        dm = M["door"]
        w.lbox(mb, la0, la1, pm - t, pm + t, lz0, lz1, dm)
        if style == "ext6":
            rows = [(0.45, 2.35), (2.65, 4.7), (5.0, 6.35)]
        else:
            rows = [(0.45, 3.0), (3.3, 6.35)]
        m = 0.28
        cols = [(la0 + m, la0 + lw / 2 - 0.08), (la0 + lw / 2 + 0.08, la1 - m)] \
            if style == "ext6" else [(la0 + m, la1 - m)]
        for z0, z1 in rows:
            for c0, c1 in cols:
                w.lbox(mb, c0, c1, pm - t - 0.015, pm + t + 0.015, z0, z1, dm)
    # lever handles on the latch side
    ka = la1 - 0.22
    w.lbox(mb, ka - 0.06, ka + 0.06, pm - t - 0.2, pm + t + 0.2, 3.0, 3.1, M["chrome"])
    return mb.build()


def build_window(coll, w, name, c, width, height, units, zs=None):
    mb = MeshBuilder(name, coll)
    a0, a1 = c - width / 2, c + width / 2
    zh = HEADER if zs is None else zs + height
    zs = zh - height if zs is None else zs
    s, po = w.s, w.po
    fr, tr, gl = M["window_frame"], M["trim"], M["glass"]
    # frame: from 0.02 proud of sheathing to 0.35 in
    f0, f1 = sorted((po + s * 0.02, po - s * 0.35))
    fw = 0.15
    w.lbox(mb, a0, a0 + fw, f0, f1, zs, zh, fr)
    w.lbox(mb, a1 - fw, a1, f0, f1, zs, zh, fr)
    w.lbox(mb, a0, a1, f0, f1, zs, zs + fw, fr)
    w.lbox(mb, a0, a1, f0, f1, zh - fw, zh, fr)
    pg = po - s * 0.17
    uw = (width - 2 * fw) / units
    for k in range(units):
        u0 = a0 + fw + k * uw
        u1 = u0 + uw
        if k:
            w.lbox(mb, u0 - 0.08, u0 + 0.08, f0, f1, zs, zh, fr)
        g0, g1 = u0 + 0.08, u1 - 0.08
        v0, v1 = zs + fw + 0.08, zh - fw - 0.08
        # sash
        for p0_, p1_ in ((pg - 0.07, pg + 0.07),):
            w.lbox(mb, g0 - 0.02, g0 + 0.1, p0_, p1_, v0, v1, fr)
            w.lbox(mb, g1 - 0.1, g1 + 0.02, p0_, p1_, v0, v1, fr)
            w.lbox(mb, g0, g1, p0_, p1_, v0 - 0.02, v0 + 0.1, fr)
            w.lbox(mb, g0, g1, p0_, p1_, v1 - 0.1, v1 + 0.02, fr)
        if height >= 5.5:  # single hung: meeting rail
            zm = (v0 + v1) / 2
            w.lbox(mb, g0, g1, pg - 0.07, pg + 0.07, zm - 0.06, zm + 0.06, fr)
        w.lbox(mb, g0, g1, pg - 0.01, pg + 0.01, v0, v1, gl)
        # colonial grilles (2 wide, 4 high on 6' units, 2 high otherwise)
        rows = 4 if height >= 5.5 else 2
        for i in range(1, 2):
            am = g0 + (g1 - g0) * i / 2
            w.lbox(mb, am - 0.03, am + 0.03, pg - 0.04, pg + 0.04, v0, v1, fr)
        for j in range(1, rows):
            zm = v0 + (v1 - v0) * j / rows
            w.lbox(mb, g0, g1, pg - 0.04, pg + 0.04, zm - 0.03, zm + 0.03, fr)
    # exterior casing, sill and drip cap
    fo = w.clad_face()
    c0, c1 = sorted((fo, fo + s * 0.06))
    cw = 0.33
    zc0 = zs - 0.1
    if w.stone and zs < STONE_TOP:
        zc0 = STONE_TOP + 0.15
    w.lbox(mb, a0 - cw, a0, c0, c1, zc0, zh + cw, tr)
    w.lbox(mb, a1, a1 + cw, c0, c1, zc0, zh + cw, tr)
    w.lbox(mb, a0 - cw, a1 + cw, c0, c1, zh, zh + cw, tr)
    d0, d1 = sorted((fo, fo + s * 0.14))
    w.lbox(mb, a0 - cw - 0.05, a1 + cw + 0.05, d0, d1, zh + cw, zh + cw + 0.06, tr)
    sill_out = (STONE_T + 0.12) if w.stone else 0.2
    s0, s1 = sorted((po - s * 0.1, po + s * sill_out))
    w.lbox(mb, a0 - 0.1, a1 + 0.1, s0, s1, zs - 0.12, zs, tr if not w.stone else M["stone"])
    # interior stool, apron and casing
    qi = w.qin
    i0, i1 = sorted((qi, qi - s * 0.1))
    w.lbox(mb, a0 - 0.2, a1 + 0.2, i0, i1, zs - 0.06, zs, tr)
    i0, i1 = sorted((qi, qi - s * 0.05))
    w.lbox(mb, a0 - 0.25, a1 + 0.25, i0, i1, zs - 0.4, zs - 0.06, tr)
    w.lbox(mb, a0 - 0.25, a0, i0, i1, zs, zh + 0.25, tr)
    w.lbox(mb, a1, a1 + 0.25, i0, i1, zs, zh + 0.25, tr)
    w.lbox(mb, a0 - 0.25, a1 + 0.25, i0, i1, zh, zh + 0.25, tr)
    return mb.build()


# ---------------------------------------------------------------------------
# Built-ins and fixtures
# ---------------------------------------------------------------------------


def cab_run(mb, f, face, a0, a1, depth=2.0, h=3.0, skip=(), counter=True):
    fb(mb, f, face, 0, depth - 0.25, a0, a1, 0, 0.33, M["toe_kick"])
    fb(mb, f, face, 0, depth - 0.05, a0, a1, 0.33, h - 0.125, M["cabinet"])
    if counter:
        fb(mb, f, face, 0, depth + 0.06, a0, a1, h - 0.125, h, M["granite"])
        fb(mb, f, face, 0, 0.05, a0, a1, h, h + 0.33, M["granite"])  # backsplash
    segs, cur = [], a0
    for s0, s1 in sorted(skip):
        if s0 > cur:
            segs.append((cur, s0))
        cur = s1
    if cur < a1:
        segs.append((cur, a1))
    for s0, s1 in segs:
        n = max(1, round((s1 - s0) / 1.6))
        wd = (s1 - s0) / n
        for i in range(n):
            b0, b1 = s0 + i * wd + 0.03, s0 + (i + 1) * wd - 0.03
            fb(mb, f, face, depth - 0.05, depth - 0.01, b0, b1, 0.4, h - 0.8, M["cabinet_front"])
            fb(mb, f, face, depth - 0.05, depth - 0.01, b0, b1, h - 0.74, h - 0.19, M["cabinet_front"])
            mid = (b0 + b1) / 2
            fb(mb, f, face, depth - 0.01, depth + 0.04, mid - 0.2, mid + 0.2, h - 0.49, h - 0.44, M["steel"])
            fb(mb, f, face, depth - 0.01, depth + 0.04, mid - 0.03, mid + 0.03, h - 1.5, h - 1.1, M["steel"])


def upper_run(mb, f, face, a0, a1, z0=4.5, z1=7.5, depth=1.0):
    fb(mb, f, face, 0, depth - 0.04, a0, a1, z0, z1, M["cabinet"])
    n = max(1, round((a1 - a0) / 1.5))
    wd = (a1 - a0) / n
    for i in range(n):
        b0, b1 = a0 + i * wd + 0.03, a0 + (i + 1) * wd - 0.03
        fb(mb, f, face, depth - 0.04, depth, b0, b1, z0 + 0.05, z1 - 0.05, M["cabinet_front"])
        knob = b0 + 0.15 if i % 2 else b1 - 0.15
        fb(mb, f, face, depth, depth + 0.04, knob - 0.03, knob + 0.03, z0 + 0.25, z0 + 0.65, M["steel"])


def tall_cabinet(mb, f, face, a0, a1, depth, h=7.5):
    fb(mb, f, face, 0, depth - 0.04, a0, a1, 0, h, M["cabinet"])
    n = max(1, round((a1 - a0) / 1.5))
    wd = (a1 - a0) / n
    for i in range(n):
        b0, b1 = a0 + i * wd + 0.03, a0 + (i + 1) * wd - 0.03
        fb(mb, f, face, depth - 0.04, depth, b0, b1, 0.35, h - 0.05, M["cabinet_front"])
        k = b1 - 0.15
        fb(mb, f, face, depth, depth + 0.04, k - 0.03, k + 0.03, 3.3, 4.0, M["steel"])


def toilet(mb, f, face, a):
    p, c = M["porcelain"], M["chrome"]
    fb(mb, f, face, 0.05, 0.65, a - 0.9, a + 0.9, 1.3, 2.55, p)        # tank
    fb(mb, f, face, 0.03, 0.68, a - 0.95, a + 0.95, 2.55, 2.63, p)      # lid
    fc(mb, f, face, 1.15, a, 0.0, 1.05, 0.55, 0.38, p)                  # pedestal
    fc(mb, f, face, 1.35, a, 1.05, 1.3, 0.85, 0.65, p)                  # bowl
    fc(mb, f, face, 1.38, a, 1.3, 1.37, 0.85, 0.66, p)                  # seat
    fb(mb, f, face, 0.65, 0.72, a + 0.5, a + 0.7, 2.3, 2.36, c)         # lever


def vanity(mb, f, face, a0, a1, sinks, depth=1.8):
    cab_run(mb, f, face, a0, a1, depth=depth, h=2.83)
    for sa in sinks:
        fc(mb, f, face, depth * 0.55, sa, 2.83, 2.835, 0.55, 0.75, M["basin"])
        fc(mb, f, face, 0.25, sa, 2.83, 3.45, 0.05, 0.05, M["chrome"], 12)
        fb(mb, f, face, 0.2, 0.7, sa - 0.04, sa + 0.04, 3.38, 3.45, M["chrome"])
        fb(mb, f, face, 0.0, 0.04, sa - 1.1, sa + 1.1, 3.6, 6.6, M["mirror"])  # mirror
        fb(mb, f, face, 0.0, 0.3, sa - 0.9, sa + 0.9, 6.9, 7.1, M["black_metal"])  # vanity light
        for k in (-0.6, 0.0, 0.6):
            fc(mb, f, face, 0.3, sa + k, 6.72, 6.9, 0.12, 0.12, M["bulb"], 12)


def closet_shelf(mb, f, face, a0, a1, z=5.5, depth=1.0, rod=True):
    fb(mb, f, face, 0, depth, a0, a1, z, z + 0.06, M["trim"])
    if rod:
        fb(mb, f, face, depth - 0.2, depth - 0.12, a0, a1, z - 0.3, z - 0.22, M["chrome"])


def ceiling_fan(mb, cx, cy):
    mb.cyl(cx, cy, 8.3, PLATE, 0.05, mat=M["black_metal"], seg=12)
    mb.cyl(cx, cy, 7.95, 8.3, 0.38, mat=M["black_metal"])
    mb.cyl(cx, cy, 7.75, 7.95, 0.3, mat=M["glass"])
    for i in range(5):
        ang = 2 * math.pi * i / 5 + 0.3
        mb.box_rot(cx, cy, 8.08, 8.13, 2.1, 0.45, ang, M["wood"], offset=0.3)


def pendant(mb, cx, cy, z=6.4):
    mb.cyl(cx, cy, z + 0.6, PLATE, 0.015, mat=M["black_metal"], seg=8)
    mb.cyl(cx, cy, z, z + 0.6, 0.45, 0.45, M["black_metal"])
    mb.cyl(cx, cy, z - 0.05, z, 0.12, mat=M["bulb"], seg=12)


def chandelier(mb, cx, cy):
    mb.cyl(cx, cy, 7.4, PLATE, 0.03, mat=M["black_metal"], seg=8)
    mb.cyl(cx, cy, 6.5, 6.6, 1.2, mat=M["black_metal"], seg=32)
    mb.cyl(cx, cy, 6.6, 7.4, 0.06, mat=M["black_metal"], seg=8)
    for i in range(6):
        ang = 2 * math.pi * i / 6
        x, y = cx + 1.2 * math.cos(ang), cy + 1.2 * math.sin(ang)
        mb.cyl(x, y, 6.6, 6.85, 0.06, mat=M["trim"], seg=8)
        mb.cyl(x, y, 6.85, 7.0, 0.04, mat=M["bulb"], seg=8)


def build_kitchen(coll):
    mb = MeshBuilder("Kitchen - Cabinets & Counters", coll)
    back = 10.66 + DW
    cab_run(mb, "S", back, 19.58, 32.15, skip=[(28.9, 30.95)])
    # undermount sink under the 3-2040 window, faucet
    fb(mb, "S", back, 0.35, 1.65, 26.3, 28.4, 3.0, 3.006, M["steel"])
    fb(mb, "S", back, 0.45, 1.55, 26.4, 27.3, 3.006, 3.01, M["black_metal"])
    fb(mb, "S", back, 0.45, 1.55, 27.4, 28.3, 3.006, 3.01, M["black_metal"])
    fc(mb, "S", back, 0.2, 27.35, 3.0, 4.15, 0.05, 0.05, M["chrome"], 12)
    fb(mb, "S", back, 0.15, 0.85, 27.3, 27.4, 4.05, 4.15, M["chrome"])
    fb(mb, "S", back, 0.0, 1.95, 28.9, 30.95, 0.33, 2.875, M["cabinet"])
    fb(mb, "S", back, 1.95, 2.0, 28.95, 30.9, 0.35, 2.85, M["steel"])  # dishwasher
    fb(mb, "S", back, 2.0, 2.05, 29.2, 30.65, 2.6, 2.66, M["steel"])
    upper_run(mb, "S", back, 19.58, 24.05)
    upper_run(mb, "S", back, 30.6, 32.15)
    # refrigerator + cabinet above
    fb(mb, "S", back, 0.0, 2.5, 32.2, 35.09, 0.0, 6.0, M["steel"])
    fb(mb, "S", back, 2.5, 2.52, 32.25, 33.62, 0.1, 5.95, M["steel"])
    fb(mb, "S", back, 2.5, 2.52, 33.67, 35.04, 0.1, 5.95, M["steel"])
    for a in (33.5, 33.79):
        fb(mb, "S", back, 2.52, 2.62, a - 0.03, a + 0.03, 3.2, 5.2, M["chrome"])
    upper_run(mb, "S", back, 32.2, 35.09, z0=6.3, z1=7.5, depth=2.4)
    # range wall (faces west)
    face = 35.0 - DW
    cab_run(mb, "W", face, 16.7, 23.83, skip=[(18.7, 21.2)])
    fb(mb, "W", face, 0.0, 2.1, 18.7, 21.2, 0.0, 2.95, M["steel"])
    fb(mb, "W", face, 0.05, 2.05, 18.72, 21.18, 2.95, 3.0, M["black_glass"])
    for u in (0.65, 1.45):
        for a in (19.3, 20.6):
            fc(mb, "W", face, u, a, 3.0, 3.01, 0.28, 0.28, M["black_metal"])
    fb(mb, "W", face, 2.1, 2.12, 19.0, 20.9, 0.9, 2.3, M["black_glass"])
    fb(mb, "W", face, 2.12, 2.2, 19.0, 20.9, 2.35, 2.42, M["chrome"])
    fb(mb, "W", face, 0.0, 1.8, 18.7, 21.2, 5.8, 6.5, M["steel"])      # hood
    fb(mb, "W", face, 0.0, 0.9, 19.5, 20.4, 6.5, PLATE, M["steel"])
    upper_run(mb, "W", face, 16.7, 18.65)
    upper_run(mb, "W", face, 21.25, 23.83)
    # 4' x 7' island, seating overhang on the west side
    mb.box(25.3, 16.85, 0, 28.7, 23.35, 0.33, M["toe_kick"])
    mb.box(25.4, 16.7, 0.33, 28.9, 23.5, 2.875, M["cabinet"])
    mb.box(24.8, 16.6, 2.875, 28.95, 23.6, 3.0, M["granite"])
    for i in range(4):
        y0 = 16.7 + i * 1.7 + 0.03
        mb.box(28.9, y0, 0.4, 28.94, y0 + 1.64, 2.2, M["cabinet_front"])
        mb.box(28.9, y0, 2.26, 28.94, y0 + 1.64, 2.7, M["cabinet_front"])
        mb.box(28.94, y0 + 0.62, 2.45, 28.98, y0 + 1.02, 2.5, M["steel"])
    for y in (18.1, 20.1, 22.1):
        pendant(mb, 26.875, y)
        # counter stools
        mb.cyl(24.2, y, 0.0, 2.2, 0.05, mat=M["black_metal"], seg=10)
        mb.cyl(24.2, y, 2.2, 2.35, 0.55, mat=M["wood"])
    return mb.build()


def build_utility(coll):
    mb = MeshBuilder("Utility & Mud Hall", coll)
    face = 5.29 + DW
    cab_run(mb, "S", face, 35.45, 41.0)
    upper_run(mb, "S", face, 35.45, 45.96)
    # utility sink
    fb(mb, "S", face, 0.4, 1.5, 38.4, 40.0, 3.0, 3.006, M["steel"])
    fc(mb, "S", face, 0.2, 39.2, 3.0, 3.9, 0.05, 0.05, M["chrome"], 12)
    for a0, a1 in ((41.05, 43.45), (43.55, 45.95)):  # washer / electric dryer
        fb(mb, "S", face, 0.0, 2.4, a0, a1, 0.0, 3.1, M["appliance"])
        fb(mb, "S", face, 0.0, 0.5, a0, a1, 3.1, 3.55, M["appliance"])
        fb(mb, "S", face, 0.5, 0.52, a0 + 0.2, a0 + 0.9, 3.25, 3.45, M["black_glass"])
        mb.hcyl("y", (a0 + a1) / 2, 1.6, face + 2.4, face + 2.46, 0.72, M["black_glass"], 28)
        mb.hcyl("y", (a0 + a1) / 2, 1.6, face + 2.39, face + 2.43, 0.82, M["chrome"], 28)
    tall_cabinet(mb, "E", 35.41 + DW, 7.4, 10.33, 1.6)
    # lockers + bench in the mud hall
    face = 10.66 + DW
    fb(mb, "S", face, 0, 1.75, 41.0, 45.96, 1.5, 1.66, M["wood"])
    fb(mb, "S", face, 0, 1.75, 41.0, 45.96, 0.0, 0.3, M["cabinet"])
    fb(mb, "S", face, 0, 0.06, 41.0, 45.96, 1.66, 5.6, M["cabinet"])
    fb(mb, "S", face, 0, 1.75, 41.0, 45.96, 5.6, 5.7, M["cabinet"])
    for i in range(5):
        a = 41.0 + i * (4.96 / 4)
        fb(mb, "S", face, 0, 1.75, a - 0.04, a + 0.04, 0.0, 7.0, M["cabinet"])
    for i in range(4):
        a0 = 41.04 + i * 1.24
        fb(mb, "S", face, 0, 1.7, a0, a0 + 1.16, 5.7, 7.0, M["cabinet"])
        fb(mb, "S", face, 1.7, 1.74, a0 + 0.03, a0 + 1.13, 5.75, 6.95, M["cabinet_front"])
        for k in (0.35, 0.8):
            fb(mb, "S", face, 0.06, 0.35, a0 + k - 0.03, a0 + k + 0.03, 4.8, 4.86, M["black_metal"])
    return mb.build()


def build_baths(coll):
    obs = []
    # half bath
    mb = MeshBuilder("Half Bath Fixtures", coll)
    toilet(mb, "S", 0.29 + DW, 48.1)
    vanity(mb, "N", 6.38 - DW, 47.1, 49.1, [48.1], depth=1.6)
    obs.append(mb.build())
    # hall bath
    mb = MeshBuilder("Hall Bath Fixtures", coll)
    toilet(mb, "W", 11.71, 30.55)
    x0, y0, x1, y1 = 0.29 + DW, 32.42 + DW, 3.14, 37.5 - DW
    p = M["porcelain"]
    mb.box(x0, y0, 0, x1, y1, 0.6, p)
    mb.box(x0, y0, 0.6, x0 + 0.25, y1, 1.75, p)
    mb.box(x1 - 0.3, y0, 0.6, x1, y1, 1.75, p)
    mb.box(x0, y0, 0.6, x1, y0 + 0.25, 1.75, p)
    mb.box(x0, y1 - 0.25, 0.6, x1, y1, 1.75, p)
    mb.box(x0 + 0.25, y0 + 0.25, 0.6, x1 - 0.3, y1 - 0.25, 0.62, M["basin"])
    mb.box(x0, y0, 1.75, x0 + 0.03, y1, 7.0, M["tile_shower"])
    mb.box(x0, y0, 1.75, x1, y0 + 0.03, 7.0, M["tile_shower"])
    mb.box(x0, y1 - 0.03, 1.75, x1, y1, 7.0, M["tile_shower"])
    mb.hcyl("y", x1 - 0.1, 6.9, y0, y1, 0.03, M["chrome"], 10)            # curtain rod
    mb.box(x0, 34.9, 6.3, x0 + 0.5, 35.0, 6.4, M["chrome"])                # shower arm
    mb.hcyl("x", 34.95, 6.3, x0 + 0.45, x0 + 0.55, 0.22, M["chrome"])
    mb.box(x0, 34.9, 2.0, x0 + 0.25, 35.0, 2.1, M["chrome"])               # spout
    tall_cabinet(mb, "N", 37.5 - DW, 3.3, 6.8, 1.5)                        # linen
    vanity(mb, "N", 37.5 - DW, 6.84, 11.83, [9.3], depth=1.9)
    for z in (1.4, 2.8, 4.2, 5.6):                                          # linen closet
        mb.box(0.29 + DW, 29.05 + DW, z, 2.4 - DW, 32.13 - DW, z + 0.06, M["trim"])
    obs.append(mb.build())
    # master bath
    mb = MeshBuilder("Master Bath Fixtures", coll)
    vanity(mb, "E", 35.29 + DW, 25.0, 31.08, [26.4, 29.2], depth=1.85)
    tall_cabinet(mb, "E", 35.29 + DW, 23.07, 24.95, 1.85)
    mb.cyl(44.25, 26.25, 0, 1.9, 1.55, 2.75, M["porcelain"], 40)            # freestanding tub
    mb.cyl(44.25, 26.25, 1.9, 1.905, 1.3, 2.5, M["basin"], 40)
    mb.cyl(44.25, 28.9 - 3.8, 0, 3.0, 0.06, mat=M["chrome"], seg=12)
    mb.box(44.2, 25.1, 2.85, 44.3, 25.9, 2.95, M["chrome"])
    # shower
    sx0, sy0, sx1, sy1 = 42.41, 29.91 + DW, 46.0 - DW, 34.99 - DW
    mb.box(sx0, sy0, 0, sx1, sy1, 0.05, M["tile_shower"])
    mb.box(sx1 - 0.03, sy0, 0.05, sx1, sy1, 8.0, M["tile_shower"])
    mb.box(sx0, sy0, 0.05, sx1, sy0 + 0.03, 8.0, M["tile_shower"])
    mb.box(sx0, sy1 - 0.03, 0.05, sx1, sy1, 8.0, M["tile_shower"])
    mb.box(42.13, 30.77, 0, 42.41, 33.77, 0.33, M["tile_shower"])            # curb
    mb.box(42.24, 30.77, 0.33, 42.30, 33.77, 7.0, M["glass"])
    mb.box(42.22, 30.77, 6.95, 42.32, 33.77, 7.03, M["chrome"])
    mb.box(42.2, 33.2, 3.2, 42.34, 33.25, 4.2, M["chrome"])
    mb.cyl(44.2, 32.45, 0.05, 0.055, 0.2, mat=M["chrome"], seg=16)
    mb.box(sx1 - 0.8, 32.4, 6.55, sx1, 32.5, 6.65, M["chrome"])
    mb.cyl(sx1 - 0.8, 32.45, 6.4, 6.55, 0.35, mat=M["chrome"])
    mb.box(sx1 - 0.08, 32.3, 3.6, sx1, 32.6, 4.0, M["chrome"])
    for z in (1.2, 1.9):                                                    # niche shelves
        mb.box(sx1 - 0.35, 33.8, z, sx1, 34.9, z + 0.05, M["tile_shower"])
    toilet(mb, "E", 33.08 + DW, 33.2)                                       # WC
    obs.append(mb.build())
    return obs


def build_closets(coll):
    mb = MeshBuilder("Closet Shelving", coll)
    closet_shelf(mb, "S", 10.29 + DW, 0.33, 7.33)
    closet_shelf(mb, "E", 0.29 + DW, 10.33, 16.34)
    closet_shelf(mb, "W", 7.37 - DW, 10.33, 16.34)
    closet_shelf(mb, "S", 16.66 + DW, 35.33, 45.96)
    closet_shelf(mb, "S", 16.66 + DW, 35.33, 45.96, z=7.0, rod=False)
    closet_shelf(mb, "W", 46.0 - DW, 16.7, 22.71)
    closet_shelf(mb, "E", 35.29 + DW, 16.7, 22.71)
    closet_shelf(mb, "E", 35.29 + DW, 16.7, 22.71, z=3.2)
    closet_shelf(mb, "W", 15.75 - DW, 45.21, 49.83)
    closet_shelf(mb, "N", 44.87 - DW, 12.21, 15.71)
    for z in (2.0, 3.5, 5.0, 6.5):                                           # storage shelving
        mb.box(56.6, 0.33, z, 58.21, 6.34, z + 0.08, M["wood"])
    return mb.build()


def build_fireplace(coll):
    mb = MeshBuilder("Wood Burning Fireplace", coll)
    st, fbx = M["fireplace_stone"], M["firebox"]
    x0, x1, y0, y1 = 21.63, 27.04, 39.13, 41.79
    ox0, ox1, oz0, oz1 = 23.0, 25.67, 1.0, 3.4
    mb.box(x0, y0, 0, ox0, y1, PLATE, st)
    mb.box(ox1, y0, 0, x1, y1, PLATE, st)
    mb.box(ox0, y0, oz1, ox1, y1, PLATE, st)
    mb.box(ox0, y0, 0, ox1, y1, oz0, st)
    mb.box(ox0, y1 - 0.6, oz0, ox1, y1, oz1, fbx)
    mb.box(ox0, y0 + 0.4, oz0, ox0 + 0.25, y1, oz1, fbx)
    mb.box(ox1 - 0.25, y0 + 0.4, oz0, ox1, y1, oz1, fbx)
    mb.box(ox0, y0 + 0.4, oz1 - 0.1, ox1, y1, oz1, fbx)
    mb.box(ox0 + 0.02, y0 + 0.02, oz0 + 0.02, ox1 - 0.02, y0 + 0.05, oz1 - 0.02, M["glass"])
    for yy in (40.4, 40.75):                                                 # logs
        mb.hcyl("x", yy, oz0 + 0.18, ox0 + 0.4, ox1 - 0.4, 0.16, M["wood"], 10)
    mb.box(21.9, 37.9, 0, 26.77, y0, 1.0, st)                               # raised hearth
    mb.box(21.8, 37.85, 1.0, 26.87, y0 + 0.1, 1.15, M["granite"])
    mb.box(21.45, 38.85, 4.55, 27.22, y0 + 0.1, 4.85, M["wood"])            # mantel
    return mb.build()


def build_lighting_fixtures(coll):
    mb = MeshBuilder("Ceiling Fans & Chandelier", coll)
    for x, y in ((6.1, 22.7), (6.1, 43.8), (24.3, 31.0), (39.5, 42.5)):
        ceiling_fan(mb, x, y)
    chandelier(mb, 13.46, 8.2)
    for x, y in ((8.0, 54.6), (39.0, 54.6)):                                # porch fans
        ceiling_fan(mb, x, y)
    return mb.build()


# ---------------------------------------------------------------------------
# Porches, roof and site
# ---------------------------------------------------------------------------


def build_structure_exterior(coll_porch, coll_roof):
    obs = []
    mb = MeshBuilder("Porch Posts & Beams", coll_porch)
    pm, stn = M["post"], M["stone"]
    # front porch: 8x8 columns on stone pedestals
    for x in (1.0, 15.3, 16.8, 31.9, 33.4, 45.5):
        y = 58.0
        mb.box(x - 0.8, y - 0.8, -0.1, x + 0.8, y + 0.8, 3.45, stn)
        mb.box(x - 0.9, y - 0.9, 3.45, x + 0.9, y + 0.9, 3.6, stn)
        mb.box(x - 0.45, y - 0.45, 3.6, x + 0.45, y + 0.45, 3.85, pm)
        mb.box(x - 0.33, y - 0.33, 3.85, x + 0.33, y + 0.33, 8.3, pm)
        mb.box(x - 0.42, y - 0.42, 8.1, x + 0.42, y + 0.42, 8.3, pm)
    mb.box(0.0, 57.67, 8.3, 46.29, 58.63, PLATE, pm)
    mb.box(0.0, 50.61, 8.3, 0.6, 58.63, PLATE, pm)
    mb.box(45.69, 50.61, 8.3, 46.29, 58.63, PLATE, pm)
    # back porch / patio / carport: 6x6 posts on the slab
    for x, y in ((0.35, 0.35), (35.3, 0.35), (60.4, 30.75), (74.45, 30.75),
                 (74.45, 15.4), (74.45, 0.35)):
        mb.box(x - 0.36, y - 0.36, -0.1, x + 0.36, y + 0.36, 0.5, pm)
        mb.box(x - 0.26, y - 0.26, 0.5, x + 0.26, y + 0.26, 8.3, pm)
        mb.box(x - 0.34, y - 0.34, 8.1, x + 0.34, y + 0.34, 8.3, pm)
    mb.box(0.0, 0.0, 8.3, 7.37, 0.7, PLATE, pm)
    mb.box(0.0, 0.0, 8.3, 0.7, 10.0, PLATE, pm)
    mb.box(19.54, 0.0, 8.3, 46.0, 0.7, PLATE, pm)
    mb.box(46.29, 30.4, 8.3, 74.79, 31.1, PLATE, pm)
    mb.box(74.09, 0.0, 8.3, 74.79, 31.1, PLATE, pm)
    mb.box(58.54, 0.0, 8.3, 74.79, 0.7, PLATE, pm)
    obs.append(mb.build())

    # ---- roofs ----
    sh, tr, so = M["shingles"], M["trim"], M["soffit"]
    rmb = MeshBuilder("Roof - Main (5-12)", coll_roof)
    back = lambda y: ZW + y * PITCH                         # noqa: E731
    front = lambda y: ZW + (58.6 - y) * PITCH                # noqa: E731

    def slab(mbx, xa, xb, ya, yb, za, zb, t, top):
        # edges: underside, high end, top, low end
        mbx.prism_x([(ya, za), (yb, zb), (yb, zb + t), (ya, za + t)], xa, xb, tr,
                    edge_mats=[so, tr, top, tr])

    slab(rmb, -1.25, 46.29, -1.25, CARPORT_RIDGE_Y, back(-1.25), back(CARPORT_RIDGE_Y), ROOF_T, sh)
    slab(rmb, -1.25, 47.54, CARPORT_RIDGE_Y, RIDGE_Y, back(CARPORT_RIDGE_Y), back(RIDGE_Y), ROOF_T, sh)
    slab(rmb, -1.25, 47.54, 59.88, RIDGE_Y, front(59.88), front(RIDGE_Y), ROOF_T, sh)
    zr = back(RIDGE_Y) + ROOF_T
    rmb.box(-1.25, RIDGE_Y - 0.45, zr - 0.15, 47.54, RIDGE_Y + 0.45, zr + 0.1, sh)
    # gutters along both eaves
    for y in (-1.35, 59.98):
        rmb.hcyl("x", y, back(-1.25) + 0.1, -1.3, 47.6, 0.16, M["trim"], 10)
    obs.append(rmb.build())

    cmb = MeshBuilder("Roof - Carport (5-12)", coll_roof)
    cfront = lambda y: ZW + (31.1 - y) * PITCH               # noqa: E731
    slab(cmb, 46.29, 75.8, -1.25, CARPORT_RIDGE_Y, back(-1.25), back(CARPORT_RIDGE_Y), ROOF_T, sh)
    slab(cmb, 46.29, 75.8, 32.35, CARPORT_RIDGE_Y, cfront(32.35), cfront(CARPORT_RIDGE_Y), ROOF_T, sh)
    zr = back(CARPORT_RIDGE_Y) + ROOF_T
    cmb.box(46.29, CARPORT_RIDGE_Y - 0.45, zr - 0.15, 75.8, CARPORT_RIDGE_Y + 0.45, zr + 0.1, sh)
    cmb.hcyl("x", 32.45, cfront(32.35) + 0.1, 46.29, 75.85, 0.16, M["trim"], 10)
    obs.append(cmb.build())

    gmb = MeshBuilder("Gable Ends", coll_roof)
    sd = M["siding"]
    gpoly = [(0.0, PLATE), (58.63, PLATE), (58.63, ZW), (RIDGE_Y, back(RIDGE_Y)), (0.0, ZW)]
    gmb.prism_x(gpoly, -TS, 0.29, sd)
    gmb.prism_x(gpoly, 46.0, 46.29 + TS, sd)
    cpoly = [(0.0, PLATE), (31.1, PLATE), (31.1, ZW), (CARPORT_RIDGE_Y, back(CARPORT_RIDGE_Y)),
             (0.0, ZW)]
    gmb.prism_x(cpoly, 74.45, 74.79 + TS, sd)
    # gable vents
    for x0, x1, yc, zc in ((-TS - 0.05, -TS, RIDGE_Y, 18.0), (46.29 + TS, 46.29 + TS + 0.05, RIDGE_Y, 18.0),
                           (74.79 + TS, 74.79 + TS + 0.05, CARPORT_RIDGE_Y, 13.3)):
        gmb.box(x0, yc - 0.9, zc - 0.6, x1, yc + 0.9, zc + 0.6, tr)
    obs.append(gmb.build())

    # ---- shed dormer with clerestory windows (2:12 standing seam roof) ----
    dcoll = coll_roof
    dx0, dx1, dy = 11.8, 36.2, 55.0
    dz_top = 16.1
    main_top = lambda y: front(y) + ROOF_T                   # noqa: E731
    dw_ = Wall(dx0, dy - 0.25, dx1, dy, "S", 0, zb=main_top(dy) - 0.5, zt=dz_top)
    dwins = [(17.1, 5.0), (24.0, 5.0), (31.0, 5.0)]
    for c, wd in dwins:
        dw_.holes.append((c - wd / 2, c + wd / 2, 11.64, 14.64))
    dmb = MeshBuilder("Shed Dormer", dcoll)
    build_wall_mesh([dw_], dmb, dmb)
    yi = 36.8
    tri = [(yi, main_top(yi)), (dy - 0.25, dz_top), (dy - 0.25, main_top(dy - 0.25) - 0.5)]
    dmb.prism_x(tri, dx0, dx0 + 0.3, sd)
    dmb.prism_x(tri, dx1 - 0.3, dx1, sd)
    tri_c = [(yi, main_top(yi)), (dy, dz_top), (dy, main_top(dy) - 0.5)]
    dmb.prism_x(tri_c, dx0 - TS, dx0, sd)
    dmb.prism_x(tri_c, dx1, dx1 + TS, sd)
    for x in (dx0 - TS - 0.02, dx1 - 0.33 + TS + 0.02):                    # corner boards
        dmb.box(x, dy, main_top(dy) - 0.3, x + 0.35, dy + TS + 0.06, dz_top, tr)
    dz = lambda y: dz_top + (dy - y) * 2 / 12                 # noqa: E731
    slab(dmb, 11.0, 37.0, 55.9, 35.4, dz(55.9), dz(35.4), 0.4, M["metal_roof"])
    obs.append(dmb.build())
    for i, (c, wd) in enumerate(dwins):
        obs.append(build_window(dcoll, dw_, "Dormer Window 2-2630 #%d" % (i + 1), c, wd, 3.0, 2,
                                zs=11.64))

    # ---- chimney (sided chase, cap, 2 flues) ----
    chm = MeshBuilder("Chimney", coll_roof)
    chm.box(21.5, 39.0, PLATE, 27.2, 41.8, 24.3, sd)
    chm.box(21.2, 38.7, 24.3, 27.5, 42.1, 24.6, tr)
    for x in (22.9, 25.2):
        chm.box(x, 40.1, 24.6, x + 0.6, 40.7, 25.5, M["black_metal"])
        chm.box(x - 0.1, 40.0, 25.5, x + 0.7, 40.8, 25.6, M["black_metal"])
    obs.append(chm.build())
    return obs


def build_slabs_and_floors(coll_slab, coll_floor):
    mb = MeshBuilder("Foundation Slab", coll_slab)
    mb.prism(OUTLINE, -1.0, 0.0, M["slab_edge"], top=M["concrete"])
    obs = [mb.build()]
    pmb = MeshBuilder("Porch & Carport Slabs", coll_slab)
    for poly in (FRONT_PORCH, BACK_PORCH, PATIO):
        pmb.prism(poly, -0.9, -0.08, M["slab_edge"], top=M["concrete"])
    pmb.prism(CARPORT, -0.9, -0.17, M["slab_edge"], top=M["concrete"])
    pmb.box(0.0, 58.63, -0.9, 46.29, 59.3, -0.42, M["concrete"])            # front step
    obs.append(pmb.build())
    fmb = MeshBuilder("Floor Finishes", coll_floor)
    fmb.prism(OUTLINE, 0.0, 0.02, M["wood_floor"])
    for x0, y0, x1, y1, m in FLOOR_ZONES:
        fmb.box(x0, y0, 0.02, x1, y1, 0.025, M[m])
    obs.append(fmb.build())
    return obs


def build_ceilings(coll):
    mb = MeshBuilder("Ceilings", coll)
    mb.prism(OUTLINE, PLATE, PLATE + 0.05, M["ceiling"])
    for poly in (FRONT_PORCH, BACK_PORCH, PATIO, CARPORT):
        mb.prism(poly, PLATE, PLATE + 0.05, M["soffit"])
    # eave soffits between the walls/beams and the fascia
    z = ZW - 1.25 * PITCH
    for x0, y0, x1, y1 in ((-1.25, -1.25, 75.8, 0.0), (-1.25, 58.63, 47.54, 59.88),
                           (-1.25, 0.0, 0.0, 58.63), (46.29, 31.1, 75.8, 32.35),
                           (74.79, 0.0, 75.8, 31.1), (46.29, 50.16, 47.54, 58.63),
                           (46.29, 31.1, 47.54, 50.16)):
        mb.box(x0, y0, z, x1, y1, z + 0.05, M["soffit"])
    return mb.build()


def build_site(coll):
    mb = MeshBuilder("Site - Ground", coll)
    mb.box(-80, -70, GRADE - 0.5, 150, 140, GRADE, M["grass"])
    obs = [mb.build()]
    dm = MeshBuilder("Site - Driveway & Walk", coll)
    dm.box(58.0, 31.1, GRADE - 0.3, 75.3, 140, -0.19, M["concrete"])
    dm.box(22.3, 59.3, GRADE - 0.3, 26.36, 140, -0.44, M["concrete"])
    obs.append(dm.build())
    return obs


def build_labels(coll):
    for text, x, y in ROOM_LABELS:
        cu = bpy.data.curves.new("Label " + text, "FONT")
        cu.body = text
        cu.size = 1.1 * FT
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        ob = bpy.data.objects.new("Label - " + text.replace("\n", " "), cu)
        ob.location = V(x, y, 0.2)
        ob.hide_render = True
        coll.objects.link(ob)


def build_lights(coll):
    rooms = [(13.46, 8.2), (27.0, 17.0), (24.3, 30.0), (24.3, 43.5), (6.1, 22.7),
             (6.1, 43.8), (6.0, 33.0), (39.5, 42.5), (40.0, 27.0), (40.6, 19.7),
             (40.7, 8.0), (40.7, 13.5), (48.1, 3.3), (13.9, 33.0), (3.8, 13.3)]
    for i, (x, y) in enumerate(rooms):
        ld = bpy.data.lights.new("Room Light %02d" % (i + 1), "POINT")
        ld.energy = 120
        ld.color = (1.0, 0.9, 0.78)
        ld.shadow_soft_size = 0.3
        ob = bpy.data.objects.new(ld.name, ld)
        ob.location = V(x, y, 8.4)
        coll.objects.link(ob)


def setup_scene(root):
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system = "IMPERIAL"
    us.length_unit = "FEET"
    us.use_separate = True
    us.scale_length = 1.0
    # world
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    if bpy.app.version < (5, 0, 0):
        world.use_nodes = True
    bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
        out = next(n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD")
        world.node_tree.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs[0].default_value = (0.62, 0.74, 0.92, 1)
    bg.inputs[1].default_value = 0.9
    # sun
    sd = bpy.data.lights.new("Sun", "SUN")
    sd.energy = 4.0
    sd.angle = math.radians(1.5)
    sun = bpy.data.objects.new("Sun", sd)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
    root.objects.link(sun)
    # cameras
    cams = {
        "Cam - Front 3-4": ((98, 112, 17), (33, 33, 7)),
        "Cam - Back 3-4": ((100, -42, 24), (34, 22, 6)),
        "Cam - Living Room": ((18.2, 37.6, 5.0), (29.0, 14.0, 3.6)),
    }
    for name, (loc, tgt) in cams.items():
        cd = bpy.data.cameras.new(name)
        cd.lens = 28 if "Living" not in name else 18
        cd.clip_start = 0.1
        cd.clip_end = 500
        ob = bpy.data.objects.new(name, cd)
        ob.location = V(*loc)
        ob.rotation_euler = (V(*tgt) - V(*loc)).to_track_quat("-Z", "Y").to_euler()
        root.objects.link(ob)
        if name == "Cam - Front 3-4":
            sc.camera = ob
    cd = bpy.data.cameras.new("Cam - Plan (top, ortho)")
    cd.type = "ORTHO"
    cd.ortho_scale = 82 * FT
    cd.clip_end = 500
    ob = bpy.data.objects.new("Cam - Plan (top, ortho)", cd)
    ob.location = V(37.4, 29.5, 120)
    root.objects.link(ob)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def clear_previous():
    root = bpy.data.collections.get(ROOT_NAME)
    if root:
        def walk(c):
            for ch in list(c.children):
                walk(ch)
            for ob in list(c.objects):
                data = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                if data is not None and data.users == 0:
                    if isinstance(data, bpy.types.Mesh):
                        bpy.data.meshes.remove(data)
                    elif isinstance(data, bpy.types.Curve):
                        bpy.data.curves.remove(data)
                    elif isinstance(data, bpy.types.Light):
                        bpy.data.lights.remove(data)
                    elif isinstance(data, bpy.types.Camera):
                        bpy.data.cameras.remove(data)
            bpy.data.collections.remove(c)
        walk(root)
    for m in list(bpy.data.materials):
        if m.name.startswith("PAL_") and m.users == 0:
            bpy.data.materials.remove(m)


def build():
    clear_previous()
    root = bpy.data.collections.new(ROOT_NAME)
    bpy.context.scene.collection.children.link(root)

    def sub(name):
        c = bpy.data.collections.new(name)
        root.children.link(c)
        return c

    c = {k: sub(k) for k in (
        "01 Foundation & Slabs", "02 Floor Finishes", "03 Walls", "04 Exterior Cladding",
        "05 Doors", "06 Windows", "07 Kitchen", "08 Baths", "09 Utility & Closets",
        "10 Fireplace", "11 Porches & Carport", "12 Ceilings & Soffits", "13 Roof",
        "14 Fans & Light Fixtures", "15 Interior Lights", "16 Site", "17 Room Labels")}

    make_materials()

    walls = [Wall(*w) for w in WALLS]
    for name, at, width, style in DOORS:
        w = find_wall(walls, at)
        cc = w.along(*at)
        w.holes.append((cc - width / 2, cc + width / 2, 0.0, DOOR_H if style != "cased" else 7.0))
    for name, at, width, height, units in WINDOWS:
        w = find_wall(walls, at)
        cc = w.along(*at)
        w.holes.append((cc - width / 2, cc + width / 2, HEADER - height, HEADER))

    core = MeshBuilder("Walls - Framing & Drywall", c["03 Walls"])
    clad = MeshBuilder("Exterior Siding & Stone", c["04 Exterior Cladding"])
    base = MeshBuilder("Baseboards", c["03 Walls"])
    build_wall_mesh(walls, core, clad, base)
    base.build()
    # corner boards on every outside corner of the building outline
    n = len(OUTLINE)
    area = sum(OUTLINE[i][0] * OUTLINE[(i + 1) % n][1] - OUTLINE[(i + 1) % n][0] * OUTLINE[i][1]
               for i in range(n))
    for i in range(n):
        p_prev, p, p_next = OUTLINE[i - 1], OUTLINE[i], OUTLINE[(i + 1) % n]
        e1 = (p[0] - p_prev[0], p[1] - p_prev[1])
        e2 = (p_next[0] - p[0], p_next[1] - p[1])
        cross = e1[0] * e2[1] - e1[1] * e2[0]
        if cross * area <= 0:
            continue  # inside corner
        # outward normals of both edges
        def nrm(e):
            L = math.hypot(*e)
            nx, ny = e[1] / L, -e[0] / L
            return (nx, ny) if area > 0 else (-nx, -ny)
        n1, n2 = nrm(e1), nrm(e2)
        dx, dy = n1[0] + n2[0], n1[1] + n2[1]
        ox, oy = p[0] + dx * (TS + 0.06), p[1] + dy * (TS + 0.06)
        ix, iy = ox - dx * 0.4, oy - dy * 0.4
        clad.box(min(ox, ix), min(oy, iy), GRADE + 0.05, max(ox, ix), max(oy, iy), PLATE, M["trim"])
    core.build()
    clad.build()

    for name, at, width, style in DOORS:
        w = find_wall(walls, at)
        build_door(c["05 Doors"], w, name, w.along(*at), width, style)
    for name, at, width, height, units in WINDOWS:
        w = find_wall(walls, at)
        build_window(c["06 Windows"], w, name, w.along(*at), width, height, units)

    build_slabs_and_floors(c["01 Foundation & Slabs"], c["02 Floor Finishes"])
    build_kitchen(c["07 Kitchen"])
    build_baths(c["08 Baths"])
    build_utility(c["09 Utility & Closets"])
    build_closets(c["09 Utility & Closets"])
    build_fireplace(c["10 Fireplace"])
    build_structure_exterior(c["11 Porches & Carport"], c["13 Roof"])
    build_ceilings(c["12 Ceilings & Soffits"])
    build_lighting_fixtures(c["14 Fans & Light Fixtures"])
    build_lights(c["15 Interior Lights"])
    build_site(c["16 Site"])
    build_labels(c["17 Room Labels"])
    setup_scene(root)
    return root


def _cli():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if bpy.app.background and "--keep" not in argv:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    if "--save" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=argv[argv.index("--save") + 1], compress=True)
    if "--glb" in argv:
        bpy.ops.export_scene.gltf(filepath=argv[argv.index("--glb") + 1], export_format="GLB",
                                  use_selection=False, export_lights=False, export_cameras=True)


if __name__ == "__main__":
    _cli()
