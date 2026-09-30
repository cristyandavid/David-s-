#!/usr/bin/env python3
"""Project orchestrator: one intake -> a full construction project package.

Runs every department module over a single project intake and assembles the
results (estimate, procurement PO, labour, schedule, safety) into one package,
written as JSON and a readable summary. This is the single entry point an
automation (e.g. an n8n Gmail workflow) calls per new project.

Intake is a JSON file (see intake/schema.json and intake/example_project.json):

    {
      "project": "Smith residence",
      "address": "...",
      "start_date": "2026-04-06",
      "site_factor": 1.0,
      "assemblies": [
        {"assembly": "exterior_wall_2x6_16oc", "length_ft": 120},
        {"assembly": "floor_system_ijoist_16oc", "area_sqft": 1000}
      ],
      "prices_file": "materials/prices.json",
      "wages_file": "labour/wages.json"
    }

Usage:
    python3 project.py --intake intake/example_project.json
    python3 project.py --intake intake/example_project.json --out out/

Prices/wages are optional; without them, quantities and hours are reported
without costs. Nothing here invents prices, wages, or legal figures.
"""

import argparse
import datetime
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _dep in ("materials", "labour", "scheduling", "safety", "procurement"):
    sys.path.insert(0, os.path.join(ROOT, _dep))

import takeoff as mat            # materials/takeoff.py
import labour_takeoff as lab     # labour/labour_takeoff.py
import schedule as sch           # scheduling/schedule.py
import checklist as saf          # safety/checklist.py
import purchase_order as pro     # procurement/purchase_order.py

HST_RATE = 0.13  # Ontario


def _size(item):
    if item.get("length_ft") is not None:
        return float(item["length_ft"])
    if item.get("area_sqft") is not None:
        return float(item["area_sqft"])
    raise ValueError(f"assembly {item.get('assembly')!r} needs length_ft or area_sqft")


def _load_optional(path):
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _safety_tasks(assemblies):
    """Map the assemblies in the job to relevant safety briefing keys."""
    keys = ["general_site"]
    for it in assemblies:
        a = it.get("assembly", "").lower()
        if any(w in a for w in ("wall", "floor", "framing")) and "framing" not in keys:
            keys.append("framing")
        if "roof" in a and "roofing" not in keys:
            keys.append("roofing")
    return keys


def build_package(intake):
    assemblies = intake.get("assemblies", [])
    prices = _load_optional(intake.get("prices_file"))
    wages = _load_optional(intake.get("wages_file"))
    factor = float(intake.get("site_factor", 1.0))
    pkg = {
        "project": intake.get("project", "Untitled project"),
        "address": intake.get("address", ""),
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "priced": prices is not None,
        "departments": {},
        "warnings": [],
    }
    dept = pkg["departments"]

    # --- Estimating: per-assembly bill of materials ------------------------
    try:
        est = []
        for it in assemblies:
            label, kind, waste, rows, total = mat.takeoff(it["assembly"], _size(it), prices)
            est.append({
                "assembly": it["assembly"], "label": label, "kind": kind,
                "waste": waste,
                "lines": [{"name": n, "qty": round(q, 2), "unit": u,
                           "cost": (round(c, 2) if c is not None else None)}
                          for n, q, u, c in rows],
                "material_cost": (round(total, 2) if total else None),
            })
        dept["estimating"] = est
    except Exception as exc:  # a bad assembly key shouldn't sink the package
        dept["estimating"] = {"error": f"{type(exc).__name__}: {exc}"}
        pkg["warnings"].append(f"estimating: {exc}")

    # --- Procurement: consolidated purchase order --------------------------
    try:
        lines, subtotal = pro.build_po(assemblies, prices)
        po = {"lines": [{"name": l["name"], "qty": round(l["qty"], 2),
                         "unit": l["unit"],
                         "unit_price": l["unit_price"],
                         "line_total": (round(l["line_total"], 2)
                                        if l["line_total"] is not None else None)}
                        for l in lines]}
        if subtotal is not None:
            hst = subtotal * HST_RATE
            po["subtotal"] = round(subtotal, 2)
            po["hst"] = round(hst, 2)
            po["grand_total"] = round(subtotal + hst, 2)
        dept["procurement"] = po
    except Exception as exc:
        dept["procurement"] = {"error": f"{type(exc).__name__}: {exc}"}
        pkg["warnings"].append(f"procurement: {exc}")

    # --- Labour ------------------------------------------------------------
    labour_days = {}   # schedule task id -> working days, derived from this scope
    try:
        rows, total_lh, total_cost, role_lh = [], 0.0, 0.0, {}
        for it in assemblies:
            r = lab.takeoff(it["assembly"], _size(it), factor, wages)
            total_lh += r["total_lh"]
            if r["total_cost"]:
                total_cost += r["total_cost"]
            for role, lh in r["role_lh"].items():
                role_lh[role] = role_lh.get(role, 0.0) + lh
            rows.append({"assembly": it["assembly"], "label": r["label"],
                         "labour_hours": round(r["total_lh"], 2),
                         "crew_size": r["crew_size"],
                         "cost": (round(r["total_cost"], 2) if r["total_cost"] else None)})
        # Connect labour -> scheduling: turn this project's actual framing hours
        # into working-day durations for the matching schedule tasks, so the
        # timeline reflects the real scope instead of the reference house.
        crew_ref = max((x["crew_size"] for x in rows), default=4)
        HOURS_PER_DAY = 8.0
        wall_lh = sum(x["labour_hours"] for x in rows if "wall" in x["assembly"])
        floor_lh = sum(x["labour_hours"] for x in rows if "floor" in x["assembly"])
        if wall_lh > 0:
            labour_days["framing_walls"] = max(1, math.ceil(wall_lh / (crew_ref * HOURS_PER_DAY)))
        if floor_lh > 0:
            labour_days["framing_floor"] = max(1, math.ceil(floor_lh / (crew_ref * HOURS_PER_DAY)))
        dept["labour"] = {
            "site_factor": factor,
            "assemblies": rows,
            "total_labour_hours": round(total_lh, 2),
            "labour_hours_by_role": {k: round(v, 2) for k, v in role_lh.items()},
            "total_labour_cost": (round(total_cost, 2) if wages else None),
            "note": "Base wages only where priced; WSIB/burden/ESA extra. Person-hours, not crew-hours.",
        }
    except Exception as exc:
        dept["labour"] = {"error": f"{type(exc).__name__}: {exc}"}
        pkg["warnings"].append(f"labour: {exc}")

    # --- Scheduling (whole-house network, scope-informed) ------------------
    try:
        tasks = sch._load(os.path.join(ROOT, "scheduling", "phases.json"))["tasks"]
        # Override reference durations with this project's labour-derived days.
        for t in tasks:
            if t["id"] in labour_days:
                t["duration_model"] = {"type": "fixed", "days": labour_days[t["id"]],
                                       "source": "labour"}
        order, info, finish = sch.cpm(tasks)
        start = intake.get("start_date")
        sched_rows = []
        for tid in order:
            i = info[tid]
            row = {"id": tid, "label": i["label"], "start_day": i["es"] + 1,
                   "duration": i["dur"], "finish_day": i["ef"],
                   "slack": i["slack"], "critical": i["critical"]}
            sched_rows.append(row)
        out = {"tasks": sched_rows, "project_working_days": finish,
               "scope_derived_tasks": sorted(labour_days),
               "critical_path": [info[t]["label"] for t in order if info[t]["critical"]]}
        if start:
            try:
                base = datetime.date.fromisoformat(start)
                out["start_date"] = start
                out["finish_date"] = sch.add_working_days(base, finish - 1).isoformat()
            except ValueError:
                pkg["warnings"].append("scheduling: start_date must be YYYY-MM-DD")
        dept["scheduling"] = out
    except Exception as exc:
        dept["scheduling"] = {"error": f"{type(exc).__name__}: {exc}"}
        pkg["warnings"].append(f"scheduling: {exc}")

    # --- Safety ------------------------------------------------------------
    try:
        keys = _safety_tasks(assemblies)
        dept["safety"] = {
            "disclaimer": "Organizational aid only - NOT legal advice. Verify every "
                          "item against current OHSA, O. Reg. 213/91, and WSIB with a "
                          "competent person / JHSC before use on site.",
            "briefings": {k: saf.briefing(k) for k in keys},
        }
    except Exception as exc:
        dept["safety"] = {"error": f"{type(exc).__name__}: {exc}"}
        pkg["warnings"].append(f"safety: {exc}")

    # --- Project totals (ties the departments into one bottom line) ---------
    po_ = dept.get("procurement", {})
    lab_ = dept.get("labour", {})
    sc_ = dept.get("scheduling", {})
    mat_total = po_.get("grand_total") if isinstance(po_, dict) else None
    lab_total = lab_.get("total_labour_cost") if isinstance(lab_, dict) else None
    totals = {
        "materials_incl_hst": mat_total,
        "labour_base_cost": lab_total,
        "total_labour_hours": lab_.get("total_labour_hours") if isinstance(lab_, dict) else None,
        "schedule_working_days": sc_.get("project_working_days") if isinstance(sc_, dict) else None,
        "schedule_finish_date": sc_.get("finish_date") if isinstance(sc_, dict) else None,
    }
    if mat_total is not None and lab_total is not None:
        totals["project_cost_estimate"] = round(mat_total + lab_total, 2)
        totals["note"] = ("Materials include 13% HST; labour is base wages only "
                          "(WSIB/burden/ESA extra, and HST on labour depends on your "
                          "setup). Estimate for planning, not a quote.")
    pkg["totals"] = totals

    return pkg


def summarize(pkg):
    L = []
    L.append("=" * 72)
    L.append(f"  PROJECT PACKAGE: {pkg['project']}")
    if pkg["address"]:
        L.append(f"  {pkg['address']}")
    L.append(f"  generated {pkg['generated']}   priced: {pkg['priced']}")
    L.append("=" * 72)

    d = pkg["departments"]

    po = d.get("procurement", {})
    if "lines" in po:
        L.append("\nPROCUREMENT (consolidated purchase order)")
        for l in po["lines"]:
            lt = f"  ${l['line_total']:>10.2f}" if l.get("line_total") is not None else ""
            L.append(f"  {l['name']:<34} {l['qty']:>9.2f} {l['unit']:<7}{lt}")
        if "grand_total" in po:
            L.append(f"  {'subtotal':<34} {'':>9} {'':<7}  ${po['subtotal']:>10.2f}")
            L.append(f"  {'HST (13%)':<34} {'':>9} {'':<7}  ${po['hst']:>10.2f}")
            L.append(f"  {'GRAND TOTAL (CAD)':<34} {'':>9} {'':<7}  ${po['grand_total']:>10.2f}")
        else:
            L.append("  (quantities only - add a prices file for costs)")

    lab_ = d.get("labour", {})
    if "total_labour_hours" in lab_:
        L.append("\nLABOUR")
        L.append(f"  total {lab_['total_labour_hours']} person-hours (site factor {lab_['site_factor']})")
        for role, lh in lab_["labour_hours_by_role"].items():
            L.append(f"    {role:<12} {lh:>8.2f} lh")
        if lab_["total_labour_cost"] is not None:
            L.append(f"  base labour cost: ${lab_['total_labour_cost']:.2f} (WSIB/burden extra)")

    sc = d.get("scheduling", {})
    if "project_working_days" in sc:
        L.append("\nSCHEDULE")
        L.append(f"  {sc['project_working_days']} working days"
                 + (f"   {sc.get('start_date')} -> {sc.get('finish_date')}" if sc.get("finish_date") else ""))
        L.append(f"  critical path: {len(sc['critical_path'])} tasks")
        if sc.get("scope_derived_tasks"):
            L.append(f"  durations from this project's labour: {', '.join(sc['scope_derived_tasks'])}")

    sf = d.get("safety", {})
    if "briefings" in sf:
        L.append("\nSAFETY")
        L.append(f"  briefings included: {', '.join(sf['briefings'].keys())}")
        L.append("  " + sf["disclaimer"])

    t = pkg.get("totals", {})
    if t.get("project_cost_estimate") is not None or t.get("total_labour_hours") is not None:
        L.append("\nPROJECT TOTALS")
        if t.get("materials_incl_hst") is not None:
            L.append(f"  materials (incl HST)   ${t['materials_incl_hst']:>12.2f}")
        if t.get("labour_base_cost") is not None:
            L.append(f"  labour (base)          ${t['labour_base_cost']:>12.2f}")
        if t.get("project_cost_estimate") is not None:
            L.append(f"  PROJECT COST ESTIMATE  ${t['project_cost_estimate']:>12.2f}")
        if t.get("total_labour_hours") is not None:
            L.append(f"  {t['total_labour_hours']} labour-hours over {t.get('schedule_working_days')} working days"
                     + (f", finishing {t['schedule_finish_date']}" if t.get("schedule_finish_date") else ""))

    if pkg["warnings"]:
        L.append("\nWARNINGS")
        for w in pkg["warnings"]:
            L.append(f"  ! {w}")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Assemble a full project package from one intake.")
    ap.add_argument("--intake", required=True, help="path to the project intake JSON")
    ap.add_argument("--out", help="directory to write project_package.json + .txt")
    args = ap.parse_args(argv)

    if args.intake == "-":
        intake = json.load(sys.stdin)          # for piping from an automation
    else:
        with open(args.intake, encoding="utf-8") as fh:
            intake = json.load(fh)

    pkg = build_package(intake)
    text = summarize(pkg)

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "project_package.json"), "w", encoding="utf-8") as fh:
            json.dump(pkg, fh, indent=2)
        with open(os.path.join(args.out, "project_package.txt"), "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
