# Digital Ontario materials & takeoff

A machine-readable catalog of Ontario construction materials and framing
assemblies, plus a tool that turns an assembly + a dimension into a bill of
materials.

| File | What it is |
|------|-----------|
| [`lumber.json`](lumber.json) | Materials catalog: SPF dimensional lumber (nominal ↔ actual), engineered lumber, sheet goods, fasteners, insulation/barriers. |
| [`assemblies.json`](assemblies.json) | Framing assemblies with takeoff factors (interior 2x4 wall, exterior 2x6 wall, I-joist floor). |
| [`prices.example.json`](prices.example.json) | Price **template** — all zeros on purpose. Copy to `prices.json` and fill with real supplier quotes. |
| [`takeoff.py`](takeoff.py) | Computes a bill of materials (and cost, if priced) from an assembly. Pure stdlib. |

## Use

```bash
python3 takeoff.py --list                                   # what's available
python3 takeoff.py interior_wall_2x4_16oc --length-ft 24    # linear assembly
python3 takeoff.py floor_system_ijoist_16oc --area-sqft 1200  # area assembly
python3 takeoff.py exterior_wall_2x6_16oc --length-ft 40 --prices prices.json  # with cost
```

Linear assemblies (walls) take `--length-ft`; area assemblies (floors) take
`--area-sqft`. Wall height and insulation are baked into each assembly's factors.

## What the numbers mean

- Quantities come from **standard framing rules of thumb** (e.g. studs at
  `12/16` per foot at 16" O.C., plus an end stud; plates = 3× wall length for a
  bottom + double top plate) with the assembly's **waste allowance** applied.
  Countable items (studs, adhesive tubes) round **up** to whole units.
- This is a **shopping list, not a structural design.** It sizes materials for
  ordering; it does not check spans, loads, fire ratings, or code compliance.

## Accuracy & honesty

- **Dimensions and sizes are factual** — SPF actuals, standard 4×8 sheets,
  precut stud lengths.
- **Prices are not included** and are never invented. `prices.example.json` is
  all zeros; put real Ontario supplier numbers in `prices.json`. Prices are CAD,
  pre-HST (add 13% for Ontario).
- **Verify against the current Ontario Building Code** (OBC — e.g. SB-12 for
  insulation/energy) and your designer/engineer before ordering or building.

## Extending it

Add an assembly to `assemblies.json` under `linear_assemblies` (per-foot
factors) or `area_assemblies` (per-square-foot factors); `takeoff.py` picks it
up with no code change. New component names should also be added to
`prices.example.json` so they can be priced.
