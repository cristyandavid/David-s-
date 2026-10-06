# Tests

Unit tests for the construction-company department math. Pure stdlib
`unittest` — no dependencies.

```bash
python3 -m unittest discover tests
```

## Covered

- **materials** — takeoff quantities (studs round up, plates, waste), unknown-assembly error, area assemblies.
- **labour** — hours positive, role-hours sum to total, elapsed = total/crew, factor scales linearly.
- **scheduling** — `duration_days` (fixed/derived/min-1), CPM on a known diamond (critical path + slack), cycle and unknown-predecessor detection, weekend-skipping calendar.
- **procurement** — line-item consolidation across assemblies.
- **project** — full package builds with no warnings; a bad assembly becomes a warning, not a crash.

## Not covered here

- `blender-bridge/examples/site_anchors.py` `convex_hull` / `layout_line`:
  these live behind `import bpy`, so they can't be imported outside Blender.
  Verified by hand in the math audit; testing them would require extracting the
  pure geometry into a bpy-free module.
- Unity C# `Fraction` / `FtIn` in `SiteAligner.cs`: run through Unity's Test
  Runner (NUnit), not Python. They're currently `private static`; testing them
  would mean exposing them as `internal` with `InternalsVisibleTo`.
