"""Put the porch ridge post back in its spec position.

Moves only the post: centred on the porch beam in x, bearing on the beam top in z
(so its top meets the ridge underside), y untouched. Prints before and after and
frames the post in the 3D view. Undo with Ctrl+Z. Set APPLY = False to preview.

Spec (notebook, 2026-10-29): 3-ply 2x6 post, 22.75 in tall, centre x = -66.25 in,
bottom on the 2-2x10 beam top, top at the ridge underside (z 130.5 in).
"""

import bpy
from mathutils import Vector

APPLY = True
BEAM = "Porch Beam (2-2x10)"
POST = "Porch Ridge Post 3-ply 2x6"
POST_X = -66.25  # inches; matches the beam centre
POST_H = 22.75
RIDGE_UNDERSIDE_Z = 130.5
TOL = 0.05

scale = bpy.context.scene.unit_settings.scale_length
k = scale / 0.0254  # Blender units -> inches


def find(name):
    return bpy.data.objects.get(name) or next(
        (o for o in bpy.data.objects if o.name.startswith(name)), None
    )


def box(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector(min(p[i] for p in pts) * k for i in range(3))
    hi = Vector(max(p[i] for p in pts) * k for i in range(3))
    return lo, hi


beam_obj, post_obj = find(BEAM), find(POST)
if beam_obj is None or post_obj is None:
    raise RuntimeError(f"Missing object: {BEAM if beam_obj is None else POST}")

blo, bhi = box(beam_obj)
plo, phi = box(post_obj)
height = phi.z - plo.z
print(f"INFO  before: centre x {(plo.x + phi.x) / 2:.2f}, bottom z {plo.z:.2f}, "
      f"top z {phi.z:.2f}, height {height:.2f} in")

dx = (blo.x + bhi.x) / 2 - (plo.x + phi.x) / 2  # centre on the beam
dz = bhi.z - plo.z  # bearing on the beam top
print(f"INFO  move: x {dx:+.2f} in, z {dz:+.2f} in")

if abs(height - POST_H) > TOL:
    print(f"WARN  post is {height:.2f} in tall, spec {POST_H}: size is wrong, not just position")

if APPLY:
    m = post_obj.matrix_world.copy()
    m.translation += Vector((dx, 0.0, dz)) / k
    post_obj.matrix_world = m
    bpy.context.view_layer.update()
    plo, phi = box(post_obj)
    print(f"INFO  after:  centre x {(plo.x + phi.x) / 2:.2f}, bottom z {plo.z:.2f}, "
          f"top z {phi.z:.2f} (ridge underside spec {RIDGE_UNDERSIDE_Z})")
    ok = abs(phi.z - RIDGE_UNDERSIDE_Z) <= TOL
    print("OK  post top meets the ridge underside" if ok else
          "CHECK  post top does not meet the ridge underside: ridge or beam is off, not the post")

for o in bpy.context.view_layer.objects:
    o.select_set(o is post_obj)
bpy.context.view_layer.objects.active = post_obj
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            region = next(r for r in area.regions if r.type == "WINDOW")
            with bpy.context.temp_override(window=window, area=area, region=region):
                bpy.ops.view3d.view_selected()
            break
