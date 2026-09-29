"""
Render preview images of the Palvic house model (Cycles).

    blender -b palvic_lot7.blend -P render_views.py -- --out renders/ [--samples 64] [--scale 50]

Views: front 3/4, back 3/4, living room interior, and a top-down cutaway plan
(roof, ceilings and site hidden).
"""

import os
import sys

import bpy

ROOT = "Palvic House - Lot 7"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


OUT = arg("--out", "renders")
SAMPLES = int(arg("--samples", "64"))
SCALE = int(arg("--scale", "100"))
ONLY = arg("--only", "")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.resolution_percentage = SCALE
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "AgX"


def coll(name):
    return bpy.data.collections[name]


def show(names_hidden):
    root = coll(ROOT)
    for c in root.children:
        c.hide_render = c.name in names_hidden


VIEWS = [
    ("front", "Cam - Front 3-4", {"15 Interior Lights", "17 Room Labels"}),
    ("back", "Cam - Back 3-4", {"15 Interior Lights", "17 Room Labels"}),
    ("living", "Cam - Living Room", {"17 Room Labels"}),
    ("plan", "Cam - Plan (top, ortho)",
     {"13 Roof", "12 Ceilings & Soffits", "16 Site", "14 Fans & Light Fixtures",
      "17 Room Labels"}),
]

for key, cam, hidden in VIEWS:
    if ONLY and key not in ONLY.split(","):
        continue
    show(hidden)
    sc.camera = bpy.data.objects[cam]
    if key == "plan":
        sc.render.resolution_x, sc.render.resolution_y = 1800, 1500
    else:
        sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.filepath = os.path.join(OUT, "palvic_%s.png" % key)
    bpy.ops.render.render(write_still=True)
    print("rendered", sc.render.filepath)

show(set())
