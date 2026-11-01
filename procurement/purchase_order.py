#!/usr/bin/env python3
"""Consolidated purchase order for Ontario framing jobs.

Builds one purchase order from one or more assembly takeoffs. It reuses the
quantity math in ../materials/takeoff.py (it does NOT re-implement it): each
assembly is run through takeoff(), then identical line items are consolidated
across assemblies into a single order.

Prices are optional and are never invented. Pass a filled-in prices.json
(copy ../materials/prices.example.json) to get unit prices, line totals, a
subtotal, 13% Ontario HST, and a grand total. Without prices you get an
order of quantities only.

Two ways to describe a job:

  1. A job-spec JSON file (recommended for real jobs):

        python3 purchase_order.py --job job.json --prices prices.json

     where job.json looks like:

        {
          "job": "TODO: job name / PO reference",
          "assemblies": [
            { "assembly": "interior_wall_2x4_16oc", "length_ft": 48 },
            { "assembly": "exterior_wall_2x6_16oc", "length_ft": 40 },
            { "assembly": "floor_system_ijoist_16oc", "area_sqft": 1200 }
          ]
        }

  2. Repeatable --add flags on the command line:

        python3 purchase_order.py \\
            --add interior_wall_2x4_16oc:length_ft=48 \\
            --add floor_system_ijoist_16oc:area_sqft=1200

Run `python3 purchase_order.py --list` to see available assemblies.
Quantities are engineering estimates (a shopping list, not a stamped
structural design). Verify against the current Ontario Building Code and
your engineer/designer before ordering or building.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIALS = os.path.join(os.path.dirname(HERE), "materials")

# Reuse the takeoff math from the materials module instead of copying it.
sys.path.insert(0, MATERIALS)
import takeoff as takeoff_mod  # noqa: E402

HST_RATE = 0.13  # Ontario HST


def _dimension(item):
    """Pull the size out of a job item, returning (size, dim_key)."""
    if "length_ft" in item and item["length_ft"] is not None:
        return float(item["length_ft"]), "length_ft"
    if "area_sqft" in item and item["area_sqft"] is not None:
        return float(item["area_sqft"]), "area_sqft"
    raise ValueError(
        f"assembly {item.get('assembly')!r} needs length_ft or area_sqft"
    )


def _parse_add(spec):
    """Parse an --add value like 'interior_wall_2x4_16oc:length_ft=48'."""
    try:
        key, dim = spec.split(":", 1)
        dim_key, value = dim.split("=", 1)
    except ValueError:
        raise ValueError(
            f"bad --add {spec!r}; use assembly:length_ft=NN or assembly:area_sqft=NN"
        )
    dim_key = dim_key.strip()
    if dim_key not in ("length_ft", "area_sqft"):
        raise ValueError(f"bad dimension {dim_key!r} in --add; use length_ft or area_sqft")
    return {"assembly": key.strip(), dim_key: float(value)}


def build_po(items, prices=None):
    """Run every assembly through takeoff() and consolidate the results.

    Returns (lines, subtotal) where lines is a list of dicts sorted by
    component name. subtotal is None when no prices were supplied.
    Each line: {name, qty, unit, unit_price, line_total, sources}.
    """
    # key = (component name, unit) -> accumulator
    consolidated = {}
    order = []  # preserve first-seen order of keys
    for item in items:
        size, _ = _dimension(item)
        if size <= 0:
            raise ValueError(f"size must be positive for {item.get('assembly')!r}")
        # No prices here: we take pure quantities, then price the consolidated
        # totals below so rounding/pricing happens in exactly one place.
        label, _kind, _waste, rows, _total = takeoff_mod.takeoff(item["assembly"], size)
        for name, qty, unit, _cost in rows:
            key = (name, unit)
            if key not in consolidated:
                consolidated[key] = {"qty": 0.0, "sources": []}
                order.append(key)
            consolidated[key]["qty"] += qty
            consolidated[key]["sources"].append(label)

    lines = []
    subtotal = 0.0 if prices else None
    unit_prices = (prices or {}).get("unit_prices", {})
    for key in sorted(order, key=lambda k: k[0].lower()):
        name, unit = key
        qty = consolidated[key]["qty"]
        unit_price, line_total = None, None
        if prices:
            p = unit_prices.get(name)
            if p and p.get("price"):
                unit_price = p["price"]
                line_total = qty * unit_price
                subtotal += line_total
        lines.append({
            "name": name,
            "qty": qty,
            "unit": unit,
            "unit_price": unit_price,
            "line_total": line_total,
            "sources": consolidated[key]["sources"],
        })
    return lines, subtotal


def _fmt_po(job_name, items, lines, subtotal, prices):
    out = []
    out.append("")
    out.append("=" * 72)
    out.append(f"  PURCHASE ORDER   {job_name}")
    out.append("=" * 72)
    out.append("  Assemblies in this order:")
    for item in items:
        size, dim_key = _dimension(item)
        dim = f"{size:g} ft" if dim_key == "length_ft" else f"{size:g} sq ft"
        out.append(f"    - {item['assembly']:<32s} {dim}")
    if prices:
        supplier = prices.get("supplier", "TODO")
        as_of = prices.get("as_of", "TODO")
        currency = prices.get("currency", "CAD")
        out.append("")
        out.append(f"  Supplier: {supplier}   Quote as-of: {as_of}   Currency: {currency}")
    out.append("-" * 72)

    wcol = max((len(l["name"]) for l in lines), default=10)
    if prices:
        header = f"  {'Item':<{wcol}}  {'Qty':>10} {'Unit':<7}  {'Unit $':>10}  {'Line $':>12}"
    else:
        header = f"  {'Item':<{wcol}}  {'Qty':>10} {'Unit':<7}"
    out.append(header)
    out.append("-" * 72)

    for l in lines:
        line = f"  {l['name']:<{wcol}}  {l['qty']:>10.2f} {l['unit']:<7}"
        if prices:
            if l["unit_price"] is not None:
                line += f"  ${l['unit_price']:>9.2f}  ${l['line_total']:>11.2f}"
            else:
                line += f"  {'(no price)':>10}  {'--':>12}"
        out.append(line)

    out.append("-" * 72)
    if prices:
        hst = subtotal * HST_RATE
        grand = subtotal + hst
        pad = wcol + 10 + 1 + 7 + 2  # align money column
        out.append(f"  {'SUBTOTAL (CAD, pre-HST)':<{pad}}  ${subtotal:>11.2f}")
        out.append(f"  {'HST (13% Ontario)':<{pad}}  ${hst:>11.2f}")
        out.append(f"  {'GRAND TOTAL (CAD)':<{pad}}  ${grand:>11.2f}")
        missing = [l["name"] for l in lines if l["unit_price"] is None]
        if missing:
            out.append("")
            out.append("  NOTE: no price for: " + ", ".join(missing))
            out.append("  Grand total EXCLUDES those lines. Fill them in prices.json.")
    else:
        out.append("  (quantities only: pass --prices prices.json for costs, subtotal & HST)")
    out.append("=" * 72)
    out.append("  Estimates only, not a stamped design. Confirm quantities, prices,")
    out.append("  and lead times before ordering. Verify against the Ontario Building Code.")
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Consolidated purchase order from framing assembly takeoffs.",
    )
    ap.add_argument("--job", help="path to a job-spec JSON file")
    ap.add_argument("--add", action="append", default=[], metavar="ASSEMBLY:DIM=VAL",
                    help="add an assembly, e.g. interior_wall_2x4_16oc:length_ft=48")
    ap.add_argument("--prices", help="path to a filled-in prices.json (optional)")
    ap.add_argument("--list", action="store_true", help="list available assemblies")
    args = ap.parse_args(argv)

    if args.list:
        return takeoff_mod.main(["--list"])

    items, job_name = [], "TODO: job name / PO reference"
    if args.job:
        with open(args.job, encoding="utf-8") as fh:
            job = json.load(fh)
        job_name = job.get("job", job_name)
        items.extend(job.get("assemblies", []))
    for spec in args.add:
        try:
            items.append(_parse_add(spec))
        except ValueError as exc:
            ap.error(str(exc))

    if not items:
        ap.error("no assemblies: pass --job job.json and/or --add ASSEMBLY:DIM=VAL (or --list)")

    prices = None
    if args.prices:
        with open(args.prices, encoding="utf-8") as fh:
            prices = json.load(fh)

    try:
        lines, subtotal = build_po(items, prices)
    except (KeyError, ValueError) as exc:
        ap.error(f"could not build PO: {exc}")

    print(_fmt_po(job_name, items, lines, subtotal, prices))
    return 0


if __name__ == "__main__":
    sys.exit(main())
