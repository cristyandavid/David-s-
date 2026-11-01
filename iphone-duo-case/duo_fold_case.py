"""Rugged 'construction' hard case for the iPhone Duo (foldable) - two shells, one per half.

Source geometry: Apple "iPhone Duo Dimensional Drawings" (accessory design guidelines, 2026-09-09):
  https://developer.apple.com/download/files/accessories/dimensional-drawings/iphone-duo.pdf
(Apple's public set is 2-D drawings only; no STEP/CAD solid is published. The PDF is NOT redistributed here.)

Closed phone: 84.10 x 117.80 x 11.30 mm. Hinge = LEFT edge (front view). Halves 5.48 mm each.
Each shell wraps ONE half on its 3 free edges (top / bottom / right) and leaves the hinge edge open so
the phone can fold flat to 164.6 mm. Shells never overlap across the seam (0.5 mm gap).

Apple case rules honoured: plastic only (no metal / no magnets), backside case thickness <= 2.1 mm,
front lip covers <= 3.06 mm of the screen border, rear camera plateau + front camera never covered,
button / port openings.  VERIFY every offset against the PDF before production.

Coords (mm): x = width (hinge at -x), y = length (top of phone +y), z = thickness (back glass z=0, front glass z=11.30)
Run: python3 duo_fold_case.py -> duo_back_shell.stl, duo_front_shell_print.stl, duo_closed.stl, duo_open.stl
"""
import os
import numpy as np
import manifold3d as m
from manifold3d import CrossSection as CS, Manifold as M
import trimesh

# ---- product (Apple drawing) -----------------------------------------------
PW, PL, PT = 84.10, 117.80, 11.30
HALF = 5.48                       # thickness of each half
GLASS_TOP = PT
PR = 11.0                         # plan corner radius (approx - verify)
# ---- case ------------------------------------------------------------------
CLR   = 0.30                      # fit clearance per side
WALL  = 2.40                      # rugged side wall
BUMP  = 1.20                      # extra corner bumper
FLOOR_OUT, FLOOR_IN = -1.90, -0.20   # back plate: 1.7 thick, 1.9 total <= 2.1 mm Apple max
SEAM  = HALF + 0.17               # middle of the 0.34 mm product gap (5.65)
GAP   = 0.50                      # shell-to-shell gap (never touch while folding)
Z_BACK_TOP  = SEAM - GAP/2        # 5.40
Z_FRONT_BOT = SEAM + GAP/2        # 5.90
LIP_T = 1.80                      # front bezel plate thickness
LIP_CLR = 0.30                    # lip standoff above the glass (raised bezel protects screen)
Z_FRONT_CAV = GLASS_TOP + LIP_CLR           # 11.60
Z_TOP = Z_FRONT_CAV + LIP_T                 # 13.40
LIP_IN = 2.90                     # lip overlap of screen border (Apple max 3.06)
HINGE_LIP = 5.00                  # lip overlap at hinge edge (Apple max 5.23)
SEG = 96

X = lambda xp: xp - PW/2          # from hinge-edge distance -> centred x
Y = lambda yd: PL/2 - yd          # from top-edge distance -> centred y

def rrect(w, h, r, d=0.0):
    r = max(r + d, 0.2)
    return CS.square((max(w + 2*d - 2*r, .1), max(h + 2*d - 2*r, .1)), center=True).offset(r, m.JoinType.Round, 2.0, SEG)

def slab(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate((0, 0, z0))

def box(x0, x1, y0, y1, z0, z1):
    return M.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

OUT = CLR + WALL
def body(z0, z1, e=1.2):           # outer envelope with softly rounded top/bottom edges
    r = lambda d: rrect(PW, PL, PR, OUT + d)
    return M.batch_hull([slab(r(-e), z0, z0+.01), slab(r(0), z0+e, z1-e), slab(r(-e), z1-.01, z1),
                         slab(r(-e*.45), z0+.3*e, z0+.31*e), slab(r(-e*.45), z1-.31*e, z1-.3*e)])

XL = X(0) - CLR                    # hinge edge: shell plate ends flush with phone (open side)
def clip_hinge(mf):
    return mf - box(XL - 200, XL, -200, 200, -50, 50)

def bumpers(z0, z1):               # chunky corner guards, free-edge corners only
    ring = slab(rrect(PW, PL, PR, OUT + BUMP), z0 + 1.0, z1 - 1.0)
    zone = box(X(PW) - 28, X(PW) + 10, -PL/2 - 10, PL/2 + 10, z0, z1) - box(X(PW) - 40, X(PW) + 20, -PL/2 + 24, PL/2 - 24, z0 - 1, z1 + 1)
    return ring ^ zone

def build_shell(z0, z1, z_cav0, z_cav1):
    s = body(z0, z1) + bumpers(z0, z1)
    s = s - slab(rrect(PW, PL, PR, CLR), z_cav0, z_cav1)
    return clip_hinge(s)

# ---------------- back shell (covers rear half + camera plateau side) -------
back = build_shell(FLOOR_OUT, Z_BACK_TOP, FLOOR_IN, Z_BACK_TOP + 1)
# rear camera plateau window (plateau X 1.06..72.8, Yd 4.7..34.7) + ~0.8 margin, open to hinge edge
win_x0, win_x1 = X(-12), X(73.6)
win_y0, win_y1 = Y(35.5), Y(3.9)
cam = rrect(win_x1 - win_x0, win_y1 - win_y0, 7.4).translate(((win_x0+win_x1)/2, (win_y0+win_y1)/2))
back = back - slab(cam, FLOOR_OUT - 1, FLOOR_IN + 0.1)

# ---------------- front shell (covers outer-display half) -------------------
front = build_shell(Z_FRONT_BOT, Z_TOP, Z_FRONT_BOT - 1, Z_FRONT_CAV)
disp = rrect(PW, PL, PR, -LIP_IN) ^ CS.square((200, 400), center=True).translate((X(HINGE_LIP) + 100, 0))
front = front - slab(disp, Z_FRONT_CAV - .1, Z_TOP + 1)
# chamfer the screen opening so fingers/phone edge swipes are not snagged
cham = M.batch_hull([slab(disp, Z_TOP - .01, Z_TOP + .01),
                     slab(disp.offset(0.9, m.JoinType.Round, 2.0, SEG), Z_TOP + .9, Z_TOP + .91)])
front = front - cham

# ---------------- button & port openings ------------------------------------
TOPY, BOTY, RX = PL/2 + OUT, -PL/2 - OUT, PW/2 + OUT
def notch(shell, which, x0=None, x1=None, y0=None, y1=None, edge=None):
    zr = (0.4, Z_BACK_TOP + 1) if which == "back" else (Z_FRONT_BOT - 1, GLASS_TOP - 0.1)
    if edge == "top":
        c = box(X(x0), X(x1), TOPY - OUT - 0.5, TOPY + 2, *zr)
    elif edge == "bottom":
        c = box(X(x0), X(x1), BOTY - 2, BOTY + OUT + 0.5, *zr)
    else:   # right edge
        c = box(RX - OUT - 0.5, RX + 3, y0, y1, *zr)
    return shell - c

for w in ("back", "front"):
    s = back if w == "back" else front
    s = notch(s, w, 37.9, 64.2, edge="top")                 # volume buttons (centres 44.35 / 57.73, 10.88 wide)
    for a, b in ((15.5, 26.8), (34.5, 51.0), (58.5, 70.0)):  # bottom mic | USB-C | speakers
        s = notch(s, w, a, b, edge="bottom")
    if w == "back":
        back = s
        back = notch(back, "back", y0=Y(54.6), y1=Y(31.6))    # side button / Touch ID (keepout 18.67)
        back = notch(back, "back", y0=Y(103.9), y1=Y(75.5))   # camera control (keepout 28.26 thin case)
    else:
        front = s

# ---------------- export -----------------------------------------------------
def to_tm(mf):
    mesh = mf.to_mesh()
    return trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)

def open_pose(tm_front):           # unfold: rotate front half 180 deg about the hinge axis
    hx = -(164.6 - PW)/2
    T = trimesh.transformations
    M_ = T.translation_matrix([hx, 0, SEAM]) @ T.rotation_matrix(np.pi, [0, 1, 0]) @ T.translation_matrix([-hx, 0, -SEAM])
    f = tm_front.copy(); f.apply_transform(M_); return f

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    tb, tf = to_tm(back), to_tm(front)
    tb.export(f"{here}/duo_back_shell.stl")
    ff = tf.copy(); ff.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    ff.apply_translation([0, 0, -ff.bounds[0][2]]); ff.export(f"{here}/duo_front_shell_print.stl")
    trimesh.util.concatenate([tb, tf]).export(f"{here}/duo_closed.stl")
    trimesh.util.concatenate([tb, open_pose(tf)]).export(f"{here}/duo_open.stl")
    phone = slab(rrect(PW, PL, PR), 0, HALF) + slab(rrect(PW, PL, PR), PT - HALF, PT)
    for n, t, mf in (("back", tb, back), ("front", tf, front)):
        print(f"{n}: watertight={t.is_watertight} vol={t.volume/1000:.1f} cm3 bounds={t.bounds.round(1).tolist()} "
              f"phone-overlap={(phone ^ mf).volume():.3f} mm3")
    print("shell/shell overlap mm3: %.3f" % (back ^ front).volume())
    print("back plate thickness (outer->phone back): %.2f mm (Apple max 2.1)" % -FLOOR_OUT)
