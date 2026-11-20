"""Digital test suite for duo_fold_case.py (fit, Apple keep-outs, cutouts, fold motion).
Run: python3 test_duo_fold_case.py   (exit code 1 on any FAIL)"""
import sys
import numpy as np
import duo_fold_case as d
from duo_fold_case import M, CS, slab, rrect, box, X, Y, PW, PL, PT, HALF, SEAM, CLR, OUT

results = []
def check(name, ok, detail=""):
    results.append(ok); print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")

back, front = d.back, d.front
vol = lambda a, b: (a ^ b).volume()

# 1. mesh integrity
for n, s in (("back", back), ("front", front)):
    tm = d.to_tm(s)
    check(f"{n}: watertight, positive volume", tm.is_watertight and tm.volume > 0, f"({tm.volume/1000:.1f} cm3)")

# 2. fit around the phone (two halves, hinge-clipped model) + shell separation
phone_b = slab(rrect(PW, PL, d.PR), 0, HALF)
phone_f = slab(rrect(PW, PL, d.PR), PT - HALF, PT)
check("phone halves do not intersect either shell", vol(phone_b + phone_f, back) + vol(phone_b + phone_f, front) < 1e-6)
check("shell-to-shell gap >= 0.4 mm", back.min_gap(front, 1.0) >= 0.4 - 1e-6, f"(min gap {back.min_gap(front, 1.0):.2f} mm)")
check("clearance phone->back shell >= 0.15 mm", phone_b.min_gap(back, 1.0) >= 0.15, f"({phone_b.min_gap(back, 1.0):.2f})")
check("clearance phone->front shell >= 0.15 mm", phone_f.min_gap(front, 1.0) >= 0.15, f"({phone_f.min_gap(front, 1.0):.2f})")

# 3. Apple rules from the drawing notes
check("back-of-phone case thickness <= 2.1 mm", -d.FLOOR_OUT <= 2.1, f"({-d.FLOOR_OUT} mm)")
check("screen-border lip overlap <= 3.06 mm", d.LIP_IN <= 3.06, f"({d.LIP_IN} mm)")
check("hinge-side lip overlap <= 5.23 mm", d.HINGE_LIP <= 5.23, f"({d.HINGE_LIP} mm)")
active = slab(rrect(PW, PL, d.PR, -2.71) ^ CS.square((200, 400), center=True).translate((X(4.13) + 100, 0)), PT, PT + 3)
check("front shell does not cover outer-display active area (2.71 mm border)", vol(active, front) < 1e-6, f"(overlap {vol(active, front):.2f} mm3)")

# 4. imaging keep-outs
plateau = slab(rrect(72.8 - 1.06, 34.7 - 4.7, 7.4).translate(((X(1.06) + X(72.8)) / 2, (Y(4.7) + Y(34.7)) / 2)), 0, 5.72)
check("rear camera plateau + lenses uncovered by back shell", vol(plateau, back) < 1e-6)
r0, ang = 6.07 / 2, np.radians(48.5)       # 97 deg full cone
cone = M.cylinder(4.0, r0, r0 + 4.0 * np.tan(ang), 64).translate((X(73.39), Y(10.62), PT))
check("front-camera 97 deg keep-out cone clear of front shell", vol(cone, front) < 1e-6)

# 5. button / port openings (probe volumes through the walls)
def probe(x0, x1, z0, z1, edge, y0=None, y1=None):
    if edge == "top":    return box(X(x0), X(x1), PL/2 + CLR, PL/2 + OUT, z0, z1)
    if edge == "bottom": return box(X(x0), X(x1), -PL/2 - OUT, -PL/2 - CLR, z0, z1)
    return box(PW/2 + CLR, PW/2 + OUT, y0, y1, z0, z1)
both = back + front   # disjoint, union is fine
probes = {
  "USB-C slot":              probe(38.4, 47.0, 0.6, 11.2, "bottom"),
  "bottom mic holes":        probe(17.78, 24.54, 0.6, 11.2, "bottom"),
  "speaker ports":           probe(60.85, 67.61, 0.6, 11.2, "bottom"),
  "(-) volume button":       probe(44.35 - 5.44, 44.35 + 5.44, 0.6, 11.2, "top"),
  "(+) volume button":       probe(57.73 - 5.44, 57.73 + 5.44, 0.6, 11.2, "top"),
}
for n, p in probes.items():
    check(f"opening clear: {n}", vol(p, both) < 1e-6, f"(blocked {vol(p, both):.2f} mm3)")
side = lambda a, b: probe(0, 0, 0.6, 5.3, "right", Y(b), Y(a))
check("opening clear: side / Touch ID button (back shell)", vol(side(33.6 - 2, 52.6 + 2), back) < 1e-6)
check("opening clear: camera control (back shell)", vol(side(81 - 2, 98.4 + 2), back) < 1e-6)

# 6. fold motion: swing front shell (+ front phone half) 0..180 deg about the hinge axis
HX = d.HX
def swing(mf, a):
    return mf.translate((-HX, 0, -SEAM)).rotate((0, -a, 0)).translate((HX, 0, SEAM))
back_static = back + (phone_b ^ box(HX, 100, -100, 100, -10, 20))
front_move = front + (phone_f ^ box(HX, 100, -100, 100, -10, 20))
worst, worst_a = 0.0, 0
for a in range(0, 181, 5):
    v = vol(swing(front_move, a), back_static)
    if v > worst: worst, worst_a = v, a
check("fold 0->180 deg: no shell/phone collision", worst < 1e-3, f"(worst overlap {worst:.2f} mm3 at {worst_a} deg)")
flat = swing(front, 180)
check("unfolded flat pose: shells do not overlap", vol(flat, back) < 1e-6, f"(overlap {vol(flat, back):.2f} mm3)")
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
