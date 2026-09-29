"""Export the scene's meshes as AR-ready files, at real-world scale.

  <name>.usdz  iPhone / iPad / Vision Pro: tap in Files or Messages -> AR
  <name>.glb   Android, Meta Quest, web viewers, Unity (glTFast package)
  <name>.fbx   Unity: drag into the Assets folder

Run after building a model (e.g. stud_wall.py), in Blender's Scripting tab or
by asking Claude: "run examples/export_ar.py in Blender".
The model is centered on its footprint with its base at floor level, so it
sits on the ground where you place it. Objects named in SKIP are left out.
"""

import os

import bpy
from mathutils import Vector

NAME = globals().get("NAME") or "stud_wall"
OUT_DIR = globals().get("OUT_DIR") or os.path.join(os.path.expanduser("~"), "Desktop")
SKIP = {"Floor"}

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name not in SKIP]
if not meshes:
    raise RuntimeError("No meshes to export")

# Footprint center + base height, from world-space bounding boxes.
corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = [min(v[i] for v in corners) for i in range(3)]
hi = [max(v[i] for v in corners) for i in range(3)]
shift = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])

bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]

os.makedirs(OUT_DIR, exist_ok=True)
paths = {ext: os.path.join(OUT_DIR, f"{NAME}.{ext}") for ext in ("usdz", "glb", "fbx")}
original = {o: o.location.copy() for o in meshes}
for o in meshes:
    o.location = [o.location[i] + shift[i] for i in range(3)]
try:
    # Y-up: Apple's AR Quick Look ignores USD's upAxis and assumes Y-up.
    bpy.ops.wm.usd_export(filepath=paths["usdz"], selected_objects_only=True,
                          export_materials=True, convert_world_material=False,
                          convert_orientation=True, export_global_up_selection="Y",
                          export_global_forward_selection="NEGATIVE_Z")
    bpy.ops.export_scene.gltf(filepath=paths["glb"], export_format="GLB",
                              use_selection=True, export_materials="EXPORT")
    bpy.ops.export_scene.fbx(filepath=paths["fbx"], use_selection=True,
                             apply_scale_options="FBX_SCALE_ALL")
finally:
    for o, loc in original.items():  # put the scene back exactly
        o.location = loc

size_m = [round(hi[i] - lo[i], 3) for i in range(3)]
result = {"objects": len(meshes), "size_m": size_m,
          "files": {k: f"{p} ({os.path.getsize(p) // 1024} KB)" for k, p in paths.items()}}
print(result)
