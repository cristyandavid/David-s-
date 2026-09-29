"""Add site control points CP_A and CP_B to the model for on-site AR alignment.

CP_A -> CP_B is the layout line you'll find on site: for a wall, the chalk
line along the face of the bottom plate. On site, the Unity app asks you to
aim at the two real marks; the model snaps so CP_A and CP_B sit on them.

If CP_A / CP_B already exist they're kept (move them in Blender to any two
points you can find on site: a slab corner, grid-line marks, an anchor bolt).
Otherwise they're placed at floor level on the long side of the tightest
rectangle around the model's footprint, so they follow the wall at any angle:
walking from CP_A to CP_B, the model is on your left. If you chalked the other
face, swap or move the points in Blender.

Run after building a model, before export_ar.py.
"""

import math

import bpy
from mathutils import Vector

SKIP = {"Floor"}
SIZE = 0.15  # empty display size, metres

scene = bpy.context.scene
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == "MESH" and o.name not in SKIP]
if not meshes:
    raise RuntimeError("No meshes found; build the model first")


def convex_hull(points):
    """Andrew's monotone chain; points are (x, y) tuples."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]

    return half(pts) + half(reversed(pts))


def layout_line(points):
    """Long front edge of the min-area rectangle around the (x, y) points.

    Returns (start, end) with the model on the left of start -> end.
    """
    hull = convex_hull(points)
    best = None
    for i in range(len(hull)):  # the min-area rectangle shares a side with the hull
        (x0, y0), (x1, y1) = hull[i], hull[(i + 1) % len(hull)]
        ang = math.atan2(y1 - y0, x1 - x0)
        u, v = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        us = [p[0] * u[0] + p[1] * u[1] for p in hull]
        vs = [p[0] * v[0] + p[1] * v[1] for p in hull]
        w, h = max(us) - min(us), max(vs) - min(vs)
        if best is None or w * h < best[0] - 1e-9:
            best = (w * h, u, v, min(us), max(us), min(vs), max(vs))
    _, u, v, u0, u1, v0, v1 = best
    if (u1 - u0) < (v1 - v0):  # run along the long side
        u, v, u0, u1, v0, v1 = v, (-u[0], -u[1]), v0, v1, -u1, -u0
    if u[0] < -1e-9 or (abs(u[0]) <= 1e-9 and u[1] < 0):  # point roughly +X
        u, v, u0, u1, v0, v1 = (-u[0], -u[1]), (-v[0], -v[1]), -u1, -u0, -v1, -v0
    at = lambda s, t: (s * u[0] + t * v[0], s * u[1] + t * v[1])
    return at(u0, v0), at(u1, v0)


verts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
floor_z = min(p.z for p in verts)
(ax, ay), (bx, by) = layout_line([(round(p.x, 6), round(p.y, 6)) for p in verts])
defaults = {"CP_A": (ax, ay, floor_z), "CP_B": (bx, by, floor_z)}

created = []
for name, loc in defaults.items():
    cp = bpy.data.objects.get(name)
    if cp is None:
        cp = bpy.data.objects.new(name, None)
        cp.empty_display_type = "SINGLE_ARROW" if name == "CP_A" else "PLAIN_AXES"
        cp.empty_display_size = SIZE
        cp.show_name = True
        cp.location = loc
        scene.collection.objects.link(cp)
        created.append(name)

bpy.context.view_layer.update()
a = bpy.data.objects["CP_A"].matrix_world.translation
b = bpy.data.objects["CP_B"].matrix_world.translation
dist = (b - a).length
inches = dist / 0.0254
if (Vector((b.x - a.x, b.y - a.y, 0))).length < 0.3:
    raise RuntimeError("CP_A and CP_B must be at least 1 ft apart horizontally")

result = {
    "created": created,
    "CP_A": [round(x, 4) for x in a],
    "CP_B": [round(x, 4) for x in b],
    "distance_m": round(dist, 4),
    "distance_ft_in": f"{int(inches // 12)}' {inches % 12:.2f}\"",
}
print(result)
