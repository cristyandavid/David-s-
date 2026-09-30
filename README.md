# SiteXR — blueprints to on-site AR

Build a model from a construction drawing, then stand on the job site and see it
overlaid full-size on the real slab, anchored to two marks you can measure
against the plan.

The pipeline has two halves:

| Directory | Runs on | What it does |
|-----------|---------|--------------|
| [`blender-bridge/`](blender-bridge/) | Your computer (with Blender) | Build a model, add two site control points (CP_A / CP_B), and export it AR-ready (USDZ / GLB / FBX) at real-world scale. |
| [`unity/`](unity/) | A phone or tablet (AR Foundation: iOS + Android) | Two-point site alignment: aim at two real marks, and the model's CP_A / CP_B snap onto them. Measured distance is checked against the plan. |

## The flow

1. **Model** — build in Blender, or run [`blender-bridge/examples/stud_wall.py`](blender-bridge/examples/stud_wall.py).
2. **Anchor** — run [`site_anchors.py`](blender-bridge/examples/site_anchors.py) to place CP_A / CP_B on the layout line (for a wall, the chalk line along the bottom plate).
3. **Export** — run [`export_ar.py`](blender-bridge/examples/export_ar.py): origin at CP_A, CP_A → CP_B along +X, real-world scale.
4. **Place on site** — open the model in the Unity [`SiteAligner`](unity/SiteXR/Runtime/SiteAligner.cs): aim at real mark A, tap; aim at mark B, tap. The overlay locks to an AR anchor and reports plan vs. measured distance.

## Getting started

- **Blender side:** [`blender-bridge/README.md`](blender-bridge/README.md) — one-command setup, and an optional Claude ↔ Blender bridge for driving Blender from Claude Code.
- **Unity side:** [`unity/README.md`](unity/README.md) — importing the exported model and wiring up the site aligner.

Ready-made stud-wall exports (with control points) are in
[`blender-bridge/examples/ar/`](blender-bridge/examples/ar/) — on an iPhone or
iPad, open `stud_wall.usdz` and view it full size.

## License

[MIT](LICENSE).
