# Labour & Crew

Labour-hour estimating for the framing assemblies in
[`../materials/assemblies.json`](../materials/assemblies.json). Where the
`materials/` module turns an assembly + a dimension into a **bill of
materials**, this module turns the same assembly + dimension into estimated
**labour-hours, a crew makeup, and (optionally) a labour cost**.

| File | What it is |
|------|-----------|
| [`crew_rates.json`](crew_rates.json) | Productivity factors: labour-hours per lin ft / per sqft, broken into tasks, keyed to the SAME assembly keys as `materials/assemblies.json`, with typical crew composition per assembly. |
| [`wages.example.json`](wages.example.json) | Wage **template** — all zeros on purpose. Copy to `wages.json` and fill with real Ontario pay rates. |
| [`labour_takeoff.py`](labour_takeoff.py) | Computes labour-hours (and base cost, if wages given) from an assembly. Pure stdlib. |

## Use

```bash
python3 labour_takeoff.py --list                                      # what's available
python3 labour_takeoff.py interior_wall_2x4_16oc --length-ft 24       # linear assembly
python3 labour_takeoff.py floor_system_ijoist_16oc --area-sqft 1200   # area assembly
python3 labour_takeoff.py exterior_wall_2x6_16oc --length-ft 40 --wages wages.json  # with cost
python3 labour_takeoff.py exterior_wall_2x6_16oc --length-ft 40 --factor 1.15       # hard-conditions
```

Linear assemblies (walls) take `--length-ft`; area assemblies (floors) take
`--area-sqft` — same convention as `materials/takeoff.py`. The assembly key and
whether it's linear or area are read from `materials/assemblies.json`; the
labour factors come from `crew_rates.json`.

## What the numbers mean

- **Labour-hours are person-hours**, not crew-hours. A crew of N working one
  hour = N labour-hours. Elapsed crew time = total labour-hours / crew size, and
  the tool prints both. Wages are paid per person-hour, so labour-hours are what
  multiply by a wage.
- Each assembly is split into the **tasks** needed to build it (framing,
  sheathing, WRB, insulation, vapour barrier, drywall hanging). Each task has a
  labour-hour factor and a **role split** used to allocate hours (and cost)
  across carpenter / apprentice / labourer.
- `--factor` applies a **site-conditions multiplier** to all hours (default
  1.0). Use ~1.1–1.4 for high walls, cold, tight access, heavy openings.
- **Scope:** carpentry to build the assembly only. **Excluded:** drywall
  taping/mudding/sanding, paint, MEP rough-in, doors/windows/trim, exterior
  cladding, cleanup/mobilization. Those are separate trades or line items.
- This is an **estimate, not a schedule or a payroll.**

## Accuracy & honesty

- **Productivity factors are factual, mid-range estimating figures** of the kind
  published in references like RSMeans and the Craftsman National Construction
  Estimator, given with their ranges in `crew_rates.json`. Productivity is a
  labour fact and does not change by jurisdiction — but **calibrate to your own
  crew's real production before you bid.**
- **Wages are never invented.** `wages.example.json` is all zeros; put real
  Ontario numbers in `wages.json`. Rates are CAD, **base wage only.**
- **Base wage is not your true cost.** Add labour **burden** on top: WSIB
  premium (rate depends on your classification unit — verify current rate with
  WSIB), CPP/EI employer portions, EHT if applicable, vacation pay (ESA minimum
  4%, rising to 6% after 5 years — verify), statutory holiday pay, and any
  benefits/pension/dues. A common all-in burden is roughly 20–40% over base, but
  confirm your own numbers.
- **Verify against current Ontario rules.** Overtime, breaks, and hours-of-work
  must follow the current **Ontario Employment Standards Act (ESA)** (overtime
  is commonly after 44 hrs/week in Ontario — verify). Premiums and coverage
  follow current **WSIB** rules. This module estimates hours and base cost only;
  it does not model overtime, ESA compliance, or WSIB.

## Extending it

Add an assembly to `crew_rates.json` under `linear_assemblies` or
`area_assemblies` using a key that already exists in
`materials/assemblies.json`; give it `tasks` (each with `lh_per_ft` or
`lh_per_sqft` plus a `role_split`) and a `crew`. `labour_takeoff.py` picks it up
with no code change. New roles should also be added to `wages.example.json`.
