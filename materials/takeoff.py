#!/usr/bin/env python3
"""Material takeoff for Ontario framing assemblies.

Turns an assembly (from assemblies.json) plus a dimension into a bill of
materials. Quantities are engineering estimates from standard framing factors,
with the assembly's waste allowance applied; they are a shopping list, not a
stamped structural design.

Examples:
    # Interior 2x4 wall, 24 ft long
    python takeoff.py interior_wall_2x4_16oc --length-ft 24

    # Exterior 2x6 wall, 40 ft, priced from your filled-in prices.json
    python takeoff.py exterior_wall_2x6_16oc --length-ft 40 --prices prices.json

    # Floor system, 1200 sq ft
    python takeoff.py floor_system_ijoist_16oc --area-sqft 1200

    # List everything available
    python takeoff.py --list
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# factor key -> (quantity unit, whether the item is counted in whole units)
LINEAR_FACTORS = {
    "per_ft":       ("ea", True),
    "extra_per_wall": ("ea", True),
    "plate_runs":   ("lin ft", False),
    "sqft_per_ft":  ("sqft", False),
    "lb_per_ft":    ("lb", False),
}
AREA_FACTORS = {
    "lin_ft_per_sqft": ("lin ft", False),
    "sqft_per_sqft":   ("sqft", False),
    "lb_per_sqft":     ("lb", False),
    "tubes_per_sqft":  ("ea", True),
}


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def _component_qty(factors, comp, size):
    """Return (quantity, unit) for one component given its factor dict."""
    qty, unit = 0.0, None
    for key, (u, _whole) in factors.items():
        if key not in comp:
            continue
        unit = u
        if key == "plate_runs":
            qty += comp[key] * size          # size = wall length (ft)
        elif key == "extra_per_wall":
            qty += comp[key]                 # flat add, e.g. the end stud
        else:
            qty += comp[key] * size          # per-ft or per-sqft factor x size
    return qty, unit


def takeoff(assembly_key, size, prices=None):
    linear = _load("assemblies.json")["linear_assemblies"]
    area = _load("assemblies.json")["area_assemblies"]

    if assembly_key in linear:
        spec, factors, kind = linear[assembly_key], LINEAR_FACTORS, "linear"
    elif assembly_key in area:
        spec, factors, kind = area[assembly_key], AREA_FACTORS, "area"
    else:
        raise KeyError(assembly_key)

    waste = spec.get("waste_allowance", 0.0)
    rows, total = [], 0.0
    for comp_name, comp in spec["components"].items():
        raw, unit = _component_qty(factors, comp, size)
        if unit is None:
            continue
        qty = raw * (1 + waste)
        whole = any(factors[k][1] for k in comp if k in factors)
        if whole:
            qty = math.ceil(qty)
        cost = None
        if prices:
            p = prices.get("unit_prices", {}).get(comp_name)
            if p and p.get("price"):
                cost = qty * p["price"]
                total += cost
        rows.append((comp_name, qty, unit, cost))
    return spec.get("label", assembly_key), kind, waste, rows, (total if prices else None)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ontario framing material takeoff.")
    ap.add_argument("assembly", nargs="?", help="assembly key (see --list)")
    ap.add_argument("--length-ft", type=float, help="wall length, for linear assemblies")
    ap.add_argument("--area-sqft", type=float, help="floor area, for area assemblies")
    ap.add_argument("--prices", help="path to a filled-in prices.json (optional)")
    ap.add_argument("--list", action="store_true", help="list available assemblies")
    args = ap.parse_args(argv)

    if args.list or not args.assembly:
        data = _load("assemblies.json")
        print("Linear assemblies (use --length-ft):")
        for k, v in data["linear_assemblies"].items():
            if k.startswith("_"):
                continue
            print(f"  {k:32s} {v.get('label', '')}")
        print("Area assemblies (use --area-sqft):")
        for k, v in data["area_assemblies"].items():
            if k.startswith("_"):
                continue
            print(f"  {k:32s} {v.get('label', '')}")
        return 0

    size = args.length_ft if args.length_ft is not None else args.area_sqft
    if size is None:
        ap.error("give --length-ft (linear) or --area-sqft (area)")
    if size <= 0:
        ap.error("size must be positive")

    prices = None
    if args.prices:
        with open(args.prices, encoding="utf-8") as fh:
            prices = json.load(fh)

    try:
        label, kind, waste, rows, total = takeoff(args.assembly, size, prices)
    except KeyError:
        ap.error(f"unknown assembly {args.assembly!r}; run --list")

    dim = f"{size:g} ft" if kind == "linear" else f"{size:g} sq ft"
    print(f"\n{label}\n{dim}   (waste allowance {waste:.0%})\n")
    wcol = max(len(r[0]) for r in rows)
    for name, qty, unit, cost in rows:
        line = f"  {name:<{wcol}}  {qty:>10.2f} {unit:<7}"
        if cost is not None:
            line += f"  ${cost:>10.2f}"
        print(line)
    if total is not None:
        print(f"\n  {'TOTAL (CAD, pre-HST)':<{wcol}}  {'':>10} {'':<7}  ${total:>10.2f}")
        print("  Add 13% HST for Ontario.")
    else:
        print("\n  (no prices: pass --prices prices.json for costs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
