# Procurement — consolidated purchase orders

Turns one or more framing assemblies (with dimensions) into a single
consolidated purchase order: quantities, and — if you supply prices — unit
prices, line totals, subtotal, 13% Ontario HST, and a grand total.

It builds directly on the [`materials/`](../materials/) module: it **reuses**
`materials/takeoff.py`'s `takeoff()` for all quantity math (it does not
re-implement it). Pure Python stdlib, no dependencies.

| File | What it is |
|------|-----------|
| [`purchase_order.py`](purchase_order.py) | CLI that runs each assembly through `takeoff()`, consolidates identical line items across assemblies, prices them, and prints a PO. |
| [`suppliers.example.json`](suppliers.example.json) | Supplier info **template** — all placeholder/TODO values. Copy to `suppliers.json` and fill in. |

Prices come from the materials module's price template,
[`materials/prices.example.json`](../materials/prices.example.json): copy it to
`prices.json` and fill in real Ontario quotes.

## Use

List available assemblies (delegates to the materials module):

```bash
python3 purchase_order.py --list
```

Build a PO from a job-spec JSON file:

```bash
python3 purchase_order.py --job job.json                    # quantities only
python3 purchase_order.py --job job.json --prices prices.json   # with cost + HST
```

Or describe the job inline with repeatable `--add ASSEMBLY:DIM=VAL` flags:

```bash
python3 purchase_order.py \
    --add interior_wall_2x4_16oc:length_ft=48 \
    --add exterior_wall_2x6_16oc:length_ft=40 \
    --add floor_system_ijoist_16oc:area_sqft=1200 \
    --prices prices.json
```

`length_ft` is for linear (wall) assemblies; `area_sqft` is for area (floor)
assemblies — same dimensions the materials takeoff uses. `--job` and `--add`
can be combined.

## Example job

`job.json`:

```json
{
  "job": "Lot 12 — main floor",
  "assemblies": [
    { "assembly": "interior_wall_2x4_16oc", "length_ft": 48 },
    { "assembly": "interior_wall_2x4_16oc", "length_ft": 24 },
    { "assembly": "exterior_wall_2x6_16oc", "length_ft": 40 },
    { "assembly": "floor_system_ijoist_16oc", "area_sqft": 1200 }
  ]
}
```

The two interior 2x4 walls above are consolidated into single line items (studs,
plates, drywall, etc. are summed across every assembly that uses them).

## How consolidation works

Each assembly is run through `materials/takeoff.py`'s `takeoff()` to get its
bill of materials. Line items are then merged by `(item name, unit)` and their
quantities summed, so you order each material once. Because countable items
(studs, adhesive tubes) are rounded **up per assembly** inside `takeoff()` — you
can't buy a fraction of a stud for a given wall — the consolidated count is the
sum of those per-wall whole counts.

## Prices, tax & honesty notes

- **Prices are user-supplied and never invented.** Without `--prices`, the PO
  prints quantities only. With `--prices prices.json`, unit prices come solely
  from that file (copy `materials/prices.example.json`, which is all zeros, and
  fill in real Ontario supplier quotes). A line with no price is shown as
  `(no price)` and **excluded** from the subtotal/grand total, with a note.
- **HST is 13% (Ontario)**, applied to the subtotal. Prices are CAD, pre-HST.
- **Suppliers and lead times are placeholders to confirm.**
  `suppliers.example.json` contains only TODO/placeholder values; lead times and
  delivery terms must be confirmed with the supplier before you schedule around
  them.
- **Quantities are estimates, not a stamped design.** They size materials for
  ordering; they do not check spans, loads, fire ratings, or code compliance.
  Verify against the current Ontario Building Code and your engineer/designer
  before ordering or building.
