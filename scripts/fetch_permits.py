#!/usr/bin/env python3
"""
fetch_permits.py

Fetches the Toronto Building Permits (Active Permits) dataset from the
Toronto Open Data CKAN API and saves a timestamped CSV snapshot.

Usage:
    python scripts/fetch_permits.py

Output:
    data/snapshots/permits_YYYY-MM-DD.csv   — dated snapshot
    data/snapshots/latest.csv               — overwritten each run (for diffing)

Environment variables (optional):
    PERMITS_SNAPSHOT_DIR  — override output directory (default: data/snapshots)
"""

import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CKAN_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
PACKAGE_ID = "building-permits-active-permits"
SNAPSHOT_DIR = Path(os.getenv("PERMITS_SNAPSHOT_DIR", "data/snapshots"))


def ckan_get(endpoint: str, params: dict) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{CKAN_BASE}/{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "permits-sync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} fetching {url}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"Network error fetching {url}: {e.reason}", file=sys.stderr)
        raise


def find_csv_resource(package: dict) -> dict:
    """Return the first active CSV datastore resource in the package."""
    resources = package.get("resources", [])
    # Prefer datastore-active CSV resources
    for r in resources:
        if r.get("datastore_active") and r.get("format", "").upper() == "CSV":
            return r
    # Fallback: any CSV resource
    for r in resources:
        if r.get("format", "").upper() == "CSV":
            return r
    raise RuntimeError(
        f"No CSV resource found in package '{PACKAGE_ID}'. "
        f"Available formats: {[r.get('format') for r in resources]}"
    )


def stream_csv_via_datastore(resource_id: str) -> list[dict]:
    """Page through the CKAN datastore to download all rows."""
    rows = []
    limit = 10_000
    offset = 0
    fields = None

    print(f"  Fetching via datastore (resource_id={resource_id}) ...", flush=True)
    while True:
        data = ckan_get(
            "datastore_search",
            {"resource_id": resource_id, "limit": limit, "offset": offset},
        )
        result = data.get("result", {})

        if fields is None:
            fields = [f["id"] for f in result.get("fields", []) if f["id"] != "_id"]

        batch = result.get("records", [])
        rows.extend(batch)

        total = result.get("total", 0)
        offset += len(batch)
        print(f"  ... {offset}/{total} rows", flush=True)

        if not batch or offset >= total:
            break

    return fields, rows


def stream_csv_via_download(resource: dict) -> tuple[list[str], list[dict]]:
    """Fallback: download the raw CSV file directly."""
    url = resource["url"]
    print(f"  Downloading CSV from {url} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "permits-sync/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        content = resp.read().decode("utf-8-sig", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    fields = reader.fieldnames or []
    return list(fields), rows


def save_snapshot(fields: list[str], rows: list[dict], run_date: str) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = SNAPSHOT_DIR / f"permits_{run_date}.csv"
    latest_path = SNAPSHOT_DIR / "latest.csv"

    def write_csv(path: Path) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    write_csv(dated_path)
    write_csv(latest_path)
    return dated_path


def main() -> None:
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[fetch_permits] run_date={run_date}")

    print(f"Fetching package metadata for '{PACKAGE_ID}' ...")
    meta = ckan_get("package_show", {"id": PACKAGE_ID})
    if not meta.get("success"):
        print("CKAN returned success=false", file=sys.stderr)
        sys.exit(1)

    package = meta["result"]
    resource = find_csv_resource(package)
    print(f"Using resource: {resource.get('name')} (id={resource['id']})")

    if resource.get("datastore_active"):
        fields, rows = stream_csv_via_datastore(resource["id"])
    else:
        fields, rows = stream_csv_via_download(resource)

    print(f"Total rows fetched: {len(rows)}")

    dated_path = save_snapshot(fields, rows, run_date)
    print(f"Saved snapshot: {dated_path}")
    print(f"Saved snapshot: {SNAPSHOT_DIR}/latest.csv")


if __name__ == "__main__":
    main()
