#!/usr/bin/env python3
"""Pre-work safety briefing for Ontario construction tasks.

Given a task/phase name, prints the typical hazards, general control
categories, and a pre-work safety checklist, each carrying its "VERIFY"
notes. It is an ORGANIZATIONAL AID to prompt a hazard assessment and a
pre-work talk - it is NOT legal advice and NOT a compliance guarantee.

Requirements and hazards are stated at a general, defensible level. Anywhere
a specific legal threshold (height, depth, distance, timeframe, dollar
amount, WSIB rate) matters, the output shows a "VERIFY:" line pointing to
the authoritative source (OHSA; O. Reg. 213/91 Construction Projects; WSIB)
instead of asserting a number. Always confirm against the current law and a
competent person / JHSC on site.

Examples:
    # Briefing for a framing crew
    python checklist.py framing

    # Briefing for excavation work
    python checklist.py excavation

    # List available tasks
    python checklist.py --list

    # Also print the broadly-applicable Ontario obligations
    python checklist.py framing --requirements
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def _wrap_bullets(items, indent="    - "):
    return [f"{indent}{it}" for it in items]


def _pre_work_checklist(task_key, task):
    """Build a generic pre-work checklist, tailored with the task's controls.

    The checklist items are procedural prompts (things to confirm before
    work), not legal assertions. Task-specific controls are folded in so the
    crew is reminded of the exact controls that apply to this phase.
    """
    generic = [
        "Site orientation completed for all workers on this task",
        "Task reviewed and a pre-work safety talk / toolbox talk held",
        "Required training confirmed for the work (see VERIFY notes)",
        "Required PPE on hand, inspected, and worn",
        "Hazards above walked and assessed for site-specific conditions",
        "First-aid kit and trained first-aider available on site",
        "Emergency plan / muster point and emergency contacts known",
        "Required site notices/postings in place (see requirements.json)",
        "Equipment and tools inspected before use",
        "Housekeeping and clear access/egress for the work area",
    ]
    control_items = [f"Control in place: {c}" for c in task.get("controls", [])]
    return generic + control_items


def briefing(task_key, show_requirements=False):
    hazards_doc = _load("hazards.json")
    tasks = hazards_doc["tasks"]

    if task_key not in tasks:
        raise KeyError(task_key)

    task = tasks[task_key]
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"SAFETY BRIEFING: {task.get('label', task_key)}")
    lines.append(f"task key: {task_key}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("!! ORGANIZATIONAL AID ONLY - NOT legal advice, NOT a compliance")
    lines.append("!! guarantee. Verify everything against the current OHSA,")
    lines.append("!! O. Reg. 213/91 (Construction Projects), and WSIB, and against a")
    lines.append("!! competent person / JHSC on site.")
    lines.append("")

    lines.append("TYPICAL HAZARDS")
    lines += _wrap_bullets(task.get("hazards", []))
    lines.append("")

    lines.append("GENERAL CONTROL CATEGORIES (hierarchy: eliminate > engineer >")
    lines.append("administrative > PPE)")
    lines += _wrap_bullets(task.get("controls", []))
    lines.append("")

    lines.append("PRE-WORK SAFETY CHECKLIST  (confirm each before starting)")
    for item in _pre_work_checklist(task_key, task):
        lines.append(f"    [ ] {item}")
    lines.append("")

    verify = task.get("verify", [])
    lines.append("VERIFY BEFORE RELYING ON THIS  (do NOT assume the numbers)")
    if verify:
        for v in verify:
            lines.append(f"    * {v}")
    else:
        lines.append("    * (no task-specific VERIFY flags recorded; still confirm")
        lines.append("      applicable requirements against OHSA / O. Reg. 213/91 / WSIB)")
    lines.append("")

    if show_requirements:
        req_doc = _load("requirements.json")
        lines.append("-" * 70)
        lines.append("BROADLY-APPLICABLE ONTARIO OBLIGATIONS (high level)")
        lines.append("-" * 70)
        for _key, req in req_doc["requirements"].items():
            lines.append(f"  {req.get('label', _key)}")
            lines.append(f"      {req.get('summary', '')}")
            v = req.get("verify")
            if v:
                lines.append(f"      {v}")
            lines.append("")

    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pre-work safety briefing for Ontario construction tasks."
    )
    ap.add_argument("task", nargs="?", help="task/phase key (see --list)")
    ap.add_argument("--list", action="store_true", help="list available tasks")
    ap.add_argument(
        "--requirements",
        action="store_true",
        help="also print broadly-applicable Ontario obligations",
    )
    args = ap.parse_args(argv)

    if args.list or not args.task:
        data = _load("hazards.json")
        print("Available tasks/phases:")
        for k, v in data["tasks"].items():
            if k.startswith("_"):
                continue
            print(f"  {k:28s} {v.get('label', '')}")
        print("\nUsage: python checklist.py <task> [--requirements]")
        return 0

    try:
        print(briefing(args.task, show_requirements=args.requirements))
    except KeyError:
        ap.error(f"unknown task {args.task!r}; run --list to see available tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
