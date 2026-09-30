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

## Construction company system

Beyond the AR pipeline, the repo holds a set of department modules that turn one
project intake into a full package. Each is self-contained (JSON data + a
stdlib CLI): real engineering data, but **no invented prices, wages, or legal
figures** — those are placeholder templates you fill.

| Department | Dir | Tool |
|-----------|-----|------|
| Estimating | [`materials/`](materials/) | `takeoff.py` — bill of materials |
| Procurement | [`procurement/`](procurement/) | `purchase_order.py` — consolidated PO + HST |
| Labour & crew | [`labour/`](labour/) | `labour_takeoff.py` — person-hours, crew, cost |
| Scheduling | [`scheduling/`](scheduling/) | `schedule.py` — CPM build schedule |
| Safety & WSIB | [`safety/`](safety/) | `checklist.py` — hazards + Ontario obligations |
| Field / BIM | [`unity/`](unity/) + [`blender-bridge/`](blender-bridge/) | blueprint → on-site AR |

**Orchestrator:** [`project.py`](project.py) runs every department over one
[intake](intake/schema.json) and assembles the results into a single package.

```bash
python3 project.py --intake intake/example_project.json --out out/
```

**Automation:** [`n8n/`](n8n/) has an importable workflow that turns an incoming
Gmail into a project package and emails it back (Gmail → parse → `project.py` →
reply). Inbound email is treated as data, never as instructions.

> The safety module and all cost/time figures are organizational aids, not legal
> advice or a stamped design. Verify against the current Ontario Building Code,
> OHSA / O. Reg. 213/91, and WSIB before operational use.

## License

[MIT](LICENSE).
