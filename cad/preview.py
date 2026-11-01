"""Render a PNG preview of cad/porch_wall_113.dxf (3D view + outside elevation).

    pip install ezdxf matplotlib
    python3 cad/preview.py
"""

import os

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS = {"FRAMING": "#d9a35f", "FOAM": "#9fb0b0", "STRAPPING": "#e6c58f", "MASONRY": "#a8503c", "STONE": "#b8b2a6"}
ALPHA = {"FRAMING": 1.0, "FOAM": 0.55, "STRAPPING": 1.0, "MASONRY": 1.0, "STONE": 1.0}

doc = ezdxf.readfile(os.path.join(HERE, "porch_wall_113.dxf"))
faces = {}
for e in doc.modelspace().query("3DFACE"):
    pts = [tuple(e.dxf.get(k)) for k in ("vtx0", "vtx1", "vtx2", "vtx3")]
    faces.setdefault(e.dxf.layer, []).append(pts)

fig = plt.figure(figsize=(14, 7))
for n, (elev, azim, title) in enumerate([(22, -62, "3D view (outside, estimated sizes)"),
                                         (0, -90, "Outside elevation")], 1):
    ax = fig.add_subplot(1, 2, n, projection="3d")
    for layer in ("FRAMING", "FOAM", "STRAPPING", "MASONRY", "STONE"):
        if layer in faces:
            ax.add_collection3d(Poly3DCollection(
                faces[layer], facecolor=COLORS[layer], edgecolor="#5a4a35", linewidths=0.2,
                alpha=ALPHA[layer]))
    ax.set_xlim(0, 144); ax.set_ylim(-48, 12); ax.set_zlim(0, 96)
    ax.set_box_aspect((144, 60, 96))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title)
    ax.set_xlabel("inches")
    if n == 2:
        ax.set_yticks([])
    ax.set_zlabel("inches")
fig.suptitle("Project 113 porch wall, pillar and post (sizes assumed)")
fig.tight_layout(rect=(0, 0, 1, 0.94))
out = os.path.join(HERE, "porch_wall_113.png")
fig.savefig(out, dpi=110)
print(out)
