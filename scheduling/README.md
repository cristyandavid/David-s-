# Ontario residential build scheduling

A machine-readable model of the standard Ontario detached-home build sequence,
plus a tool that runs the Critical Path Method (CPM) over it: topological
sort, forward/backward pass, earliest start/finish per phase, the critical
path, and optional calendar dates.

| File | What it is |
|------|-----------|
| [`phases.json`](phases.json) | The build sequence as a task network: each task has an `id`, `label`, `predecessors`, and a `duration_model` (`fixed` days, or `derived` from a work quantity × crew productivity). |
| [`schedule.py`](schedule.py) | Topological sort + CPM forward/backward pass. Prints an ordered schedule with start day, duration, finish day, slack, and the critical path. Pure stdlib. |

## Use

```bash
python3 schedule.py                            # working-day schedule
python3 schedule.py --start-date 2026-04-06    # calendar dates (weekends skipped)
python3 schedule.py --critical-only            # only the critical-path tasks
python3 schedule.py --phases phases.json       # explicit input file
```

`***` in the `crit` column marks a critical-path task (zero slack): if it
slips, the whole project slips.

## The method, in a sentence

CPM does a **forward pass** in dependency order to find each task's earliest
start/finish (a task starts as soon as all its predecessors finish), then a
**backward pass** to find each task's latest start/finish; tasks with zero
slack (earliest = latest) form the **critical path** — the longest chain that
sets the project duration.

## Where durations come from

Durations are **derived from work, not guessed**:

- `fixed` tasks (permit approval, concrete cure, inspections) are calendar
  waits, not crew output — a plain number of days.
- `derived` tasks compute `duration = ceil(quantity / (crew × productivity))`,
  minimum 1 day. `quantity` is the real work (linear feet of wall, square feet
  of floor, roofing squares…); `crew × productivity` is the daily output.

The **work quantities** in `phases.json` are sized for one reference house
(see `_reference_project`: a 2-storey detached, ~2,000 sq ft, full basement,
~180 ft foundation perimeter). Change them to match your project.

## Assumptions (all tunable)

- **Crew sizes and productivity rates are assumptions**, not measured from your
  crews. Every one is marked `"tunable": true` in `phases.json` with a note.
  They are typical small-builder figures; replace them with your own history
  for a real schedule. (Example baked in: plumbing is the slowest of the three
  parallel rough-ins, so it drives the rough-in window on the reference house.)
- **Sequence** follows the normal residential order: permits → excavation →
  footings → foundation → cure → backfill → framing (floor, walls, roof) →
  sheathing → roofing ∥ windows/doors → rough-ins (elec ∥ plumb ∥ HVAC) →
  rough-in inspection → insulation → drywall → finishes → final inspection.
  Roofing and windows/doors run in parallel; the three rough-ins run in
  parallel. Adjust predecessors for your own overlap/staging.
- **Calendar mode skips weekends only.** Statutory holidays are **not**
  handled — add them yourself. A weekend `--start-date` is bumped to Monday.
- **Queue times are not modelled.** Permit issuance and inspection *booking*
  can add days or weeks; the `fixed` inspection tasks are the on-site time
  only, not the wait for an inspector.

## Treat the output as a planning aid

This computes a **defensible baseline**, not a commitment. It ignores weather,
trade availability, supply lead times, inspection/permit queues, and change
orders. Before you commit dates, verify against **real trade calendars**, the
**municipal inspection queue**, weather windows, and the **Ontario Building
Code**. It does not check spans, loads, or code compliance.

## Extending it

Add a task to the `tasks` list in `phases.json` with an `id`, `label`,
`predecessors` (list of ids), and a `duration_model`; `schedule.py` picks it
up with no code change. Cycles and unknown predecessors are detected and
reported. Split coarse phases (especially `finishes`) into sub-tasks for a
tighter schedule.
