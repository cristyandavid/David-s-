# Safety & WSIB

A machine-readable catalog of common Ontario construction hazards, general
control categories, and high-level safety/WSIB obligations, plus a tool that
prints a pre-work safety briefing and checklist for a given task or phase.

> **This is an organizational aid, NOT legal advice and NOT a compliance
> guarantee.** It exists to prompt hazard assessment and a pre-work safety
> talk. It does not state specific legal thresholds. You must verify every
> requirement against the **current** Occupational Health and Safety Act
> (OHSA), **O. Reg. 213/91 (Construction Projects)**, and **WSIB**, and against
> a competent person / Joint Health and Safety Committee (JHSC) on your site.

| File | What it is |
|------|-----------|
| [`hazards.json`](hazards.json) | Construction tasks/phases mapped to typical hazards and general control categories, each with `VERIFY` flags where a specific legal value is needed. |
| [`requirements.json`](requirements.json) | High-level Ontario safety and WSIB obligations that broadly apply (training, PPE, fall protection, first aid, site notices, WSIB coverage/reporting), each with a `VERIFY` note. |
| [`checklist.py`](checklist.py) | Prints hazards, controls, and a pre-work safety checklist for a task, each line carrying its `VERIFY` notes. Pure stdlib. |

## Use

```bash
python3 checklist.py --list                 # available tasks/phases
python3 checklist.py framing                # briefing for framing work
python3 checklist.py excavation             # briefing for excavation
python3 checklist.py roofing --requirements # briefing + broad Ontario obligations
```

Each briefing has four parts: **typical hazards**, **general control
categories** (in hazard-control-hierarchy order), a **pre-work checklist** to
tick off before starting, and a **VERIFY** section listing exactly what to
confirm against the authoritative source before relying on it.

## What the "VERIFY" flags mean

The single most important design rule of this module: **it never invents a
safety number.** Fall-protection trigger heights, trench-shoring depths, power-
line clearance distances, first-aid kit contents, JHSC worker-count
thresholds, WSIB reporting deadlines, premium rates, and rate groups all change
and are easy to get wrong. Where a specific value matters, the data shows a
`VERIFY: <what to check> - <source>` line **instead of** a number. Treat every
`VERIFY` as a task you must close out against:

- **OHSA** - Occupational Health and Safety Act (general duties, JHSC,
  reporting, violence/harassment).
- **O. Reg. 213/91 (Construction Projects)** - the construction-specific
  regulation (fall protection, guardrails, scaffolds, excavation, formwork,
  hoisting, notices).
- **WSIB** - coverage/registration, premiums, injury reporting, clearance
  certificates.
- Related regulations where noted: O. Reg. 278/05 (Asbestos), O. Reg. 490/09
  (Designated Substances), O. Reg. 632/05 (Confined Spaces), O. Reg. 297/13
  (awareness training), WHMIS, Ontario Electrical Safety Code / ESA, and the
  Ontario Fire Code.

## Accuracy & honesty

- **General duties and hazard/control categories are stated at a broad,
  defensible level** (e.g. "fall protection is required for work at heights",
  "guardrails are the preferred control", "most construction employers must
  carry WSIB coverage"). These are widely correct at that level.
- **No specific numeric thresholds, clause numbers, penalty amounts, or WSIB
  rate/group numbers are asserted.** Anything requiring a specific value is a
  `VERIFY` flag pointing to the source.
- **This is not a hazard assessment.** It is a starting template. A competent
  person must perform a site-specific assessment; site conditions, the specific
  work, and current law govern.
- When in doubt, **verify rather than assume.** A wrong safety figure is worse
  than a prompt to check.

## Extending it

Add a task under `tasks` in `hazards.json` with `label`, `hazards`, `controls`,
and `verify` arrays; `checklist.py` picks it up with no code change. Keep
controls at a general category level and add a `VERIFY` flag for anything that
would require a specific legal threshold. Add broad obligations under
`requirements` in `requirements.json` in the same shape (`label`, `summary`,
`applies_to`, `verify`).
