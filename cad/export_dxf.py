"""Export the project 113 porch wall as a 3D DXF that any CAD program opens.

Reuses the framing layout from blender-bridge/examples/wall_with_openings.py,
so the Blender model and the CAD file always match. Units are inches
(DXF $INSUNITS = inches). Each part is a box made of 3DFACEs on a layer named
for what it is: FRAMING, FOAM, STRAPPING.

    pip install ezdxf
    python3 cad/export_dxf.py            # writes cad/porch_wall_113.dxf

Open the .dxf in SketchUp (File > Import, units: inches), AutoCAD, Fusion 360,
FreeCAD or Rhino.

ASSUMED sizes below are estimates from the site photos, not measurements.
Replace them with tape measurements and re-run.
"""

import os
import runpy

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))
LAYOUT = os.path.join(HERE, "..", "blender-bridge", "examples", "wall_with_openings.py")
OUT = os.path.join(HERE, "porch_wall_113.dxf")

# ASSUMED (from the photos, not measured)
WALL_FT = 12
HEIGHT_FT = 8
OPENINGS = [{"name": "Front Window", "x": 30, "w": 72, "h": 48, "sill": 30}]   # the three-pane window

M_TO_IN = 1 / 0.0254
LAYERS = {"wood": ("FRAMING", 40), "foam": ("FOAM", 8), "strap": ("STRAPPING", 30)}

layout = runpy.run_path(LAYOUT, init_globals={"LAYOUT_ONLY": True, "WALL_FT": WALL_FT, "HEIGHT_FT": HEIGHT_FT,
                                              "OPENINGS": OPENINGS})
members = layout["members"]

doc = ezdxf.new("R2000", setup=True)
doc.units = ezdxf.units.IN
for name, color in LAYERS.values():
    doc.layers.add(name, color=color)
msp = doc.modelspace()

for name, kind, (sx, sy, sz), (cx, cy, cz) in members:
    x0, x1 = (cx - sx / 2) * M_TO_IN, (cx + sx / 2) * M_TO_IN
    y0, y1 = (cy - sy / 2) * M_TO_IN, (cy + sy / 2) * M_TO_IN
    z0, z1 = (cz - sz / 2) * M_TO_IN, (cz + sz / 2) * M_TO_IN
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in faces:
        msp.add_3dface([c[i] for i in f], dxfattribs={"layer": LAYERS[kind][0]})

doc.saveas(OUT)
print(f"{len(members)} parts, {len(members) * 6} faces -> {OUT}")
