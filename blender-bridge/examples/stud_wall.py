"""Build and render a 2x4 stud wall, 16 in. on center.

Run in Blender's Scripting tab, or ask Claude:
"run blender-bridge/examples/stud_wall.py in Blender".
Replaces the current scene.
"""

import os

import bpy

WALL_FT = 16      # wall length
HEIGHT_FT = 8     # overall height, bottom plate to top plates
SPACING_IN = 16   # stud spacing, on center
OUT = globals().get("OUT") or os.path.join(os.path.expanduser("~"), "stud_wall.png")

IN = 0.0254                 # metres per inch
T, D = 1.5 * IN, 3.5 * IN   # actual 2x4 size


def material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    return mat


def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.data.materials.append(mat)
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
wood = material("SPF Lumber", (0.80, 0.58, 0.33))
floor = material("Floor", (0.25, 0.25, 0.27))
L, H = WALL_FT * 12 * IN, HEIGHT_FT * 12 * IN

box("Bottom Plate", (L, D, T), (L / 2, 0, T / 2), wood)
box("Top Plate 1", (L, D, T), (L / 2, 0, H - 1.5 * T), wood)
box("Top Plate 2", (L, D, T), (L / 2, 0, H - T / 2), wood)

stud_h = H - 3 * T
count = int(L // (SPACING_IN * IN)) + 1
xs = [min(max(i * SPACING_IN * IN, T / 2), L - T / 2) for i in range(count)]
if xs[-1] < L - T:
    xs.append(L - T / 2)
for i, x in enumerate(xs, 1):
    box(f"Stud {i:02d}", (T, D, stud_h), (x, 0, T + stud_h / 2), wood)

bpy.ops.mesh.primitive_plane_add(size=40, location=(L / 2, 0, 0))
bpy.context.object.data.materials.append(floor)

bpy.ops.object.light_add(type="SUN", rotation=(0.9, 0.3, 0.7))
bpy.context.object.data.energy = 3

target = bpy.data.objects.new("Camera Target", None)
target.location = (L / 2, 0, H / 2)
scene.collection.objects.link(target)
bpy.ops.object.camera_add(location=(L / 2 + 2.5, -7.5, 1.6))
cam = bpy.context.object
cam.constraints.new("TRACK_TO").target = target
scene.camera = cam

scene.world = bpy.data.worlds.new("Sky")
scene.world.color = (0.35, 0.42, 0.55)
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.render.resolution_x, scene.render.resolution_y = 1200, 700
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)

result = {"studs": len(xs), "wall_ft": WALL_FT, "render": OUT}
print(result)
