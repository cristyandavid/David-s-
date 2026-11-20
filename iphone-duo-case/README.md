# iPhone case designs (parametric, 3D-printable)

| Script | Output |
|---|---|
| `duo_fold_case.py` | **iPhone Duo (foldable)** rugged job-site case: `duo_back_shell.stl`, `duo_front_shell_print.stl`, `duo_closed.stl`, `duo_open.stl` |
| `duo_case.py` (`PHONE=pro\|mini`) | Candy-bar iPhone two-shell case |
| `build_blend.py` | Blender scene for the mini case |

## iPhone Duo source data
Dimensions come from Apple's public *iPhone Duo Dimensional Drawings* (2-D, 2026-09-09):
https://developer.apple.com/download/files/accessories/dimensional-drawings/iphone-duo.pdf
Apple publishes no STEP/solid CAD publicly; the PDF is Apple's copyright and is not stored in this repo.

Rules applied from the drawing notes: no metal / no magnets, back-of-phone case thickness <= 2.1 mm (this design: 1.9 mm),
screen-border overlap <= 3.06 mm (2.6 mm), hinge-side overlap <= 5.23 mm (4.0 mm; keeps the whole display active area visible), camera plateau / front camera /
ports / buttons uncovered.

## Print notes
PETG or ABS, 0.2 mm layers, 4 walls. Front shell prints bezel-down (STL already flipped), back shell prints floor-down.
Print the back shell first and test-fit. Unverified: plan corner radius (11 mm assumed), exact button/port offsets.

## Tests
`python3 test_duo_fold_case.py` runs 21 digital checks (watertight, fit vs. Apple drawing, Apple case rules, camera/sensor keep-outs,
button + port openings, fold 0-180 deg collision sweep). They caught and fixed: lip covering display active area, and shells
colliding when unfolded (shells now stop 0.4 mm short of the hinge axis, so the hinge spine itself is uncovered).
These are geometry tests only - a physical print/fit test is still required.
