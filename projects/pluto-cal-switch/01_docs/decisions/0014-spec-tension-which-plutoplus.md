---
id: 0014
date: 2026-07-27
status: superseded-by-0015
tags: [spec-tension, mechanical]
---
# 0014 — SPEC TENSION T5: which PlutoPlus? Built to the 34.88 mm midpoint

## Context

The board mates to three of the PlutoPlus's four SMA jacks, so their pitch is a
hard geometric input. Two physical units were measured
(`spf/plutoplus_hardware/README.md`) **and they DIFFER**:

| unit | U7→U12 total span |
|---|---|
| genuine | **35.04 mm** |
| clone | **34.72 mm** |
| difference | **0.32 mm** |

There is also a documented three-way ambiguity in what "Pluto+" names: the
2020/21 Release V1 that the open-hardware plots describe; a genuine vendor V2
respin from ~Sept 2021; and a **2025 knock-off with completely different PCB
artwork** sold as "Pluto+ V2". Anyone buying today most likely has V2 or the
knock-off, not the board the published plots describe. The vendor never
mentioned moving a connector in the V1→V2 respin, and the knock-off's own
layout image shows the same edge with the same port order — so the geometry
PROBABLY carries across, and "probably" is not what you build a rigid mount on.

The pitch RATIOS are solid: two independent extractions of the CAD plot agree
to **0.003 mm** on 12.023 / 11.599 / 11.980 mm, and the design intent is almost
certainly exactly 12.00 / 11.60 / 12.00. It is the ABSOLUTE scale that carries
a residual ~1 %.

**The user has not been asked which unit this board is for.**

## Options

- **Design to the genuine unit (35.04 mm).** A board built for it sits 0.32 mm
  off nominal on a clone — **beyond SMP's ±0.25–0.30 mm float.**
- **Design to the clone (34.72 mm).** Symmetric problem.
- **Ask the user and design to one.** Correct, but the user is absent and this
  blocks the entire floorplan.
- **Design to the 34.88 mm MIDPOINT.** CHOSEN, as **D6**.
- **Make the SMP positions adjustable** (slotted mounts, a flex interposer).
  REJECTED: an edge-launch SMP's position IS the routed board outline; there is
  nothing to slot. It would also put the RF reference plane on a movable part.

## Decision

**Build to the 34.88 mm midpoint — each board sits ±0.16 mm off nominal on
EITHER unit, comfortably inside SMP's ±0.25–0.30 mm radial float.**

Concretely, the three SMP centres are placed at the measured RATIOS scaled to
the midpoint span, NOT at a uniform pitch: the R2→R1 gap is ~0.4 mm tighter
than the outer gaps, and that asymmetry survived an attempt to refute it (a
photogrammetric pass on the protruding BARRELS found near-uniform spacing, but
those barrels stick out ~11 mm and parallax swamps a 3.5 % difference;
re-measured on the SILKSCREEN boxes, which lie flat at equal depth, the CAD
ratios reproduce and uniform pitch is excluded at ~3σ).

**This is an ASSUMPTION MADE IN THE USER'S ABSENCE and it is flagged in the
report.**

## Consequences

- **±0.16 mm of the ±0.25–0.30 mm SMP budget is spent on this assumption
  alone**, before the ±0.49 mm RSS two-board fabrication stack is counted. The
  margin is real but not generous, and it is the strongest reason to answer
  this question rather than live with it.
- **If the user names their unit, the change is a single number in
  `floorplan.yaml`** — the three SMP anchor X coordinates scale from 34.88 mm
  to 35.04 or 34.72. No part changes, no re-route of anything but the three
  launch stubs. **Cheap to reverse, which is why the midpoint is a defensible
  place to wait.**
- **If the user has BOTH units and wants one board to serve both**, the
  midpoint is not merely a compromise — it is the correct answer, and this ADR
  becomes the decision rather than a placeholder.
- **A caliper measurement on the actual unit retires this entirely** and is
  five minutes of work. It should be taken together with the two other physical
  checks this design is waiting on: the **RF axis height above the Pluto's
  PCB** (still not established — ADR-0006) and the **SMA gender** (inferred,
  not cited).
- The `pluto-plus-mechanical.md` uncertainty analysis reached the same place
  from the other direction: for a rigid mount ±0.5 mm of accumulated position
  error is fatal, and the whole reason SMP was chosen is that it absorbs an
  error of this size. **D6 is what that float is being SPENT on** — it should
  not also be spent on sloppy fabrication tolerances elsewhere.

## Superseded — 2026-07-27, by ADR-0015 (user directive A8)

**D6 is RETIRED, not answered — and that is a strictly better outcome than an
answer would have been.** With SMA cables between the two boards
(ADR-0015), this board's connector positions are not referenced to the
PlutoPlus's at all. There is no midpoint to build to, no ±0.16 mm of SMP float
to spend on an unanswered question, and no floorplan number that has to change
if the user later names their unit.

The consequence worth carrying forward: **the 0.32 mm disagreement between two
units both sold as "PlutoPlus" — the headline finding of
`spf/plutoplus_hardware/` and the reason M-IMPORT exists — now costs this
design NOTHING.** A cabled board fits the genuine unit, the clone, and any
future revision, because it is referenced to none of them. That is the
strongest resolution a spec tension can get: not a decision under uncertainty,
but a design that stops consuming the uncertain quantity.

The three-way ambiguity in what "Pluto+" names (2020/21 V1, a genuine ~Sept
2021 V2 respin, a 2025 knock-off with different artwork) is unchanged and
remains recorded in the device record. It is simply no longer this board's
problem.
