"""Count the 8 ft boards needed for the BEL-RM-006 bulkhead pieces.

Measures each tagged mesh's longest side in inches, then packs the pieces onto
8 ft (96 in) stock, longest first, allowing a saw kerf per cut. Prints the
board count and waste so it can be compared with the written takeoff
(ops feed: about 44 boards of 2x2, 8 ft, for the 137 new pieces).

Set ONLY_NEW to a name tag if the new pieces are marked; by default all tagged
pieces are counted, so the total will exceed the 137-new-piece figure.
Reads the model only. Run in Blender's Text Editor with the model open.
"""

import bpy
from mathutils import Vector

TAG = "BEL-RM-006"
ONLY_NEW = None  # e.g. "NEW" to count only objects whose name contains it
STOCK = 96.0  # inches
KERF = 0.125  # inches per cut

scale = bpy.context.scene.unit_settings.scale_length
bpy.context.view_layer.update()
k = scale / 0.0254


def length_in(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)) * k


pieces = sorted(
    (
        length_in(o)
        for o in bpy.data.objects
        if o.type == "MESH"
        and (TAG in o.name or any(TAG in c.name for c in o.users_collection))
        and (ONLY_NEW is None or ONLY_NEW in o.name)
    ),
    reverse=True,
)
if not pieces:
    raise RuntimeError(f"No meshes found with {TAG}")

too_long = [p for p in pieces if p > STOCK]
boards = []  # remaining length per board
for p in (q for q in pieces if q <= STOCK):
    need = p + KERF
    for i, left in enumerate(boards):
        if left >= need:
            boards[i] = left - need
            break
    else:
        boards.append(STOCK - need)

total = sum(pieces)
print(f"INFO  {len(pieces)} pieces, {total:.1f} in ({total / 12:.1f} ft) of material")
print(f"INFO  {len(boards)} x 8 ft boards, {sum(boards) / 12:.1f} ft offcut")
if too_long:
    print(f"FAIL  {len(too_long)} pieces longer than {STOCK:.0f} in need splicing: "
          f"{[round(p, 1) for p in too_long[:5]]}")
