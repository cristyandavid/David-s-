#!/usr/bin/env python3
"""
diff_permits.py

Compares two Toronto Building Permits CSV snapshots and writes a Markdown
change report summarising new, closed, and modified permits.

Usage:
    # Auto-detect: diffs the two most recent snapshots in data/snapshots/
    python scripts/diff_permits.py

    # Explicit files:
    python scripts/diff_permits.py data/snapshots/permits_2026-04-06.csv \
                                   data/snapshots/permits_2026-04-13.csv

Output:
    data/reports/diff_<new-date>.md

Key field used for record identity: APPLICATION_NUMBER
Change detection fields (subset most useful for permit intelligence):
    STATUS, PERMIT_TYPE, DESCRIPTION, WORK_TYPE, WARD_NAME, STREET_NAME,
    CURRENT_USE, PROPOSED_USE, ESTIMATED_COST, ISSUED_DATE, COMPLETED_DATE
"""

import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_DIR = Path(os.getenv("PERMITS_SNAPSHOT_DIR", "data/snapshots"))
REPORTS_DIR = Path(os.getenv("PERMITS_REPORTS_DIR", "data/reports"))

# Primary key in the dataset
KEY_FIELD = "APPLICATION_NUMBER"

# Fields worth tracking for changes (case-insensitive match attempted)
TRACKED_FIELDS = [
    "STATUS",
    "PERMIT_TYPE",
    "DESCRIPTION",
    "WORK_TYPE",
    "WARD_NAME",
    "STREET_NAME",
    "CURRENT_USE",
    "PROPOSED_USE",
    "ESTIMATED_COST",
    "ISSUED_DATE",
    "COMPLETED_DATE",
    "PERMIT_NUM",
]


def load_snapshot(path: Path) -> tuple[list[str], dict[str, dict]]:
    """Load a CSV snapshot. Returns (fieldnames, {key: row_dict})."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    # Normalise field names to upper-case for consistent matching
    normalised = []
    for row in rows:
        normalised.append({k.upper().strip(): v for k, v in row.items()})

    index = {}
    missing_key = 0
    for row in normalised:
        key = row.get(KEY_FIELD, "").strip()
        if key:
            index[key] = row
        else:
            missing_key += 1

    if missing_key:
        print(
            f"  Warning: {missing_key} rows in {path.name} missing '{KEY_FIELD}' — skipped",
            file=sys.stderr,
        )

    upper_fields = [f.upper().strip() for f in fields]
    return upper_fields, index


def detect_changes(
    old_row: dict, new_row: dict
) -> list[tuple[str, str, str]]:
    """Return list of (field, old_value, new_value) for tracked fields that changed."""
    changes = []
    for field in TRACKED_FIELDS:
        old_val = old_row.get(field, "").strip()
        new_val = new_row.get(field, "").strip()
        if old_val != new_val:
            changes.append((field, old_val, new_val))
    return changes


def find_two_latest_snapshots() -> tuple[Path, Path] | None:
    """Return (older, newer) of the two most recent dated snapshot files.

    Returns None when fewer than 2 snapshots exist (first-run baseline case).
    """
    candidates = sorted(SNAPSHOT_DIR.glob("permits_????-??-??.csv"))
    if len(candidates) < 2:
        return None
    return candidates[-2], candidates[-1]


def extract_date_from_path(path: Path) -> str:
    """Extract YYYY-MM-DD from a snapshot filename, or use today."""
    stem = path.stem  # e.g. permits_2026-04-13
    parts = stem.split("_", 1)
    return parts[1] if len(parts) == 2 else datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fmt_row_summary(row: dict) -> str:
    """One-line human-readable summary of a permit row."""
    parts = []
    for field in ["PERMIT_NUM", "APPLICATION_NUMBER", "PERMIT_TYPE", "WORK_TYPE",
                  "STREET_NAME", "WARD_NAME", "STATUS"]:
        val = row.get(field, "").strip()
        if val:
            parts.append(val)
    return " | ".join(parts) if parts else "(no summary fields)"


def build_report(
    old_path: Path,
    new_path: Path,
    old_index: dict,
    new_index: dict,
    fields: list[str],
) -> str:
    old_date = extract_date_from_path(old_path)
    new_date = extract_date_from_path(new_path)

    added_keys = sorted(set(new_index) - set(old_index))
    removed_keys = sorted(set(old_index) - set(new_index))
    common_keys = set(old_index) & set(new_index)

    modified: list[tuple[str, list]] = []
    for key in sorted(common_keys):
        changes = detect_changes(old_index[key], new_index[key])
        if changes:
            modified.append((key, changes))

    lines = [
        f"# Permit Diff: {old_date} → {new_date}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total permits ({old_date}) | {len(old_index):,} |",
        f"| Total permits ({new_date}) | {len(new_index):,} |",
        f"| **New permits** | **{len(added_keys):,}** |",
        f"| **Closed / removed** | **{len(removed_keys):,}** |",
        f"| **Modified records** | **{len(modified):,}** |",
        "",
    ]

    # --- New permits ---
    lines += [f"## New Permits ({len(added_keys):,})", ""]
    if added_keys:
        lines += ["| Application # | Summary |", "|---|---|"]
        for key in added_keys[:200]:
            summary = fmt_row_summary(new_index[key])
            lines.append(f"| `{key}` | {summary} |")
        if len(added_keys) > 200:
            lines.append(f"| … | _{len(added_keys) - 200} more not shown_ |")
    else:
        lines.append("_No new permits._")
    lines.append("")

    # --- Removed permits ---
    lines += [f"## Removed / Closed Permits ({len(removed_keys):,})", ""]
    if removed_keys:
        lines += ["| Application # | Last Known Summary |", "|---|---|"]
        for key in removed_keys[:200]:
            summary = fmt_row_summary(old_index[key])
            lines.append(f"| `{key}` | {summary} |")
        if len(removed_keys) > 200:
            lines.append(f"| … | _{len(removed_keys) - 200} more not shown_ |")
    else:
        lines.append("_No removed permits._")
    lines.append("")

    # --- Modified records ---
    lines += [f"## Modified Records ({len(modified):,})", ""]
    if modified:
        for key, changes in modified[:100]:
            summary = fmt_row_summary(new_index[key])
            lines.append(f"### `{key}` — {summary}")
            lines.append("")
            lines += ["| Field | Before | After |", "|---|---|---|"]
            for field, old_val, new_val in changes:
                lines.append(
                    f"| {field} | {old_val or '_(empty)_'} | {new_val or '_(empty)_'} |"
                )
            lines.append("")
        if len(modified) > 100:
            lines.append(f"_{len(modified) - 100} more modified records not shown._")
            lines.append("")
    else:
        lines.append("_No field-level changes detected._")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) == 3:
        old_path = Path(sys.argv[1])
        new_path = Path(sys.argv[2])
    elif len(sys.argv) == 1:
        result = find_two_latest_snapshots()
        if result is None:
            # First-run baseline: only one snapshot exists, nothing to diff yet.
            candidates = sorted(SNAPSHOT_DIR.glob("permits_????-??-??.csv"))
            run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if candidates:
                run_date = extract_date_from_path(candidates[-1])
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            baseline_report = (
                f"# Permit Baseline: {run_date}\n\n"
                f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"
                "This is the first snapshot. No previous data to diff against.\n"
                "A full diff will be produced on the next weekly run.\n"
            )
            report_path = REPORTS_DIR / f"diff_{run_date}.md"
            report_path.write_text(baseline_report, encoding="utf-8")
            print(f"[diff_permits] First run — baseline report written: {report_path}")
            sys.exit(0)
        old_path, new_path = result
    else:
        print(
            "Usage: diff_permits.py [old_snapshot.csv new_snapshot.csv]",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[diff_permits] comparing:")
    print(f"  OLD: {old_path}")
    print(f"  NEW: {new_path}")

    print("Loading snapshots ...")
    old_fields, old_index = load_snapshot(old_path)
    new_fields, new_index = load_snapshot(new_path)
    print(f"  OLD rows: {len(old_index):,}")
    print(f"  NEW rows: {len(new_index):,}")

    # Use new snapshot's fields for report context
    report = build_report(old_path, new_path, old_index, new_index, new_fields)

    new_date = extract_date_from_path(new_path)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"diff_{new_date}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written: {report_path}")

    # Also print summary to stdout for CI logs
    for line in report.split("\n")[:30]:
        print(line)


if __name__ == "__main__":
    main()
