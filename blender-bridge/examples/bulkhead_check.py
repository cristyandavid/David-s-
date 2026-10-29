"""Check the 113 Bellefair dining room bulkhead (BEL-RM-006) is a full perimeter.

Finds every mesh whose name, or whose collection name, contains BEL-RM-006 and
checks, in world space and inches:

  * the piece count matches the expected total,
  * all four sides of the footprint have framing along them,
  * no side has a gap longer than MAX_GAP between pieces.

It reads the model only and changes nothing. The plan note is "bulkhead in
dining room, all sides from existing blue": the existing north run is the
reference and the other three sides must close the rectangle. Piece sizes and
the room dimensions are not checked here; add them once confirmed on site.

Run in Blender's Text Editor with the Bellefair_Framing_FIXED model open.
"""

import bpy
from mathutils import Vector

TAG = "BEL-RM-006"
EXPECTED_PIECES = 164  # from the Oct 29 ops feed
MAX_GAP = 1.5  # inches between pieces along a side
EDGE_TOL = 3.0  # inches: a piece "is on" a side if it reaches within this

scale = bpy.context.scene.unit_settings.scale_length
bpy.context.view_layer.update()
results = []


def say(ok, text):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {text}")


def inches(obj):
    """World-space (xmin, xmax, ymin, ymax) in inches."""
    k = scale / 0.0254
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs, ys = [p.x * k for p in pts], [p.y * k for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def tagged(obj):
    return obj.type == "MESH" and (
        TAG in obj.name or any(TAG in c.name for c in obj.users_collection)
    )


def longest_gap(spans, lo, hi):
    """Longest uncovered stretch between lo and hi given (start, end) spans."""
    reach, gap = lo, 0.0
    for start, end in sorted(spans):
        gap = max(gap, start - reach)
        reach = max(reach, end)
    return max(gap, hi - reach)


pieces = [(o, inches(o)) for o in bpy.data.objects if tagged(o)]
if not pieces:
    raise RuntimeError(f"No meshes found with {TAG} in the name or collection")

say(len(pieces) == EXPECTED_PIECES, f"piece count: {len(pieces)} (expected {EXPECTED_PIECES})")

x0 = min(b[0] for _, b in pieces)
x1 = max(b[1] for _, b in pieces)
y0 = min(b[2] for _, b in pieces)
y1 = max(b[3] for _, b in pieces)
print(f"INFO  footprint {x1 - x0:.1f} x {y1 - y0:.1f} in "
      f"({(x1 - x0) / 12:.2f} x {(y1 - y0) / 12:.2f} ft)")

# side name, pieces reaching that edge, their span along it, edge length
sides = {
    "north": ([b for _, b in pieces if b[3] >= y1 - EDGE_TOL], (0, 1), (x0, x1)),
    "south": ([b for _, b in pieces if b[2] <= y0 + EDGE_TOL], (0, 1), (x0, x1)),
    "west": ([b for _, b in pieces if b[0] <= x0 + EDGE_TOL], (2, 3), (y0, y1)),
    "east": ([b for _, b in pieces if b[1] >= x1 - EDGE_TOL], (2, 3), (y0, y1)),
}
for name, (on_edge, (i, j), (lo, hi)) in sides.items():
    if not on_edge:
        say(False, f"{name} side: no framing along it")
        continue
    gap = longest_gap([(b[i], b[j]) for b in on_edge], lo, hi)
    say(gap <= MAX_GAP, f"{name} side: {len(on_edge)} pieces, longest gap {gap:.2f} in")

print("ALL PASS" if all(results) else "CHECK FAILED: see FAIL lines above")
