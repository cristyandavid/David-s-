"""Find where the porch ridge / rafters cut into the roof plywood, and clear it.

Prints each clashing pair with the overlap depth in inches, selects those
objects, and frames the 3D view on them.

With APPLY = False (default) it changes nothing. With APPLY = True it lifts each
clashing plywood piece straight up by its overlap, re-tests, and repeats until
clear or until a piece would move more than MAX_MOVE. The ridge is never moved:
its height is verified against the binder (11 ft). Undo with Ctrl+Z.

Edit the name lists below if nothing is found. Run in Blender's Text Editor with
the model open.
"""

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

APPLY = False
FRAMING_WORDS = ("ridge", "rafter")  # lower-case parts of object names
SHEATHING_WORDS = ("sheath", "plywood", "osb", "roof deck")
MIN_DEPTH = 0.02  # inches; ignore smaller overlaps
MARGIN = 0.01  # inches of clearance added when lifting
MAX_MOVE = 0.5  # inches; most any one plywood piece may be lifted in total
MAX_PASSES = 5

scale = bpy.context.scene.unit_settings.scale_length
k = scale / 0.0254  # Blender units -> inches


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


def world_tree(obj, depsgraph):
    """BVH tree in world space (FromObject alone uses local space)."""
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    verts = [obj.matrix_world @ v.co for v in mesh.vertices]
    polys = [p.vertices[:] for p in mesh.polygons]
    tree = BVHTree.FromPolygons(verts, polys)
    ev.to_mesh_clear()
    box = (
        Vector(min(v[i] for v in verts) for i in range(3)),
        Vector(max(v[i] for v in verts) for i in range(3)),
    )
    return tree, box


def find_clashes():
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    built = {o.name: world_tree(o, depsgraph) for o in framing + sheathing}
    found = []
    for f in framing:
        ftree, (flo, fhi) = built[f.name]
        for s in sheathing:
            stree, (slo, shi) = built[s.name]
            depth = [min(fhi[i], shi[i]) - max(flo[i], slo[i]) for i in range(3)]
            if min(depth) > 0 and ftree.overlap(stree):
                found.append((f.name, s.name, min(depth) * k))
    return sorted(found, key=lambda c: -c[2])


moved = {}  # plywood name -> inches lifted so far
clashes = find_clashes()
first = clashes
for n in range(MAX_PASSES if APPLY else 0):
    todo = {}
    for fname, sname, d in clashes:
        todo[sname] = max(todo.get(sname, 0.0), d)
    if not todo:
        break
    for sname, d in todo.items():
        lift = d + MARGIN
        if moved.get(sname, 0.0) + lift > MAX_MOVE:
            print(f"SKIP  {sname}: would move more than {MAX_MOVE} in; check by hand")
            continue
        obj = bpy.data.objects[sname]
        m = obj.matrix_world.copy()
        m.translation.z += lift / k
        obj.matrix_world = m
        moved[sname] = moved.get(sname, 0.0) + lift
    clashes = find_clashes()

for sname, d in moved.items():
    print(f"MOVED {sname}: lifted {d:.3f} in")
for fname, sname, d in first:
    flag = "CLASH" if d >= MIN_DEPTH else "touch"
    print(f"{flag}  {fname}  x  {sname}: about {d:.2f} in of overlap (box estimate)")
left = [c for c in clashes if c[2] >= MIN_DEPTH]
print(f"{'CHECK FAILED' if left else 'ALL CLEAR'}: "
      f"{len(first)} clashing pairs found, {len(left)} left")

if first:
    names = {n for c in first for n in c[:2]}
    for o in bpy.context.view_layer.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[first[0][0]]
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=window, area=area, region=region):
                    bpy.ops.view3d.view_selected()
                break
