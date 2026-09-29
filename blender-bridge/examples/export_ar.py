"""Export the scene's meshes as AR-ready files, at real-world scale.

  <name>.usdz  iPhone / iPad / Vision Pro: tap in Files or Messages -> AR
  <name>.glb   Android, Meta Quest, web viewers, Unity (glTFast package)
  <name>.fbx   Unity: drag into Assets/Site Models/ (see unity/README.md)

Placement in the exported files:
  - Site-aligned (CP_A and CP_B exist, see site_anchors.py): the origin is
    CP_A and CP_A -> CP_B runs along +X. The control points are exported too,
    so the Unity site aligner can snap them onto the real marks.
  - Otherwise: centred on the footprint with its base at floor level.

Run in Blender's Scripting tab, or ask Claude: "run examples/export_ar.py in
Blender". Objects named in SKIP are left out. The Blender scene isn't changed.
"""

import math
import os

import bpy
from mathutils import Matrix, Vector

NAME = globals().get("NAME") or "stud_wall"
OUT_DIR = globals().get("OUT_DIR") or os.path.join(os.path.expanduser("~"), "Desktop")
SKIP = {"Floor"}

scene = bpy.context.scene
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == "MESH" and o.name not in SKIP]
if not meshes:
    raise RuntimeError("No meshes to export")
cps = [bpy.data.objects.get(n) for n in ("CP_A", "CP_B")]
site_aligned = all(cp is not None and cp.name in scene.objects for cp in cps)

corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = [min(v[i] for v in corners) for i in range(3)]
hi = [max(v[i] for v in corners) for i in range(3)]

if site_aligned:
    a, b = (cp.matrix_world.translation.copy() for cp in cps)
    yaw = math.atan2(b.y - a.y, b.x - a.x)
    to_export = Matrix.Rotation(-yaw, 4, "Z") @ Matrix.Translation(-a)
    exported = meshes + cps
else:
    to_export = Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    exported = meshes

bpy.ops.object.select_all(action="DESELECT")
for o in exported:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]

os.makedirs(OUT_DIR, exist_ok=True)
paths = {ext: os.path.join(OUT_DIR, f"{NAME}.{ext}") for ext in ("usdz", "glb", "fbx")}

# Move only top-level objects; children follow. Restore exactly afterwards.
roots = [o for o in exported if o.parent not in exported]
original = {o: o.matrix_basis.copy() for o in roots}
for o in roots:
    o.matrix_world = to_export @ o.matrix_world
try:
    # Y-up: Apple's AR Quick Look ignores USD's upAxis and assumes Y-up.
    bpy.ops.wm.usd_export(filepath=paths["usdz"], selected_objects_only=True,
                          export_materials=True, convert_world_material=False,
                          convert_orientation=True, export_global_up_selection="Y",
                          export_global_forward_selection="NEGATIVE_Z")
    bpy.ops.export_scene.gltf(filepath=paths["glb"], export_format="GLB",
                              use_selection=True, export_materials="EXPORT")
    bpy.ops.export_scene.fbx(filepath=paths["fbx"], use_selection=True,
                             object_types={"MESH", "EMPTY"},
                             apply_scale_options="FBX_SCALE_ALL")
finally:
    for o, basis in original.items():
        o.matrix_basis = basis
    bpy.context.view_layer.update()

result = {
    "placement": "site-aligned: origin CP_A, CP_A->CP_B = +X" if site_aligned
                 else "centred (run site_anchors.py first for on-site alignment)",
    "objects": len(exported),
    "size_m": [round(hi[i] - lo[i], 3) for i in range(3)],
    "files": {k: f"{p} ({os.path.getsize(p) // 1024} KB)" for k, p in paths.items()},
}
print(result)
