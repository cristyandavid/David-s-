"""Parametric 'Duo' hard case for an iPhone: two shells (back + front) that
lap-join and snap together, printable without supports.

Run:  python3 duo_case.py      -> back_shell.stl, front_shell.stl, assembled.stl
All units mm. x = width, y = height (top of phone is +y), z = thickness
(back of phone at low z). Defaults approximate iPhone 17 Pro.
VERIFY the dimensions & cutout positions against your exact model before printing.
"""
import numpy as np
import manifold3d as m
from manifold3d import CrossSection as CS, Manifold as M
import trimesh

# ---- phone (edit for your model) ------------------------------------------
import os, sys
PROFILES = {   # W, H, T, corner R, camera (cx offset from left, cy offset from top, size, radius), key y-offsets from top
    "pro":  dict(W=71.9, H=150.0, T=8.75, R=11.0, cam=(20.5, 21.5, 38.0, 9.0),
                 act=28, volu=44, vold=62, pwr=50, ctl=42, volh=13.5),
    # iPhone 13/12 mini (approx): 64.2 x 131.5 x 7.65, dual camera
    "mini": dict(W=64.2, H=131.5, T=7.65, R=9.0, cam=(16.5, 16.5, 29.0, 7.5),
                 act=24, volu=36, vold=51, pwr=40, ctl=-999, volh=11.0),
}
PROFILE = os.environ.get("PHONE", "pro")
P = PROFILES[PROFILE]
W, H, T, R = P["W"], P["H"], P["T"], P["R"]
# ---- case parameters -------------------------------------------------------
CLR   = 0.25    # clearance around phone per side
WALL  = 2.0     # side wall
FLOOR = 1.6     # back plate thickness
TOP   = 1.4     # front bezel plate thickness
BEZEL = 1.6     # how far front lip overlaps the screen edge
LAP_H = 3.0     # height of overlap joint
LAP_GAP = 0.15  # joint clearance
SEG = 96

def rrect(w, h, r, d=0.0):
    r = max(r + d, 0.2)
    s = CS.square((max(w + 2*d - 2*r, .1), max(h + 2*d - 2*r, .1)), center=True)
    return s.offset(r, m.JoinType.Round, 2.0, SEG)

def slab(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate((0, 0, z0))

CW, CH = W + 2*CLR, H + 2*CLR                  # cavity size
OW, OH = CW + 2*WALL, CH + 2*WALL              # outer size
CR = R + CLR
OR = CR + WALL
z_cav0 = FLOOR
z_cav1 = FLOOR + T + 2*CLR
Z_TOP  = z_cav1 + TOP
ZS     = FLOOR + T*0.5                         # split plane

# outer body: hull of slices -> softly rounded top/bottom edges
def outer_body(z0, z1, e=1.2):
    mid = slab(rrect(OW, OH, OR), z0 + e, z1 - e)
    lo = slab(rrect(OW, OH, OR, -e), z0, z0 + .01)
    hi = slab(rrect(OW, OH, OR, -e), z1 - .01, z1)
    mid2 = slab(rrect(OW, OH, OR, -e*.45), z0 + .3*e, z0 + .31*e) 
    hi2 = slab(rrect(OW, OH, OR, -e*.45), z1 - .31*e, z1 - .3*e)
    return M.batch_hull([lo, mid, hi, mid2, hi2])

body = outer_body(0, Z_TOP)
cavity = slab(rrect(CW, CH, CR), z_cav0, z_cav1)

# ---- lap joint ------------------------------------------------------------
# ring between outer wall and cavity; split it into inner half (back owns) and outer half (front owns)
mid_off = WALL/2
inner_ring_outline = rrect(OW, OH, OR, -mid_off - LAP_GAP/2)      # boundary between halves (back side)
outer_ring_outline = rrect(OW, OH, OR, -mid_off + LAP_GAP/2)      # (front side)

back = body ^ slab(rrect(OW+4, OH+4, OR+2), 0, ZS)                 # everything below split
back = back - cavity
# remove outer half of wall in the lap zone -> back keeps inner tongue
lap_zone_b = slab(rrect(OW+4, OH+4, OR+2), ZS - LAP_H, ZS+.01) - slab(inner_ring_outline, ZS - LAP_H - .1, ZS + .1)
back = back - lap_zone_b

front = body ^ slab(rrect(OW+4, OH+4, OR+2), ZS, Z_TOP+1)
front = front - cavity
# front skirt extends down to ZS-LAP_H as outer half only
skirt = (slab(rrect(OW, OH, OR), ZS - LAP_H, ZS+.01)
         - slab(outer_ring_outline, ZS - LAP_H - .1, ZS + .1))
skirt = skirt ^ body
front = front + skirt
# front also needs the cavity free where the back tongue sits (already open inside)
# screen opening with bezel lip
screen_open = slab(rrect(CW - 2*BEZEL, CH - 2*BEZEL, CR - BEZEL), z_cav1 - .1, Z_TOP + 1)
front = front - screen_open
# chamfer the screen opening edge slightly
cham = M.batch_hull([slab(rrect(CW - 2*BEZEL, CH - 2*BEZEL, CR - BEZEL), Z_TOP - .01, Z_TOP + .5),
                     slab(rrect(CW - 2*BEZEL + 1.6, CH - 2*BEZEL + 1.6, CR - BEZEL + .8), Z_TOP + .5, Z_TOP + .51)])
front = front - cham

# ---- snap detents (bumps on back tongue, grooves in front skirt) -----------
def capsule_x(x, y, z, length, rad):    # bump running along y at x
    return M.cylinder(length, rad, rad, 24).rotate((-90, 0, 0)).translate((x, y - length/2, z))
tx = OW/2 - mid_off - LAP_GAP/2                 # outer face of tongue
for sx in (-1, 1):
    for yy in (-H*0.25, H*0.25):
        bump = capsule_x(sx*tx, yy, ZS - LAP_H/2, 14, .35)
        back = back + (bump ^ slab(rrect(OW, OH, OR), 0, Z_TOP))
        groove = capsule_x(sx*tx, yy, ZS - LAP_H/2, 14.6, .45)
        front = front - groove
# finger-pry notches at bottom seam
for sx in (-1, 1):
    n = M.cube((2.6, 14, 1.2), True).translate((sx*(OW/2), 0, ZS))
    back = back - n.translate((0, 0, -0.6))

# ---- cutouts ----------------------------------------------------------------
def box(cx, cy, cz, sx, sy, sz, r=0.0):
    if r > 0:
        return slab(rrect(sx, sy, r), cz - sz/2, cz + sz/2).translate((cx, cy, 0))
    return M.cube((sx, sy, sz), True).translate((cx, cy, cz))

zc = (z_cav0 + z_cav1)/2
# camera plateau (back, top-left looking at back)  -- adjust to your model
cx, cy, cs, cr = P['cam']
cam = box(-W/2 + cx, H/2 - cy, FLOOR/2, cs, cs, FLOOR*3, cr)
back = back - cam
# USB-C + speaker/mic grilles (bottom edge)  y = -OH/2
bottom_cuts = [box(0, -OH/2, zc, 14.0, WALL*5, 6.8)]
for i in range(6):                          # speaker + mic holes
    for sx in (-1, 1):
        bottom_cuts.append(M.cylinder(WALL*4, 1.0, 1.0, 24).rotate((90, 0, 0))
                           .translate((sx*(10 + i*3.4), -OH/2 + WALL*2, zc)))
for c in bottom_cuts:
    back = back - c
    front = front - c
# side keys (left: action + volume, right: power / camera control)
side_cuts = [
    box(-OW/2, H/2 - P['act'], zc, WALL*5, 8.5, 4.4),     # action button
    box(-OW/2, H/2 - P['volu'], zc, WALL*5, P['volh'], 4.4),    # volume up
    box(-OW/2, H/2 - P['vold'], zc, WALL*5, P['volh'], 4.4),    # volume down
    box(+OW/2, H/2 - P['pwr'], zc, WALL*5, 18.0 if PROFILE=='mini' else 22.0, 4.4),    # side/power
    box(+OW/2, -H/2 + 42, zc, WALL*5, 11.0, 4.4),   # camera control
]
for c in side_cuts:
    back = back - c
    front = front - c

# ---- export -----------------------------------------------------------------
def to_tm(mf):
    mesh = mf.to_mesh()
    return trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)

if __name__ == "__main__":
    import os
    SUF = '' if PROFILE == 'pro' else '_' + PROFILE
    here = os.path.dirname(os.path.abspath(__file__))
    # print orientation: back shell as-is (floor on bed); front shell flipped (bezel plate on bed)
    tb = to_tm(back); tf = to_tm(front)
    tb.export(f"{here}/back_shell{SUF}.stl")
    ff = tf.copy(); ff.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    ff.apply_translation([0, 0, -ff.bounds[0][2]])
    ff.export(f"{here}/front_shell_print{SUF}.stl")
    asm = trimesh.util.concatenate([tb, tf]); asm.export(f"{here}/assembled{SUF}.stl")
    for n, t in (("back", tb), ("front", tf)):
        print(n, "watertight:", t.is_watertight, "volume cm3: %.1f" % (t.volume/1000), "bounds", t.bounds.round(1).tolist())
    print("overall (mm): %.1f x %.1f x %.1f" % (OW, OH, Z_TOP))
