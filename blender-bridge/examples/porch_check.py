"""Check the 113 Bellefair porch ridge post against the notebook spec.

Reads world-space bounding boxes of three objects and prints PASS / FAIL per
check, in inches. Changes nothing. Run it in Blender's Text Editor (or through
the bridge) with the Bellefair_Framing_FIXED model open.

Spec: 3-ply 2x6 post (4.5 x 5.5 in) under a double 2x8 ridge, bearing on the
porch beam (2-2x10, 9.25 in deep). The engineer's fastening detail is NOT
checked: it is owed by the site coordinator and must not be invented.
"""

import bpy
from mathutils import Vector

TOL = 0.25  # inches

BEAM = "Porch Beam (2-2x10)"
RIDGE2 = "Porch Gable Ridge 2x8 Ply 2"
POST = "Porch Ridge Post 3-ply 2x6"

# Spec values, inches. z is height, x is along the ridge.
BEAM_DEPTH = 9.25
BEAM_REF_Z = 98.5  # "top of posts"; may be the beam's underside or its top
RIDGE_Z = (130.5, 137.8)
RIDGE_X = (-84.0, -10.2)
POST_X = -66.25
POST_H = 22.75
POST_SECTION = (4.5, 5.5)

scale = bpy.context.scene.unit_settings.scale_length
bpy.context.view_layer.update()
results = []


def box(name):
    """World-space (min, max) corners in inches, or None if the object is missing.

    Matches the exact name first, then a name prefix: the build appends a
    suffix such as " (notebook spec 2026-10-29)".
    """
    obj = bpy.data.objects.get(name) or next(
        (o for o in bpy.data.objects if o.name.startswith(name)), None
    )
    if obj is None:
        return None
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    k = scale / 0.0254
    lo = Vector([min(c[i] for c in corners) * k for i in range(3)])
    hi = Vector([max(c[i] for c in corners) * k for i in range(3)])
    return lo, hi


def check(label, actual, expected):
    ok = abs(actual - expected) <= TOL
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {actual:.2f} in (spec {expected})")


beam, ridge, post = box(BEAM), box(RIDGE2), box(POST)
for name, b in ((BEAM, beam), (RIDGE2, ridge), (POST, post)):
    if b is None:
        results.append(False)
        print(f"FAIL  missing object: {name}")

if ridge:
    ft, inch = divmod(ridge[0].z, 12)
    print(f"INFO  ridge underside {ft:.0f}'-{inch:.2f}\", top {ridge[1].z / 12:.2f} ft")
    check("ridge ply 2 bottom z", ridge[0].z, RIDGE_Z[0])
    check("ridge ply 2 top z", ridge[1].z, RIDGE_Z[1])
    check("ridge ply 2 start x", ridge[0].x, RIDGE_X[0])
    check("ridge ply 2 end x", ridge[1].x, RIDGE_X[1])

if post:
    size = sorted([post[1].x - post[0].x, post[1].y - post[0].y])
    check("post section (short side)", size[0], POST_SECTION[0])
    check("post section (long side)", size[1], POST_SECTION[1])
    check("post height", post[1].z - post[0].z, POST_H)
    check("post centre x", (post[0].x + post[1].x) / 2, POST_X)
    if ridge:
        check("post top meets ridge underside", post[1].z, ridge[0].z)

if beam:
    check("beam depth", beam[1].z - beam[0].z, BEAM_DEPTH)
    if post:
        check("post bears on beam top", post[0].z, beam[1].z)
    mid = (beam[0].x + beam[1].x) / 2
    print(f"INFO  beam x {beam[0].x:.2f} to {beam[1].x:.2f}, centre {mid:.2f}")
    if post:
        off = (post[0].x + post[1].x) / 2 - mid
        print(f"INFO  post is {off:+.2f} in from the beam centre (0 = centred)")
    under = abs(beam[0].z - BEAM_REF_Z) <= TOL
    top = abs(beam[1].z - BEAM_REF_Z) <= TOL
    which = "underside" if under else "top" if top else "neither face"
    print(f"INFO  {BEAM_REF_Z} in matches the beam {which} "
          f"(beam z {beam[0].z:.2f} to {beam[1].z:.2f})")

print("ALL PASS" if results and all(results) else "CHECK FAILED: see FAIL lines above")
