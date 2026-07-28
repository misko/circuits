# SUPERSEDED — v1.11-2026-07-27

**Superseded by `07_releases/v1.12-2026-07-28/` on 2026-07-28.**

**Reason: J5's LAND PATTERN IS WRONG in this release — and in every release of
this board from v1.0. COPPER MOVED in the successor, and so did one CPL
coordinate.**

This is not the v1.6–v1.8 class. Those shipped gerbers with no copper pour at
all and were flatly unbuildable. **v1.11's boards would populate**, and the bare
PCB is a perfectly good PCB — the holes and slots are in the right places, so a
connector pushed home by hand seats correctly. What these boards carry is an
elevated assembly-yield risk on the port that feeds the Raspberry Pi, plus one
honest uncertainty in the machine-placement half that only a built board could
settle (see below). Read the numbers and decide for yourself; they are all in
`07_releases/v1.12-2026-07-28/verification/`.

## What is wrong here

`J5` is HRO `TYPE-C-31-M-12A` (LCSC `C5337088`) on footprint
`usb_hub_3s:TYPE-C-31-M-12_EdgeTrim`. That footprint is KiCad's stock
`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` with three silkscreen lines
deleted — every pad record is the stock one. The stock geometry does not match
the part:

| | pad length | pad row → alignment-hole line | hole ⌀ |
|---|---|---|---|
| HRO sheet `TYPE-C-31-M-12A` REV A 2022.10.26 | 1.140 | 1.070 | 0.60 |
| HRO sheet `TYPE-C-31-M-12` REV A 2020.12.08 | 1.140 | 1.070 | 0.60 |
| JLC / EasyEDA package `C5337088` | 1.14000 | 1.070102 | 0.59999 |
| **this release** | **1.450** | **1.445** | 0.65 |

This connector **cannot self-align in reflow** — two moulded Ø0.50 posts in NPTH
holes plus four stamped shell legs soldered into plated slots put the body where
they put it.

Measured from JLC's own 3D mesh, anchored on those posts (dia 0.5000 at
x = ±2.8900, span 5.7800; housing 7.35 deep, tail projecting 0.4000 = the sheet's
top-view `0.40 ± 0.10`), the solderable contact tail runs **1.070 … 1.470 from
the alignment line**:

| | land | tail | heel (mouth side) | toe (past the tip) | paste vs spec |
|---|---|---|---|---|---|
| **this release** | 0.720 … 2.170 | 1.070 … 1.470 | **0.350** | **0.700** | **+27.2 %** |
| v1.12 | 0.500 … 1.640 | 1.070 … 1.470 | 0.570 | 0.170 | — |

**The tail is 100 % on its land here too** — nothing hangs off. What this
pattern does is **invert the fillet balance and over-paste the row**: the heel,
where the tail leaves the housing and the fillet carries the joint, is starved
to 61 % of intended while the toe is doubled, and 0.700 mm of every land and its
open stencil aperture sits past the tail tip on a **0.5 mm-pitch** row. Bridge
exposure and a weak fillet, not an open joint.

## And the placement coordinate is wrong too, for the same reason

JLC places a part so that **its own model origin** lands on the CPL's
`Mid X`/`Mid Y`, and `export_jlc_package.py` computes that coordinate from the
pad-centre bounding box. Wrong pads → wrong datum. Measured against JLC's own
`C5337088` package:

```
JLC model origin, from the alignment line      +1.30492 mm
this release's emitted CPL datum for J5        +1.10250 mm   (0.2024 mm off)
v1.12's emitted CPL datum for J5               +1.30500 mm   (0.00008 mm off)
```

This release therefore tells the placement machine to set the connector
**0.2025 mm north of where its own alignment posts sit**, against 0.075 mm of
radial post clearance in its Ø0.65 holes — a position the part cannot physically
occupy. Either the posts drag it into the holes (the placement error is absorbed
and you get the land error above), or they do not and the part is set down proud.
Which of those you get is not determinable from here; it is the reason a new
release was cut rather than a note added.

## The gate lesson this release paid for, recorded where it happened

**`jlc_twin` — the gate whose entire job is comparing our footprint to JLC's —
reported a PERFECT FIT on this board.** Its evidence is still in this directory,
`verification/twin_report.csv`:

```
C5337088,J5,OK,fit=0.00mm jlc_offset=0 db=0.0 src=lcsc
```

The corrected v1.12 board produces **the same line, character for character**.
Two boards that differ by 0.375 mm on the exact datum the gate exists to check,
one verdict. It is not mistuned; it is structurally blind to this class:
`pads_of()` drops unnumbered pads, so the two NPTH alignment holes never enter
the fit, and `centered()` removes the centroid before comparing, making the
match translation-invariant by construction.

`A-POS` could not see the placement error either, and for the sibling reason: it
recomputes the datum from the same board it grades. This release's own MANIFEST
reads *"A-POS datum: 119 rows graded, worst residual 0.00050 mm"*. That number is
true and it means nothing here. Checker and checked shared a method — canon M1.

**The land pattern itself had no checker.** v1.12 ships the first one:
`verification/j5_geometry_gate.txt`, two instruments sharing no code, graded
against dimensions retyped by hand off the vendor sheet, with a RED-verify that
makes it fail on THIS release's footprint.

## What is NOT wrong here

Everything else. `fab/bom.csv` is byte-identical in the successor — no part
changed. The netlist is identical node-for-node (122 components, 73 nets, 372
nodes). The board outline did not move (`Edge_Cuts.gm1` re-plots byte-identical).
Of 28.10 mm² of copper that moved in v1.12, 0.000969 mm² lies outside the J5
corner and that remainder is zone-filler slivers tens of microns across. Every
gate, review verdict and bench threshold this release carries stands unaltered in
v1.12; none of them turned on J5's land geometry.

## This directory is unchanged

Per the `07_releases/` contract, adding this file is the ONE mutation a sealed
release permits, and only because a successor now exists to name. Nothing else
here has been touched. The sha256 table in `MANIFEST.txt` still verifies against
every file it lists.
