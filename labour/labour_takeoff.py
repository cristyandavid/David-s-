#!/usr/bin/env python3
"""Labour takeoff for Ontario framing assemblies.

Companion to ../materials/takeoff.py. Turns an assembly (from
materials/assemblies.json) plus a dimension into estimated LABOUR-HOURS and a
crew makeup, using the productivity factors in crew_rates.json. With --wages it
also prices the labour.

Labour-hours are PERSON-hours. Elapsed crew time = labour-hours / crew size.
Wages are paid per person-hour, so labour-hours are what multiply by a wage.
These are estimating figures, not a schedule or a payroll; calibrate to your
crew and verify Ontario ESA/WSIB handling separately (see wages.example.json).

Examples:
    # Interior 2x4 wall, 24 ft long
    python labour_takeoff.py interior_wall_2x4_16oc --length-ft 24

    # Exterior 2x6 wall, 40 ft, priced from your filled-in wages.json
    python labour_takeoff.py exterior_wall_2x6_16oc --length-ft 40 --wages wages.json

    # Floor system, 1200 sq ft, with a 1.15 conditions factor
    python labour_takeoff.py floor_system_ijoist_16oc --area-sqft 1200 --factor 1.15

    # List everything available
    python labour_takeoff.py --list
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIALS = os.path.join(HERE, "..", "materials", "assemblies.json")

# labour-hour factor key -> the size it multiplies (linear=length ft, area=sqft)
LH_KEYS = ("lh_per_ft", "lh_per_sqft")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _assembly_kind(assemblies, key):
    """Return 'linear' or 'area' by looking the key up in materials."""
    if key in assemblies.get("linear_assemblies", {}):
        return "linear"
    if key in assemblies.get("area_assemblies", {}):
        return "area"
    raise KeyError(key)


def takeoff(assembly_key, size, factor=1.0, wages=None):
    assemblies = _load(MATERIALS)
    rates = _load(os.path.join(HERE, "crew_rates.json"))

    kind = _assembly_kind(assemblies, assembly_key)          # from materials
    group = "linear_assemblies" if kind == "linear" else "area_assemblies"
    if assembly_key not in rates.get(group, {}):
        raise KeyError(f"{assembly_key} has no factors in crew_rates.json")
    spec = rates[group][assembly_key]

    wage_table = (wages or {}).get("hourly_wages", {})
    rows, total_lh, total_cost = [], 0.0, 0.0
    role_lh = {}                                             # role -> labour-hours
    for task_name, task in spec["tasks"].items():
        per_unit = next((task[k] for k in LH_KEYS if k in task), None)
        if per_unit is None:
            continue
        lh = per_unit * size * factor
        total_lh += lh
        cost = None
        for role, share in task.get("role_split", {}).items():
            role_lh[role] = role_lh.get(role, 0.0) + lh * share
            w = wage_table.get(role, {}).get("wage")
            if wages and w:
                cost = (cost or 0.0) + lh * share * w
        if cost is not None:
            total_cost += cost
        rows.append((task_name, lh, cost))

    crew = spec.get("crew", [])
    crew_size = sum(c.get("count", 1) for c in crew) or 1
    return {
        "label": spec.get("label", assembly_key),
        "kind": kind,
        "factor": factor,
        "rows": rows,
        "total_lh": total_lh,
        "crew": crew,
        "crew_size": crew_size,
        "elapsed_hr": total_lh / crew_size,
        "role_lh": role_lh,
        "total_cost": (total_cost if wages else None),
    }


def _print_list():
    assemblies = _load(MATERIALS)
    rates = _load(os.path.join(HERE, "crew_rates.json"))
    print("Linear assemblies (use --length-ft):")
    for k, v in rates.get("linear_assemblies", {}).items():
        if k.startswith("_"):
            continue
        print(f"  {k:32s} {v.get('label', '')}")
    print("Area assemblies (use --area-sqft):")
    for k, v in rates.get("area_assemblies", {}).items():
        if k.startswith("_"):
            continue
        print(f"  {k:32s} {v.get('label', '')}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ontario framing labour takeoff.")
    ap.add_argument("assembly", nargs="?", help="assembly key (see --list)")
    ap.add_argument("--length-ft", type=float, help="wall length, for linear assemblies")
    ap.add_argument("--area-sqft", type=float, help="floor area, for area assemblies")
    ap.add_argument("--factor", type=float, default=1.0,
                    help="site-conditions multiplier on all hours (default 1.0; hard jobs ~1.1-1.4)")
    ap.add_argument("--wages", help="path to a filled-in wages.json (optional)")
    ap.add_argument("--list", action="store_true", help="list available assemblies")
    args = ap.parse_args(argv)

    if args.list or not args.assembly:
        _print_list()
        return 0

    size = args.length_ft if args.length_ft is not None else args.area_sqft
    if size is None:
        ap.error("give --length-ft (linear) or --area-sqft (area)")
    if size <= 0:
        ap.error("size must be positive")
    if args.factor <= 0:
        ap.error("--factor must be positive")

    wages = None
    if args.wages:
        wages = _load(args.wages)

    try:
        r = takeoff(args.assembly, size, factor=args.factor, wages=wages)
    except KeyError as exc:
        ap.error(f"unknown assembly: {exc}; run --list")

    dim = f"{size:g} ft" if r["kind"] == "linear" else f"{size:g} sq ft"
    factor_note = "" if r["factor"] == 1.0 else f"   (conditions factor x{r['factor']:g})"
    print(f"\n{r['label']}\n{dim}{factor_note}\n")

    wcol = max(len(x[0]) for x in r["rows"])
    print("  Task breakdown (labour-hours = person-hours):")
    for name, lh, cost in r["rows"]:
        line = f"    {name:<{wcol}}  {lh:>8.2f} lh"
        if cost is not None:
            line += f"  ${cost:>10.2f}"
        print(line)

    print(f"\n  {'TOTAL labour-hours (person-hours)':<{wcol}}  {r['total_lh']:>8.2f} lh")
    crew_desc = " + ".join(
        f"{c.get('count', 1)}x {c['role']}" for c in r["crew"]
    ) or "n/a"
    print(f"  Crew: {crew_desc}  ({r['crew_size']} people)")
    print(f"  Elapsed crew time (hours) = {r['total_lh']:.2f} / {r['crew_size']} "
          f"= {r['elapsed_hr']:.2f} hr")

    print("\n  Labour-hours by role (for costing):")
    for role, lh in sorted(r["role_lh"].items(), key=lambda x: -x[1]):
        print(f"    {role:<12}  {lh:>8.2f} lh")

    if r["total_cost"] is not None:
        print(f"\n  {'TOTAL labour cost (CAD, base wage only)':<{wcol}}  "
              f"{'':>8}    ${r['total_cost']:>10.2f}")
        print("  Base wage only: add WSIB, CPP/EI, vacation/stat, burden separately.")
        print("  Verify overtime/ESA handling; this is not payroll.")
    else:
        print("\n  (no wages: pass --wages wages.json for base labour cost)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
