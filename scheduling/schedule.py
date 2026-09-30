#!/usr/bin/env python3
"""Critical-path schedule for an Ontario residential build.

Reads a task network (phases.json), computes each task's duration from its
work quantity and crew productivity, does a topological sort, then a forward
and backward pass (the Critical Path Method) to find earliest start/finish
days and the critical path. Optionally prints calendar dates, skipping
weekends.

Durations are ENGINEERING ESTIMATES, not commitments: they ignore weather,
trade availability, inspection/permit queue times, supply lead times and
change orders. Treat the output as a planning aid and verify against real
trade calendars, the municipal inspection queue and the Ontario Building Code.

Examples:
    python3 schedule.py                              # working-day schedule
    python3 schedule.py --start-date 2026-04-06      # calendar dates (skip weekends)
    python3 schedule.py --critical-only              # only the critical path
    python3 schedule.py --phases phases.json         # explicit input file
"""

import argparse
import datetime
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Data loading + duration model
# ---------------------------------------------------------------------------

def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def duration_days(model):
    """Working-day duration for one task's duration_model.

    fixed:   days as given.
    derived: ceil(quantity / (crew * productivity)), at least 1 day.
    """
    kind = model.get("type")
    if kind == "fixed":
        d = int(model["days"])
        if d < 0:
            raise ValueError("fixed duration cannot be negative")
        return d
    if kind == "derived":
        qty = float(model["quantity"])
        crew = float(model["crew"])
        prod = float(model["productivity"])
        if qty < 0 or crew <= 0 or prod <= 0:
            raise ValueError("derived model needs quantity>=0, crew>0, productivity>0")
        daily = crew * prod
        return max(1, math.ceil(qty / daily))
    raise ValueError(f"unknown duration_model type: {kind!r}")


# ---------------------------------------------------------------------------
# Topological sort (Kahn) with cycle detection
# ---------------------------------------------------------------------------

def topo_sort(tasks):
    """Return task ids in dependency order.

    Raises CycleError listing the tasks stuck in a cycle (or pointing at a
    missing predecessor) if no valid ordering exists.
    """
    ids = {t["id"] for t in tasks}
    preds = {t["id"]: list(t.get("predecessors", [])) for t in tasks}

    # Validate predecessor references up front.
    for tid, plist in preds.items():
        for p in plist:
            if p not in ids:
                raise CycleError(
                    f"task {tid!r} lists unknown predecessor {p!r}", stuck=[tid]
                )

    indeg = {tid: 0 for tid in ids}
    succ = {tid: [] for tid in ids}
    for tid, plist in preds.items():
        for p in plist:
            indeg[tid] += 1
            succ[p].append(tid)

    # Deterministic order: process ready nodes in input order.
    order_index = {t["id"]: i for i, t in enumerate(tasks)}
    ready = sorted([tid for tid in ids if indeg[tid] == 0], key=order_index.get)
    out = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        newly = []
        for m in succ[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                newly.append(m)
        ready.extend(sorted(newly, key=order_index.get))

    if len(out) != len(ids):
        stuck = sorted(tid for tid in ids if tid not in set(out))
        raise CycleError(
            "dependency cycle: these tasks can never start because they "
            "depend on each other (directly or indirectly)",
            stuck=stuck,
        )
    return out


class CycleError(Exception):
    def __init__(self, message, stuck=None):
        super().__init__(message)
        self.stuck = stuck or []


# ---------------------------------------------------------------------------
# CPM forward + backward pass
# ---------------------------------------------------------------------------

def cpm(tasks):
    """Critical Path Method over the task list.

    Returns (order, info) where info[id] is a dict with:
      dur, es, ef, ls, lf, slack, critical, label, predecessors.
    Days are 0-based working-day offsets internally; es/ef are the standard
    CPM values (es = earliest a task can start; ef = es + dur).
    """
    order = topo_sort(tasks)
    by_id = {t["id"]: t for t in tasks}
    preds = {t["id"]: list(t.get("predecessors", [])) for t in tasks}
    succ = {tid: [] for tid in by_id}
    for tid, plist in preds.items():
        for p in plist:
            succ[p].append(tid)

    dur = {tid: duration_days(by_id[tid]["duration_model"]) for tid in by_id}

    # Forward pass, in topological order.
    es, ef = {}, {}
    for tid in order:
        es[tid] = max((ef[p] for p in preds[tid]), default=0)
        ef[tid] = es[tid] + dur[tid]

    project_finish = max(ef.values(), default=0)

    # Backward pass, in reverse topological order.
    ls, lf = {}, {}
    for tid in reversed(order):
        lf[tid] = min((ls[s] for s in succ[tid]), default=project_finish)
        ls[tid] = lf[tid] - dur[tid]

    info = {}
    for tid in order:
        slack = ls[tid] - es[tid]
        info[tid] = {
            "label": by_id[tid].get("label", tid),
            "predecessors": preds[tid],
            "dur": dur[tid],
            "es": es[tid],
            "ef": ef[tid],
            "ls": ls[tid],
            "lf": lf[tid],
            "slack": slack,
            "critical": slack == 0,
        }
    return order, info, project_finish


# ---------------------------------------------------------------------------
# Calendar mapping (skip weekends)
# ---------------------------------------------------------------------------

def add_working_days(base, n):
    """Date that is n working days after `base`.

    n=0 returns `base` if base is a weekday, else the next weekday.
    Weekends (Sat/Sun) are skipped. Holidays are NOT handled.
    """
    d = base
    while d.weekday() >= 5:      # move a weekend start to Monday
        d += datetime.timedelta(days=1)
    steps = n
    while steps > 0:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            steps -= 1
    return d


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_schedule(order, info, project_finish, start_date=None, critical_only=False):
    rows = [tid for tid in order if info[tid]["critical"] or not critical_only]
    # Sort display by earliest start, then original order for ties.
    pos = {tid: i for i, tid in enumerate(order)}
    rows.sort(key=lambda t: (info[t]["es"], pos[t]))

    base = None
    if start_date is not None:
        base = datetime.date.fromisoformat(start_date)
        shifted = add_working_days(base, 0)
        if shifted != base:
            print(f"Note: {start_date} is a weekend; starting Monday {shifted.isoformat()}.")
        base = shifted

    lblw = max((len(info[t]["label"]) for t in rows), default=5)
    if base is None:
        header = f"  {'#':>2}  {'task':<{lblw}}  {'start':>5} {'dur':>4} {'fin':>5}  {'slack':>5}  crit"
    else:
        header = f"  {'#':>2}  {'task':<{lblw}}  {'start date':>10}  {'dur':>4}  {'finish date':>11}  {'slack':>5}  crit"
    print()
    print(header)
    print("  " + "-" * (len(header) - 2))

    for i, tid in enumerate(rows, 1):
        n = info[tid]
        star = "***" if n["critical"] else ""
        if base is None:
            # Present as 1-based inclusive working days.
            start_day = n["es"] + 1
            fin_day = n["ef"]
            print(f"  {i:>2}  {n['label']:<{lblw}}  {start_day:>5} {n['dur']:>4} {fin_day:>5}  {n['slack']:>5}  {star}")
        else:
            start_cal = add_working_days(base, n["es"])
            finish_cal = add_working_days(base, n["ef"] - 1)   # inclusive last working day
            print(f"  {i:>2}  {n['label']:<{lblw}}  {start_cal.isoformat():>10}  {n['dur']:>4}  {finish_cal.isoformat():>11}  {n['slack']:>5}  {star}")

    print()
    crit = [tid for tid in order if info[tid]["critical"]]
    print(f"  Project duration: {project_finish} working days.")
    if base is not None:
        finish_cal = add_working_days(base, project_finish - 1)
        print(f"  Calendar finish (weekends skipped, holidays NOT): {finish_cal.isoformat()}.")
    print(f"  Critical path ({len(crit)} tasks, *** above):")
    print("    " + " -> ".join(crit))
    print()
    print("  Estimate only: durations come from assumed crew sizes and")
    print("  productivity. Verify against real trade availability, weather,")
    print("  and the municipal permit/inspection queue before committing dates.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Critical-path schedule for an Ontario residential build.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--phases", default=os.path.join(HERE, "phases.json"),
                    help="path to the task-network JSON (default: phases.json beside this script)")
    ap.add_argument("--start-date", help="project start, YYYY-MM-DD; prints calendar dates (weekends skipped)")
    ap.add_argument("--critical-only", action="store_true", help="print only the critical-path tasks")
    args = ap.parse_args(argv)

    try:
        data = _load(args.phases)
    except FileNotFoundError:
        ap.error(f"phases file not found: {args.phases}")
    except json.JSONDecodeError as e:
        ap.error(f"phases file is not valid JSON: {e}")

    tasks = data.get("tasks")
    if not tasks:
        ap.error("phases file has no 'tasks' list")

    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        ap.error(f"duplicate task id(s): {', '.join(dupes)}")

    if args.start_date:
        try:
            datetime.date.fromisoformat(args.start_date)
        except ValueError:
            ap.error("--start-date must be YYYY-MM-DD")

    try:
        order, info, project_finish = cpm(tasks)
    except CycleError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if e.stuck:
            print("  Involved tasks: " + ", ".join(e.stuck), file=sys.stderr)
        print("  Fix the predecessors so the network is acyclic, then re-run.", file=sys.stderr)
        return 2
    except (KeyError, ValueError) as e:
        print(f"ERROR: bad task data: {e}", file=sys.stderr)
        return 2

    print_schedule(order, info, project_finish,
                   start_date=args.start_date, critical_only=args.critical_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
