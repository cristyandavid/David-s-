"""Find where the porch ridge / rafters cut into the roof plywood, and show them.

Prints each clashing pair with the overlap depth in inches, selects those
objects, and frames the 3D view on them. Changes no geometry.

The ridge height is verified against the binder (11 ft), so do not lower the
ridge to cure a clash: trim or re-seat the plywood instead, or tell Claude
which piece is wrong. Edit the name lists below if nothing is found.

Run in Blender's Text Editor with the model open.
"""

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FRAMING_WORDS = ("ridge", "rafter")  # lower-case parts of object names
SHEATHING_WORDS = ("sheath", "plywood", "osb", "roof deck")
MIN_DEPTH = 0.02  # inches; ignore smaller overlaps

scale = bpy.context.scene.unit_settings.scale_length
k = scale / 0.0254
depsgraph = bpy.context.evaluated_depsgraph_get()


def named(words, exclude=()):
    return [
        o for o in bpy.data.objects
        if o.type == "MESH"
        and any(w in o.name.lower() for w in words)
        and not any(w in o.name.lower() for w in exclude)
    ]


framing = named(FRAMING_WORDS)
sheathing = named(SHEATHING_WORDS, exclude=FRAMING_WORDS)
print(f"INFO  {len(framing)} ridge/rafter objects, {len(sheathing)} sheathing objects")
if not framing or not sheathing:
    raise RuntimeError("Nothing to compare: edit FRAMING_WORDS / SHEATHING_WORDS")


def bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (
        Vector(min(p[i] for p in pts) for i in range(3)),
        Vector(max(p[i] for p in pts) for i in range(3)),
    )


def tree(obj):
    return BVHTree.FromObject(obj, depsgraph)


boxes = {o.name: bbox(o) for o in framing + sheathing}
trees = {}
clashes = []
for f in framing:
    flo, fhi = boxes[f.name]
    for s in sheathing:
        slo, shi = boxes[s.name]
        depth = [min(fhi[i], shi[i]) - max(flo[i], slo[i]) for i in range(3)]
        if min(depth) <= 0:
            continue
        trees.setdefault(f.name, tree(f))
        trees.setdefault(s.name, tree(s))
        if not trees[f.name].overlap(trees[s.name]):
            continue
        clashes.append((f.name, s.name, min(depth) * k))

clashes.sort(key=lambda c: -c[2])
for fname, sname, d in clashes:
    flag = "CLASH" if d >= MIN_DEPTH else "touch"
    print(f"{flag}  {fname}  x  {sname}: about {d:.2f} in of overlap (box estimate)")
print(f"{'CHECK FAILED' if clashes else 'ALL CLEAR'}: {len(clashes)} clashing pairs")

if clashes:
    names = {n for c in clashes for n in c[:2]}
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[clashes[0][0]]
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=window, area=area, region=region):
                    bpy.ops.view3d.view_selected()
                break
