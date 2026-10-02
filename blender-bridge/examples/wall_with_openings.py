"""Build and render a framed wall with a door and a window, plus foam and strapping.

This is the wall as it goes up on site: 2x4 studs at 16 in. on center, a
bottom plate and double top plate, king and jack studs, doubled 2x10 headers,
a window sill with cripples, 4x8 rigid foam on the outside (like DuroSpan GPS
R5, 1-1/16 in.), vertical strapping on the stud lines and a trim frame
round each opening.

Run in Blender's Scripting tab, or ask Claude:
"run blender-bridge/examples/wall_with_openings.py in Blender".
Replaces the current scene. Then run site_anchors.py and export_ar.py as usual
(pass NAME = "wall_113" to export_ar.py to name the files).

The outside face is -Y. Edit the numbers below to match your wall.
"""

import os

try:
    import bpy
except ImportError:   # plain Python: lets cad/export_dxf.py reuse the layout
    bpy = None

WALL_FT = globals().get("WALL_FT", 12)      # wall length
HEIGHT_FT = globals().get("HEIGHT_FT", 8)     # overall height, bottom plate to top plates
SPACING_IN = 16   # stud spacing, on center
# Rough openings, in inches. x = from the left end of the wall to the left edge
# of the opening. h = rough opening height. sill = floor to the bottom of the
# opening (0 for a door).
OPENINGS = globals().get("OPENINGS") or [
    {"name": "Door",   "x": 24, "w": 38, "h": 82, "sill": 0},
    {"name": "Window", "x": 84, "w": 26, "h": 26, "sill": 42},
]
FOAM = True            # rigid foam on the outside face
FOAM_THICK_IN = 1.0625  # 1-1/16 in.
STRAPPING = True       # vertical strapping on the stud lines + trim round openings
STRAP_THICK_IN, STRAP_WIDTH_IN = 0.75, 2.5   # 1x3
OUT = globals().get("OUT") or os.path.join(os.path.expanduser("~"), "wall_with_openings.png")

IN = 0.0254                 # metres per inch
T, D = 1.5 * IN, 3.5 * IN   # actual 2x4 size
HEADER_D = 9.25 * IN        # actual 2x10

L, H = WALL_FT * 12 * IN, HEIGHT_FT * 12 * IN
FOAM_T = FOAM_THICK_IN * IN
STRAP_T, STRAP_W = STRAP_THICK_IN * IN, STRAP_WIDTH_IN * IN
FOAM_Y = -(D + FOAM_T) / 2
STRAP_Y = -(D + STRAP_T) / 2 - (FOAM_T if FOAM else 0)
TOP = H - 2 * T             # underside of the double top plate

members = []   # (name, kind, (sx, sy, sz), (cx, cy, cz)); sizes and centres in metres


def add(name, kind, x0, x1, z0, z1, y=0.0, depth=D):
    """A member spanning x0..x1 and z0..z1 (metres), `depth` thick, centred at y."""
    members.append((name, kind, (x1 - x0, depth, z1 - z0),
                    ((x0 + x1) / 2, y, (z0 + z1) / 2)))


# Openings, in metres, with the framing clear zone (king + jack studs) round each
ops = []
for o in OPENINGS:
    x0, x1 = o["x"] * IN, (o["x"] + o["w"]) * IN
    z0, z1 = o["sill"] * IN, (o["sill"] + o["h"]) * IN
    if z0 > 0 and z0 < T + 1e-9:
        raise ValueError(f"{o['name']}: sill must be 0 (door) or above the bottom plate")
    if x0 - 2 * T < 0 or x1 + 2 * T > L:
        raise ValueError(f"{o['name']} doesn't fit inside the wall with its king and jack studs")
    if z1 + HEADER_D > TOP + 1e-9:
        raise ValueError(f"{o['name']}: the 2x10 header doesn't fit under the top plates, "
                         "so lower the opening or make the wall taller")
    ops.append({"name": o["name"], "x0": x0, "x1": x1, "z0": z0, "z1": z1})
for i, a in enumerate(ops):
    for b in ops[i + 1:]:
        if a["x0"] - 2 * T < b["x1"] + 2 * T and b["x0"] - 2 * T < a["x1"] + 2 * T:
            raise ValueError(f"{a['name']} and {b['name']} are too close together")

# Plates
add("Bottom Plate", "wood", 0, L, 0, T)
add("Top Plate 1", "wood", 0, L, H - 2 * T, H - T)
add("Top Plate 2", "wood", 0, L, H - T, H)

# Common studs at 16 in. on center, plus one at each end. Studs, and cripples above
# and below openings, share the same layout
count = int(L // (SPACING_IN * IN)) + 1
xs = [min(max(i * SPACING_IN * IN, T / 2), L - T / 2) for i in range(count)]
if xs[-1] < L - T:
    xs.append(L - T / 2)
stud_lines = []
for x in xs:
    sx0, sx1 = x - T / 2, x + T / 2
    hit = [o for o in ops if sx1 > o["x0"] - 2 * T and sx0 < o["x1"] + 2 * T]
    if not hit:
        add(f"Stud {len(stud_lines) + 1:02d}", "wood", sx0, sx1, T, TOP)
        stud_lines.append(x)
        continue
    o = hit[0]
    if o["x0"] <= x <= o["x1"] and sx0 >= o["x0"] and sx1 <= o["x1"]:   # cripples
        n = len([m for m in members if m[0].startswith("Cripple")]) + 1
        add(f"Cripple {n:02d} (above {o['name']})", "wood", sx0, sx1, o["z1"] + HEADER_D, TOP)
        if o["z0"] > 0:
            add(f"Cripple {n + 1:02d} (below {o['name']})", "wood", sx0, sx1, T, o["z0"] - T)
        stud_lines.append(x)

# King studs, jack studs, headers and sills
for o in ops:
    n = o["name"]
    add(f"King Stud L ({n})", "wood", o["x0"] - 2 * T, o["x0"] - T, T, TOP)
    add(f"King Stud R ({n})", "wood", o["x1"] + T, o["x1"] + 2 * T, T, TOP)
    add(f"Jack Stud L ({n})", "wood", o["x0"] - T, o["x0"], T, o["z1"])
    add(f"Jack Stud R ({n})", "wood", o["x1"], o["x1"] + T, T, o["z1"])
    for ply, y in (("A", -(D - T) / 2), ("B", (D - T) / 2)):       # 2 plies, flush to each face
        add(f"Header {ply} ({n})", "wood", o["x0"] - T, o["x1"] + T, o["z1"], o["z1"] + HEADER_D,
            y=y, depth=T)
    if o["z0"] > 0:
        add(f"Sill ({n})", "wood", o["x0"], o["x1"], o["z0"] - T, o["z0"])

# Foam: 4 ft x 8 ft sheets on the outside, cut round the openings
if FOAM:
    def cut(rect, hole):
        """Rect minus hole, as up to 4 rects (x0, x1, z0, z1)."""
        x0, x1, z0, z1 = rect
        hx0, hx1, hz0, hz1 = hole
        if hx0 >= x1 or hx1 <= x0 or hz0 >= z1 or hz1 <= z0:
            return [rect]
        out = []
        if hx0 > x0:
            out.append((x0, hx0, z0, z1))
        if hx1 < x1:
            out.append((hx1, x1, z0, z1))
        mx0, mx1 = max(x0, hx0), min(x1, hx1)
        if hz0 > z0:
            out.append((mx0, mx1, z0, hz0))
        if hz1 < z1:
            out.append((mx0, mx1, hz1, z1))
        return out

    sheets = []
    for sx in range(0, int(round(L / IN)), 48):
        for sz in range(0, int(round(H / IN)), 96):
            sheets.append((sx * IN, min((sx + 48) * IN, L), sz * IN, min((sz + 96) * IN, H)))
    n = 0
    for sheet in sheets:
        pieces = [sheet]
        for o in ops:
            pieces = [r for p in pieces for r in cut(p, (o["x0"], o["x1"], o["z0"], o["z1"]))]
        for x0, x1, z0, z1 in pieces:
            n += 1
            add(f"Foam {n:02d}", "foam", x0, x1, z0, z1, y=FOAM_Y, depth=FOAM_T)

# Strapping on the stud lines, and a 2x4 trim frame round each opening
if STRAPPING:
    clear = [(o["x0"] - STRAP_W, o["x1"] + STRAP_W) for o in ops]
    n = 0
    for x in stud_lines:
        if any(a < x < b for a, b in clear):
            continue
        n += 1
        add(f"Strap {n:02d}", "strap", x - STRAP_W / 2, x + STRAP_W / 2, 0, H,
            y=STRAP_Y, depth=STRAP_T)
    for o in ops:
        t_y = FOAM_Y - (FOAM_T + T) / 2 if FOAM else -(D + T) / 2
        name = o["name"]
        add(f"Trim Top ({name})", "strap", o["x0"] - T, o["x1"] + T, o["z1"], o["z1"] + D, y=t_y, depth=T)
        add(f"Trim Left ({name})", "strap", o["x0"] - T, o["x0"], o["z0"] + (T if o["z0"] else 0), o["z1"], y=t_y, depth=T)
        add(f"Trim Right ({name})", "strap", o["x1"], o["x1"] + T, o["z0"] + (T if o["z0"] else 0), o["z1"], y=t_y, depth=T)
        if o["z0"] > 0:
            add(f"Trim Sill ({name})", "strap", o["x0"] - T, o["x1"] + T, o["z0"] - D, o["z0"], y=t_y, depth=T)


if bpy is not None:   # without Blender (e.g. cad/export_dxf.py) only the framing layout is built
    def material(name, rgb):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
        return mat


    # Clear the scene by hand. Don't use read_factory_settings/read_homefile:
    # they reset preferences, which disables the Claude Bridge add-on mid-request.
    scene = bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                       bpy.data.lights, bpy.data.worlds):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

    mats = {
        "wood": material("SPF Lumber", (0.80, 0.58, 0.33)),
        "foam": material("Rigid Foam", (0.62, 0.66, 0.66)),
        "strap": material("Strapping", (0.88, 0.72, 0.48)),
    }
    floor = material("Floor", (0.25, 0.25, 0.27))
    for name, kind, size, loc in members:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = size
        obj.data.materials.append(mats[kind])

    bpy.ops.mesh.primitive_plane_add(size=40, location=(L / 2, 0, 0))
    bpy.context.object.name = "Floor"
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

    result = {"members": len(members), "openings": [o["name"] for o in ops],
              "wall_ft": WALL_FT, "render": OUT}
    print(result)
